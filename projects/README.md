# 🏫 SMART CAMPUS COMPLAINT SYSTEM

A modern, full-stack, lightweight college campus facility issue reporting and tracking web application built with **Python (Flask)**, **SQLite**, **HTML5**, **CSS3**, and **JavaScript**.

---

## 📌 Project Overview
The **Smart Campus Complaint System** provides a seamless digital workflow for college students to report campus issues (such as broken fans, broken lights, dirty classrooms, water shortages, and Wi-Fi outages) with location details, detailed descriptions, and image evidence. Campus administrators can track, assign, update resolution statuses, and provide official feedback remarks in real time.

---

## ✨ Features

### 🎓 Student Features
- **Account Registration & Login**: Secure authentication with Werkzeug password hashing.
- **Dynamic Student Dashboard**: Real-time stats (Total, Pending, In Progress, Resolved) pulled directly from SQLite.
- **Submit Complaints**:
  - Category dropdown (`Broken Fan`, `Broken Light`, `Dirty Classroom`, `Water Problem`, `Wi-Fi Issue`, `Electrical Problem`, `Cleanliness`, `Other`).
  - Title, detailed description, and campus location fields.
  - Photo evidence upload with real-time browser preview.
  - Automatic sequential complaint code generation (`CMP-0001`, `CMP-0002`, etc.).
- **Visual Status Progress Tracker**: 4-step visual timeline tracking complaint progression (`Submitted` ➔ `Assigned` ➔ `In Progress` ➔ `Resolved` or `Rejected`).
- **Official Admin Feedback**: View remarks and maintenance updates directly from facility staff.
- **Privacy & Security**: Students can only view and access their own submitted complaints.

### 🛡️ Administrator Features
- **Centralized Administration Dashboard**: Campus-wide metrics overview with real-time statistics cards.
- **Multi-criteria Filtering & Search**:
  - Filter complaints by status (`All`, `Pending`, `Assigned`, `In Progress`, `Resolved`, `Rejected`).
  - Filter by category.
  - Search by Complaint Code, Student Name, Location, or Title.
- **Complaint Management**:
  - View full student contact details and uploaded photo evidence in an expandable modal.
  - Update complaint workflow status.
  - Add official remarks / action notes with automatic timestamp updates.
- **Role-Based Access Control**: Protected administrative routes that prevent unauthorized student access.

---

## 💻 Technologies Used

| Layer | Technology |
|---|---|
| **Backend Framework** | Python 3, Flask 3.x |
| **Authentication & Security** | Werkzeug (`generate_password_hash`, `check_password_hash`), Flask Sessions |
| **Database** | SQLite 3 (Auto-initialized with Foreign Key support) |
| **Frontend UI** | HTML5, CSS3 (Custom Design System), JavaScript (ES6) |
| **Styling & Icons** | Custom `style.css`, Bootstrap 5.3.3, Bootstrap Icons 1.11.3 |

---

## 📂 Project Structure

```text
Smart-Campus-Complaint-System/
│
├── app.py                      # Core Flask backend, routes, database models & init
├── database.db                 # SQLite database (auto-created on first run)
├── requirements.txt            # Python dependencies
├── README.md                   # Complete documentation and setup guide
│
├── templates/                  # Jinja2 HTML Templates
│   ├── base.html               # Base layout with sidebar, navbar, and flash alerts
│   ├── login.html              # Authentication sign-in page
│   ├── register.html           # Student registration page
│   ├── student_dashboard.html  # Student metrics and complaints table
│   ├── submit_complaint.html   # Complaint submission form with photo upload
│   ├── complaint_details.html  # Student detailed view with 4-step progress tracker
│   ├── admin_dashboard.html    # Admin management panel with statistics and filters
│   └── admin_complaint.html    # Admin review and status update form
│
└── static/                     # Static Web Assets
    ├── css/
    │   └── style.css           # Modern campus design system & responsive styling
    ├── js/
    │   └── script.js           # Client-side preview, sidebar toggle, and search
    └── uploads/                # Stored complaint evidence images
```

---

## 🚀 Installation & Running the Application

### 1. Prerequisites
- Python 3.8+ installed on Windows, macOS, or Linux.

### 2. Set Up a Virtual Environment
Open a terminal (PowerShell or Command Prompt on Windows) in the project directory:

```bash
# Create a virtual environment named 'venv'
python -m venv venv

# Activate the virtual environment on Windows (PowerShell)
venv\Scripts\Activate.ps1
# OR on Command Prompt:
# venv\Scripts\activate.bat
# OR on macOS/Linux:
# source venv/bin/activate
```

### 3. Install Required Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python app.py
```

The server will automatically:
1. Initialize the `database.db` SQLite database file with all necessary tables.
2. Seed the default Administrator account if not already present.
3. Create the `static/uploads/` directory for photo uploads.
4. Launch the web server on `http://127.0.0.1:5000`.

Open your browser and navigate to:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🔑 Login Credentials

### 🛡️ Default Administrator Account
*Automatically generated when the application first runs:*
- **Email:** `admin@campus.com`
- **Password:** `admin123`

### 🎓 Student Account Instructions
1. Navigate to `http://127.0.0.1:5000/register`.
2. Enter your Full Name, Email, and Password (minimum 6 characters).
3. Click **Register Account**.
4. Log in using your registered email and password to access the Student Dashboard.

---

## 📷 How Image Upload Works
1. When a student attaches a photo in the complaint form, the client-side JavaScript (`script.js`) validates the format and provides an instant preview.
2. When submitted, the Flask backend validates the file extension against allowed formats (`.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`).
3. To prevent filename collisions and directory traversal security risks, a unique UUID-based safe filename is generated using `werkzeug.utils.secure_filename` (e.g. `cmp_a1b2c3d4_evidence.jpg`).
4. The file is saved inside `static/uploads/` and the filename is stored in the `complaints` SQLite table.
5. Both students and administrators can view the image and click it to open a full-size modal.

---

## ⚙️ How the System Works (CRUD & Architecture)
- **Create**: Students submit complaints through the `/student/submit` route, which writes a record to the `complaints` table in SQLite and saves the uploaded photo.
- **Read**: Dynamic queries fetch student-specific complaints on the student dashboard and campus-wide records on the admin dashboard.
- **Update**: Admins update the status (`Pending` ➔ `Assigned` ➔ `In Progress` ➔ `Resolved` / `Rejected`) and provide remarks via `/admin/complaint/<id>/update`.
- **Session & Security**: Sessions store the authenticated user ID and role. Custom decorators (`@login_required`, `@student_required`, `@admin_required`) protect all sensitive routes.
- **Data Persistence**: SQLite `database.db` persists all data; restarting the server retains all users, complaints, status changes, and remarks without data loss.

---

## 🛠️ Troubleshooting Common Issues

1. **PowerShell script execution policy error on `venv\Scripts\Activate`**:
   Run PowerShell as Administrator and execute:
   ```powershell
   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```
   Then try activating again.

2. **Port 5000 already in use**:
   Change the port in `app.py` at the bottom:
   ```python
   app.run(debug=True, host="127.0.0.1", port=5050)
   ```

3. **Missing `static/uploads` folder permissions**:
   The app automatically creates `static/uploads/` on launch. Ensure write permissions exist for the current user folder.

---

## 📄 License
Educational prototype built for campus facility management.
