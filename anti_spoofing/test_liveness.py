import cv2
import sys
import os

# Allow importing RetinaFace from the cloned repository
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

REPO_PATH = os.path.join(
    PROJECT_ROOT,
    "face-anti-spoofing"
)

sys.path.insert(0, REPO_PATH)

from uniface import RetinaFace
from liveness_detector import LivenessDetector


# Load models
liveness_detector = LivenessDetector()
face_detector = RetinaFace()

# Open webcam
camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("ERROR: Could not open camera.")
    exit()

print("Anti-Spoofing test started.")
print("Press Q to quit.")

while True:
    success, frame = camera.read()

    if not success:
        break

    # Detect faces using RetinaFace
    faces = face_detector.detect(frame)

    for face in faces:

        bbox = face.bbox

        result = liveness_detector.check_liveness(
            frame,
            bbox
        )

        label = result["label"]
        confidence = result["confidence"]

        x1, y1, x2, y2 = map(int, bbox)

        if label == "REAL":
            color = (0, 255, 0)
        else:
            color = (0, 0, 255)

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            color,
            2
        )

        text = f"{label} {confidence * 100:.1f}%"

        cv2.putText(
            frame,
            text,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2
        )

    cv2.imshow(
        "Member 2 - Anti-Spoofing",
        frame
    )

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


camera.release()
cv2.destroyAllWindows()