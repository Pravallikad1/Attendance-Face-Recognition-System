from sqlalchemy.orm import Session

from models import Student, Attendance
from schemas import AttendanceSessionRequest


def process_attendance(
    db: Session,
    request: AttendanceSessionRequest
):
    results = []

    # Get all registered students
    students = db.query(Student).all()

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
                "anti_spoofing_label": face.anti_spoofing.label
            })
            continue

        # Find registered student
        student = db.query(Student).filter(
            Student.student_id == face.student_id
        ).first()

        # --------------------------------------------------
        # REAL + REGISTERED + ATTENDANCE ALLOWED
        # --------------------------------------------------
        if (
            student
            and face.anti_spoofing.label == "REAL"
            and face.attendance_allowed
        ):
            present_students.add(face.student_id)

            existing = db.query(Attendance).filter(
                Attendance.student_id == face.student_id,
                Attendance.session_id == request.attendance_session
            ).first()

            if not existing:
                attendance = Attendance(
                    student_id=face.student_id,
                    session_id=request.attendance_session,
                    status="PRESENT",
                    confidence=face.anti_spoofing.confidence,
                    anti_spoofing_label="REAL"
                )

                db.add(attendance)

            results.append({
                "student_id": face.student_id,
                "status": "PRESENT",
                "confidence": face.anti_spoofing.confidence,
                "anti_spoofing_label": "REAL"
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
                "anti_spoofing_label": "SPOOF"
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
                "anti_spoofing_label": face.anti_spoofing.label
            })

        # --------------------------------------------------
        # UNKNOWN STUDENT ID
        # --------------------------------------------------
        else:
            results.append({
                "student_id": face.student_id,
                "status": "UNKNOWN",
                "confidence": face.anti_spoofing.confidence,
                "anti_spoofing_label": face.anti_spoofing.label
            })

    # --------------------------------------------------
    # MARK ONLY UNDETECTED STUDENTS AS ABSENT
    # --------------------------------------------------
    for student in students:

        # Skip students already processed
        if student.student_id in present_students:
            continue

        if student.student_id in rejected_students:
            continue

        existing = db.query(Attendance).filter(
            Attendance.student_id == student.student_id,
            Attendance.session_id == request.attendance_session
        ).first()

        if not existing:
            attendance = Attendance(
                student_id=student.student_id,
                session_id=request.attendance_session,
                status="ABSENT",
                confidence=None,
                anti_spoofing_label=None
            )

            db.add(attendance)

            results.append({
                "student_id": student.student_id,
                "status": "ABSENT",
                "confidence": None,
                "anti_spoofing_label": None
            })

    db.commit()

    return results