"""
VidyAI - Demo data seeder
Run once to populate the database with realistic sample data.
"""
import json
from database import (
    init_db, get_db, create_user, upsert_progress,
    new_id, now_iso
)


def seed():
    init_db()
    conn = get_db()

    # ── Users ────────────────────────────────────────────────
    # Check if already seeded
    existing = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if existing > 0:
        print("Database already seeded. Skipping.")
        conn.close()
        return

    # Students
    students = [
        ("Aarav Patel",    "aarav@vidyai.edu",    "student123", "student", "7"),
        ("Priya Sharma",   "priya@vidyai.edu",    "student123", "student", "8"),
        ("Rahul Desai",    "rahul@vidyai.edu",    "student123", "student", "6"),
        ("Nisha Joshi",    "nisha@vidyai.edu",    "student123", "student", "9"),
        ("Mohan Prajapati","mohan@vidyai.edu",    "student123", "student", "7"),
        ("Kavya Shah",     "kavya@vidyai.edu",    "student123", "student", "8"),
    ]
    student_ids = []
    for name, email, pwd, role, grade in students:
        conn.execute(
            "INSERT INTO users (id, name, email, password, role, class_grade, created_at) VALUES (?,?,?,?,?,?,?)",
            (new_id(), name, email, pwd, role, grade, now_iso()),
        )
        sid = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()["id"]
        student_ids.append(sid)

    # Teachers
    teachers = [
        ("Meena Teacher",   "meena@vidyai.edu",   "teacher123", "teacher", None),
        ("Ramesh Teacher",  "ramesh@vidyai.edu",  "teacher123", "teacher", None),
    ]
    for name, email, pwd, role, grade in teachers:
        conn.execute(
            "INSERT INTO users (id, name, email, password, role, class_grade, created_at) VALUES (?,?,?,?,?,?,?)",
            (new_id(), name, email, pwd, role, grade, now_iso()),
        )

    # Demo login accounts
    conn.execute(
        "INSERT INTO users (id, name, email, password, role, class_grade, created_at) VALUES (?,?,?,?,?,?,?)",
        (new_id(), "Demo Student", "student@demo.com", "demo123", "student", "7", now_iso()),
    )
    conn.execute(
        "INSERT INTO users (id, name, email, password, role, class_grade, created_at) VALUES (?,?,?,?,?,?,?)",
        (new_id(), "Demo Teacher", "teacher@demo.com", "demo123", "teacher", None, now_iso()),
    )

    # ── Subjects ────────────────────────────────────────────
    subjects = [
        ("Mathematics",  "MATH"),
        ("Science",      "SCI"),
        ("English",      "ENG"),
        ("Social Studies","SST"),
        ("Gujarati",     "GUJ"),
        ("Hindi",        "HIN"),
        ("Computer",     "COMP"),
    ]
    subject_map = {}
    for name, code in subjects:
        sid = new_id()
        subject_map[code] = sid
        try:
            conn.execute("INSERT INTO subjects (id, name, code) VALUES (?,?,?)", (sid, name, code))
        except Exception:
            pass

    # ── Topics ───────────────────────────────────────────────
    topics = [
        ("MATH", "Fractions",              "7"),
        ("MATH", "Algebra Basics",         "7"),
        ("MATH", "Geometry",               "7"),
        ("MATH", "Decimals",               "6"),
        ("MATH", "Linear Equations",       "8"),
        ("MATH", "Quadratic Equations",    "9"),
        ("SCI",  "Photosynthesis",         "7"),
        ("SCI",  "Cell Structure",         "8"),
        ("SCI",  "Newton's Laws",          "9"),
        ("SCI",  "Ecosystem",              "6"),
        ("ENG",  "Grammar - Tenses",       "7"),
        ("ENG",  "Essay Writing",          "8"),
        ("SST",  "Indian Constitution",    "8"),
        ("SST",  "Geography - Rivers",     "7"),
    ]
    for code, tname, grade in topics:
        conn.execute(
            "INSERT INTO topics (id, subject_id, name, class_grade) VALUES (?,?,?,?)",
            (new_id(), subject_map.get(code, new_id()), tname, grade),
        )

    # ── Learning Progress (Aarav - student_ids[0]) ───────────
    aarav_id = student_ids[0]
    aarav_progress = [
        ("Mathematics", "Fractions",       45,  "in_progress"),
        ("Mathematics", "Algebra Basics",  72,  "in_progress"),
        ("Mathematics", "Geometry",        86,  "completed"),
        ("Science",     "Photosynthesis",  68,  "in_progress"),
        ("English",     "Grammar - Tenses",78,  "completed"),
    ]
    for subj, topic, score, status in aarav_progress:
        conn.execute(
            "INSERT INTO learning_progress (id, student_id, subject, topic, score, attempts, status, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            (new_id(), aarav_id, subj, topic, score, 2, status, now_iso()),
        )

    # Priya
    priya_id = student_ids[1]
    priya_progress = [
        ("Mathematics", "Linear Equations", 88, "completed"),
        ("Mathematics", "Fractions",        92, "completed"),
        ("Science",     "Cell Structure",   55, "in_progress"),
        ("Science",     "Photosynthesis",   76, "completed"),
    ]
    for subj, topic, score, status in priya_progress:
        conn.execute(
            "INSERT INTO learning_progress (id, student_id, subject, topic, score, attempts, status, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            (new_id(), priya_id, subj, topic, score, 1, status, now_iso()),
        )

    # Rahul
    rahul_id = student_ids[2]
    rahul_progress = [
        ("Mathematics", "Decimals",    60, "in_progress"),
        ("Science",     "Ecosystem",   74, "in_progress"),
        ("English",     "Grammar - Tenses", 42, "in_progress"),
    ]
    for subj, topic, score, status in rahul_progress:
        conn.execute(
            "INSERT INTO learning_progress (id, student_id, subject, topic, score, attempts, status, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            (new_id(), rahul_id, subj, topic, score, 1, status, now_iso()),
        )

    # ── Resources ────────────────────────────────────────────
    resources = [
        ("Introduction to Fractions",         "Learn fractions from basics with visual examples.",      "https://www.khanacademy.org/math/cc-third-grade-math/fractions",          "article", "Mathematics", "6",  "Fractions",    "beginner",  "Khan Academy"),
        ("Photosynthesis Explained",           "Simple explanation of photosynthesis for Class 7.",      "https://www.byjus.com/biology/photosynthesis/",                            "video",   "Science",     "7",  "Photosynthesis","beginner",  "BYJU's"),
        ("Newton's Laws of Motion",            "Interactive lessons on Newton's three laws.",             "https://www.khanacademy.org/science/physics/forces-newtons-laws",          "article", "Science",     "9",  "Newton's Laws", "medium",    "Khan Academy"),
        ("Grammar: Tenses Practice",           "Practice all tenses with exercises.",                    "https://www.grammarly.com/blog/verb-tenses/",                              "article", "English",     "7",  "Grammar",      "medium",    "Grammarly"),
        ("Algebra Basics - IBM SkillsBuild",   "Free algebra course from IBM SkillsBuild.",              "https://skillsbuild.org/",                                                 "article", "Mathematics", "8",  "Algebra",      "medium",    "IBM SkillsBuild"),
        ("Cell Structure - NCERT",             "NCERT Class 8 Science Chapter on Cell Structure.",       "https://ncert.nic.in/",                                                    "article", "Science",     "8",  "Cell Structure","medium",    "NCERT"),
        ("OER India Resources",                "Open Educational Resources for Indian schools.",          "https://diksha.gov.in/",                                                   "article", "General",     None, "General",      "beginner",  "DIKSHA"),
        ("Quadratic Equations Practice",       "Step-by-step quadratic equation solver with examples.", "https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:quadratic-functions-equations", "article", "Mathematics", "9", "Quadratic Equations", "hard", "Khan Academy"),
        ("Indian Constitution Overview",       "Easy guide to the Indian Constitution for Class 8.",    "https://ncert.nic.in/",                                                    "article", "Social Studies","8","Indian Constitution","medium","NCERT"),
        ("Ecosystem - DIKSHA",                 "Interactive lesson on ecosystem for Class 6.",           "https://diksha.gov.in/",                                                   "video",   "Science",     "6",  "Ecosystem",    "beginner",  "DIKSHA"),
    ]
    for title, desc, url, rtype, subj, grade, topic, diff, source in resources:
        conn.execute(
            "INSERT INTO resources (id, title, description, url, type, subject, class_grade, topic, difficulty, source, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (new_id(), title, desc, url, rtype, subj, grade, topic, diff, source, now_iso()),
        )

    # ── Sample Lesson Plan ───────────────────────────────────
    teacher_row = conn.execute("SELECT id FROM users WHERE role='teacher' LIMIT 1").fetchone()
    teacher_id = teacher_row["id"] if teacher_row else new_id()
    lesson_content = {
        "title": "Photosynthesis - How Plants Make Food",
        "learning_objectives": [
            "Understand the process of photosynthesis",
            "Identify the inputs and outputs of photosynthesis",
            "Explain the role of chlorophyll and sunlight",
        ],
        "introduction": "Ask students: 'How do you get your food?' Lead discussion toward plants making their own food.",
        "explanation": "Photosynthesis is the process by which plants use sunlight, water, and carbon dioxide to produce glucose and oxygen. The equation is: 6CO2 + 6H2O + light -> C6H₁2O6 + 6O2",
        "examples": ["Leaves turning green in sunlight", "Aquatic plants releasing oxygen bubbles"],
        "activity": "Group activity: Draw a diagram of a leaf and label the parts involved in photosynthesis.",
        "questions": ["What are the raw materials for photosynthesis?", "What gas is released during photosynthesis?", "Why do plants need sunlight?"],
        "homework": "Draw a diagram showing the process of photosynthesis and label all parts.",
        "summary": "Plants make their own food using sunlight, water, and CO2 through a process called photosynthesis.",
    }
    conn.execute(
        "INSERT INTO lesson_plans (id, user_id, title, class_grade, subject, topic, duration, content, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (new_id(), teacher_id, "Photosynthesis - How Plants Make Food", "7", "Science", "Photosynthesis", "45 minutes", json.dumps(lesson_content), now_iso()),
    )

    conn.commit()
    conn.close()
    print("[OK] Database seeded successfully!")
    print("\nDemo accounts:")
    print("  Student -> student@demo.com  / demo123")
    print("  Teacher -> teacher@demo.com  / demo123")


if __name__ == "__main__":
    seed()
