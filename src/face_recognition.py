from deepface import DeepFace
import os
import json

faces_path = "output/faces"
dataset_path = "dataset"

THRESHOLD = 0.4
results = []

for face_file in sorted(os.listdir(faces_path)):

    face_path = os.path.join(faces_path, face_file)

    best_student = None
    best_distance = 999

    for student_id in os.listdir(dataset_path):

        student_folder = os.path.join(dataset_path, student_id)

        if not os.path.isdir(student_folder):
            continue

        for image_file in os.listdir(student_folder):

            image_path = os.path.join(student_folder, image_file)

            try:
                result = DeepFace.verify(
                    img1_path=image_path,
                    img2_path=face_path,
                    model_name="Facenet",
                    detector_backend="skip",
                    enforce_detection=False
                )

                distance = result["distance"]

                if distance < best_distance:
                    best_distance = distance
                    best_student = student_id

            except:
                pass

    confidence = max(0, min(100, (1 - best_distance) * 100))

    if best_distance <= THRESHOLD:
        status = "RECOGNIZED"
        student = best_student
    else:
        status = "UNKNOWN"
        student = "UNKNOWN"

    result_data = {
        "face": face_file,
        "student_id": student,
        "confidence": round(confidence, 2),
        "status": status
    }

    results.append(result_data)

    print(result_data)

with open("output/recognition_results.json", "w") as file:
    json.dump(results, file, indent=4)

print("\nRecognition completed!")
print("Saved: output/recognition_results.json")