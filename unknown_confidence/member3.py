def process_recognition(student_id, distance, threshold=0.40):
    """
    Classify a face as RECOGNIZED or UNKNOWN
    using FaceNet distance.

    Lower distance = better match.
    """

    # Convert distance into an easy-to-understand confidence score.
    confidence = max(0, min(100, (1 - distance) * 100))
    confidence = round(confidence, 2)

    if distance <= threshold:

        if distance <= threshold * 0.50:
            confidence_level = "HIGH"
        else:
            confidence_level = "MEDIUM"

        return {
            "student_id": student_id,
            "status": "RECOGNIZED",
            "distance": round(distance, 4),
            "confidence": confidence,
            "confidence_level": confidence_level
        }

    else:

        return {
            "student_id": "UNKNOWN",
            "status": "UNKNOWN",
            "distance": round(distance, 4),
            "confidence": confidence,
            "confidence_level": "LOW"
        }