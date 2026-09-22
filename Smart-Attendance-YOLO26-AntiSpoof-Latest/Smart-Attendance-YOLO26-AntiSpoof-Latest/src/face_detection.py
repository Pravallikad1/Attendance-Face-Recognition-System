from functools import lru_cache
from pathlib import Path
import sys
from typing import List, Dict, Optional, Tuple

import cv2
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]

MODEL_DIR = ROOT / "models" / "yolo26_face"
TRAINED_MODEL = MODEL_DIR / "best.pt"
FALLBACK_MODEL = MODEL_DIR / "yolo26n.pt"
ROOT_FALLBACK_MODEL = ROOT / "yolo26n.pt"

OUTPUT_DIR = ROOT / "output"
OUTPUT_FILE = OUTPUT_DIR / "detected_faces.jpg"

CONFIDENCE = 0.35
IOU = 0.50
IMG_SIZE = 640


def _resolve_model_path() -> Path:
    """Return the best available YOLO26 face model path."""
    candidates = [TRAINED_MODEL, FALLBACK_MODEL, ROOT_FALLBACK_MODEL]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        "No YOLO26 face model was found. Expected one of: "
        + ", ".join(str(path) for path in candidates)
    )


@lru_cache(maxsize=1)
def load_model():
    """Load the YOLO26 face detector once and reuse it."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model_path = _resolve_model_path()
    print(f"Loading YOLO26 face model: {model_path}")
    return YOLO(str(model_path))


def detect_faces_in_image(
    image,
    model=None,
    confidence: float = CONFIDENCE,
    iou: float = IOU,
    img_size: int = IMG_SIZE,
) -> Tuple[List[Dict], object]:
    """
    Detect faces in an OpenCV BGR image using the trained YOLO26 model.

    Returns
    -------
    detections:
        List of dictionaries with ``bbox`` in [x1, y1, x2, y2] format
        and YOLO detection confidence.
    result:
        The raw first Ultralytics result object.
    """
    if image is None or getattr(image, "size", 0) == 0:
        raise ValueError("A valid OpenCV image is required.")

    detector = model or load_model()

    predict_kwargs = {
        "source": image,
        "conf": confidence,
        "iou": iou,
        "imgsz": img_size,
        "verbose": False,
    }
    if hasattr(detector, "names") and isinstance(detector.names, dict):
        face_ids = [k for k, v in detector.names.items() if str(v).lower() == "face"]
        if face_ids:
            predict_kwargs["classes"] = face_ids

    results = detector.predict(**predict_kwargs)

    result = results[0]
    detections: List[Dict] = []

    if result.boxes is not None:
        boxes = result.boxes.xyxy.cpu().numpy()
        scores = result.boxes.conf.cpu().numpy()

        for box, score in zip(boxes, scores):
            x1, y1, x2, y2 = [int(v) for v in box]
            detections.append(
                {
                    "bbox": [x1, y1, x2, y2],
                    "confidence": float(score),
                }
            )

    return detections, result


def detect_faces(image_path, save_annotated: bool = True):
    """Backward-compatible file based face-detection helper."""
    image = cv2.imread(str(image_path))

    if image is None:
        raise FileNotFoundError(f"Could not read image: {image_path}")

    detections, result = detect_faces_in_image(image)

    if save_annotated:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(OUTPUT_FILE), result.plot())
        print(f"Result saved: {OUTPUT_FILE}")

    print(f"Faces detected: {len(detections)}")
    return image, detections


if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])
    else:
        input_path = ROOT / "test1.jpeg"

    detect_faces(input_path)
