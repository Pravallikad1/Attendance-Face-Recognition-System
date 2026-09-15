import cv2

# Load image
image = cv2.imread("test.jpg")

# Get image size
height, width = image.shape[:2]

# Load YuNet face detector
model_path = "models/face_detection_yunet_2023mar.onnx"

detector = cv2.FaceDetectorYN.create(
    model_path,
    "",
    (width, height),
    0.6,
    0.3,
    5000
)

# Detect faces
_, faces = detector.detect(image)

if faces is None:
    print("No faces detected")
else:
    print("Faces detected:", len(faces))

    for face in faces:
        x, y, w, h = face[:4].astype(int)
        confidence = face[-1]

        cv2.rectangle(
            image,
            (x, y),
            (x + w, y + h),
            (0, 255, 0),
            2
        )

        cv2.putText(
            image,
            f"{confidence:.2f}",
            (x, y - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1
        )

# Save result
cv2.imwrite("output/detected_faces.jpg", image)

print("Result saved in output/detected_faces.jpg")