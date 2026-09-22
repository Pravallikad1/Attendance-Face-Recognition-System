from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class AntiSpoofingResult(BaseModel):
    label: str = Field(..., pattern="^(REAL|SPOOF|UNKNOWN)$")
    confidence: float = Field(..., ge=0.0, le=1.0)


class FaceAttendance(BaseModel):
    face_id: int
    student_id: Optional[str] = None
    anti_spoofing: AntiSpoofingResult
    attendance_allowed: bool
    recognition_confidence: Optional[float] = None


class AttendanceSessionRequest(BaseModel):
    attendance_session: str
    course_id: Optional[str] = None
    room_number: Optional[int] = None
    faculty_id: Optional[str] = None
    faces: List[FaceAttendance]


class AttendanceResponse(BaseModel):
    attendance_session: str
    student_id: str
    status: str
    confidence: Optional[float] = None
    anti_spoofing_label: Optional[str] = None
    recognition_confidence: Optional[float] = None


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


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: str
    name: str
    registration_number: Optional[str] = None
    faculty_id: Optional[str] = None


class CourseResponse(BaseModel):
    course_id: str
    course_name: str
    faculty_id: Optional[str] = None
    semester: Optional[int] = None
    slot: Optional[str] = None

    class Config:
        from_attributes = True


class RoomResponse(BaseModel):
    building_code: Optional[str] = None
    room_number: int
    capacity: Optional[int] = None

    class Config:
        from_attributes = True