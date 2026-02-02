import os
import requests
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from dotenv import load_dotenv
import sqlite3

load_dotenv()

app = Flask(__name__)
app.secret_key = "super_secret_admin_key"

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "chatgpt-42.p.rapidapi.com")
RAPIDAPI_ENDPOINT = os.getenv("RAPIDAPI_ENDPOINT", "/gpt4o")


# ================= HELPERS =================

def load_knowledge():
    try:
        with open("dept_knowledge.txt", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""

DEPT_KNOWLEDGE = load_knowledge()


def get_timetable(day_name):
    conn = sqlite3.connect("college.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT day, time_from, time_to, subject, room, faculty, class_group
        FROM timetable
        WHERE TRIM(LOWER(day)) = TRIM(LOWER(?))
    """, (day_name,))

    rows = cursor.fetchall()
    conn.close()
    return rows


def get_latest_notices():
    conn = sqlite3.connect("college.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT title, description, category, posted_on
        FROM notices
        ORDER BY posted_on DESC
        LIMIT 5
    """)

    rows = cursor.fetchall()
    conn.close()
    return rows


# ================= ROUTES =================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin"))
        return "❌ Wrong password"
    return render_template("admin_login.html")


@app.route("/admin")
def admin():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    conn = sqlite3.connect("college.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM faculty_new")
    faculty_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM notices")
    notice_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM timetable")
    timetable_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT id, title, description, category, posted_on
        FROM notices
        ORDER BY posted_on DESC
    """)
    notices = cursor.fetchall()

    conn.close()

    return render_template(
        "admin.html",
        notices=notices,
        faculty_count=faculty_count,
        notice_count=notice_count,
        timetable_count=timetable_count
    )


@app.route("/admin/add-notice", methods=["POST"])
def add_notice():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    conn = sqlite3.connect("college.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO notices (title, description, category, posted_on)
        VALUES (?, ?, ?, DATE('now'))
    """, (
        request.form.get("title"),
        request.form.get("description"),
        request.form.get("category")
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


@app.route("/admin/delete-notice/<int:notice_id>", methods=["POST"])
def delete_notice(notice_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    conn = sqlite3.connect("college.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notices WHERE id = ?", (notice_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


@app.route("/admin-logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


# ================= CHATBOT =================

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"reply": "Please type something 😊"})

    text = user_message.lower()
    words = text.split()

    conn = sqlite3.connect("college.db")
    cursor = conn.cursor()

    # -------- FACULTY --------
    faculty_rows = cursor.execute(
        "SELECT faculty_code, name, email, cabin FROM faculty_new"
    ).fetchall()

    for code, name, email, cabin in faculty_rows:
        if code.lower() in words or name.lower() in text:
            conn.close()
            return jsonify({
                "reply": f"👩‍🏫 {name}\n📧 {email}\n🏢 Cabin: {cabin}"
            })

    # -------- SUBJECT FULL FORM --------
    subjects = cursor.execute(
        "SELECT subject_code, subject_name FROM subjects"
    ).fetchall()

    explain_words = ["what is", "full form", "meaning", "define", "about"]

    for code, name in subjects:
        if code.lower() in words or name.lower() in text:
            if any(w in text for w in explain_words):
                conn.close()
                return jsonify({
                    "reply": f"📘 {code} stands for {name}"
                })

    # -------- SUBJECT FACULTY --------
    for code, name in subjects:
        if code.lower() in words or name.lower() in text:
            rows = cursor.execute("""
                SELECT f.name, fs.role
                FROM faculty_subjects fs
                JOIN faculty_new f
                ON fs.faculty_code = f.faculty_code
                WHERE fs.subject_code = ?
            """, (code,)).fetchall()

            conn.close()

            if rows:
                reply = "📚 Faculty for this subject:\n"
                for n, role in rows:
                    reply += f"• {n} ({role})\n"
                return jsonify({"reply": reply})

    # -------- TIMETABLE --------
    days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    found_day = next((d for d in days if d in text), None)

    if "timetable" in text or found_day:
        if not found_day:
            found_day = "monday"

        rows = get_timetable(found_day)

        if rows:
            reply = f"📅 Timetable for {found_day.capitalize()}:\n\n"
            for day, tf, tt, subject, room, faculty, group in rows:
                reply += f"⏱ {tf}-{tt} → {subject} in {room} | {group} ({faculty})\n"
            return jsonify({"reply": reply})

        return jsonify({"reply": "No timetable data found for that day."})

    # -------- NOTICES --------
    if any(k in text for k in ["notice", "announcement", "news", "circular"]):
        notices = get_latest_notices()

        if notices:
            reply = "📢 Latest Notices:\n\n"
            for t, d, c, date in notices:
                reply += f"📌 {t}\n{d}\nCategory: {c}\nDate: {date}\n\n"
            return jsonify({"reply": reply})

        return jsonify({"reply": "No notices right now."})

    # -------- AI FALLBACK --------
    if not RAPIDAPI_KEY:
        return jsonify({"reply": "AI key missing"}), 500

    payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful college assistant."},
            {"role": "user", "content": DEPT_KNOWLEDGE + "\n\n" + user_message}
        ]
    }

    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
    }

    try:
        resp = requests.post(
            f"https://{RAPIDAPI_HOST}{RAPIDAPI_ENDPOINT}",
            json=payload,
            headers=headers,
            timeout=30
        )

        return jsonify({"reply": resp.json().get("result", "No response")})

    except Exception as e:
        return jsonify({"reply": f"Error: {e}"}), 500


# ================= RUN =================

if __name__ == "__main__":
    app.run(debug=True)
