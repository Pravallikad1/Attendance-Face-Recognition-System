import cv2
import os

image = cv2.imread("test.jpg")

height, width = image.shape[:2]

detector = cv2.FaceDetectorYN.create(
    "models/face_detection_yunet_2023mar.onnx",
    "",
    (width, height),
    0.6,
    0.3,
    5000
)

_, faces = detector.detect(image)

os.makedirs("output/faces", exist_ok=True)

if faces is None:
    print("No faces detected")
else:
    print("Faces detected:", len(faces))

    for i, face in enumerate(faces):
        x, y, w, h = face[:4].astype(int)

        cropped_face = image[y:y+h, x:x+w]

        filename = f"output/faces/face_{i+1}.jpg"

        cv2.imwrite(filename, cropped_face)

        print("Saved:", filename)