from pathlib import Path
from ultralytics import YOLO


ROOT = Path(__file__).resolve().parents[1]

MODEL = (
    ROOT /
    "models" /
    "yolo26_face" /
    "best.pt"
)

DATA = (
    ROOT /
    "training" /
    "dataset.yaml"
)


def main():

    if not MODEL.exists():

        raise FileNotFoundError(

            f"Trained model not found:\n"
            f"{MODEL}\n\n"

            "Run this first:\n"
            "python training/train_yolo26.py"
        )

    print(
        "Loading trained YOLO26 model..."
    )

    model = YOLO(
        str(MODEL)
    )

    print(
        "Validating model..."
    )

    metrics = model.val(

        data=str(DATA),

        imgsz=640,

        split="test"
    )

    print()
    print(
        "Validation completed."
    )

    print(
        metrics
    )


if __name__ == "__main__":
    main()