"""
End-to-end per-image analysis pipeline:
YOLO26 face detection -> MiniFASNetV2 liveness -> FaceNet recognition.

This module DOES NOT write attendance to the database. It returns analysis
results so the faculty can review/confirm them before attendance is saved.
"""

from pathlib import Path
from typing import Dict, List, Optional

import cv2
import numpy as np

from anti_spoofing.liveness_detector import LivenessDetector
from src.face_detection import detect_faces_in_image, load_model
from src.face_recognition import recognize_face_image

ROOT = Path(__file__).resolve().parents[1]


def _crop_bbox(image, bbox, padding_ratio: float = 0.10):
    x1, y1, x2, y2 = [int(v) for v in bbox]
    height, width = image.shape[:2]

    box_w = max(1, x2 - x1)
    box_h = max(1, y2 - y1)
    pad_x = int(box_w * padding_ratio)
    pad_y = int(box_h * padding_ratio)

    x1 = max(0, x1 - pad_x)
    y1 = max(0, y1 - pad_y)
    x2 = min(width, x2 + pad_x)
    y2 = min(height, y2 + pad_y)

    if x2 <= x1 or y2 <= y1:
        return None

    crop = image[y1:y2, x1:x2]
    return crop if crop.size else None


def analyze_image(
    image,
    yolo_model=None,
    liveness_detector: Optional[LivenessDetector] = None,
) -> List[Dict]:
    """Analyze one OpenCV BGR image and return one result per detected face."""
    if image is None or getattr(image, "size", 0) == 0:
        raise ValueError("A valid OpenCV image is required.")

    yolo_model = yolo_model or load_model()
    liveness_detector = liveness_detector or LivenessDetector()

    detections, _ = detect_faces_in_image(image, model=yolo_model)
    results: List[Dict] = []

    for face_id, detection in enumerate(detections, start=1):
        bbox = detection["bbox"]
        liveness = liveness_detector.check_liveness(image, bbox)

        recognition = {
            "student_id": None,
            "status": "SKIPPED",
            "distance": None,
            "confidence": 0.0,
        }

        # Do not perform identity recognition on spoof/uncertain inputs.
        if liveness["label"] == "REAL":
            face_crop = _crop_bbox(image, bbox)
            if face_crop is not None:
                recognition = recognize_face_image(face_crop)

        student_id = recognition.get("student_id")
        is_recognized = recognition.get("status") == "RECOGNIZED"
        attendance_allowed = bool(
            liveness["label"] == "REAL" and is_recognized and student_id
        )

        results.append(
            {
                "face_id": face_id,
                "bbox": bbox,
                "detection_confidence": float(detection["confidence"]),
                "student_id": student_id if is_recognized else None,
                "recognition": recognition,
                "anti_spoofing": liveness,
                "attendance_allowed": attendance_allowed,
            }
        )

    return results


def decode_image_bytes(data: bytes):
    array = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Uploaded file is not a valid image.")
    return image
