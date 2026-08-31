import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import UUID

import joblib

from app.core.config import settings

ARTIFACT_VERSION = "classical-ml-v1"
MODEL_FILENAME = "model.joblib"
METADATA_FILENAME = "metadata.json"


class ArtifactError(ValueError):
    pass


def _controlled_base(base_dir: Path | None = None) -> Path:
    return (base_dir or settings.trained_models_dir).resolve()


def resolve_artifact_dir(relative_path: str, base_dir: Path | None = None) -> Path:
    if not relative_path or Path(relative_path).is_absolute() or ".." in Path(relative_path).parts:
        raise ArtifactError("Artifact path must be relative to the controlled models directory.")
    base = _controlled_base(base_dir)
    candidate = (base / relative_path).resolve()
    if base != candidate and base not in candidate.parents:
        raise ArtifactError("Artifact path escapes the controlled models directory.")
    return candidate


def _checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as artifact_file:
        for chunk in iter(lambda: artifact_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class ArtifactStore:
    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = _controlled_base(base_dir)

    def save(self, training_run_id: UUID, payload: dict[str, Any], metadata: dict[str, Any]) -> tuple[str, str]:
        artifact_dir = self.base_dir / str(training_run_id)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        model_path = artifact_dir / MODEL_FILENAME
        metadata_path = artifact_dir / METADATA_FILENAME

        joblib.dump(payload, model_path)
        checksum = _checksum(model_path)
        metadata_with_integrity = {
            **metadata,
            "artifact_version": ARTIFACT_VERSION,
            "artifact_checksum": checksum,
            "model_filename": MODEL_FILENAME,
        }
        metadata_path.write_text(json.dumps(metadata_with_integrity, indent=2, sort_keys=True), encoding="utf-8")
        return str(artifact_dir.relative_to(self.base_dir)), checksum

    def load(self, relative_path: str) -> tuple[dict[str, Any], dict[str, Any]]:
        _artifact_dir, model_path, metadata = self.validate_metadata(relative_path)
        payload = joblib.load(model_path)
        required_keys = {
            "classifier",
            "vectorizer",
            "preprocessing_config",
            "text_composition_config",
            "label_mapping",
            "training_config",
        }
        if not isinstance(payload, dict) or not required_keys.issubset(payload):
            raise ArtifactError("Artifact payload is malformed.")
        return payload, metadata

    def validate_metadata(self, relative_path: str) -> tuple[Path, Path, dict[str, Any]]:
        artifact_dir = resolve_artifact_dir(relative_path, self.base_dir)
        model_path = artifact_dir / MODEL_FILENAME
        metadata_path = artifact_dir / METADATA_FILENAME
        if not model_path.exists() or not metadata_path.exists():
            raise ArtifactError("Artifact is incomplete; expected model.joblib and metadata.json.")

        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("artifact_version") != ARTIFACT_VERSION:
            raise ArtifactError("Artifact version is not compatible with this loader.")
        expected_checksum = metadata.get("artifact_checksum")
        if not expected_checksum or _checksum(model_path) != expected_checksum:
            raise ArtifactError("Artifact checksum validation failed.")
        return artifact_dir, model_path, metadata
