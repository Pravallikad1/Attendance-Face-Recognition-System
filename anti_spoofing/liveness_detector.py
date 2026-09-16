"""
Anti-Spoofing / Liveness Detection Module
Member 2 - Smart Attendance System
"""

import os
import sys

import cv2
import numpy as np
import onnxruntime as ort


# Locate the pretrained MiniFASNetV2 model
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(
    CURRENT_DIR,
    "weights",
    "MiniFASNetV2.onnx"
)

class LivenessDetector:
    """Passive face anti-spoofing using MiniFASNetV2."""

    def __init__(self, model_path=MODEL_PATH, scale=2.7):
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Anti-spoofing model not found: {model_path}"
            )

        self.scale = scale

        self.session = ort.InferenceSession(
            model_path,
            providers=["CPUExecutionProvider"],
        )

        input_cfg = self.session.get_inputs()[0]
        self.input_name = input_cfg.name
        self.input_size = tuple(input_cfg.shape[2:])

        self.output_name = self.session.get_outputs()[0].name

    def _crop_face(self, image, bbox):
        x1, y1, x2, y2 = bbox

        x = int(x1)
        y = int(y1)
        box_w = int(x2 - x1)
        box_h = int(y2 - y1)

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

        center_x = x + box_w / 2
        center_y = y + box_h / 2

        crop_x1 = max(0, int(center_x - new_w / 2))
        crop_y1 = max(0, int(center_y - new_h / 2))
        crop_x2 = min(src_w - 1, int(center_x + new_w / 2))
        crop_y2 = min(src_h - 1, int(center_y + new_h / 2))

        cropped = image[
            crop_y1:crop_y2 + 1,
            crop_x1:crop_x2 + 1
        ]

        return cv2.resize(
            cropped,
            self.input_size[::-1]
        )

    def _softmax(self, values):
        exp_values = np.exp(
            values - np.max(values, axis=1, keepdims=True)
        )

        return exp_values / np.sum(
            exp_values,
            axis=1,
            keepdims=True
        )

    def check_liveness(self, image, bbox):
        """
        Check whether one detected face is REAL or SPOOF.

        Parameters
        ----------
        image:
            Full OpenCV BGR image.

        bbox:
            Face coordinates:
            [x1, y1, x2, y2]

        Returns
        -------
        dict:
            {
                "label": "REAL" or "SPOOF",
                "confidence": float
            }
        """

        face = self._crop_face(image, bbox)

        face = face.astype(np.float32)
        face = np.transpose(face, (2, 0, 1))
        face = np.expand_dims(face, axis=0)

        output = self.session.run(
            [self.output_name],
            {self.input_name: face},
        )[0]

        probabilities = self._softmax(output)

        label_index = int(np.argmax(probabilities))
        confidence = float(
            probabilities[0, label_index]
        )

        # MiniFASNet output used by the working repository:
        # class 1 -> Real
        # other class -> Fake/Spoof
        label = "REAL" if label_index == 1 else "SPOOF"

        return {
            "label": label,
            "confidence": confidence,
        }


if __name__ == "__main__":
    detector = LivenessDetector()

    print("Anti-spoofing model loaded successfully!")
    print("Model:", MODEL_PATH)