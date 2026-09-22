import json
import os
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import cv2
import numpy as np
from deepface import DeepFace

from config import DATASET_DIR, FACE_RECOGNITION_MODEL, FACE_RECOGNITION_THRESHOLD

ROOT = Path(__file__).resolve().parents[1]
FACES_DIR = ROOT / "output" / "faces"
OUTPUT_FILE = ROOT / "output" / "recognition_results.json"

MODEL_NAME = FACE_RECOGNITION_MODEL
DISTANCE_THRESHOLD = FACE_RECOGNITION_THRESHOLD

# In-memory cache for reference embeddings
_CACHE_STUDENT_IDS: Optional[List[str]] = None
_CACHE_EMBEDDINGS: Optional[np.ndarray] = None


def valid_image(path: Path) -> bool:
    return path.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def _load_or_build_embeddings() -> Tuple[List[str], np.ndarray]:
    """Load precalculated embeddings or build in-memory cache."""
    global _CACHE_STUDENT_IDS, _CACHE_EMBEDDINGS

    if _CACHE_STUDENT_IDS is not None and _CACHE_EMBEDDINGS is not None:
        return _CACHE_STUDENT_IDS, _CACHE_EMBEDDINGS

    dataset_path = Path(DATASET_DIR)
    if not dataset_path.exists():
        return [], np.empty((0, 128), dtype=np.float32)

    # 1. Try to load existing DeepFace pickle file in dataset directory
    pkl_candidates = list(dataset_path.glob("ds_model_facenet_*.pkl"))
    student_ids: List[str] = []
    embeddings_list: List[np.ndarray] = []

    if pkl_candidates:
        pkl_path = pkl_candidates[0]
        try:
            with open(pkl_path, "rb") as f:
                records = pickle.load(f)

            for item in records:
                identity = item.get("identity")
                raw_emb = item.get("embedding")
                if identity and raw_emb is not None:
                    # identity can be 'dataset/24BCA3008/img1.jpg' or 'dataset\\24BCA3008\\img1.jpg'
                    parts = Path(identity).parts
                    # find folder name under dataset
                    if len(parts) >= 2:
                        s_id = parts[-2]
                    else:
                        s_id = Path(identity).parent.name

                    emb_arr = np.array(raw_emb, dtype=np.float32)
                    norm = np.linalg.norm(emb_arr)
                    if norm > 0:
                        emb_arr = emb_arr / norm
                        student_ids.append(s_id)
                        embeddings_list.append(emb_arr)
        except Exception as e:
            print(f"Warning: Could not load embeddings pickle: {e}")

    # 2. If pickle didn't load or was empty, build from images
    if not embeddings_list:
        print("Building face recognition embeddings database from dataset images...")
        for student_folder in sorted(p for p in dataset_path.iterdir() if p.is_dir()):
            for ref_img in sorted(student_folder.iterdir()):
                if not ref_img.is_file() or not valid_image(ref_img):
                    continue
                try:
                    rep = DeepFace.represent(
                        img_path=str(ref_img),
                        model_name=MODEL_NAME,
                        detector_backend="skip",
                        enforce_detection=False,
                    )
                    if rep and len(rep) > 0:
                        emb_arr = np.array(rep[0]["embedding"], dtype=np.float32)
                        norm = np.linalg.norm(emb_arr)
                        if norm > 0:
                            emb_arr = emb_arr / norm
                            student_ids.append(student_folder.name)
                            embeddings_list.append(emb_arr)
                except Exception:
                    continue

    if embeddings_list:
        _CACHE_STUDENT_IDS = student_ids
        _CACHE_EMBEDDINGS = np.vstack(embeddings_list)
    else:
        _CACHE_STUDENT_IDS = []
        _CACHE_EMBEDDINGS = np.empty((0, 128), dtype=np.float32)

    print(f"Face recognition initialized: {len(_CACHE_STUDENT_IDS)} reference embeddings cached.")
    return _CACHE_STUDENT_IDS, _CACHE_EMBEDDINGS


def get_students_without_face_data(registration_numbers) -> set:
    """
    Return the subset of *registration_numbers* that have no reference embeddings
    in the dataset.  These students are registered in the DB but cannot be
    automatically recognised by the AI pipeline.

    Args:
        registration_numbers: any iterable of student registration-number strings.

    Returns:
        A set of registration numbers with zero dataset images.
    """
    cached_ids, _ = _load_or_build_embeddings()
    students_with_data = set(cached_ids)
    return {reg for reg in registration_numbers if reg not in students_with_data}


def recognize_face_image(face_image) -> Dict:
    """
    Recognize one cropped face image against reference dataset using vectorized cosine distance.
    Returns recognition status, student_id, distance, and confidence.
    """
    if face_image is None or getattr(face_image, "size", 0) == 0:
        return {
            "student_id": None,
            "confidence": 0.0,
            "distance": None,
            "status": "UNKNOWN",
        }

    cached_ids, cached_embs = _load_or_build_embeddings()
    if len(cached_ids) == 0 or cached_embs.shape[0] == 0:
        return {
            "student_id": None,
            "confidence": 0.0,
            "distance": None,
            "status": "UNKNOWN",
        }

    try:
        rep = DeepFace.represent(
            img_path=face_image,
            model_name=MODEL_NAME,
            detector_backend="skip",
            enforce_detection=False,
        )
        if not rep or len(rep) == 0:
            return {
                "student_id": None,
                "confidence": 0.0,
                "distance": None,
                "status": "UNKNOWN",
            }

        query_emb = np.array(rep[0]["embedding"], dtype=np.float32)
        norm = np.linalg.norm(query_emb)
        if norm > 0:
            query_emb = query_emb / norm

        # Compute cosine similarity with all reference embeddings via vector dot-product
        similarities = np.dot(cached_embs, query_emb)
        distances = 1.0 - similarities

        best_idx = int(np.argmin(distances))
        best_distance = float(distances[best_idx])
        best_student = cached_ids[best_idx]

        if best_distance <= DISTANCE_THRESHOLD:
            status = "RECOGNIZED"
            student_id = best_student
        else:
            status = "UNKNOWN"
            student_id = None

        confidence = max(0.0, min(100.0, (1.0 - best_distance) * 100.0))
        return {
            "student_id": student_id,
            "confidence": round(confidence, 2),
            "distance": round(best_distance, 4),
            "status": status,
        }
    except Exception as exc:
        print(f"Face recognition error: {exc}")
        return {
            "student_id": None,
            "confidence": 0.0,
            "distance": None,
            "status": "UNKNOWN",
        }


def recognize():
    """Backward-compatible batch recognition of output/faces/*.jpg."""
    if not FACES_DIR.exists():
        raise FileNotFoundError(f"Face crop directory not found: {FACES_DIR}")

    results = []
    for face_path in sorted(FACES_DIR.iterdir()):
        if not face_path.is_file() or not valid_image(face_path):
            continue

        face_image = cv2.imread(str(face_path))
        if face_image is None:
            continue

        result = recognize_face_image(face_image)
        result = {"face": face_path.name, **result}
        results.append(result)
        print(result)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(results, file, indent=4)

    print(f"\nRecognition completed: {len(results)} face(s)")
    print(f"Saved: {OUTPUT_FILE}")
    return results


if __name__ == "__main__":
    recognize()
