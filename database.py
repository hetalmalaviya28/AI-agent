"""
VidyAI – SQLite database layer
Manages all persistent state: users, conversations, messages,
students, assessments, lesson plans, resources, etc.
"""
import sqlite3
import uuid
import json
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "vidyai.db"


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id          TEXT PRIMARY KEY,
        name        TEXT NOT NULL,
        email       TEXT UNIQUE NOT NULL,
        password    TEXT NOT NULL,
        role        TEXT NOT NULL DEFAULT 'student',  -- student | teacher | admin
        class_grade TEXT,
        created_at  TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS conversations (
        id          TEXT PRIMARY KEY,
        user_id     TEXT NOT NULL,
        title       TEXT NOT NULL DEFAULT 'New Chat',
        mode        TEXT NOT NULL DEFAULT 'general',
        created_at  TEXT NOT NULL,
        updated_at  TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS messages (
        id              TEXT PRIMARY KEY,
        conversation_id TEXT NOT NULL,
        role            TEXT NOT NULL,  -- user | assistant | system
        content         TEXT NOT NULL,
        created_at      TEXT NOT NULL,
        FOREIGN KEY(conversation_id) REFERENCES conversations(id)
    );

    CREATE TABLE IF NOT EXISTS subjects (
        id   TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        code TEXT UNIQUE NOT NULL
    );

    CREATE TABLE IF NOT EXISTS topics (
        id         TEXT PRIMARY KEY,
        subject_id TEXT NOT NULL,
        name       TEXT NOT NULL,
        class_grade TEXT NOT NULL,
        FOREIGN KEY(subject_id) REFERENCES subjects(id)
    );

    CREATE TABLE IF NOT EXISTS assessments (
        id          TEXT PRIMARY KEY,
        user_id     TEXT NOT NULL,
        title       TEXT NOT NULL,
        subject     TEXT NOT NULL,
        topic       TEXT NOT NULL,
        class_grade TEXT NOT NULL,
        difficulty  TEXT NOT NULL DEFAULT 'medium',
        questions   TEXT NOT NULL,  -- JSON array
        created_at  TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS assessment_attempts (
        id            TEXT PRIMARY KEY,
        assessment_id TEXT NOT NULL,
        student_id    TEXT NOT NULL,
        answers       TEXT NOT NULL,  -- JSON
        score         REAL NOT NULL,
        total         INTEGER NOT NULL,
        feedback      TEXT,
        created_at    TEXT NOT NULL,
        FOREIGN KEY(assessment_id) REFERENCES assessments(id),
        FOREIGN KEY(student_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS learning_progress (
        id          TEXT PRIMARY KEY,
        student_id  TEXT NOT NULL,
        subject     TEXT NOT NULL,
        topic       TEXT NOT NULL,
        score       REAL,
        attempts    INTEGER DEFAULT 0,
        status      TEXT DEFAULT 'not_started',  -- not_started | in_progress | completed
        updated_at  TEXT NOT NULL,
        FOREIGN KEY(student_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS lesson_plans (
        id          TEXT PRIMARY KEY,
        user_id     TEXT NOT NULL,
        title       TEXT NOT NULL,
        class_grade TEXT NOT NULL,
        subject     TEXT NOT NULL,
        topic       TEXT NOT NULL,
        duration    TEXT,
        content     TEXT NOT NULL,  -- JSON
        created_at  TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS resources (
        id          TEXT PRIMARY KEY,
        title       TEXT NOT NULL,
        description TEXT,
        url         TEXT,
        type        TEXT NOT NULL DEFAULT 'article',  -- article | video | quiz | worksheet
        subject     TEXT,
        class_grade TEXT,
        topic       TEXT,
        difficulty  TEXT DEFAULT 'medium',
        source      TEXT DEFAULT 'OER',
        created_at  TEXT NOT NULL
    );
    """)

    conn.commit()
    conn.close()


# ──────────────────────────────
#  Helper utilities
# ──────────────────────────────

def new_id():
    return str(uuid.uuid4())


def now_iso():
    return datetime.now(timezone.utc).isoformat()


# ──────────────────────────────
#  Users
# ──────────────────────────────

def create_user(name, email, password, role="student", class_grade=None):
    conn = get_db()
    uid = new_id()
    conn.execute(
        "INSERT INTO users (id, name, email, password, role, class_grade, created_at) VALUES (?,?,?,?,?,?,?)",
        (uid, name, email, password, role, class_grade, now_iso()),
    )
    conn.commit()
    conn.close()
    return uid


def get_user_by_email(email):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(uid):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ──────────────────────────────
#  Conversations
# ──────────────────────────────

def create_conversation(user_id, title="New Chat", mode="general"):
    conn = get_db()
    cid = new_id()
    ts = now_iso()
    conn.execute(
        "INSERT INTO conversations (id, user_id, title, mode, created_at, updated_at) VALUES (?,?,?,?,?,?)",
        (cid, user_id, title, mode, ts, ts),
    )
    conn.commit()
    conn.close()
    return cid


def get_conversations(user_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM conversations WHERE user_id=? ORDER BY updated_at DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_conversation(cid):
    conn = get_db()
    row = conn.execute("SELECT * FROM conversations WHERE id=?", (cid,)).fetchone()
    conn.close()
    return dict(row) if row else None


def rename_conversation(cid, title):
    conn = get_db()
    conn.execute("UPDATE conversations SET title=?, updated_at=? WHERE id=?", (title, now_iso(), cid))
    conn.commit()
    conn.close()


def delete_conversation(cid):
    conn = get_db()
    conn.execute("DELETE FROM messages WHERE conversation_id=?", (cid,))
    conn.execute("DELETE FROM conversations WHERE id=?", (cid,))
    conn.commit()
    conn.close()


def touch_conversation(cid, title=None):
    conn = get_db()
    if title:
        conn.execute("UPDATE conversations SET updated_at=?, title=? WHERE id=?", (now_iso(), title, cid))
    else:
        conn.execute("UPDATE conversations SET updated_at=? WHERE id=?", (now_iso(), cid))
    conn.commit()
    conn.close()


# ──────────────────────────────
#  Messages
# ──────────────────────────────

def add_message(conversation_id, role, content):
    conn = get_db()
    mid = new_id()
    conn.execute(
        "INSERT INTO messages (id, conversation_id, role, content, created_at) VALUES (?,?,?,?,?)",
        (mid, conversation_id, role, content, now_iso()),
    )
    conn.commit()
    conn.close()
    return mid


def get_messages(conversation_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM messages WHERE conversation_id=? ORDER BY created_at ASC",
        (conversation_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ──────────────────────────────
#  Learning Progress
# ──────────────────────────────

def upsert_progress(student_id, subject, topic, score, status="in_progress"):
    conn = get_db()
    existing = conn.execute(
        "SELECT id, attempts FROM learning_progress WHERE student_id=? AND subject=? AND topic=?",
        (student_id, subject, topic),
    ).fetchone()
    if existing:
        attempts = existing["attempts"] + 1
        conn.execute(
            "UPDATE learning_progress SET score=?, attempts=?, status=?, updated_at=? WHERE id=?",
            (score, attempts, status, now_iso(), existing["id"]),
        )
    else:
        conn.execute(
            "INSERT INTO learning_progress (id, student_id, subject, topic, score, attempts, status, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            (new_id(), student_id, subject, topic, score, 1, status, now_iso()),
        )
    conn.commit()
    conn.close()


def get_student_progress(student_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM learning_progress WHERE student_id=? ORDER BY updated_at DESC",
        (student_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ──────────────────────────────
#  Lesson Plans
# ──────────────────────────────

def save_lesson_plan(user_id, title, class_grade, subject, topic, duration, content_dict):
    conn = get_db()
    lid = new_id()
    conn.execute(
        "INSERT INTO lesson_plans (id, user_id, title, class_grade, subject, topic, duration, content, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (lid, user_id, title, class_grade, subject, topic, duration, json.dumps(content_dict), now_iso()),
    )
    conn.commit()
    conn.close()
    return lid


def get_lesson_plans(user_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM lesson_plans WHERE user_id=? ORDER BY created_at DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ──────────────────────────────
#  Assessments
# ──────────────────────────────

def save_assessment(user_id, title, subject, topic, class_grade, difficulty, questions_list):
    conn = get_db()
    aid = new_id()
    conn.execute(
        "INSERT INTO assessments (id, user_id, title, subject, topic, class_grade, difficulty, questions, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (aid, user_id, title, subject, topic, class_grade, difficulty, json.dumps(questions_list), now_iso()),
    )
    conn.commit()
    conn.close()
    return aid


def get_assessments(user_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM assessments WHERE user_id=? ORDER BY created_at DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["questions"] = json.loads(d["questions"])
        result.append(d)
    return result


def get_assessment_by_id(aid):
    conn = get_db()
    row = conn.execute("SELECT * FROM assessments WHERE id=?", (aid,)).fetchone()
    conn.close()
    if row:
        d = dict(row)
        d["questions"] = json.loads(d["questions"])
        return d
    return None


# ──────────────────────────────
#  Resources
# ──────────────────────────────

def get_resources(subject=None, class_grade=None, topic=None):
    conn = get_db()
    q = "SELECT * FROM resources WHERE 1=1"
    params = []
    if subject:
        q += " AND subject=?"
        params.append(subject)
    if class_grade:
        q += " AND class_grade=?"
        params.append(class_grade)
    if topic:
        q += " AND topic LIKE ?"
        params.append(f"%{topic}%")
    q += " ORDER BY created_at DESC"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]
