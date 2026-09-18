from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    course = Column(String, nullable=True)

    attendance = relationship("Attendance", back_populates="student")


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(
        String,
        ForeignKey("students.student_id"),
        nullable=False
    )

    session_id = Column(String, nullable=False)
    status = Column(String, nullable=False)
    confidence = Column(Float, nullable=True)
    anti_spoofing_label = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="attendance")