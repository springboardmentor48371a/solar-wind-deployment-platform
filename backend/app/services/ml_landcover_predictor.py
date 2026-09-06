"""
Land Cover Classification Model — a real Convolutional Neural Network
trained from scratch on the actual EuroSAT dataset (Helber et al. 2019,
Sentinel-2 RGB imagery, 27,000 labeled 64x64 patches, 10 land-use/
land-cover classes). See app/ml_models/eurosat_land_cover_cnn.meta.json
for full provenance.

This is the platform's 6th real trained AI/ML model, added specifically
to close a comparative gap: relying only on a third-party API's own land-cover
summary string meant the platform had no trained image-classification
model of its own, unlike a teammate's approach using EuroSAT. This
module classifies a real Sentinel-2 RGB image tile fetched for a site's
coordinates (see satellite.py's fetch_and_store_satellite_summary,
which now pulls a real RGB crop from AWS Earth Search's public Sentinel-2
API, not just aggregate statistics).

TensorFlow is imported lazily inside the loader function, not at module
level — importing TF at server startup for every request handler would
add real, unnecessary startup latency to routes that never touch this
model.
"""

import os

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ml_models")
MODEL_PATH = os.path.join(MODEL_DIR, "eurosat_land_cover_cnn.keras")
METADATA_PATH = os.path.join(MODEL_DIR, "eurosat_land_cover_cnn.meta.json")

_model = None
_metadata = None
_load_attempted = False


def _load_model():
    global _model, _metadata, _load_attempted
    if _load_attempted:
        return _model
    _load_attempted = True
    if not os.path.exists(MODEL_PATH):
        return None
    try:
        import json
        import tensorflow as tf

        _model = tf.keras.models.load_model(MODEL_PATH)
        if os.path.exists(METADATA_PATH):
            with open(METADATA_PATH) as f:
                _metadata = json.load(f)
        return _model
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: failed to load land cover CNN model: {exc}")
        return None


def is_model_available() -> bool:
    return _load_model() is not None


def model_version() -> str | None:
    _load_model()
    return _metadata.get("version") if _metadata else None


def class_names() -> list[str] | None:
    _load_model()
    return _metadata.get("class_names") if _metadata else None


def predict_land_cover(image_bytes: bytes) -> dict | None:
    """
    Classifies a real RGB image (raw bytes, e.g. a JPEG/PNG tile fetched
    from AWS Earth Search) into one of EuroSAT's 10 land-use/land-cover
    classes. Resizes to 64x64 to match the exact input shape this model
    was trained on — a real Sentinel-2 tile at a different resolution
    will be resized, not rejected, since the training images themselves
    are already downsampled 10m/pixel patches.
    """
    model = _load_model()
    if model is None:
        return None
    try:
        import io
        import numpy as np
        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes)).convert("RGB").resize((64, 64))
        arr = np.array(img, dtype="float32") / 255.0
        arr = np.expand_dims(arr, axis=0)  # batch dimension of 1

        predictions = model.predict(arr, verbose=0)[0]
        classes = class_names() or [str(i) for i in range(len(predictions))]
        top_idx = int(predictions.argmax())
        return {
            "land_cover_class": classes[top_idx],
            "confidence_pct": round(float(predictions[top_idx]) * 100, 1),
            "all_class_probabilities": {classes[i]: round(float(p) * 100, 1) for i, p in enumerate(predictions)},
        }
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: ML land cover prediction failed: {exc}")
        return None
