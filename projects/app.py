import os
import sqlite3
import uuid
from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

# Application Setup & Configurations
BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "database.db"
UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

app = Flask(__name__)
app.config["SECRET_KEY"] = "campus-complaint-secret-key-2026-secure"
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max upload size

# Ensure upload directory exists
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)


# ==========================================
# Database Connection & Initialization
# ==========================================

def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        # Enable Foreign Key support for SQLite
        g.db.execute("PRAGMA foreign_keys = ON;")
    return g.db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, "db"):
        g.db.close()


@app.template_filter("format_datetime")
def format_datetime(value, fmt="%Y-%m-%d %H:%M"):
    """Format string or datetime object to readable date and time."""
    if not value:
        return ""
    if isinstance(value, str):
        return value[:16]
    if hasattr(value, "strftime"):
        return value.strftime(fmt)
    return str(value)


def init_db():
    """
    Initializes database tables if they do not exist and seeds the default admin user.
    Preserves all existing data across app restarts.
    """
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    # Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Complaints Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_code TEXT UNIQUE NOT NULL,
            student_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            location TEXT NOT NULL,
            image_filename TEXT,
            status TEXT NOT NULL DEFAULT 'Pending',
            admin_remark TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(student_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)

    # Seed Default Admin Account if not present
    cursor.execute("SELECT id FROM users WHERE email = ?", ("admin@campus.com",))
    admin_exists = cursor.fetchone()
    if not admin_exists:
        hashed_pw = generate_password_hash("admin123")
        cursor.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
            ("Campus Administrator", "admin@campus.com", hashed_pw, "admin")
        )
        print("Default admin account created: admin@campus.com / admin123")

    db.commit()
    db.close()


# Run init_db on application startup
init_db()


# ==========================================
# Helper Functions & Decorators
# ==========================================

def allowed_file(filename):
    """Check if the uploaded file has an allowed image extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def login_required(f):
    """Decorator to enforce that the user is logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def student_required(f):
    """Decorator to enforce that the user is a logged-in student."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in as a student.", "warning")
            return redirect(url_for("login"))
        if session.get("role") != "student":
            flash("Admin accounts cannot access student pages.", "info")
            return redirect(url_for("admin_dashboard"))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to enforce that the user is a logged-in administrator."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in as an administrator.", "warning")
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            flash("Unauthorized access: Administrator privileges required.", "danger")
            return redirect(url_for("student_dashboard"))
        return f(*args, **kwargs)
    return decorated_function


CATEGORIES = [
    "Broken Fan",
    "Broken Light",
    "Dirty Classroom",
    "Water Problem",
    "Wi-Fi Issue",
    "Electrical Problem",
    "Cleanliness",
    "Other"
]

STATUS_LIST = ["Pending", "Assigned", "In Progress", "Resolved", "Rejected"]


# ==========================================
# Authentication Routes
# ==========================================

@app.route("/")
def index():
    """Landing route - redirects to appropriate dashboard if logged in, else to login page."""
    if "user_id" in session:
        if session.get("role") == "admin":
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("student_dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Handles student and admin login."""
    if "user_id" in session:
        if session.get("role") == "admin":
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("student_dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter both email and password.", "danger")
            return render_template("login.html")

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["email"] = user["email"]
            session["role"] = user["role"]

            flash(f"Welcome back, {user['name']}!", "success")
            if user["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("student_dashboard"))
        else:
            flash("Invalid email or password.", "danger")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Handles student registration."""
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Form validations
        if not name or not email or not password or not confirm_password:
            flash("All fields are required.", "danger")
            return render_template("register.html", name=name, email=email)

        if "@" not in email or "." not in email:
            flash("Please enter a valid email address.", "danger")
            return render_template("register.html", name=name, email=email)

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template("register.html", name=name, email=email)

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html", name=name, email=email)

        db = get_db()
        cursor = db.cursor()

        # Check uniqueness of email
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            flash("Email already registered. Please log in or use a different email.", "warning")
            return render_template("register.html", name=name, email=email)

        # Hash password and insert student
        hashed_password = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, 'student')",
            (name, email, hashed_password)
        )
        db.commit()

        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/logout")
def logout():
    """Logs out the user and clears session."""
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for("login"))


# ==========================================
# Student Routes
# ==========================================

@app.route("/student/dashboard")
@student_required
def student_dashboard():
    """Student Dashboard with statistics and recent complaints table."""
    db = get_db()
    cursor = db.cursor()
    student_id = session["user_id"]

    # Calculate real statistics from SQLite
    cursor.execute("SELECT COUNT(*) as total FROM complaints WHERE student_id = ?", (student_id,))
    total_complaints = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as pending FROM complaints WHERE student_id = ? AND status = 'Pending'", (student_id,))
    pending_complaints = cursor.fetchone()["pending"]

    cursor.execute("SELECT COUNT(*) as in_progress FROM complaints WHERE student_id = ? AND status = 'In Progress'", (student_id,))
    in_progress_complaints = cursor.fetchone()["in_progress"]

    cursor.execute("SELECT COUNT(*) as resolved FROM complaints WHERE student_id = ? AND status = 'Resolved'", (student_id,))
    resolved_complaints = cursor.fetchone()["resolved"]

    # Fetch all complaints for this student
    cursor.execute("""
        SELECT * FROM complaints 
        WHERE student_id = ? 
        ORDER BY created_at DESC
    """, (student_id,))
    complaints = cursor.fetchall()

    return render_template(
        "student_dashboard.html",
        total_complaints=total_complaints,
        pending_complaints=pending_complaints,
        in_progress_complaints=in_progress_complaints,
        resolved_complaints=resolved_complaints,
        complaints=complaints
    )


@app.route("/student/submit", methods=["GET", "POST"])
@student_required
def submit_complaint():
    """Form to submit a new campus complaint."""
    if request.method == "POST":
        category = request.form.get("category", "").strip()
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        location = request.form.get("location", "").strip()
        file = request.files.get("photo")

        # Validation
        if not category or not title or not description or not location:
            flash("All fields are required.", "danger")
            return render_template(
                "submit_complaint.html",
                categories=CATEGORIES,
                category=category,
                title=title,
                description=description,
                location=location
            )

        if category not in CATEGORIES:
            flash("Please select a valid category.", "danger")
            return render_template(
                "submit_complaint.html",
                categories=CATEGORIES,
                category=category,
                title=title,
                description=description,
                location=location
            )

        image_filename = None
        if file and file.filename != "":
            if allowed_file(file.filename):
                ext = file.filename.rsplit(".", 1)[1].lower()
                # Secure unique filename
                unique_name = f"cmp_{uuid.uuid4().hex[:10]}_{secure_filename(file.filename.rsplit('.', 1)[0])}.{ext}"
                save_path = Path(app.config["UPLOAD_FOLDER"]) / unique_name
                file.save(str(save_path))
                image_filename = unique_name
            else:
                flash("Only image files (PNG, JPG, JPEG, GIF, WEBP) are allowed.", "danger")
                return render_template(
                    "submit_complaint.html",
                    categories=CATEGORIES,
                    category=category,
                    title=title,
                    description=description,
                    location=location
                )

        db = get_db()
        cursor = db.cursor()

        # Generate unique sequential complaint code CMP-0001
        cursor.execute("SELECT MAX(id) as max_id FROM complaints")
        row = cursor.fetchone()
        next_id = (row["max_id"] or 0) + 1
        complaint_code = f"CMP-{next_id:04d}"

        cursor.execute("""
            INSERT INTO complaints (
                complaint_code, student_id, category, title, description, location, image_filename, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending')
        """, (complaint_code, session["user_id"], category, title, description, location, image_filename))
        
        complaint_id = cursor.lastrowid
        db.commit()

        flash("Complaint submitted successfully.", "success")
        return redirect(url_for("complaint_details", complaint_id=complaint_id))

    return render_template("submit_complaint.html", categories=CATEGORIES)


@app.route("/student/complaint/<int:complaint_id>")
@student_required
def complaint_details(complaint_id):
    """Detailed view and visual status timeline of a specific student complaint."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT * FROM complaints 
        WHERE id = ? AND student_id = ?
    """, (complaint_id, session["user_id"]))
    complaint = cursor.fetchone()

    if not complaint:
        flash("Complaint not found.", "warning")
        return redirect(url_for("student_dashboard"))

    return render_template("complaint_details.html", complaint=complaint)


@app.route("/student/complaints")
@student_required
def student_complaints_list():
    """View all complaints submitted by the logged-in student."""
    return redirect(url_for("student_dashboard"))


# ==========================================
# Admin Routes
# ==========================================

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    """Admin Dashboard with comprehensive overview, statistics, and filters."""
    db = get_db()
    cursor = db.cursor()

    # Calculate real campus-wide statistics from SQLite
    cursor.execute("SELECT COUNT(*) as total FROM complaints")
    total_complaints = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as pending FROM complaints WHERE status = 'Pending'")
    pending_count = cursor.fetchone()["pending"]

    cursor.execute("SELECT COUNT(*) as assigned FROM complaints WHERE status = 'Assigned'")
    assigned_count = cursor.fetchone()["assigned"]

    cursor.execute("SELECT COUNT(*) as in_progress FROM complaints WHERE status = 'In Progress'")
    in_progress_count = cursor.fetchone()["in_progress"]

    cursor.execute("SELECT COUNT(*) as resolved FROM complaints WHERE status = 'Resolved'")
    resolved_count = cursor.fetchone()["resolved"]

    cursor.execute("SELECT COUNT(*) as rejected FROM complaints WHERE status = 'Rejected'")
    rejected_count = cursor.fetchone()["rejected"]

    # Filter and Search Handling
    status_filter = request.args.get("status", "").strip()
    category_filter = request.args.get("category", "").strip()
    search_query = request.args.get("q", "").strip()

    query = """
        SELECT c.*, u.name as student_name, u.email as student_email 
        FROM complaints c
        JOIN users u ON c.student_id = u.id
        WHERE 1=1
    """
    params = []

    if status_filter and status_filter != "All":
        query += " AND c.status = ?"
        params.append(status_filter)

    if category_filter and category_filter != "All":
        query += " AND c.category = ?"
        params.append(category_filter)

    if search_query:
        query += " AND (c.complaint_code LIKE ? OR u.name LIKE ? OR c.location LIKE ? OR c.title LIKE ?)"
        wildcard = f"%{search_query}%"
        params.extend([wildcard, wildcard, wildcard, wildcard])

    query += " ORDER BY c.created_at DESC"

    cursor.execute(query, tuple(params))
    complaints = cursor.fetchall()

    return render_template(
        "admin_dashboard.html",
        total_complaints=total_complaints,
        pending_count=pending_count,
        assigned_count=assigned_count,
        in_progress_count=in_progress_count,
        resolved_count=resolved_count,
        rejected_count=rejected_count,
        complaints=complaints,
        categories=CATEGORIES,
        status_list=STATUS_LIST,
        selected_status=status_filter or "All",
        selected_category=category_filter or "All",
        search_query=search_query
    )


@app.route("/admin/complaints")
@admin_required
def admin_complaints():
    """Alias for admin dashboard with filter support."""
    return redirect(url_for("admin_dashboard", **request.args))


@app.route("/admin/complaint/<int:complaint_id>", methods=["GET"])
@admin_required
def admin_complaint_details(complaint_id):
    """Admin view for reviewing and managing a specific complaint."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT c.*, u.name as student_name, u.email as student_email 
        FROM complaints c
        JOIN users u ON c.student_id = u.id
        WHERE c.id = ?
    """, (complaint_id,))
    complaint = cursor.fetchone()

    if not complaint:
        flash("Complaint not found.", "warning")
        return redirect(url_for("admin_dashboard"))

    return render_template(
        "admin_complaint.html",
        complaint=complaint,
        status_list=STATUS_LIST
    )


@app.route("/admin/complaint/<int:complaint_id>/update", methods=["POST"])
@admin_required
def update_complaint_status(complaint_id):
    """Updates complaint status, admin remarks, and modified timestamp."""
    new_status = request.form.get("status", "").strip()
    admin_remark = request.form.get("admin_remark", "").strip()

    if new_status not in STATUS_LIST:
        flash("Invalid status selected.", "danger")
        return redirect(url_for("admin_complaint_details", complaint_id=complaint_id))

    db = get_db()
    cursor = db.cursor()

    # Check if complaint exists
    cursor.execute("SELECT id FROM complaints WHERE id = ?", (complaint_id,))
    if not cursor.fetchone():
        flash("Complaint not found.", "danger")
        return redirect(url_for("admin_dashboard"))

    # Update complaint status, remark, and updated_at
    cursor.execute("""
        UPDATE complaints 
        SET status = ?, admin_remark = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (new_status, admin_remark, complaint_id))
    db.commit()

    flash("Complaint updated successfully.", "success")
    return redirect(url_for("admin_complaint_details", complaint_id=complaint_id))


# ==========================================
# Main Application Entry Point
# ==========================================

if __name__ == "__main__":
    # Runs the Flask server on local port 5000
    print("\n" + "=" * 55)
    print("  SMART CAMPUS COMPLAINT SYSTEM RUNNING")
    print("  URL: http://127.0.0.1:5000")
    print("  Admin Credentials: admin@campus.com / admin123")
    print("=" * 55 + "\n")
    app.run(debug=True, host="127.0.0.1", port=5000)
