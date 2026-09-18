from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import Student, Attendance
from schemas import (
    StudentCreate,
    StudentResponse,
    AttendanceSessionRequest
)
from attendance import process_attendance


# Create database tables
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Smart Attendance Backend",
    description="Member 4 - Attendance and Database Backend",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "Smart Attendance Backend is running"
    }


# --------------------------------------------------
# STUDENT APIs
# --------------------------------------------------

@app.post("/students", response_model=StudentResponse)
def create_student(
    student: StudentCreate,
    db: Session = Depends(get_db)
):
    existing = db.query(Student).filter(
        Student.student_id == student.student_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Student already exists"
        )

    new_student = Student(
        student_id=student.student_id,
        name=student.name,
        course=student.course
    )

    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    return new_student


@app.get("/students")
def get_students(
    db: Session = Depends(get_db)
):
    students = db.query(Student).all()

    return [
        {
            "student_id": student.student_id,
            "name": student.name,
            "course": student.course
        }
        for student in students
    ]


# --------------------------------------------------
# ATTENDANCE API
# --------------------------------------------------

@app.post("/attendance")
def mark_attendance(
    request: AttendanceSessionRequest,
    db: Session = Depends(get_db)
):
    results = process_attendance(db, request)

    return {
        "attendance_session": request.attendance_session,
        "results": results
    }


# --------------------------------------------------
# GET ATTENDANCE
# --------------------------------------------------

@app.get("/attendance")
def get_attendance(
    session_id: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(Attendance)

    if session_id:
        query = query.filter(
            Attendance.session_id == session_id
        )

    records = query.all()

    return [
        {
            "student_id": record.student_id,
            "session_id": record.session_id,
            "status": record.status,
            "confidence": record.confidence,
            "anti_spoofing_label": record.anti_spoofing_label,
            "timestamp": record.timestamp
        }
        for record in records
    ]