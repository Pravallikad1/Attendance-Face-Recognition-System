from pathlib import Path
from ultralytics import YOLO


ROOT = Path(__file__).resolve().parents[1]

DATA = (
    ROOT /
    "training" /
    "dataset.yaml"
)

MODEL_DIR = (
    ROOT /
    "models" /
    "yolo26_face"
)

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True
)


MODEL = "yolo26n.pt"

EPOCHS = 50

IMAGE_SIZE = 640

BATCH = 8


def main():

    if not DATA.exists():

        raise FileNotFoundError(

            f"{DATA} not found.\n"

            "First run:\n"

            "python "
            "training/prepare_yolo_dataset.py"
        )

    print(
        "Loading YOLO26 model..."
    )

    model = YOLO(
        MODEL
    )

    print(
        "Starting YOLO26 training..."
    )

    model.train(

        data=str(DATA),

        epochs=EPOCHS,

        imgsz=IMAGE_SIZE,

        batch=BATCH,

        patience=15,

        project=str(MODEL_DIR),

        name="training",

        exist_ok=True,

        pretrained=True,

        verbose=True
    )

    best = (
        MODEL_DIR /
        "training" /
        "weights" /
        "best.pt"
    )

    stable = (
        MODEL_DIR /
        "best.pt"
    )

    if best.exists():

        stable.write_bytes(
            best.read_bytes()
        )

        print()
        print(
            "YOLO26 training completed."
        )

        print(
            f"Best model saved to:"
        )

        print(
            stable
        )

    else:

        print(
            "Training finished, "
            "but best.pt was not found."
        )


if __name__ == "__main__":
    main()