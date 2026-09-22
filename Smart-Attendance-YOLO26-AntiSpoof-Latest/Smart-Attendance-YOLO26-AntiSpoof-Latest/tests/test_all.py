import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from config import DATABASE_URL
from database import SessionLocal
from models import Student, Faculty, Course, AttendanceSession, AttendanceRecord, User
from auth import verify_password, get_password_hash, create_access_token, decode_access_token
from schemas import AttendanceSessionRequest, FaceAttendance, AntiSpoofingResult
from attendance import process_attendance
from main import app

client = TestClient(app)


def test_database_connection():
    """Verify database connection and schema tables."""
    db = SessionLocal()
    try:
        students = db.query(Student).all()
        assert len(students) > 0, "Students table should have records"
        courses = db.query(Course).all()
        assert len(courses) > 0, "Courses table should have records"
        faculty = db.query(Faculty).all()
        assert len(faculty) > 0, "Faculty table should have records"
    finally:
        db.close()


def test_password_hashing_and_jwt():
    """Verify password hashing and JWT token life cycle."""
    pw = "secretPassword123"
    hashed = get_password_hash(pw)
    assert verify_password(pw, hashed) is True
    assert verify_password("wrongPassword", hashed) is False

    token = create_access_token({"sub": "testuser", "role": "FACULTY"})
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "testuser"
    assert payload["role"] == "FACULTY"


def test_auth_login_api():
    """Verify login API with seeded faculty user."""
    # Faculty login
    response = client.post("/auth/login", json={"username": "faculty", "password": "faculty123"})
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "access_token" in data
    assert data["role"].upper() == "FACULTY"

    # Invalid login
    bad_resp = client.post("/auth/login", json={"username": "faculty", "password": "wrongpassword"})
    assert bad_resp.status_code == 401


def test_courses_and_rooms_api():
    """Verify courses and rooms listing endpoints."""
    resp = client.get("/courses")
    assert resp.status_code == 200
    courses = resp.json()
    assert len(courses) >= 6

    resp_rooms = client.get("/rooms")
    assert resp_rooms.status_code == 200
    rooms = resp_rooms.json()
    assert len(rooms) >= 6


def test_attendance_session_processing():
    """Verify course-filtered attendance marking and absent calculation."""
    db = SessionLocal()
    try:
        session_id = "TEST_SESSION_001"
        # Cleanup any prior test run
        db.query(AttendanceRecord).filter(AttendanceRecord.session_id == session_id).delete()
        db.query(AttendanceSession).filter(AttendanceSession.session_id == session_id).delete()
        db.commit()

        # Enrolled student in CSE2025: 24BCA3008
        request = AttendanceSessionRequest(
            attendance_session=session_id,
            course_id="CSE2025",
            room_number=401,
            faculty_id="F001",
            faces=[
                FaceAttendance(
                    face_id=1,
                    student_id="24BCA3008",
                    anti_spoofing=AntiSpoofingResult(label="REAL", confidence=0.98),
                    attendance_allowed=True,
                    recognition_confidence=95.4,
                )
            ],
        )

        results = process_attendance(db, request)
        assert len(results) > 0

        present_rec = next((r for r in results if r["student_id"] == "24BCA3008"), None)
        assert present_rec is not None
        assert present_rec["status"] == "PRESENT"
        assert present_rec["anti_spoofing_label"] == "REAL"

        # Verify attendance record saved in DB
        db_rec = db.query(AttendanceRecord).filter(
            AttendanceRecord.session_id == session_id,
            AttendanceRecord.registration_number == "24BCA3008"
        ).first()
        assert db_rec is not None
        assert db_rec.status == "PRESENT"

        # Clean up test session
        db.query(AttendanceRecord).filter(AttendanceRecord.session_id == session_id).delete()
        db.query(AttendanceSession).filter(AttendanceSession.session_id == session_id).delete()
        db.commit()
    finally:
        db.close()


def test_analytics_api():
    """Verify analytics stats endpoint."""
    resp = client.get("/analytics")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_students" in data
    assert "total_courses" in data
    assert data["total_students"] > 0
    assert data["total_courses"] > 0


def test_static_files_served():
    """Verify index.html and frontend assets are served correctly."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "<title>" in resp.text

    resp_dash = client.get("/dashboard.html")
    assert resp_dash.status_code == 200


def test_no_face_data_student_workflow():
    """Verify students without face dataset (24BCA8190, 24BCA5631) workflow:
    1. Remain registered students and enrolled in courses.
    2. Correctly identified via /courses/{course_id}/no-face-data endpoint.
    3. At attendance finalization, assigned FACE_DATA_UNAVAILABLE with specific message.
    4. Enrolled-but-undetected students with face data get ABSENT.
    5. No false PRESENT marking or identity swapping.
    """
    db = SessionLocal()
    try:
        # 1. Verify students exist and are registered
        s_5631 = db.query(Student).filter(Student.registration_number == "24BCA5631").first()
        s_8190 = db.query(Student).filter(Student.registration_number == "24BCA8190").first()
        assert s_5631 is not None, "24BCA5631 must remain registered"
        assert s_8190 is not None, "24BCA8190 must remain registered"

        # 2. Verify course enrollments
        resp_c = client.get("/courses/CSE2025")
        assert resp_c.status_code == 200
        course_data = resp_c.json()
        enrolled_ids = [s["registration_number"] for s in course_data["students"]]
        assert "24BCA5631" in enrolled_ids, "24BCA5631 must be enrolled in CSE2025"

        # 3. Verify no-face-data endpoint identifies them
        resp_nf = client.get("/courses/CSE2025/no-face-data")
        assert resp_nf.status_code == 200
        nf_ids = resp_nf.json().get("no_face_data", [])
        assert "24BCA5631" in nf_ids

        # 4. Finalize attendance session where 24BCA5631 is not detected
        session_id = "TEST_NO_FACE_SESSION_01"
        db.query(AttendanceRecord).filter(AttendanceRecord.session_id == session_id).delete()
        db.query(AttendanceSession).filter(AttendanceSession.session_id == session_id).delete()
        db.commit()

        # Let 24BCA3008 be the only detected real face
        request = AttendanceSessionRequest(
            attendance_session=session_id,
            course_id="CSE2025",
            room_number=401,
            faculty_id="F001",
            faces=[
                FaceAttendance(
                    face_id=1,
                    student_id="24BCA3008",
                    anti_spoofing=AntiSpoofingResult(label="REAL", confidence=0.99),
                    attendance_allowed=True,
                    recognition_confidence=97.0,
                )
            ],
        )

        results = process_attendance(db, request)

        # Find 24BCA5631 record
        rec_5631 = next((r for r in results if r["student_id"] == "24BCA5631"), None)
        assert rec_5631 is not None
        assert rec_5631["status"] == "FACE_DATA_UNAVAILABLE"
        assert "Face data unavailable" in rec_5631["message"]

        # Verify other absent students get ABSENT message
        other_absent = [r for r in results if r["status"] == "ABSENT"]
        assert len(other_absent) > 0
        assert "Student not detected — marked Absent." in other_absent[0]["message"]

        # Verify DB record
        db_rec = db.query(AttendanceRecord).filter(
            AttendanceRecord.session_id == session_id,
            AttendanceRecord.registration_number == "24BCA5631"
        ).first()
        assert db_rec is not None
        assert db_rec.status == "FACE_DATA_UNAVAILABLE"

        # Cleanup
        db.query(AttendanceRecord).filter(AttendanceRecord.session_id == session_id).delete()
        db.query(AttendanceSession).filter(AttendanceSession.session_id == session_id).delete()
        db.commit()
    finally:
        db.close()

