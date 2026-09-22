import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'attendance_final.db'}")

# Security & JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY", "smart-attendance-super-secret-key-2026-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24)))  # 24 hours

# Model & AI Pipeline paths
YOLO_MODEL_PATH = os.getenv("YOLO_MODEL_PATH", str(BASE_DIR / "models" / "yolo26_face" / "best.pt"))
FALLBACK_YOLO_PATH = str(BASE_DIR / "yolo26n.pt")
ANTISPOOF_MODEL_PATH = os.getenv("ANTISPOOF_MODEL_PATH", str(BASE_DIR / "anti_spoofing" / "models" / "MiniFASNetV2.onnx"))
DATASET_DIR = Path(os.getenv("DATASET_DIR", str(BASE_DIR / "dataset")))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", str(BASE_DIR / "output")))

# Thresholds
LIVENESS_REAL_INDEX = int(os.getenv("REAL_CLASS_INDEX", "1"))
LIVENESS_THRESHOLD = float(os.getenv("LIVENESS_THRESHOLD", "0.50"))
FACE_RECOGNITION_THRESHOLD = float(os.getenv("FACE_RECOGNITION_THRESHOLD", "0.40"))
FACE_RECOGNITION_MODEL = os.getenv("FACE_RECOGNITION_MODEL", "Facenet")

# Server configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
