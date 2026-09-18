from pydantic import BaseModel, Field
from typing import Optional, List


class AntiSpoofingResult(BaseModel):
    label: str = Field(..., pattern="^(REAL|SPOOF|UNKNOWN)$")
    confidence: float = Field(..., ge=0.0, le=1.0)


class FaceAttendance(BaseModel):
    face_id: int
    student_id: Optional[str] = None
    anti_spoofing: AntiSpoofingResult
    attendance_allowed: bool


class AttendanceSessionRequest(BaseModel):
    attendance_session: str
    faces: List[FaceAttendance]


class AttendanceResponse(BaseModel):
    attendance_session: str
    student_id: str
    status: str
    confidence: Optional[float] = None
    anti_spoofing_label: Optional[str] = None


class StudentCreate(BaseModel):
    student_id: str
    name: str
    course: Optional[str] = None


class StudentResponse(BaseModel):
    student_id: str
    name: str
    course: Optional[str] = None

    class Config:
        from_attributes = True