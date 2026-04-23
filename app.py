from flask import Flask, render_template, request, redirect
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, datetime
from langdetect import detect

app = Flask(__name__)
app.secret_key = "secret123"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()

    conn.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )""")

    conn.execute("""CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT,
        language TEXT,
        timestamp TEXT
    )""")

    conn.commit()
    conn.close()

init_db()

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return User(user["id"], user["username"]) if user else None

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            login_user(User(user["id"], user["username"]))
            return redirect("/dashboard")

        return "Invalid username or password"

    return render_template("login.html")

LANGUAGE_MAP = {
    "en": "English",
    "ta": "Tamil",
    "hi": "Hindi",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "sw": "Swahili",
    "zh-cn": "Chinese",
    "ar": "Arabic",
    "ru": "Russian",
    "kn": "Kannada",
    "te": "Telugu",
    "ml": "Malayalam"
}

@app.route("/")
def home():
    return redirect("/dashboard")

@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()
    history = conn.execute(
        "SELECT text, language, timestamp FROM predictions ORDER BY id DESC LIMIT 5"
    ).fetchall()
    conn.close()
    return render_template("dashboard.html", history=history)

@app.route("/detect", methods=["GET","POST"])
@login_required
def detect_page():
    result = None

    if request.method == "POST":
        text = request.form["text"]

        try:
            code = detect(text)
            result = LANGUAGE_MAP.get(code, code)   # converts to full name
        except:
            result = "Unknown"

        conn = get_db()
        conn.execute("INSERT INTO predictions (text, language, timestamp) VALUES (?,?,?)",
                     (text, result, str(datetime.datetime.now())))
        conn.commit()
        conn.close()

    return render_template("detect.html", result=result)

@app.route("/history")
@login_required
def history():
    conn = get_db()
    rows = conn.execute(
        "SELECT text, language, timestamp FROM predictions ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return render_template("history.html", rows=rows)

@app.route("/graphs")
@login_required
def graphs():
    conn = get_db()

    data = conn.execute(
        "SELECT language, COUNT(*) as count FROM predictions GROUP BY language"
    ).fetchall()

    conn.close()

    labels = [x["language"] for x in data]
    values = [x["count"] for x in data]

    return render_template("graphs.html", labels=labels, values=values)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)
import os
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
