# YOLO26 + Anti-Spoofing changes completed

Current backend pipeline:

`YOLO26 face detection -> MiniFASNetV2 anti-spoofing -> FaceNet/DeepFace recognition -> attendance decision`

## Changes included

- Anti-spoofing now consumes YOLO26 bounding boxes directly (`[x1, y1, x2, y2]`).
- RetinaFace is no longer used by the anti-spoofing webcam test.
- Added `REAL`, `SPOOF`, and `UNKNOWN` liveness results.
- Added configurable liveness confidence threshold using `LIVENESS_UNKNOWN_THRESHOLD` (default `0.60`).
- REAL class index is configurable with `LIVENESS_REAL_CLASS_INDEX` (default `1`).
- Added multi-frame liveness voting for the webcam test to stabilize predictions.
- Added `/analyze-image` FastAPI endpoint for image upload and end-to-end analysis.
- Recognition is only allowed to continue for faces classified as `REAL`.
- Added `onnxruntime` and `python-multipart` dependencies.
- Added `tf-keras==2.21.0` for compatibility with TensorFlow 2.21 / DeepFace.

## Verified so far

The `/analyze-image` endpoint has returned HTTP 200 and successfully executed YOLO26 detection, MiniFASNetV2 liveness, and DeepFace recognition. A test face was classified as `REAL` with high liveness confidence; recognition returned `UNKNOWN`, so the next development step is tuning/validating the face-recognition dataset, path/ID mapping, and threshold using known registered students.

## Run

Use Python 3.11 in a virtual environment.

```powershell
pip install -r requirements.txt
python anti_spoofing/test_liveness.py
uvicorn main:app --reload
```

Swagger docs:

`http://127.0.0.1:8000/docs`

Test `POST /analyze-image` with a registered student's image.
