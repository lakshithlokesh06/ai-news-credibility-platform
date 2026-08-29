from pathlib import Path
from typing import Any

from app.explainability.config import TRANSFORMER_LIMITATIONS, ExplanationError
from app.explainability.normalization import RawAttribution, ranked_items
from app.explainability.phrase_aggregation import aggregate_transformer_tokens
from app.explainability.shap_integration import create_text_explainer
from app.ml.artifacts import ArtifactError
from app.ml.transformer_artifacts import TransformerArtifactStore
from app.ml.transformer_device import select_device
from app.ml.transformer_probabilities import softmax_probabilities
from app.models.article import ArticleLabel
from app.models.training import ClassicalModelType, ModelFamily
from app.schemas.ml import ExplanationRequest, ExplanationResponse, PredictionResponse
from app.schemas.preprocessing import TextCompositionConfig
from app.services.preprocessing import compose_article_text, preprocess_for_transformer


class TransformerExplainer:
    def __init__(self, artifact_base_dir: Path | None = None) -> None:
        self.artifact_store = TransformerArtifactStore(artifact_base_dir)

    def explain(
        self,
        training_run,
        request: ExplanationRequest,
        prediction: PredictionResponse,
    ) -> ExplanationResponse:
        if request.explanation.method == "coefficient":
            raise ExplanationError(
                "Coefficient explanations are not available for transformer models.",
                "unsupported_explanation_method",
            )

        try:
            import torch
        except ImportError as exc:
            raise ExplanationError("PyTorch is required for transformer explanations.", "unavailable_dependency") from exc

        try:
            device = select_device("auto")
            model, tokenizer, metadata = self.artifact_store.load(training_run.artifact_path, device=device)
        except (ArtifactError, RuntimeError, ValueError) as exc:
            raise ExplanationError(str(exc), "missing_or_invalid_artifact") from exc

        text_config = TextCompositionConfig(**metadata["text_composition_config"])
        transformer_config = metadata["transformer_config"]
        composed = compose_article_text(title=request.title, content=request.content, config=text_config)
        processed = preprocess_for_transformer(composed)
        max_length = min(
            int(transformer_config.get("max_sequence_length", request.explanation.max_transformer_length)),
            request.explanation.max_transformer_length,
        )

        def predict_probabilities(texts: list[str]) -> list[list[float]]:
            encoded = tokenizer(
                texts,
                truncation=True,
                padding=True,
                max_length=max_length,
                return_tensors="pt",
            )
            encoded = {key: value.to(torch.device(device)) for key, value in encoded.items()}
            with torch.no_grad():
                logits = model(**encoded).logits.detach().cpu().numpy().tolist()
            rows = []
            for row in logits:
                probabilities = softmax_probabilities(row)
                rows.append([
                    probabilities.get(ArticleLabel.REAL.value, 0.0),
                    probabilities.get(ArticleLabel.FAKE.value, 0.0),
                ])
            return rows

        try:
            explainer = create_text_explainer(
                predict_probabilities,
                tokenizer,
                [ArticleLabel.REAL.value, ArticleLabel.FAKE.value],
            )
            shap_values = explainer(
                [processed],
                max_evals=request.explanation.max_evaluations,
                batch_size=1,
            )
            attributions = self._normalise_shap_values(shap_values, tokenizer, processed, max_length)
        except RuntimeError as exc:
            raise ExplanationError(str(exc), "unavailable_dependency") from exc
        except Exception as exc:
            raise ExplanationError(f"Transformer SHAP computation failed: {exc}", "shap_computation_failed") from exc

        return ExplanationResponse(
            training_run_id=training_run.id,
            model_family=ModelFamily.TRANSFORMER,
            model_type=ClassicalModelType(training_run.model_type),
            model_name=metadata.get("base_model_name") or training_run.base_model_name,
            predicted_label=prediction.predicted_label,
            real_probability=prediction.real_probability,
            fake_probability=prediction.fake_probability,
            confidence=prediction.confidence,
            probability_method=prediction.probability_method,
            explanation_method="shap_text",
            explained_class=prediction.predicted_label,
            influences_toward_real=ranked_items(
                attributions,
                direction=ArticleLabel.REAL,
                config=request.explanation,
            ),
            influences_toward_fake=ranked_items(
                attributions,
                direction=ArticleLabel.FAKE,
                config=request.explanation,
            ),
            limitations=TRANSFORMER_LIMITATIONS,
            message=(
                "SHAP token attribution explains the fine-tuned transformer artifact's local behavior; "
                "it is not independent fact verification."
            ),
        )

    @staticmethod
    def _normalise_shap_values(
        shap_values: Any,
        tokenizer: Any,
        processed_text: str,
        max_length: int,
    ) -> list[RawAttribution]:
        import numpy as np

        values = np.asarray(shap_values.values)
        if values.ndim == 3:
            real_scores = values[0, :, 0].astype(float).tolist()
            fake_scores = values[0, :, 1].astype(float).tolist()
        elif values.ndim == 2:
            real_scores = values[0].astype(float).tolist()
            fake_scores = [-score for score in real_scores]
        else:
            raise ExplanationError("Unexpected SHAP text attribution shape.", "shap_computation_failed")

        tokens = TransformerExplainer._tokens_from_shap_or_tokenizer(shap_values, tokenizer, processed_text, max_length)
        offsets = TransformerExplainer._offsets_from_tokenizer(tokenizer, processed_text, max_length)
        size = min(len(tokens), len(real_scores), len(fake_scores))
        return aggregate_transformer_tokens(tokens[:size], real_scores[:size], fake_scores[:size], offsets[:size] if offsets else None)

    @staticmethod
    def _tokens_from_shap_or_tokenizer(
        shap_values: Any,
        tokenizer: Any,
        processed_text: str,
        max_length: int,
    ) -> list[str]:
        data = getattr(shap_values, "data", None)
        if data is not None:
            try:
                first = data[0]
                if isinstance(first, (list, tuple)):
                    return [str(token) for token in first]
            except (IndexError, TypeError):
                pass
        encoded = tokenizer(
            [processed_text],
            truncation=True,
            padding=True,
            max_length=max_length,
        )
        input_ids = encoded.get("input_ids", [[]])[0]
        if hasattr(tokenizer, "convert_ids_to_tokens"):
            return [str(token) for token in tokenizer.convert_ids_to_tokens(input_ids)]
        return [str(token_id) for token_id in input_ids]

    @staticmethod
    def _offsets_from_tokenizer(
        tokenizer: Any,
        processed_text: str,
        max_length: int,
    ) -> list[tuple[int, int]] | None:
        try:
            encoded = tokenizer(
                [processed_text],
                truncation=True,
                padding=True,
                max_length=max_length,
                return_offsets_mapping=True,
            )
        except (TypeError, NotImplementedError, ValueError):
            return None
        offsets = encoded.get("offset_mapping")
        if not offsets:
            return None
        first = offsets[0]
        return [(int(start), int(end)) for start, end in first]
