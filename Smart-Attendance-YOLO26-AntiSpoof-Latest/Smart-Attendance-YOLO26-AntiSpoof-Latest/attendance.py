from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from models import Student, StudentCourse, AttendanceRecord, AttendanceSession
from schemas import AttendanceSessionRequest
from src.face_recognition import get_students_without_face_data


def process_attendance(
    db: Session,
    request: AttendanceSessionRequest,
) -> List[Dict[str, Any]]:
    results = []
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today_date = datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.now().strftime("%H:%M:%S")

    # 1. Ensure AttendanceSession is recorded
    if request.attendance_session:
        existing_session = db.query(AttendanceSession).filter(
            AttendanceSession.session_id == request.attendance_session
        ).first()

        if not existing_session:
            new_session = AttendanceSession(
                session_id=request.attendance_session,
                course_id=request.course_id or "GENERAL",
                faculty_id=request.faculty_id,
                room_number=request.room_number,
                date=today_date,
                start_time=current_time,
                end_time=None,
            )
            db.add(new_session)
            db.commit()

    # 2. Determine target student list for absent marking (filtered by course if specified)
    if request.course_id:
        enrolled = db.query(StudentCourse).filter(
            StudentCourse.course_id == request.course_id
        ).all()
        target_student_ids = {ec.registration_number for ec in enrolled}
        # If no students enrolled under this course code, fallback to all active students
        if not target_student_ids:
            all_students = db.query(Student).all()
            target_student_ids = {s.registration_number for s in all_students}
    else:
        all_students = db.query(Student).all()
        target_student_ids = {s.registration_number for s in all_students}

    # Enrolled students who have NO reference images in the dataset and can
    # therefore never be automatically recognised by the AI pipeline.
    no_face_data = get_students_without_face_data(target_student_ids)

    # Students who are confirmed PRESENT
    present_students = set()

    # Students whose face was detected but attendance was rejected
    rejected_students = set()

    for face in request.faces:
        # --------------------------------------------------
        # UNKNOWN FACE
        # --------------------------------------------------
        if face.student_id is None:
            results.append({
                "student_id": None,
                "status": "UNKNOWN",
                "confidence": face.anti_spoofing.confidence,
                "anti_spoofing_label": face.anti_spoofing.label,
                "recognition_confidence": face.recognition_confidence,
            })
            continue

        # Find registered student
        student = db.query(Student).filter(
            Student.registration_number == face.student_id
        ).first()

        rec_conf = getattr(face, "recognition_confidence", None)

        # --------------------------------------------------
        # REAL + REGISTERED + ATTENDANCE ALLOWED
        # --------------------------------------------------
        if (
            student
            and face.anti_spoofing.label == "REAL"
            and face.attendance_allowed
        ):
            present_students.add(face.student_id)

            existing = db.query(AttendanceRecord).filter(
                AttendanceRecord.registration_number == face.student_id,
                AttendanceRecord.session_id == request.attendance_session
            ).first()

            if not existing:
                attendance = AttendanceRecord(
                    registration_number=face.student_id,
                    session_id=request.attendance_session,
                    status="PRESENT",
                    confidence=face.anti_spoofing.confidence,
                    anti_spoofing_label="REAL",
                    recognition_confidence=rec_conf,
                    timestamp=now_str,
                )
                db.add(attendance)
            else:
                existing.status = "PRESENT"
                existing.confidence = face.anti_spoofing.confidence
                existing.anti_spoofing_label = "REAL"
                existing.recognition_confidence = rec_conf
                existing.timestamp = now_str

            results.append({
                "student_id": face.student_id,
                "status": "PRESENT",
                "confidence": face.anti_spoofing.confidence,
                "anti_spoofing_label": "REAL",
                "recognition_confidence": rec_conf,
            })

        # --------------------------------------------------
        # SPOOF DETECTED
        # --------------------------------------------------
        elif (
            student
            and face.anti_spoofing.label == "SPOOF"
        ):
            rejected_students.add(face.student_id)
            results.append({
                "student_id": face.student_id,
                "status": "REJECTED_SPOOF",
                "confidence": face.anti_spoofing.confidence,
                "anti_spoofing_label": "SPOOF",
                "recognition_confidence": rec_conf,
            })

        # --------------------------------------------------
        # REGISTERED BUT NOT ALLOWED
        # --------------------------------------------------
        elif student:
            rejected_students.add(face.student_id)
            results.append({
                "student_id": face.student_id,
                "status": "REJECTED",
                "confidence": face.anti_spoofing.confidence,
                "anti_spoofing_label": face.anti_spoofing.label,
                "recognition_confidence": rec_conf,
            })

        # --------------------------------------------------
        # UNKNOWN STUDENT ID
        # --------------------------------------------------
        else:
            results.append({
                "student_id": face.student_id,
                "status": "UNKNOWN",
                "confidence": face.anti_spoofing.confidence,
                "anti_spoofing_label": face.anti_spoofing.label,
                "recognition_confidence": rec_conf,
            })

    # --------------------------------------------------
    # MARK ONLY ENROLLED, UNDETECTED STUDENTS AS ABSENT
    # (or FACE_DATA_UNAVAILABLE when the student has no reference images)
    # --------------------------------------------------
    for reg_no in target_student_ids:
        # Skip students already processed
        if reg_no in present_students or reg_no in rejected_students:
            continue

        # Distinguish between "no face data" and "has data but was not detected"
        if reg_no in no_face_data:
            final_status = "FACE_DATA_UNAVAILABLE"
            message = "Face data unavailable — student could not be automatically verified."
        else:
            final_status = "ABSENT"
            message = "Student not detected — marked Absent."

        existing = db.query(AttendanceRecord).filter(
            AttendanceRecord.registration_number == reg_no,
            AttendanceRecord.session_id == request.attendance_session
        ).first()

        if not existing:
            attendance = AttendanceRecord(
                registration_number=reg_no,
                session_id=request.attendance_session,
                status=final_status,
                confidence=None,
                anti_spoofing_label=None,
                recognition_confidence=None,
                timestamp=now_str,
            )
            db.add(attendance)

        results.append({
            "student_id": reg_no,
            "status": final_status,
            "message": message,
            "confidence": None,
            "anti_spoofing_label": None,
            "recognition_confidence": None,
        })

    db.commit()
    return results