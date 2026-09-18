from member3 import process_recognition


faces = [
    {"student_id": "24BCA7313", "distance": 0.10},
    {"student_id": "24BCA7286", "distance": 0.25},
    {"student_id": "UNKNOWN_PERSON", "distance": 0.65},
    {"student_id": "24BCA7428", "distance": 0.35}
]


for face in faces:

    result = process_recognition(
        face["student_id"],
        face["distance"]
    )

    print(result)