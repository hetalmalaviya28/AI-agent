# -*- coding: utf-8 -*-
"""
VidyAI - Main Flask Application
Production-style AI Education Platform for Gujarat government schools.
"""
import os
import sys
import json
import hashlib
import functools
from pathlib import Path

# Force UTF-8 output on Windows so print() handles unicode characters
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from flask import (
    Flask, render_template, request, jsonify,
    session, redirect, url_for, Response, stream_with_context
)
from flask_cors import CORS
from dotenv import load_dotenv

from database import (
    init_db, create_user, get_user_by_email, get_user_by_id,
    create_conversation, get_conversations, get_conversation,
    rename_conversation, delete_conversation, touch_conversation,
    add_message, get_messages,
    get_student_progress, upsert_progress,
    save_lesson_plan, get_lesson_plans,
    save_assessment, get_assessments, get_assessment_by_id,
    get_resources, new_id
)
from ai_engine import chat_stream, chat_sync

# ──────────────────────────────
#  Bootstrap
# ──────────────────────────────

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("SECRET_KEY", "vidyai-dev-secret-change-in-production")
CORS(app, supports_credentials=True)

# Initialize DB on startup
init_db()

# ──────────────────────────────
#  Auth helpers
# ──────────────────────────────

def hash_password(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()


def login_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"error": "Authentication required", "redirect": "/login"}), 401
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated


def teacher_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required"}), 401
        user = get_user_by_id(session["user_id"])
        if not user or user["role"] not in ("teacher", "admin"):
            return jsonify({"error": "Teacher access required"}), 403
        return f(*args, **kwargs)
    return decorated


def current_user():
    uid = session.get("user_id")
    if uid:
        return get_user_by_id(uid)
    return None


# ──────────────────────────────
#  Page routes
# ──────────────────────────────

@app.route("/")
def index():
    user = current_user()
    if user:
        if user["role"] == "teacher":
            return redirect(url_for("teacher_dashboard"))
        return redirect(url_for("student_dashboard"))
    return redirect(url_for("login_page"))


@app.route("/login")
def login_page():
    if current_user():
        return redirect(url_for("index"))
    return render_template("login.html")


@app.route("/register")
def register_page():
    if current_user():
        return redirect(url_for("index"))
    return render_template("register.html")


@app.route("/chat")
@login_required
def chat_page():
    user = current_user()
    return render_template("chat.html", user=user)


@app.route("/student")
@login_required
def student_dashboard():
    user = current_user()
    return render_template("student_dashboard.html", user=user)


@app.route("/teacher")
@login_required
def teacher_dashboard():
    user = current_user()
    return render_template("teacher_dashboard.html", user=user)


@app.route("/resources")
@login_required
def resources_page():
    user = current_user()
    return render_template("resources.html", user=user)


@app.route("/assessments")
@login_required
def assessments_page():
    user = current_user()
    return render_template("assessments.html", user=user)


@app.route("/lesson-plans")
@login_required
def lesson_plans_page():
    user = current_user()
    return render_template("lesson_plans.html", user=user)


# ──────────────────────────────
#  Auth API
# ──────────────────────────────

@app.route("/api/auth/login", methods=["POST"])
def api_login():
    data = request.get_json(force=True)
    email = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "").strip()

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    user = get_user_by_email(email)
    if not user:
        return jsonify({"error": "Invalid email or password."}), 401

    if user["password"] != hash_password(password) and user["password"] != password:
        return jsonify({"error": "Invalid email or password."}), 401

    session["user_id"] = user["id"]
    session.permanent = True

    return jsonify({
        "success": True,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "class_grade": user["class_grade"],
        },
        "redirect": "/teacher" if user["role"] == "teacher" else "/student",
    })


@app.route("/api/auth/register", methods=["POST"])
def api_register():
    data = request.get_json(force=True)
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "").strip()
    role = (data.get("role") or "student").strip()
    class_grade = (data.get("class_grade") or "").strip() or None

    if not name or not email or not password:
        return jsonify({"error": "Name, email, and password are required."}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400
    if get_user_by_email(email):
        return jsonify({"error": "An account with this email already exists."}), 409

    uid = create_user(name, email, hash_password(password), role, class_grade)
    session["user_id"] = uid

    return jsonify({
        "success": True,
        "redirect": "/teacher" if role == "teacher" else "/student",
    })


@app.route("/api/auth/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"success": True, "redirect": "/login"})


@app.route("/api/auth/me")
def api_me():
    user = current_user()
    if not user:
        return jsonify({"error": "Not authenticated"}), 401
    return jsonify({
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "class_grade": user["class_grade"],
    })


# ──────────────────────────────
#  Conversations API
# ──────────────────────────────

@app.route("/api/conversations", methods=["GET"])
@login_required
def api_get_conversations():
    user = current_user()
    convs = get_conversations(user["id"])
    return jsonify(convs)


@app.route("/api/conversations", methods=["POST"])
@login_required
def api_create_conversation():
    user = current_user()
    data = request.get_json(force=True)
    mode = data.get("mode", "general")
    title = data.get("title", "New Chat")
    cid = create_conversation(user["id"], title, mode)
    return jsonify({"id": cid, "title": title, "mode": mode})


@app.route("/api/conversations/<cid>", methods=["GET"])
@login_required
def api_get_conversation(cid):
    user = current_user()
    conv = get_conversation(cid)
    if not conv or conv["user_id"] != user["id"]:
        return jsonify({"error": "Conversation not found"}), 404
    messages = get_messages(cid)
    return jsonify({"conversation": conv, "messages": messages})


@app.route("/api/conversations/<cid>", methods=["PATCH"])
@login_required
def api_update_conversation(cid):
    user = current_user()
    conv = get_conversation(cid)
    if not conv or conv["user_id"] != user["id"]:
        return jsonify({"error": "Conversation not found"}), 404
    data = request.get_json(force=True)
    title = data.get("title")
    if title:
        rename_conversation(cid, title.strip())
    return jsonify({"success": True})


@app.route("/api/conversations/<cid>", methods=["DELETE"])
@login_required
def api_delete_conversation(cid):
    user = current_user()
    conv = get_conversation(cid)
    if not conv or conv["user_id"] != user["id"]:
        return jsonify({"error": "Conversation not found"}), 404
    delete_conversation(cid)
    return jsonify({"success": True})


# ──────────────────────────────
#  Chat (Streaming) API
# ──────────────────────────────

@app.route("/api/chat", methods=["POST"])
@login_required
def api_chat():
    user = current_user()
    data = request.get_json(force=True)

    user_message = (data.get("message") or "").strip()
    conversation_id = data.get("conversation_id")
    mode = data.get("mode", "general")

    if not user_message:
        return jsonify({"error": "Message cannot be empty."}), 400

    # Create or validate conversation
    if conversation_id:
        conv = get_conversation(conversation_id)
        if not conv or conv["user_id"] != user["id"]:
            conversation_id = None

    if not conversation_id:
        # Auto-title from first message (truncate to 50 chars)
        title = user_message[:50] + ("..." if len(user_message) > 50 else "")
        conversation_id = create_conversation(user["id"], title, mode)

    # Fetch history
    history = get_messages(conversation_id)

    # Save user message
    add_message(conversation_id, "user", user_message)

    # Stream AI response
    full_response = []

    def generate():
        for chunk in chat_stream(mode, history, user_message):
            # Collect chunks to save to DB after stream ends
            if '"done": true' not in chunk and '"done": false' in chunk:
                try:
                    payload = json.loads(chunk[6:].strip())  # strip "data: "
                    full_response.append(payload.get("chunk", ""))
                except Exception:
                    pass
            yield chunk
        # Save assistant message after stream completes
        complete = "".join(full_response)
        if complete:
            add_message(conversation_id, "assistant", complete)
            touch_conversation(conversation_id)

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "X-Conversation-Id": conversation_id,
        }
    )


# ──────────────────────────────
#  Student Progress API
# ──────────────────────────────

@app.route("/api/progress", methods=["GET"])
@login_required
def api_get_progress():
    user = current_user()
    progress = get_student_progress(user["id"])
    return jsonify(progress)


@app.route("/api/progress", methods=["POST"])
@login_required
def api_update_progress():
    user = current_user()
    data = request.get_json(force=True)
    subject = data.get("subject", "")
    topic = data.get("topic", "")
    score = float(data.get("score", 0))
    status = data.get("status", "in_progress")
    if subject and topic:
        upsert_progress(user["id"], subject, topic, score, status)
    return jsonify({"success": True})


# ──────────────────────────────
#  Assessments API
# ──────────────────────────────

@app.route("/api/assessments", methods=["GET"])
@login_required
def api_get_assessments():
    user = current_user()
    assessments = get_assessments(user["id"])
    return jsonify(assessments)


@app.route("/api/assessments/generate", methods=["POST"])
@login_required
def api_generate_assessment():
    user = current_user()
    data = request.get_json(force=True)

    class_grade = data.get("class_grade", "7")
    subject = data.get("subject", "Mathematics")
    topic = data.get("topic", "")
    num_questions = min(int(data.get("num_questions", 5)), 20)
    difficulty = data.get("difficulty", "medium")
    q_type = data.get("question_type", "mcq")

    if not topic:
        return jsonify({"error": "Topic is required."}), 400

    prompt = (
        f"Generate {num_questions} {q_type.upper()} questions for Class {class_grade} {subject} on the topic: '{topic}'. "
        f"Difficulty: {difficulty}. "
        f"Format each question exactly as specified in your assessment mode instructions. "
        f"Include correct answers and explanations."
    )

    ai_response = chat_sync("assessment", [], prompt)

    title = f"{subject} – {topic} ({class_grade})"
    questions_data = [{"content": ai_response, "type": q_type}]
    aid = save_assessment(user["id"], title, subject, topic, class_grade, difficulty, questions_data)

    return jsonify({
        "id": aid,
        "title": title,
        "content": ai_response,
        "subject": subject,
        "topic": topic,
        "class_grade": class_grade,
        "difficulty": difficulty,
    })


@app.route("/api/assessments/<aid>", methods=["GET"])
@login_required
def api_get_assessment(aid):
    assessment = get_assessment_by_id(aid)
    if not assessment:
        return jsonify({"error": "Assessment not found"}), 404
    return jsonify(assessment)


# ──────────────────────────────
#  Lesson Plans API
# ──────────────────────────────

@app.route("/api/lesson-plans", methods=["GET"])
@login_required
def api_get_lesson_plans():
    user = current_user()
    plans = get_lesson_plans(user["id"])
    return jsonify(plans)


@app.route("/api/lesson-plans/generate", methods=["POST"])
@login_required
def api_generate_lesson_plan():
    user = current_user()
    data = request.get_json(force=True)

    class_grade = data.get("class_grade", "7")
    subject = data.get("subject", "")
    topic = data.get("topic", "")
    duration = data.get("duration", "45 minutes")
    objectives = data.get("objectives", "")
    difficulty = data.get("difficulty", "medium")

    if not subject or not topic:
        return jsonify({"error": "Subject and topic are required."}), 400

    prompt = (
        f"Create a complete, detailed lesson plan for:\n"
        f"Class: {class_grade}\nSubject: {subject}\nTopic: {topic}\n"
        f"Duration: {duration}\nDifficulty: {difficulty}\n"
        f"Learning Objectives: {objectives if objectives else 'Standard curriculum objectives'}\n\n"
        f"Follow the lesson plan format exactly as specified in your instructions."
    )

    content = chat_sync("lesson_planner", [], prompt)
    title = f"{subject} – {topic} (Class {class_grade})"
    content_dict = {"markdown": content}
    lid = save_lesson_plan(user["id"], title, class_grade, subject, topic, duration, content_dict)

    return jsonify({
        "id": lid,
        "title": title,
        "content": content,
        "class_grade": class_grade,
        "subject": subject,
        "topic": topic,
        "duration": duration,
    })


# ──────────────────────────────
#  Resources API
# ──────────────────────────────

@app.route("/api/resources", methods=["GET"])
@login_required
def api_get_resources():
    subject = request.args.get("subject")
    class_grade = request.args.get("class_grade")
    topic = request.args.get("topic")
    resources = get_resources(subject, class_grade, topic)
    return jsonify(resources)


# ──────────────────────────────
#  Analytics API
# ──────────────────────────────

@app.route("/api/analytics/student", methods=["GET"])
@login_required
def api_student_analytics():
    user = current_user()
    progress = get_student_progress(user["id"])

    if not progress:
        return jsonify({
            "overall_score": 0,
            "strong_topics": [],
            "weak_topics": [],
            "total_topics": 0,
            "completed": 0,
            "in_progress": 0,
            "progress": [],
        })

    scores = [p["score"] for p in progress if p["score"] is not None]
    overall = round(sum(scores) / len(scores), 1) if scores else 0

    strong = [p for p in progress if p["score"] and p["score"] >= 70]
    weak = [p for p in progress if p["score"] and p["score"] < 60]
    completed = [p for p in progress if p["status"] == "completed"]
    in_progress = [p for p in progress if p["status"] == "in_progress"]

    return jsonify({
        "overall_score": overall,
        "strong_topics": strong,
        "weak_topics": weak,
        "total_topics": len(progress),
        "completed": len(completed),
        "in_progress": len(in_progress),
        "progress": progress,
    })


@app.route("/api/analytics/teacher", methods=["GET"])
@login_required
def api_teacher_analytics():
    from database import get_db
    conn = get_db()

    students = conn.execute("SELECT COUNT(*) as c FROM users WHERE role='student'").fetchone()["c"]
    teachers = conn.execute("SELECT COUNT(*) as c FROM users WHERE role='teacher'").fetchone()["c"]
    assessments = conn.execute("SELECT COUNT(*) as c FROM assessments").fetchone()["c"]
    lesson_plans = conn.execute("SELECT COUNT(*) as c FROM lesson_plans").fetchone()["c"]

    # Progress overview
    all_progress = conn.execute("SELECT * FROM learning_progress").fetchall()
    weak_students_set = set()
    topic_scores = {}

    for p in all_progress:
        t = p["topic"]
        if t not in topic_scores:
            topic_scores[t] = []
        topic_scores[t].append(p["score"] or 0)
        if (p["score"] or 0) < 60:
            weak_students_set.add(p["student_id"])

    # Common weak topics (avg score < 60)
    weak_topics = []
    for t, scores in topic_scores.items():
        avg = sum(scores) / len(scores)
        if avg < 60:
            weak_topics.append({"topic": t, "avg_score": round(avg, 1)})
    weak_topics.sort(key=lambda x: x["avg_score"])

    # Recent students
    recent_students = conn.execute(
        "SELECT name, class_grade, created_at FROM users WHERE role='student' ORDER BY created_at DESC LIMIT 5"
    ).fetchall()

    conn.close()

    return jsonify({
        "total_students": students,
        "total_teachers": teachers,
        "total_assessments": assessments,
        "total_lesson_plans": lesson_plans,
        "students_needing_support": len(weak_students_set),
        "weak_topics": weak_topics[:5],
        "recent_students": [dict(s) for s in recent_students],
    })


# ──────────────────────────────
#  AI Recommendations API
# ──────────────────────────────

@app.route("/api/recommendations", methods=["GET"])
@login_required
def api_recommendations():
    user = current_user()
    progress = get_student_progress(user["id"])

    if not progress:
        return jsonify({"recommendations": [], "message": "Start learning to get personalized recommendations!"})

    # Build context for AI
    progress_summary = "\n".join([
        f"- {p['subject']} / {p['topic']}: {p['score']}% ({p['status']})"
        for p in progress
    ])

    prompt = (
        f"Student: {user['name']}, Class {user.get('class_grade', 'unknown')}\n"
        f"Learning progress:\n{progress_summary}\n\n"
        f"Based on this data, provide:\n"
        f"1. Top 3 specific topic recommendations (what to study next and why)\n"
        f"2. 3 practice questions for the weakest topic\n"
        f"3. One motivational message\n"
        f"Keep it concise and encouraging."
    )

    ai_response = chat_sync("personalized", [], prompt)
    return jsonify({"recommendations": ai_response})


# ──────────────────────────────
#  Run
# ──────────────────────────────

if __name__ == "__main__":
    # Auto-seed if DB is empty
    try:
        from seed import seed
        seed()
    except Exception as e:
        print(f"Seeding skipped: {e}")

    debug = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")
    port = int(os.environ.get("PORT", 5000))
    print(f"\n[VidyAI] Running at http://localhost:{port}")
    print(f"   Demo Student: student@demo.com / demo123")
    print(f"   Demo Teacher: teacher@demo.com / demo123\n")
    app.run(debug=debug, port=port, host="0.0.0.0")
