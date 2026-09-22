from pathlib import Path
import sys
import cv2
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]

MODEL_DIR = ROOT / "models" / "yolo26_face"

TRAINED_MODEL = MODEL_DIR / "best.pt"
FALLBACK_MODEL = MODEL_DIR / "yolo26n.pt"

OUTPUT_DIR = ROOT / "output" / "faces"

CONFIDENCE = 0.35
IOU = 0.50
IMG_SIZE = 640
PADDING = 10


def load_model():

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    if TRAINED_MODEL.exists():
        model_path = TRAINED_MODEL
    else:
        model_path = FALLBACK_MODEL

    print(
        f"Loading YOLO26 model: {model_path}"
    )

    return YOLO(str(model_path))


def clamp_box(
    x1,
    y1,
    x2,
    y2,
    width,
    height
):

    x1 = max(
        0,
        min(x1, width - 1)
    )

    y1 = max(
        0,
        min(y1, height - 1)
    )

    x2 = max(
        0,
        min(x2, width)
    )

    y2 = max(
        0,
        min(y2, height)
    )

    return x1, y1, x2, y2


def crop_faces(image_path):

    image = cv2.imread(
        str(image_path)
    )

    if image is None:
        raise FileNotFoundError(
            f"Could not read image: {image_path}"
        )

    model = load_model()

    results = model.predict(
        source=image,
        conf=CONFIDENCE,
        iou=IOU,
        imgsz=IMG_SIZE,
        classes=[0],
        verbose=False
    )

    result = results[0]

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # Remove old generated face crops
    for old_file in OUTPUT_DIR.glob("face_*.jpg"):
        old_file.unlink()

    height, width = image.shape[:2]

    saved = 0

    if result.boxes is not None:

        boxes = result.boxes.xyxy.cpu().numpy()

        scores = result.boxes.conf.cpu().numpy()

        for index, (box, score) in enumerate(
            zip(boxes, scores),
            start=1
        ):

            x1, y1, x2, y2 = [
                int(v) for v in box
            ]

            x1 -= PADDING
            y1 -= PADDING

            x2 += PADDING
            y2 += PADDING

            x1, y1, x2, y2 = clamp_box(
                x1,
                y1,
                x2,
                y2,
                width,
                height
            )

            if x2 <= x1 or y2 <= y1:
                continue

            crop = image[
                y1:y2,
                x1:x2
            ]

            output_file = (
                OUTPUT_DIR /
                f"face_{index}.jpg"
            )

            if cv2.imwrite(
                str(output_file),
                crop
            ):

                saved += 1

                print(
                    f"Saved: {output_file} "
                    f"(confidence={float(score):.3f})"
                )

    if saved == 0:

        print("No faces detected.")

    else:

        print(
            f"Saved {saved} face crop(s)"
        )

        print(
            f"Location: {OUTPUT_DIR}"
        )

    return saved


if __name__ == "__main__":

    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])
    else:
        input_path = ROOT / "test1.jpeg"

    crop_faces(input_path)