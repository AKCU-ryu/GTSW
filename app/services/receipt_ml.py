"""TensorFlow helpers to train and use a receipt image classifier."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional

try:  # pragma: no cover - optional dependency handling
    import numpy as np
except Exception as exc:  # pragma: no cover - triggered when numpy is missing
    np = None  # type: ignore[assignment]
    _NUMPY_ERROR: Exception | None = exc
else:
    _NUMPY_ERROR = None

LOGGER = logging.getLogger(__name__)

MODEL_PATH = Path("instance/receipt_classifier.h5")
LABELS_PATH = MODEL_PATH.with_suffix(".labels.json")
TRAIN_DIR = Path("./data/receipts/train")
TEST_DIR = Path("./data/receipts/test")


@dataclass
class ReceiptImagePrediction:
    """Return payload for predicted receipt information."""

    label: str
    confidence: float


class ReceiptModelNotReady(RuntimeError):
    """Raised when the TensorFlow model is unavailable."""


def _ensure_tensorflow():
    """Import TensorFlow/Keras lazily to avoid heavy startup costs."""

    try:  # pragma: no branch - intentionally a single import guard
        from tensorflow.keras.applications import VGG16, vgg16  # noqa: F401
        from tensorflow.keras.layers import Dense, Dropout, Flatten  # noqa: F401
        from tensorflow.keras.models import Sequential, load_model  # noqa: F401
        from tensorflow.keras.preprocessing.image import ImageDataGenerator, img_to_array, load_img  # noqa: F401
    except Exception as exc:  # pragma: no cover - environment specific failure
        raise ReceiptModelNotReady(
            "TensorFlow/Keras is required for image analysis. Install tensorflow>=2.13"
        ) from exc
    return (
        VGG16,
        vgg16,
        Sequential,
        load_model,
        Dense,
        Dropout,
        Flatten,
        ImageDataGenerator,
        load_img,
        img_to_array,
    )


def train_model(
    model_path: Path = MODEL_PATH,
    train_dir: Path = TRAIN_DIR,
    test_dir: Path = TEST_DIR,
    epochs: int = 20,
) -> tuple[Path, dict[str, int]]:
    """Train the receipt classifier using transfer learning."""

    (
        VGG16,
        vgg16,
        Sequential,
        _,
        Dense,
        Dropout,
        Flatten,
        ImageDataGenerator,
        load_img,  # noqa: F841 - imported for parity with provided sample
        img_to_array,  # noqa: F841
    ) = _ensure_tensorflow()

    if not train_dir.exists() or not any(train_dir.iterdir()):
        raise ReceiptModelNotReady(
            f"학습 데이터 경로({train_dir})에 이미지가 존재하지 않습니다."
        )

    train_datagen = ImageDataGenerator(
        rotation_range=180,
        width_shift_range=0.2,
        height_shift_range=0.2,
        horizontal_flip=True,
        vertical_flip=True,
        brightness_range=(0.5, 1.5),
    )
    test_datagen = ImageDataGenerator()

    train_generator = train_datagen.flow_from_directory(
        train_dir,
        target_size=(224, 224),
        batch_size=32,
        class_mode="categorical",
    )
    test_generator = test_datagen.flow_from_directory(
        test_dir,
        target_size=(224, 224),
        batch_size=32,
        class_mode="categorical",
    )

    class_num = len(train_generator.class_indices)
    base_model = VGG16(weights="imagenet", include_top=False, input_shape=(224, 224, 3))
    for layer in base_model.layers:
        layer.trainable = False

    model = Sequential(
        [
            base_model,
            Flatten(),
            Dense(1024, activation="relu"),
            Dropout(0.5),
            Dense(class_num, activation="softmax"),
        ]
    )
    model.compile(loss="categorical_crossentropy", optimizer="adam", metrics=["acc"])
    history = model.fit(
        train_generator,
        steps_per_epoch=len(train_generator),
        epochs=epochs,
        validation_data=test_generator,
        validation_steps=len(test_generator),
    )

    model_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(model_path)
    LABELS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LABELS_PATH.open("w", encoding="utf-8") as fh:
        json.dump(train_generator.class_indices, fh)

    LOGGER.info("Model trained and stored at %s", model_path)
    LOGGER.debug("Training history: %s", history.history)
    return model_path, train_generator.class_indices


def _load_model_bundle(model_path: Path = MODEL_PATH):
    (
        _,
        vgg16,
        _Sequential,
        load_model,
        _Dense,
        _Dropout,
        _Flatten,
        _ImageDataGenerator,
        load_img,
        img_to_array,
    ) = _ensure_tensorflow()

    if not model_path.exists():
        raise ReceiptModelNotReady(
            "학습된 영수증 분류 모델을 찾을 수 없습니다. 먼저 train_model을 실행해주세요."
        )
    if not LABELS_PATH.exists():
        raise ReceiptModelNotReady("클래스 레이블 파일이 존재하지 않습니다.")

    model = load_model(model_path)
    with LABELS_PATH.open("r", encoding="utf-8") as fh:
        class_indices = json.load(fh)
    # Reverse index for readability
    class_labels = {int(idx): label for label, idx in class_indices.items()}
    return model, class_labels, load_img, img_to_array, vgg16


def predict_image_bytes(data: bytes, filename: Optional[str] = None) -> ReceiptImagePrediction:
    """Predict the store label using the trained TensorFlow model."""

    if not data:
        raise ReceiptModelNotReady("이미지 데이터가 비어 있습니다.")

    if _NUMPY_ERROR is not None:
        raise ReceiptModelNotReady("numpy가 설치되어 있어야 이미지를 예측할 수 있습니다.") from _NUMPY_ERROR

    model, class_labels, load_img, img_to_array, vgg16 = _load_model_bundle()

    with NamedTemporaryFile(suffix=Path(filename or "receipt.jpg").suffix) as temp:
        temp.write(data)
        temp.flush()
        image = load_img(temp.name, target_size=(224, 224))
        array = img_to_array(image).reshape((1, 224, 224, 3))
        array = vgg16.preprocess_input(array)
        predictions = model.predict(array)

    class_idx = int(np.argmax(predictions))
    confidence = float(np.max(predictions)) * 100
    label = class_labels.get(class_idx, f"class-{class_idx}")
    return ReceiptImagePrediction(label=label, confidence=confidence)
