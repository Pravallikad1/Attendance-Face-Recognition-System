from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from config import DEBUG, HOST, PORT
from database import Base, engine, get_db
from models import (
    Student,
    Faculty,
    Course,
    StudentCourse,
    Room,
    Timetable,
    AttendanceSession,
    AttendanceRecord,
    User,
)
from schemas import (
    StudentCreate,
    StudentResponse,
    AttendanceSessionRequest,
    LoginRequest,
    TokenResponse,
    CourseResponse,
    RoomResponse,
)
from auth import (
    verify_password,
    create_access_token,
    get_current_user,
    require_faculty,
    require_student,
)
from attendance import process_attendance

# Initialize tables (safe no-op if tables exist)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart Attendance System API",
    description=(
        "Smart Attendance Platform powered by YOLO26 face detection, "
        "MiniFASNetV2 anti-spoofing, and FaceNet recognition."
    ),
    version="2.0.0",
)

# --------------------------------------------------
# CORS MIDDLEWARE
# --------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# AUTHENTICATION APIs
# --------------------------------------------------
@app.post("/auth/login", response_model=TokenResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate student or faculty member and return JWT token."""
    user = db.query(User).filter(
        (User.username == credentials.username) |
        (User.registration_number == credentials.username) |
        (User.user_id == credentials.username)
    ).first()

    if not user:
        # Check faculty email
        faculty = db.query(Faculty).filter(Faculty.email == credentials.username).first()
        if faculty:
            user = db.query(User).filter(User.faculty_id == faculty.faculty_id).first()

    if not user or not verify_password(credentials.password, user.password_hash or ""):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Determine display name
    name = user.username
    if user.role.upper() == "FACULTY" and user.faculty_id:
        fac = db.query(Faculty).filter(Faculty.faculty_id == user.faculty_id).first()
        if fac:
            name = fac.faculty_name
    elif user.role.upper() == "STUDENT" and user.registration_number:
        stu = db.query(Student).filter(Student.registration_number == user.registration_number).first()
        if stu and stu.student_name:
            name = stu.student_name

    token = create_access_token(
        data={
            "sub": user.username,
            "role": user.role,
            "user_id": user.user_id,
            "registration_number": user.registration_number,
            "faculty_id": user.faculty_id,
            "name": name,
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.user_id,
        "name": name,
        "registration_number": user.registration_number,
        "faculty_id": user.faculty_id,
    }


@app.get("/auth/me")
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the authenticated user profile."""
    name = current_user.username
    if current_user.role.upper() == "FACULTY" and current_user.faculty_id:
        fac = db.query(Faculty).filter(Faculty.faculty_id == current_user.faculty_id).first()
        if fac:
            name = fac.faculty_name
    elif current_user.role.upper() == "STUDENT" and current_user.registration_number:
        stu = db.query(Student).filter(Student.registration_number == current_user.registration_number).first()
        if stu and stu.student_name:
            name = stu.student_name

    return {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "role": current_user.role,
        "name": name,
        "registration_number": current_user.registration_number,
        "faculty_id": current_user.faculty_id,
        "status": current_user.status,
    }


# --------------------------------------------------
# COURSE & ROOM APIs
# --------------------------------------------------
@app.get("/courses", response_model=List[CourseResponse])
def get_courses(db: Session = Depends(get_db)):
    """List all available courses."""
    return db.query(Course).all()


@app.get("/courses/{course_id}")
def get_course_detail(course_id: str, db: Session = Depends(get_db)):
    """Get course information and enrolled students."""
    course = db.query(Course).filter(Course.course_id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    enrollments = db.query(StudentCourse).filter(StudentCourse.course_id == course_id).all()
    enrolled_ids = [e.registration_number for e in enrollments]

    students = db.query(Student).filter(Student.registration_number.in_(enrolled_ids)).all() if enrolled_ids else []

    return {
        "course_id": course.course_id,
        "course_name": course.course_name,
        "faculty_id": course.faculty_id,
        "semester": course.semester,
        "slot": course.slot,
        "enrolled_count": len(students),
        "students": [
            {
                "registration_number": s.registration_number,
                "student_name": s.student_name or f"Student {s.registration_number}",
                "status": s.status,
            }
            for s in students
        ],
    }


@app.get("/courses/{course_id}/no-face-data")
def get_course_no_face_data(course_id: str, db: Session = Depends(get_db)):
    """Return enrolled student IDs that have no reference face images in the dataset."""
    from src.face_recognition import get_students_without_face_data

    enrollments = db.query(StudentCourse).filter(StudentCourse.course_id == course_id).all()
    enrolled_ids = {e.registration_number for e in enrollments}
    no_data_ids = get_students_without_face_data(enrolled_ids)
    return {"course_id": course_id, "no_face_data": sorted(no_data_ids)}


@app.get("/rooms", response_model=List[RoomResponse])
def get_rooms(db: Session = Depends(get_db)):
    """List all classroom rooms."""
    return db.query(Room).all()


@app.get("/timetable")
def get_timetable(db: Session = Depends(get_db)):
    """Get weekly timetable."""
    return db.query(Timetable).all()


# --------------------------------------------------
# STUDENT APIs
# --------------------------------------------------
@app.get("/students")
def get_students(db: Session = Depends(get_db)):
    """List all students."""
    students = db.query(Student).all()
    return [
        {
            "student_id": s.registration_number,
            "registration_number": s.registration_number,
            "name": s.student_name or f"Student {s.registration_number}",
            "semester": s.semester,
            "status": s.status,
        }
        for s in students
    ]


@app.get("/students/{student_id}")
def get_student_detail(student_id: str, db: Session = Depends(get_db)):
    """Get individual student profile, courses, and attendance statistics."""
    student = db.query(Student).filter(Student.registration_number == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    enrolled = db.query(StudentCourse).filter(StudentCourse.registration_number == student_id).all()
    records = db.query(AttendanceRecord).filter(AttendanceRecord.registration_number == student_id).all()

    total_sessions = len(records)
    present_sessions = sum(1 for r in records if r.status == "PRESENT")
    percentage = round((present_sessions / total_sessions * 100), 2) if total_sessions > 0 else 100.0

    return {
        "student_id": student.registration_number,
        "registration_number": student.registration_number,
        "name": student.student_name or f"Student {student.registration_number}",
        "email": student.email,
        "semester": student.semester,
        "status": student.status,
        "total_sessions": total_sessions,
        "present_sessions": present_sessions,
        "absent_sessions": total_sessions - present_sessions,
        "attendance_percentage": percentage,
        "courses": [
            {
                "course_id": c.course_id,
                "course_name": c.course_name,
                "semester": c.semester,
            }
            for c in enrolled
        ],
        "attendance_history": [
            {
                "session_id": r.session_id,
                "status": r.status,
                "confidence": r.confidence,
                "recognition_confidence": r.recognition_confidence,
                "anti_spoofing_label": r.anti_spoofing_label,
                "timestamp": r.timestamp,
            }
            for r in records
        ],
    }


@app.post("/students", response_model=StudentResponse)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    """Create a new student record."""
    existing = db.query(Student).filter(
        Student.registration_number == student.student_id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Student already exists")

    new_student = Student(
        registration_number=student.student_id,
        student_name=student.name,
        semester=5,
        status="Active",
    )
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return {
        "student_id": new_student.registration_number,
        "name": new_student.student_name,
        "course": None,
    }


# --------------------------------------------------
# IMAGE ANALYSIS API (AI Pipeline)
# --------------------------------------------------
@app.post("/analyze-image")
async def analyze_uploaded_image(image: UploadFile = File(...)):
    """
    Run one captured classroom image through:
    YOLO26 -> MiniFASNetV2 -> FaceNet.
    Returns detected faces, bounding boxes, liveness, and recognized student IDs.
    """
    if image.content_type and not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload an image file.")

    try:
        from src.attendance_pipeline import decode_image_bytes, analyze_image

        data = await image.read()
        frame = decode_image_bytes(data)
        faces = analyze_image(frame)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Image analysis failed: {type(exc).__name__} - {str(exc)}",
        ) from exc

    return {
        "filename": image.filename,
        "faces_detected": len(faces),
        "faces": faces,
    }


# --------------------------------------------------
# ATTENDANCE APIs
# --------------------------------------------------
@app.post("/attendance")
def mark_attendance(
    request: AttendanceSessionRequest,
    db: Session = Depends(get_db),
):
    """Commit verified attendance session and records to the database."""
    results = process_attendance(db, request)
    return {
        "attendance_session": request.attendance_session,
        "course_id": request.course_id,
        "results": results,
    }


@app.get("/attendance")
def get_attendance(
    session_id: Optional[str] = None,
    student_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Query recorded attendance entries."""
    query = db.query(AttendanceRecord)
    if session_id:
        query = query.filter(AttendanceRecord.session_id == session_id)
    if student_id:
        query = query.filter(AttendanceRecord.registration_number == student_id)

    records = query.all()
    return [
        {
            "student_id": record.registration_number,
            "registration_number": record.registration_number,
            "session_id": record.session_id,
            "status": record.status,
            "confidence": record.confidence,
            "recognition_confidence": record.recognition_confidence,
            "anti_spoofing_label": record.anti_spoofing_label,
            "timestamp": record.timestamp,
        }
        for record in records
    ]


@app.get("/attendance/sessions")
def get_attendance_sessions(db: Session = Depends(get_db)):
    """List all recorded sessions with aggregate totals."""
    sessions = db.query(AttendanceSession).order_by(desc(AttendanceSession.date)).all()
    results = []
    for s in sessions:
        records = db.query(AttendanceRecord).filter(AttendanceRecord.session_id == s.session_id).all()
        course = db.query(Course).filter(Course.course_id == s.course_id).first()
        course_name = course.course_name if course else s.course_id

        total = len(records)
        present = sum(1 for r in records if r.status == "PRESENT")
        absent = sum(1 for r in records if r.status == "ABSENT")

        results.append({
            "id": s.session_id,
            "session_id": s.session_id,
            "date": s.date,
            "time": s.start_time,
            "course": course_name,
            "course_id": s.course_id,
            "room": f"Room {s.room_number}" if s.room_number else "Main Hall",
            "room_number": s.room_number,
            "faculty_id": s.faculty_id,
            "total": total,
            "present": present,
            "absent": absent,
        })
    return results


@app.get("/analytics")
def get_analytics(db: Session = Depends(get_db)):
    """Get aggregate attendance stats and course-wise percentages."""
    total_records = db.query(AttendanceRecord).count()
    present_records = db.query(AttendanceRecord).filter(AttendanceRecord.status == "PRESENT").count()
    overall_pct = round((present_records / total_records * 100), 2) if total_records > 0 else 0.0

    total_students = db.query(Student).count()
    total_courses = db.query(Course).count()
    total_sessions = db.query(AttendanceSession).count()

    # Course-wise breakdown
    courses = db.query(Course).all()
    course_stats = []
    for c in courses:
        sessions = db.query(AttendanceSession).filter(AttendanceSession.course_id == c.course_id).all()
        s_ids = [s.session_id for s in sessions]
        c_records = db.query(AttendanceRecord).filter(AttendanceRecord.session_id.in_(s_ids)).all() if s_ids else []
        c_total = len(c_records)
        c_present = sum(1 for r in c_records if r.status == "PRESENT")
        c_pct = round((c_present / c_total * 100), 2) if c_total > 0 else 0.0
        course_stats.append({
            "course_id": c.course_id,
            "course_name": c.course_name,
            "total_sessions": len(sessions),
            "attendance_rate": c_pct,
        })

    return {
        "overall_attendance_rate": overall_pct,
        "total_students": total_students,
        "total_courses": total_courses,
        "total_sessions": total_sessions,
        "courses": course_stats,
    }


# --------------------------------------------------
# FRONTEND STATIC FILES SERVING
# --------------------------------------------------
frontend_dir = Path(__file__).resolve().parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(str(frontend_dir / "index.html"))

    @app.get("/{page_name}.html")
    def serve_html_page(page_name: str):
        page_path = frontend_dir / f"{page_name}.html"
        if page_path.exists():
            return FileResponse(str(page_path))
        raise HTTPException(status_code=404, detail="Page not found")
