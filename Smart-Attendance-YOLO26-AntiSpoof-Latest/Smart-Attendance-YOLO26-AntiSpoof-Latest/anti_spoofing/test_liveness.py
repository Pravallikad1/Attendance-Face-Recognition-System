"""
Live anti-spoofing test using the SAME YOLO26 detector as the attendance system.

Run from the project root:
    python anti_spoofing/test_liveness.py

Press Q to quit.
"""

from pathlib import Path
import sys

import cv2

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.face_detection import load_model, detect_faces_in_image
from anti_spoofing.liveness_detector import LivenessDetector
from anti_spoofing.temporal_liveness import LivenessVoteAggregator


def iou(box_a, box_b):
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    x1 = max(ax1, bx1)
    y1 = max(ay1, by1)
    x2 = min(ax2, bx2)
    y2 = min(ay2, by2)

    inter = max(0, x2 - x1) * max(0, y2 - y1)
    area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
    area_b = max(0, bx2 - bx1) * max(0, by2 - by1)
    union = area_a + area_b - inter
    return inter / union if union else 0.0


class SimpleIoUTracker:
    """Minimal tracker only for the liveness test window."""

    def __init__(self, threshold=0.30, max_missing=8):
        self.threshold = threshold
        self.max_missing = max_missing
        self.next_id = 1
        self.tracks = {}

    def update(self, boxes):
        for track in self.tracks.values():
            track["missing"] += 1

        assignments = []
        used_tracks = set()

        for box in boxes:
            best_id = None
            best_score = 0.0
            for track_id, track in self.tracks.items():
                if track_id in used_tracks:
                    continue
                score = iou(box, track["bbox"])
                if score > best_score:
                    best_score = score
                    best_id = track_id

            if best_id is None or best_score < self.threshold:
                best_id = self.next_id
                self.next_id += 1
                self.tracks[best_id] = {"bbox": box, "missing": 0}
            else:
                self.tracks[best_id]["bbox"] = box
                self.tracks[best_id]["missing"] = 0

            used_tracks.add(best_id)
            assignments.append(best_id)

        expired = [
            track_id
            for track_id, track in self.tracks.items()
            if track["missing"] > self.max_missing
        ]
        for track_id in expired:
            del self.tracks[track_id]

        return assignments, expired


def color_for(label):
    if label == "REAL":
        return (0, 255, 0)
    if label == "SPOOF":
        return (0, 0, 255)
    return (0, 215, 255)


def main():
    yolo_model = load_model()
    liveness_detector = LivenessDetector()
    smoother = LivenessVoteAggregator(history_size=5, min_votes=3)
    tracker = SimpleIoUTracker()

    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        raise RuntimeError("Could not open camera.")

    print("YOLO26 + MiniFASNetV2 anti-spoofing test started.")
    print("Press Q to quit.")
    print(
        "Validate the class mapping with a live face and known attacks "
        "(printed photo / phone screen) before using it for attendance."
    )

    while True:
        success, frame = camera.read()
        if not success:
            break

        detections, _ = detect_faces_in_image(frame, model=yolo_model)
        boxes = [d["bbox"] for d in detections]
        track_ids, expired = tracker.update(boxes)
        for track_id in expired:
            smoother.reset(track_id)

        for detection, track_id in zip(detections, track_ids):
            bbox = detection["bbox"]
            raw_result = liveness_detector.check_liveness(frame, bbox)
            stable = smoother.update(track_id, raw_result)

            x1, y1, x2, y2 = bbox
            label = stable["label"]
            color = color_for(label)

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            text = (
                f"T{track_id} {label} {stable['confidence'] * 100:.1f}% "
                f"R{stable['real_votes']}/S{stable['spoof_votes']}"
            )
            cv2.putText(
                frame,
                text,
                (x1, max(20, y1 - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                color,
                2,
            )

        cv2.imshow("YOLO26 + Anti-Spoofing Test", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
