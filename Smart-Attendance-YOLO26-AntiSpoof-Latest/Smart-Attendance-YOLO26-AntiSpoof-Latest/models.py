from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from database import Base


class Student(Base):
    __tablename__ = "students"

    registration_number = Column(String, primary_key=True, index=True)
    student_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    semester = Column(Integer, nullable=True)
    status = Column(String, default="Active")

    # Compatibility properties for legacy code expecting .student_id and .name
    @property
    def student_id(self):
        return self.registration_number

    @student_id.setter
    def student_id(self, val):
        self.registration_number = val

    @property
    def name(self):
        return self.student_name or f"Student {self.registration_number}"

    @name.setter
    def name(self, val):
        self.student_name = val

    @property
    def course(self):
        return None


class Faculty(Base):
    __tablename__ = "faculty"

    faculty_id = Column(String, primary_key=True, index=True)
    faculty_name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    department = Column(String, nullable=True)
    designation = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    status = Column(String, default="ACTIVE")


class Course(Base):
    __tablename__ = "courses"

    course_id = Column(String, primary_key=True, index=True)
    course_name = Column(String, nullable=False)
    faculty_id = Column(String, nullable=True)
    semester = Column(Integer, nullable=True)
    slot = Column(String, nullable=True)


class StudentCourse(Base):
    __tablename__ = "student_courses"

    registration_number = Column(String, primary_key=True)
    course_id = Column(String, primary_key=True)
    course_name = Column(String, nullable=True)
    semester = Column(Integer, nullable=True)


class Room(Base):
    __tablename__ = "rooms"

    building_code = Column(String, nullable=True)
    room_number = Column(Integer, primary_key=True)
    capacity = Column(Integer, nullable=True)


class Timetable(Base):
    __tablename__ = "timetable"

    course_id = Column(String, primary_key=True)
    faculty_id = Column(String, nullable=True)
    room_number = Column(Integer, primary_key=True)
    day = Column(String, primary_key=True)
    start_time = Column(String, primary_key=True)
    end_time = Column(String, nullable=True)


class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"

    session_id = Column(String, primary_key=True, index=True)
    course_id = Column(String, nullable=False)
    faculty_id = Column(String, nullable=True)
    room_number = Column(Integer, nullable=True)
    date = Column(String, nullable=True)
    start_time = Column(String, nullable=True)
    end_time = Column(String, nullable=True)


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    record_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    session_id = Column(String, nullable=False, index=True)
    registration_number = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False)
    confidence = Column(Float, nullable=True)
    anti_spoofing_label = Column(String, nullable=True)
    timestamp = Column(String, nullable=True)
    recognition_confidence = Column(Float, nullable=True)

    # Compatibility properties for legacy code expecting .student_id
    @property
    def student_id(self):
        return self.registration_number

    @student_id.setter
    def student_id(self, val):
        self.registration_number = val


# Backward compatibility alias
Attendance = AttendanceRecord


class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, nullable=False)  # "FACULTY" or "STUDENT"
    registration_number = Column(String, nullable=True)
    faculty_id = Column(String, nullable=True)
    status = Column(String, default="ACTIVE")
    password_hash = Column(String, nullable=True)