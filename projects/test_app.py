import io
import os
import sqlite3
import time
from pathlib import Path
from app import app, init_db, DATABASE

def run_tests():
    print("=========================================")
    print("  RUNNING COMPREHENSIVE FLASK TESTS")
    print("=========================================\n")

    # Reset DB for fresh clean test run
    if DATABASE.exists():
        try:
            os.remove(DATABASE)
        except Exception:
            pass

    client = app.test_client()

    # 1. Test database initialization
    init_db()
    assert DATABASE.exists(), "database.db was not created!"
    print("[PASS] Database initialized successfully.")

    # 2. Verify Admin user created
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT email, role FROM users WHERE email = 'admin@campus.com'")
    admin_row = cursor.fetchone()
    assert admin_row is not None, "Admin user missing!"
    assert admin_row[1] == 'admin', "Admin role is incorrect!"
    print(f"[PASS] Default admin verified: {admin_row[0]} ({admin_row[1]})")
    conn.close()

    # 3. Test Student Registration
    res = client.post('/register', data={
        'name': 'John Doe',
        'email': 'johndoe@campus.edu',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Registration successful" in res.data
    print("[PASS] Student registration works.")

    # 4. Test Duplicate Email Prevention
    res = client.post('/register', data={
        'name': 'Duplicate User',
        'email': 'johndoe@campus.edu',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    assert b"Email already registered" in res.data
    print("[PASS] Duplicate email validation works.")

    # 5. Test Student Login
    res = client.post('/login', data={
        'email': 'johndoe@campus.edu',
        'password': 'password123'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Welcome back, John Doe" in res.data
    assert b"Student Dashboard" in res.data
    print("[PASS] Student login & redirection works.")

    # 6. Test Complaint Submission (with dummy photo upload)
    dummy_image = (io.BytesIO(b"fake image content test"), 'campus_fan.jpg')
    res = client.post('/student/submit', data={
        'category': 'Broken Fan',
        'title': 'Ceiling fan in room 204 not working',
        'description': 'The fan makes loud noise and stopped rotating.',
        'location': 'Science Block Room 204',
        'photo': dummy_image
    }, content_type='multipart/form-data', follow_redirects=True)
    assert res.status_code == 200
    assert b"Complaint submitted successfully" in res.data
    assert b"CMP-0001" in res.data
    assert b"Science Block Room 204" in res.data
    print("[PASS] Complaint submission with image upload & code CMP-0001 works.")

    # 7. Test Student Dashboard shows real database data
    res = client.get('/student/dashboard')
    assert res.status_code == 200
    assert b"CMP-0001" in res.data
    assert b"Ceiling fan in room 204 not working" in res.data
    print("[PASS] Student dashboard displays complaint from SQLite.")

    # 8. Test Student trying to access Admin route (Should be denied / redirected)
    res = client.get('/admin/dashboard', follow_redirects=True)
    assert b"Unauthorized access" in res.data or b"Student Dashboard" in res.data
    print("[PASS] Student role authorization protection verified.")

    # 9. Test Logout
    res = client.get('/logout', follow_redirects=True)
    assert b"logged out" in res.data
    print("[PASS] Logout works.")

    # 10. Test Admin Login
    res = client.post('/login', data={
        'email': 'admin@campus.com',
        'password': 'admin123'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Campus Administration" in res.data or b"Admin Dashboard" in res.data
    assert b"CMP-0001" in res.data
    print("[PASS] Admin login and view all complaints works.")

    # 11. Test Admin Complaint Details & Status Update
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM complaints WHERE complaint_code = 'CMP-0001'")
    cmp_id = cursor.fetchone()[0]
    conn.close()

    res = client.get(f'/admin/complaint/{cmp_id}')
    assert res.status_code == 200
    assert b"John Doe" in res.data
    assert b"johndoe@campus.edu" in res.data

    # Update status to "In Progress" with an admin remark
    res = client.post(f'/admin/complaint/{cmp_id}/update', data={
        'status': 'In Progress',
        'admin_remark': 'Electrician Mr. Robert assigned to repair.'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Complaint updated successfully" in res.data
    assert b"In Progress" in res.data
    print("[PASS] Admin status update & remarks work.")

    # 12. Test Student Tracking View reflects the In Progress status & remark
    client.get('/logout')
    client.post('/login', data={
        'email': 'johndoe@campus.edu',
        'password': 'password123'
    }, follow_redirects=True)
    res = client.get(f'/student/complaint/{cmp_id}')
    assert res.status_code == 200
    assert b"Electrician Mr. Robert assigned to repair." in res.data
    assert b"In Progress" in res.data
    print("[PASS] Student tracking reflects real-time admin status update & remark.")

    # 13. Test data persistence across app re-init
    init_db() # simulate app restart
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM complaints")
    count = cursor.fetchone()[0]
    assert count >= 1, "Data was deleted upon re-initialization!"
    conn.close()
    print(f"[PASS] Data persistence verified across application restarts ({count} complaint(s) preserved).")

    print("\n=========================================")
    print("  ALL 13 END-TO-END TESTS PASSED 100%!")
    print("=========================================\n")

if __name__ == '__main__':
    run_tests()
