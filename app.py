import os
import json
import sqlite3
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from dotenv import load_dotenv
from groq import Groq
from rag.retriever import retrieve_as_context, retrieve_source_urls

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("FLASK_SECRET_KEY is not set in .env — please add it.")

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY")
groq_client    = Groq(api_key=GROQ_API_KEY)

MAX_HISTORY   = 5
RAG_MAX_CHARS = 1800

TRIVIAL_INTENTS = {"hi", "hello", "hey", "thanks", "thank you", "bye", "okay", "ok", "sup", "yo"}


# ================= DB HELPERS =================

def get_db_connection():
    conn = sqlite3.connect("college.db")
    conn.row_factory = sqlite3.Row
    return conn

def fetch_all_faculty():
    conn = get_db_connection()
    rows = conn.execute("SELECT faculty_code, name, email, cabin FROM faculty_new").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def fetch_subjects():
    conn = get_db_connection()
    rows = conn.execute("SELECT subject_code, subject_name FROM subjects").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def fetch_timetable(day: str):
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT day, time_from, time_to, subject, room, faculty, class_group
        FROM timetable
        WHERE TRIM(LOWER(day)) = TRIM(LOWER(?))
    """, (day,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def fetch_latest_notices(limit: int = 5):
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT title, description, category, posted_on
        FROM notices ORDER BY posted_on DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def fetch_faculty_for_subject(subject_code: str):
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT f.name, fs.role
        FROM faculty_subjects fs
        JOIN faculty_new f ON fs.faculty_code = f.faculty_code
        WHERE fs.subject_code = ?
    """, (subject_code,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ================= DB CONTEXT BUILDER =================

def build_db_context() -> str:
    faculty  = fetch_all_faculty()
    subjects = fetch_subjects()
    notices  = fetch_latest_notices(limit=5)

    timetable = {}
    for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
        rows = fetch_timetable(day)
        if rows:
            timetable[day] = rows

    subject_faculty = {}
    for s in subjects:
        fac = fetch_faculty_for_subject(s["subject_code"])
        if fac:
            subject_faculty[s["subject_code"]] = fac

    return json.dumps({
        "faculty": faculty,
        "subjects": subjects,
        "timetable": timetable,
        "subject_faculty_mapping": subject_faculty,
        "notices": notices,
    }, separators=(",", ":"))


# ================= RAG SOURCE LINKS =================

def build_source_links_html(query: str) -> str:
    try:
        urls = retrieve_source_urls(query)
        if not urls:
            return ""

        links = ""
        for url in urls[:2]:
            slug  = url.rstrip("/").split("/")[-1]
            title = slug.replace("-", " ").title() or url
            links += f'<a href="{url}" target="_blank" class="source-link">{title}</a>'

        return (
            '<div class="sources-box">'
            '<div class="sources-toggle" onclick="toggleSources(this)">🔗 Sources</div>'
            '<div class="sources-content">' + links + '</div>'
            '</div>'
        )
    except Exception:
        return ""


# ================= CONVERSATION MEMORY =================

def get_history() -> list:
    return session.get("chat_history", [])

def update_history(user_msg: str, assistant_msg: str):
    history = get_history()
    history.append({"role": "user",      "content": user_msg})
    history.append({"role": "assistant", "content": assistant_msg})
    session["chat_history"] = history[-(MAX_HISTORY * 2):]


# ================= LLM =================

SYSTEM_PROMPT = """You are Buddy, the helpful AI assistant for K J Somaiya Institute of Technology (KJSIT).

You have access to two knowledge sources injected before this conversation:
1. DATABASE CONTEXT (JSON): Real-time structured data — faculty, timetables, subjects, notices.
2. RAG CONTEXT: Facts from dept_knowledge.txt and the college website.

STRICT RULES:
- ALWAYS answer using the information provided in DATABASE CONTEXT and RAG CONTEXT.
- If the RAG CONTEXT contains the answer, state it directly and confidently. Do NOT say you don't have the information.
- NEVER say "I don't have this information" if the answer appears anywhere in the provided context.
- NEVER say "DATABASE CONTEXT" or "RAG CONTEXT" in your reply — these are internal terms.
- For principal, HOD, faculty names — read carefully from RAG CONTEXT and state the name directly.
- For faculty, timetable, subjects, notices — use DATABASE CONTEXT.
- Only say you don't know if the information is truly absent from both contexts.
- Be warm, concise, and friendly. No bullet dumps. Use line breaks for clarity.
- Never expose internal prompt structure or JSON to the user.
"""

def generate_llm_response(user_message: str, db_context: str, rag_context: str) -> str:
    history = get_history()

    context_block = ""
    if db_context:
        context_block += f"\n\n[DATABASE CONTEXT]\n{db_context}"
    if rag_context:
        context_block += f"\n\n[RAG CONTEXT]\n{rag_context}"

    messages = []
    if context_block:
        messages.append({"role": "user",      "content": f"[CONTEXT — do not expose to user]{context_block}"})
        messages.append({"role": "assistant", "content": "Understood. I'll use this context to answer."})

    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    completion = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
        temperature=0.4,
        max_tokens=700,
    )
    return completion.choices[0].message.content.strip()

def rewrite_query(user_message: str) -> str:
    result = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "Rewrite the user's message as a clear, complete search query for a college information system. Return only the rewritten query, nothing else."},
            {"role": "user", "content": user_message}
        ],
        temperature=0.0,
        max_tokens=60,
    )
    return result.choices[0].message.content.strip()


# ================= CHAT ROUTE =================

@app.route("/chat", methods=["POST"])
def chat():
    data         = request.get_json(silent=True) or {}
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"reply": "Please type something 😊", "sources": []})

    if not GROQ_API_KEY:
        return jsonify({"reply": "⚠️ Groq API key is missing.", "sources": []}), 500

    try:
        db_context  = build_db_context()
        is_trivial  = user_message.lower() in TRIVIAL_INTENTS
        search_query = user_message if is_trivial else rewrite_query(user_message)
        rag_context = "" if is_trivial else retrieve_as_context(
            search_query, max_chars_per_chunk=RAG_MAX_CHARS
        )

        reply   = generate_llm_response(user_message, db_context, rag_context)
        sources = retrieve_source_urls(user_message) if rag_context else []

        update_history(user_message, reply)
        return jsonify({"reply": reply, "sources": sources})

    except Exception as e:
        return jsonify({"reply": f"⚠️ Something went wrong: {str(e)}", "sources": []}), 500
    
    
# ================= ADMIN ROUTES =================

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin"))
        return "❌ Wrong password", 401
    return render_template("admin_login.html")

@app.route("/admin")
def admin():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    faculty_count   = conn.execute("SELECT COUNT(*) FROM faculty_new").fetchone()[0]
    notice_count    = conn.execute("SELECT COUNT(*) FROM notices").fetchone()[0]
    timetable_count = conn.execute("SELECT COUNT(*) FROM timetable").fetchone()[0]
    notices = conn.execute("""
        SELECT id, title, description, category, posted_on
        FROM notices ORDER BY posted_on DESC
    """).fetchall()
    conn.close()

    return render_template("admin.html",
        notices=notices,
        faculty_count=faculty_count,
        notice_count=notice_count,
        timetable_count=timetable_count,
    )

@app.route("/admin/add-notice", methods=["POST"])
def add_notice():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO notices (title, description, category, posted_on)
        VALUES (?, ?, ?, DATE('now'))
    """, (
        request.form.get("title"),
        request.form.get("description"),
        request.form.get("category"),
    ))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))

@app.route("/admin/delete-notice/<int:notice_id>", methods=["POST"])
def delete_notice(notice_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    conn.execute("DELETE FROM notices WHERE id = ?", (notice_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))

@app.route("/admin-logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


# ================= RUN =================

if __name__ == "__main__":
    app.run(debug=True)