from pathlib import Path

from app.models.article import ArticleLabel
from app.ml.artifacts import ArtifactError
from app.ml.transformer_artifacts import TransformerArtifactStore
from app.ml.transformer_device import select_device
from app.ml.transformer_probabilities import prediction_from_logits
from app.schemas.ml import PredictionRequest
from app.schemas.preprocessing import TextCompositionConfig
from app.services.preprocessing import compose_article_text, preprocess_for_transformer


class TransformerInferenceService:
    def __init__(self, artifact_base_dir: Path | None = None) -> None:
        self.artifact_store = TransformerArtifactStore(artifact_base_dir)

    def predict(self, training_run, request: PredictionRequest) -> tuple[ArticleLabel, float, float, float, str | None]:
        try:
            import torch
        except ImportError as exc:
            raise ArtifactError("PyTorch is required for transformer inference.") from exc

        device = select_device("auto")
        model, tokenizer, metadata = self.artifact_store.load(training_run.artifact_path, device=device)
        text_config = TextCompositionConfig(**metadata["text_composition_config"])
        transformer_config = metadata["transformer_config"]
        composed = compose_article_text(title=request.title, content=request.content, config=text_config)
        processed = preprocess_for_transformer(composed)
        encoded = tokenizer(
            [processed],
            truncation=True,
            padding=True,
            max_length=transformer_config["max_sequence_length"],
            return_tensors="pt",
        )
        encoded = {key: value.to(torch.device(device)) for key, value in encoded.items()}
        with torch.no_grad():
            logits = model(**encoded).logits.detach().cpu().numpy()[0].tolist()
        predicted_label, probabilities, confidence = prediction_from_logits(logits)
        return (
            predicted_label,
            probabilities.get(ArticleLabel.REAL.value, 0.0),
            probabilities.get(ArticleLabel.FAKE.value, 0.0),
            confidence,
            metadata.get("base_model_name"),
        )

