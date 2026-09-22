from pathlib import Path
import random
import shutil
import cv2


ROOT = Path(__file__).resolve().parents[1]

SOURCE = ROOT / "dataset"

OUT = ROOT / "training" / "yolo_dataset"

YUNET = (
    ROOT /
    "models" /
    "face_detection_yunet_2023mar.onnx"
)

SEED = 42

TRAIN_RATIO = 0.70
VAL_RATIO = 0.20
TEST_RATIO = 0.10

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp"
}


def make_dirs():

    for split in [
        "train",
        "val",
        "test"
    ]:

        (
            OUT /
            "images" /
            split
        ).mkdir(
            parents=True,
            exist_ok=True
        )

        (
            OUT /
            "labels" /
            split
        ).mkdir(
            parents=True,
            exist_ok=True
        )


def detect_face_yunet(
    image,
    detector
):

    height, width = image.shape[:2]

    detector.setInputSize(
        (width, height)
    )

    _, faces = detector.detect(image)

    if faces is None:
        return None

    if len(faces) == 0:
        return None

    # Select largest detected face
    best = max(
        faces,
        key=lambda f:
        max(0.0, float(f[2]))
        *
        max(0.0, float(f[3]))
    )

    x, y, face_width, face_height = [
        float(v)
        for v in best[:4]
    ]

    x1 = max(
        0.0,
        x
    )

    y1 = max(
        0.0,
        y
    )

    x2 = min(
        float(width),
        x + face_width
    )

    y2 = min(
        float(height),
        y + face_height
    )

    if x2 <= x1 or y2 <= y1:
        return None

    return (
        x1,
        y1,
        x2,
        y2
    )


def to_yolo(
    box,
    width,
    height
):

    x1, y1, x2, y2 = box

    center_x = (
        (x1 + x2) / 2
    ) / width

    center_y = (
        (y1 + y2) / 2
    ) / height

    box_width = (
        x2 - x1
    ) / width

    box_height = (
        y2 - y1
    ) / height

    return [
        max(0, min(1, center_x)),
        max(0, min(1, center_y)),
        max(0, min(1, box_width)),
        max(0, min(1, box_height))
    ]


def main():

    if not SOURCE.exists():

        raise FileNotFoundError(
            f"Dataset not found: {SOURCE}"
        )

    if not YUNET.exists():

        raise FileNotFoundError(
            f"YuNet model not found: {YUNET}"
        )

    make_dirs()

    random.seed(SEED)

    detector = cv2.FaceDetectorYN.create(

        str(YUNET),

        "",

        (320, 320),

        0.5,

        0.3,

        5000
    )

    images = []

    # Read:
    # dataset/student_id/image.jpg

    for student_dir in sorted(
        SOURCE.iterdir()
    ):

        if not student_dir.is_dir():
            continue

        for image_path in sorted(
            student_dir.iterdir()
        ):

            if (
                image_path.suffix.lower()
                in IMAGE_EXTENSIONS
            ):

                images.append(
                    (
                        student_dir.name,
                        image_path
                    )
                )

    if not images:

        raise RuntimeError(
            "No student images found."
        )

    random.shuffle(images)

    total = len(images)

    train_end = int(
        total * TRAIN_RATIO
    )

    val_end = (
        train_end
        +
        int(total * VAL_RATIO)
    )

    splits = {

        "train":
            images[:train_end],

        "val":
            images[
                train_end:val_end
            ],

        "test":
            images[val_end:]
    }

    counters = {
        "train": 0,
        "val": 0,
        "test": 0
    }

    skipped = []

    for split, items in splits.items():

        for student_id, source_path in items:

            image = cv2.imread(
                str(source_path)
            )

            if image is None:

                skipped.append(
                    (
                        student_id,
                        str(source_path),
                        "unreadable"
                    )
                )

                continue

            height, width = image.shape[:2]

            box = detect_face_yunet(
                image,
                detector
            )

            if box is None:

                skipped.append(
                    (
                        student_id,
                        str(source_path),
                        "no_face_detected"
                    )
                )

                continue

            counters[split] += 1

            filename = (
                f"{student_id}_"
                f"{source_path.stem}_"
                f"{counters[split]}"
            )

            destination_image = (
                OUT /
                "images" /
                split /
                f"{filename}"
                f"{source_path.suffix.lower()}"
            )

            destination_label = (
                OUT /
                "labels" /
                split /
                f"{filename}.txt"
            )

            shutil.copy2(
                source_path,
                destination_image
            )

            center_x, center_y, box_width, box_height = (
                to_yolo(
                    box,
                    width,
                    height
                )
            )

            destination_label.write_text(

                f"0 "
                f"{center_x:.6f} "
                f"{center_y:.6f} "
                f"{box_width:.6f} "
                f"{box_height:.6f}\n",

                encoding="utf-8"
            )

    print()
    print("YOLO26 dataset prepared.")
    print(
        f"Train: {counters['train']}"
    )
    print(
        f"Val:   {counters['val']}"
    )
    print(
        f"Test:  {counters['test']}"
    )
    print(
        f"Skipped: {len(skipped)}"
    )

    print(
        f"Output: {OUT}"
    )

    if skipped:

        print()
        print(
            "Images that were skipped:"
        )

        for item in skipped:

            print(
                " ",
                item
            )


if __name__ == "__main__":
    main()