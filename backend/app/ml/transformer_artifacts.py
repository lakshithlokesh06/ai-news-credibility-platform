import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import UUID

from app.core.config import settings
from app.ml.artifacts import ArtifactError, resolve_artifact_dir

TRANSFORMER_ARTIFACT_VERSION = "transformer-ml-v1"
HF_MODEL_DIR = "hf_model"
METADATA_FILENAME = "metadata.json"


def _base(base_dir: Path | None = None) -> Path:
    return (base_dir or settings.trained_models_dir).resolve()


def _manifest_checksum(artifact_dir: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(file for file in artifact_dir.rglob("*") if file.is_file()):
        if path.name == METADATA_FILENAME:
            continue
        digest.update(str(path.relative_to(artifact_dir)).encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


class TransformerArtifactStore:
    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = _base(base_dir)

    def save(self, training_run_id: UUID, model, tokenizer, metadata: dict[str, Any]) -> tuple[str, str]:
        artifact_dir = self.base_dir / str(training_run_id)
        hf_dir = artifact_dir / HF_MODEL_DIR
        hf_dir.mkdir(parents=True, exist_ok=True)
        model.save_pretrained(hf_dir)
        tokenizer.save_pretrained(hf_dir)
        checksum = _manifest_checksum(artifact_dir)
        metadata_payload = {
            **metadata,
            "artifact_version": TRANSFORMER_ARTIFACT_VERSION,
            "artifact_checksum": checksum,
            "hf_model_dir": HF_MODEL_DIR,
        }
        (artifact_dir / METADATA_FILENAME).write_text(
            json.dumps(metadata_payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return str(artifact_dir.relative_to(self.base_dir)), checksum

    def load_metadata(self, relative_path: str) -> tuple[Path, dict[str, Any]]:
        artifact_dir = resolve_artifact_dir(relative_path, self.base_dir)
        metadata_path = artifact_dir / METADATA_FILENAME
        hf_dir = artifact_dir / HF_MODEL_DIR
        if not metadata_path.exists() or not hf_dir.is_dir():
            raise ArtifactError("Transformer artifact is incomplete.")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("artifact_version") != TRANSFORMER_ARTIFACT_VERSION:
            raise ArtifactError("Transformer artifact version is not compatible.")
        if _manifest_checksum(artifact_dir) != metadata.get("artifact_checksum"):
            raise ArtifactError("Transformer artifact checksum validation failed.")
        if not (hf_dir / "config.json").exists():
            raise ArtifactError("Transformer artifact is missing config.json.")
        return hf_dir, metadata

    def load(self, relative_path: str, device: str = "cpu"):
        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
        except ImportError as exc:
            raise ArtifactError(
                "Transformers and PyTorch are required to load transformer artifacts."
            ) from exc

        hf_dir, metadata = self.load_metadata(relative_path)
        tokenizer = AutoTokenizer.from_pretrained(hf_dir, local_files_only=True)
        model = AutoModelForSequenceClassification.from_pretrained(hf_dir, local_files_only=True)
        model.to(torch.device(device))
        model.eval()
        return model, tokenizer, metadata

