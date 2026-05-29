# Buddy — AI Chatbot for KJSIT

Buddy is an AI-powered chatbot built for **K J Somaiya Institute of Technology (KJSIT)**. It answers student queries about faculty, timetables, subjects, notices, and general college information — using a combination of a live SQLite database and a RAG (Retrieval-Augmented Generation) pipeline powered by Groq's LLaMA model.

---

## Features

- 💬 **Conversational AI** — Maintains multi-turn chat history (last 5 exchanges)
- 🗃️ **Live Database Queries** — Fetches real-time faculty, timetable, subjects, and notice data from SQLite
- 📚 **RAG Pipeline** — Retrieves relevant context from `dept_knowledge.txt` and college website content
- 🔗 **Source Links** — Displays source URLs when answering from RAG context
- 🔔 **Notices Board** — Students can view latest college notices
- 🔐 **Admin Panel** — Password-protected dashboard to add/delete notices and view DB stats
- ⚡ **Query Rewriting** — Rewrites vague user queries into cleaner search terms before RAG retrieval

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| LLM | Groq API (`llama-3.1-8b-instant`) |
| RAG | Custom retriever (`rag/retriever.py`) |
| Database | SQLite (`college.db`) |
| Frontend | HTML/CSS/JS (Jinja2 templates) |
| Config | `python-dotenv` |

---

## Project Structure

```
├── app.py                  # Main Flask application
├── college.db              # SQLite database
├── rag/
│   └── retriever.py        # RAG retrieval logic
├── templates/
│   ├── index.html          # Chat UI
│   ├── home.html
│   ├── admin.html          # Admin dashboard
│   └── admin_login.html
├── .env                    # Environment variables (not committed)
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup & Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the root directory:

```env
FLASK_SECRET_KEY=your_secret_key_here
ADMIN_PASSWORD=your_admin_password
GROQ_API_KEY=your_groq_api_key
```

> Get your free Groq API key at [console.groq.com](https://console.groq.com)

### 5. Run the app

```bash
python app.py
```

The app will be live at `http://127.0.0.1:5000`

---

## 🗄️ Database Schema

The app uses `college.db` with the following tables:

| Table | Description |
|---|---|
| `faculty_new` | Faculty details — code, name, email, cabin |
| `subjects` | Subject code and name |
| `timetable` | Day-wise schedule with room, faculty, class group |
| `notices` | College notices with title, description, category, date |
| `faculty_subjects` | Many-to-many mapping of faculty to subjects |

---

## 🔐 Admin Panel

Access the admin panel at `/admin-login`.

Admins can:
- View faculty, notice, and timetable counts
- Add new notices (title, description, category)
- Delete existing notices
- Log out securely

---

## 🌐 API Endpoints

| Method | Route | Description |
|---|---|---|
| `GET` | `/` | Chat interface |
| `GET` | `/home` | Home page |
| `POST` | `/chat` | Main chat endpoint (JSON) |
| `GET/POST` | `/admin-login` | Admin login |
| `GET` | `/admin` | Admin dashboard (protected) |
| `POST` | `/admin/add-notice` | Add a notice |
| `POST` | `/admin/delete-notice/<id>` | Delete a notice |
| `GET` | `/admin-logout` | Logout |

### `/chat` Request/Response

**Request:**
```json
{ "message": "Who teaches Data Structures?" }
```

**Response:**
```json
{
  "reply": "Data Structures is taught by Prof. XYZ.",
  "sources": ["https://kjsit.somaiya.edu/..."]
}
```

---

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) or refer to the Render setup guide below.

### Recommended: Render

1. Push your code to GitHub
2. Go to [render.com](https://render.com) → New Web Service → Connect your repo
3. Set **Build Command**: `pip install -r requirements.txt`
4. Set **Start Command**: `gunicorn app:app`
5. Add environment variables (`GROQ_API_KEY`, `FLASK_SECRET_KEY`, `ADMIN_PASSWORD`) in the Render dashboard

> ⚠️ `college.db` won't persist across deploys on Render's free tier. Use a persistent disk (paid) or migrate to PostgreSQL for production.

---

## 📝 Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `FLASK_SECRET_KEY` | ✅ | Secret key for Flask sessions |
| `GROQ_API_KEY` | ✅ | API key for Groq LLM |
| `ADMIN_PASSWORD` | ✅ | Password for the admin panel |

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you'd like to change.

---

## 📄 License

This project is for educational purposes at KJSIT. All rights reserved.
