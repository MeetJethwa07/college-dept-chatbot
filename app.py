import os
import requests
import csv
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import sqlite3
from flask import session, redirect, url_for
import subprocess


load_dotenv()

app = Flask(__name__)
load_dotenv()

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
app.secret_key = "super_secret_admin_key"

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "chatgpt-42.p.rapidapi.com")
RAPIDAPI_ENDPOINT = os.getenv("RAPIDAPI_ENDPOINT", "/gpt4o")


def load_knowledge():
    try:
        with open("dept_knowledge.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


DEPT_KNOWLEDGE = load_knowledge()


def get_timetable(class_name, day_name):
    conn = sqlite3.connect("college.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT time, subject, room, teacher
        FROM timetable
        WHERE class_name = ? AND day = ?
    """, (class_name, day_name))

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

def get_dashboard_stats():
    conn = sqlite3.connect("college.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM faculty")
    faculty_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM notices")
    notice_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM timetable")
    timetable_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM chatbot_logs")
    chat_count = cursor.fetchone()[0]

    conn.close()

    return faculty_count, notice_count, timetable_count, chat_count


def get_faculty_info(query):
    query = query.lower()
    results = []

    try:
        conn = sqlite3.connect("college.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT short_code, name, subject, email, cabin
            FROM faculty
        """)
        rows = cursor.fetchall()

        for sc, name, subject, email, cabin in rows:
            if (
                subject.lower() in query
                or name.lower() in query
                or sc.lower() in query
            ):
                results.append({
                    "short_code": sc,
                    "name": name,
                    "subject": subject,
                    "email": email,
                    "cabin": cabin
                })

        conn.close()

    except Exception as e:
        print("DB error:", e)

    return results

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password")

        print("Entered password:", password)  # DEBUG LINE

        if password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin"))
        else:
            return "❌ Wrong password"

    return render_template("admin_login.html")


@app.route("/admin")
def admin():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    conn = sqlite3.connect("college.db")
    cursor = conn.cursor()

    # 🔧 Ensure chatbot_logs table exists (FIX)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chatbot_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_query TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Dashboard stats
    cursor.execute("SELECT COUNT(*) FROM faculty")
    faculty_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM notices")
    notice_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM timetable")
    timetable_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM chatbot_logs")
    chat_count = cursor.fetchone()[0]

    # Notices
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
        timetable_count=timetable_count,
        chat_count=chat_count
    )


@app.route("/admin/add-notice", methods=["POST"])
def add_notice():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    title = request.form.get("title")
    description = request.form.get("description")
    category = request.form.get("category")

    conn = sqlite3.connect("college.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO notices (title, description, category, posted_on)
        VALUES (?, ?, ?, DATE('now'))
    """, (title, description, category))

    conn.commit()
    conn.close()

    return "✅ Notice added successfully! <br><br><a href='/admin'>Back</a>"

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

@app.route("/admin/edit-notice/<int:notice_id>", methods=["GET", "POST"])
def edit_notice(notice_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    conn = sqlite3.connect("college.db")
    cursor = conn.cursor()

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        category = request.form.get("category")

        cursor.execute("""
            UPDATE notices
            SET title = ?, description = ?, category = ?
            WHERE id = ?
        """, (title, description, category, notice_id))

        conn.commit()
        conn.close()
        return redirect(url_for("admin"))

    cursor.execute("""
        SELECT id, title, description, category
        FROM notices
        WHERE id = ?
    """, (notice_id,))

    notice = cursor.fetchone()
    conn.close()

    return render_template("edit_notice.html", notice=notice)


@app.route("/admin-logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"reply": "Please type a question first."})

    user_lower = user_message.lower()

    # ===== FACULTY FEATURE =====
    faculty_keywords = [
        "teach", "teaches", "teacher", "faculty",
        "prof", "sir", "maam", "email", "cabin"
    ]

    if any(word in user_lower for word in faculty_keywords):
        faculty_rows = get_faculty_info(user_lower)
        if faculty_rows:
            reply = "👨‍🏫 Faculty Information:\n\n"
            for f in faculty_rows:
                reply += (
                    f"📌 {f['name']}\n"
                    f"   Subject: {f['subject']}\n"
                    f"   Cabin: {f['cabin']}\n"
                    f"   Email: {f['email']}\n\n"
                )
            return jsonify({"reply": reply})
        else:
            return jsonify({
                "reply": "Sorry, faculty information is not available in the database."
            })

    # ===== TIMETABLE FEATURE =====
    days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    found_day = next((d for d in days if d in user_lower), None)

    class_name = "EXTC A"  # must match DB value exactly

    if "timetable" in user_lower or found_day:
        if not found_day:
            found_day = "monday"

        rows = get_timetable(class_name, found_day)

        if rows:
            summary = f"📅 Timetable for {class_name} on {found_day.capitalize()}:\n\n"

            for time, subject, room, teacher in rows:
                summary += f"⏱ {time} → {subject} in {room} ({teacher})\n"

            return jsonify({"reply": summary})
        else:
            return jsonify({"reply": "No timetable data found for that day."})

        
            # ===== NOTICES FEATURE (FORCED) =====
    notice_keywords = [
        "notice", "notices", "announcement",
        "announcements", "news", "circular"
    ]

    if any(word in user_lower for word in notice_keywords):
        notices = get_latest_notices()

        if notices:
            reply = "📢 Latest College Notices:\n\n"
            for title, desc, category, date in notices:
                reply += (
                    f"📌 {title}\n"
                    f"{desc}\n"
                    f"Category: {category}\n"
                    f"Date: {date}\n\n"
                )
            return jsonify({"reply": reply})
        else:
            return jsonify({
                "reply": "There are no active notices at the moment."
            })

    # ===== AI FALLBACK =====
    if not RAPIDAPI_KEY:
        return jsonify({"reply": "Server error: RAPIDAPI_KEY missing"}), 500

    prompt_context = (
        "You are a helpful chatbot for a college department.\n\n"
        f"{DEPT_KNOWLEDGE}\n\n"
        f"Question: {user_message}"
    )

    payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt_context}
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

        data = resp.json()
        reply = data.get("result", "Sorry, no response.")
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(    )
