"""
Anti-Spoofing / Liveness Detection Module
Smart Attendance System

MiniFASNetV2 is independent from YOLO26. YOLO26 provides the face bbox;
this module classifies the cropped face as REAL, SPOOF, or UNKNOWN.
"""

import os
from typing import Dict, Sequence

import cv2
import numpy as np
import onnxruntime as ort

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(CURRENT_DIR, "weights", "MiniFASNetV2.onnx")

# The current MiniFASNetV2 checkpoint used in this project maps class 1 to REAL.
# Keep this configurable so the mapping can be changed after validation if needed.
DEFAULT_REAL_CLASS_INDEX = int(os.getenv("LIVENESS_REAL_CLASS_INDEX", "1"))

# Do not force a low-confidence prediction into REAL/SPOOF. Tune this threshold
# using your own phone-camera validation set.
DEFAULT_UNKNOWN_THRESHOLD = float(
    os.getenv("LIVENESS_UNKNOWN_THRESHOLD", "0.60")
)


class LivenessDetector:
    """Passive face anti-spoofing using MiniFASNetV2."""

    def __init__(
        self,
        model_path: str = MODEL_PATH,
        scale: float = 2.7,
        unknown_threshold: float = DEFAULT_UNKNOWN_THRESHOLD,
        real_class_index: int = DEFAULT_REAL_CLASS_INDEX,
    ):
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Anti-spoofing model not found: {model_path}"
            )

        if not 0.0 <= unknown_threshold <= 1.0:
            raise ValueError("unknown_threshold must be between 0 and 1.")

        self.scale = scale
        self.unknown_threshold = unknown_threshold
        self.real_class_index = real_class_index

        self.session = ort.InferenceSession(
            model_path,
            providers=["CPUExecutionProvider"],
        )

        input_cfg = self.session.get_inputs()[0]
        self.input_name = input_cfg.name
        self.input_size = tuple(input_cfg.shape[2:])
        self.output_name = self.session.get_outputs()[0].name

    def _crop_face(self, image, bbox: Sequence[int]):
        if image is None or getattr(image, "size", 0) == 0:
            raise ValueError("A valid OpenCV image is required.")

        if len(bbox) != 4:
            raise ValueError("bbox must be [x1, y1, x2, y2].")

        x1, y1, x2, y2 = [int(v) for v in bbox]
        box_w = x2 - x1
        box_h = y2 - y1

        if box_w <= 0 or box_h <= 0:
            raise ValueError("Invalid face bounding box.")

        src_h, src_w = image.shape[:2]

        scale = min(
            (src_h - 1) / box_h,
            (src_w - 1) / box_w,
            self.scale,
        )

        new_w = box_w * scale
        new_h = box_h * scale
        center_x = x1 + box_w / 2
        center_y = y1 + box_h / 2

        crop_x1 = max(0, int(center_x - new_w / 2))
        crop_y1 = max(0, int(center_y - new_h / 2))
        crop_x2 = min(src_w, int(center_x + new_w / 2))
        crop_y2 = min(src_h, int(center_y + new_h / 2))

        cropped = image[crop_y1:crop_y2, crop_x1:crop_x2]
        if cropped.size == 0:
            raise ValueError("Face crop is empty after clipping bbox.")

        return cv2.resize(cropped, self.input_size[::-1])

    @staticmethod
    def _softmax(values):
        values = np.asarray(values)
        if values.ndim == 1:
            values = np.expand_dims(values, axis=0)

        exp_values = np.exp(values - np.max(values, axis=1, keepdims=True))
        return exp_values / np.sum(exp_values, axis=1, keepdims=True)

    def check_liveness(self, image, bbox: Sequence[int]) -> Dict:
        """
        Check one YOLO26-detected face.

        Returns a dictionary containing:
          label: REAL | SPOOF | UNKNOWN
          confidence: confidence of the raw winning class (0..1)
          class_index: raw MiniFASNet class index
          probabilities: all output probabilities, useful for validation
        """
        face = self._crop_face(image, bbox)

        # Preserve the preprocessing used by the existing working checkpoint.
        face = face.astype(np.float32)
        face = np.transpose(face, (2, 0, 1))
        face = np.expand_dims(face, axis=0)

        output = self.session.run(
            [self.output_name],
            {self.input_name: face},
        )[0]

        probabilities = self._softmax(output)
        label_index = int(np.argmax(probabilities[0]))
        confidence = float(probabilities[0, label_index])

        if confidence < self.unknown_threshold:
            label = "UNKNOWN"
        elif label_index == self.real_class_index:
            label = "REAL"
        else:
            label = "SPOOF"

        return {
            "label": label,
            "confidence": confidence,
            "class_index": label_index,
            "probabilities": [float(v) for v in probabilities[0]],
        }


if __name__ == "__main__":
    detector = LivenessDetector()
    print("Anti-spoofing model loaded successfully!")
    print("Model:", MODEL_PATH)
    print("REAL class index:", detector.real_class_index)
    print("UNKNOWN threshold:", detector.unknown_threshold)
