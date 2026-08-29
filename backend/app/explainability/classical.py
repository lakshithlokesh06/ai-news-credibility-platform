from collections.abc import Sequence
from typing import Any

from app.explainability.config import CLASSICAL_LIMITATIONS, ExplanationError
from app.explainability.normalization import RawAttribution, ranked_items
from app.explainability.shap_integration import compute_linear_shap_values
from app.ml.artifacts import ArtifactError, ArtifactStore
from app.models.article import ArticleLabel
from app.models.training import ClassicalModelType, ModelFamily
from app.schemas.ml import ExplanationConfig, ExplanationRequest, ExplanationResponse, PredictionResponse
from app.schemas.preprocessing import PreprocessingConfig, TextCompositionConfig
from app.services.preprocessing import compose_article_text, preprocess_for_classical_ml


class ClassicalExplainer:
    def __init__(self, artifact_store: ArtifactStore) -> None:
        self.artifact_store = artifact_store

    def explain(
        self,
        training_run,
        request: ExplanationRequest,
        prediction: PredictionResponse,
    ) -> ExplanationResponse:
        try:
            payload, _metadata = self.artifact_store.load(training_run.artifact_path)
        except ArtifactError as exc:
            raise ExplanationError(str(exc), "missing_or_invalid_artifact") from exc

        composed = compose_article_text(
            title=request.title,
            content=request.content,
            config=TextCompositionConfig(**payload["text_composition_config"]),
        )
        processed = preprocess_for_classical_ml(
            composed,
            PreprocessingConfig(**payload["preprocessing_config"]),
        )
        vectorizer = payload["vectorizer"]
        classifier = payload["classifier"]
        features = vectorizer.transform([processed])
        if features.nnz == 0:
            attributions: list[RawAttribution] = []
            method = "coefficient_tfidf_local"
        else:
            method, positive_values = self._feature_values(
                classifier,
                features,
                ClassicalModelType(training_run.model_type),
                request.explanation,
            )
            attributions = self._attributions_from_values(
                vectorizer.get_feature_names_out(),
                features,
                classifier.classes_,
                positive_values,
            )

        return ExplanationResponse(
            training_run_id=training_run.id,
            model_family=ModelFamily.CLASSICAL,
            model_type=ClassicalModelType(training_run.model_type),
            model_name=training_run.base_model_name,
            predicted_label=prediction.predicted_label,
            real_probability=prediction.real_probability,
            fake_probability=prediction.fake_probability,
            confidence=prediction.confidence,
            probability_method=prediction.probability_method,
            explanation_method=method,
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
            limitations=CLASSICAL_LIMITATIONS + [self._method_limitation(training_run.model_type, method)],
            message=(
                "Feature attribution explains the trained model's local behavior for this text; "
                "it is not independent fact verification."
            ),
        )

    def _feature_values(
        self,
        classifier: Any,
        features: Any,
        model_type: ClassicalModelType,
        config: ExplanationConfig,
    ) -> tuple[str, Sequence[float]]:
        if config.method == "shap":
            if model_type != ClassicalModelType.LOGISTIC_REGRESSION:
                raise ExplanationError(
                    "SHAP is currently supported for Logistic Regression classical artifacts; "
                    "Linear SVM explanations use the underlying decision function.",
                    "unsupported_explanation_method",
                )
            try:
                return "shap_linear_logistic", compute_linear_shap_values(classifier, features)
            except RuntimeError as exc:
                raise ExplanationError(str(exc), "unavailable_dependency") from exc
            except Exception as exc:
                raise ExplanationError(f"SHAP computation failed: {exc}", "shap_computation_failed") from exc

        if model_type == ClassicalModelType.LOGISTIC_REGRESSION:
            return "coefficient_tfidf_local", self._logistic_contributions(classifier, features)

        if model_type == ClassicalModelType.LINEAR_SVM:
            return "linear_svm_underlying_decision_function", self._linear_svm_contributions(classifier, features)

        raise ExplanationError("This classical model type is not explainable.", "unsupported_model_type")

    @staticmethod
    def _logistic_contributions(classifier: Any, features: Any) -> list[float]:
        if not hasattr(classifier, "coef_"):
            raise ExplanationError("Logistic Regression artifact is missing coefficients.", "incompatible_artifact")
        coefficient = classifier.coef_[0]
        row = features.toarray()[0]
        return [float(value * weight) for value, weight in zip(row, coefficient, strict=True)]

    @staticmethod
    def _linear_svm_contributions(classifier: Any, features: Any) -> list[float]:
        calibrated_estimators = getattr(classifier, "calibrated_classifiers_", None)
        if not calibrated_estimators:
            raise ExplanationError("Linear SVM artifact is missing calibrated estimators.", "incompatible_artifact")

        coefficients = []
        for calibrated in calibrated_estimators:
            estimator = getattr(calibrated, "estimator", None) or getattr(calibrated, "estimator_", None)
            if estimator is not None and hasattr(estimator, "coef_"):
                coefficients.append(estimator.coef_[0])
        if not coefficients:
            raise ExplanationError("Linear SVM artifact is missing underlying linear coefficients.", "incompatible_artifact")

        row = features.toarray()[0]
        average = sum(coefficients) / len(coefficients)
        return [float(value * weight) for value, weight in zip(row, average, strict=True)]

    @staticmethod
    def _attributions_from_values(
        feature_names: Sequence[str],
        features: Any,
        classes: Sequence[Any],
        values_for_positive_class: Sequence[float],
    ) -> list[RawAttribution]:
        class_values = [str(label) for label in classes]
        if len(class_values) != 2:
            raise ExplanationError("Only binary REAL/FAKE artifacts are explainable.", "incompatible_artifact")
        positive_class = ArticleLabel(class_values[1])
        negative_class = ArticleLabel(class_values[0])

        sparse_row = features.tocoo()
        attributions = []
        for column in sparse_row.col:
            feature = str(feature_names[column])
            positive_score = float(values_for_positive_class[column])
            attributions.append(
                RawAttribution(
                    text=feature,
                    score_for_real=positive_score if positive_class == ArticleLabel.REAL else -positive_score,
                    score_for_fake=positive_score if positive_class == ArticleLabel.FAKE else -positive_score,
                )
            )

        # If sklearn ever orders labels differently, the explicit class mapping above keeps direction stable.
        if {positive_class, negative_class} != {ArticleLabel.REAL, ArticleLabel.FAKE}:
            raise ExplanationError("Artifact label mapping is not the expected REAL/FAKE binary mapping.", "incompatible_artifact")
        return attributions

    @staticmethod
    def _method_limitation(model_type: str, method: str) -> str:
        if model_type == ClassicalModelType.LINEAR_SVM.value:
            return (
                "Linear SVM attributions refer to the underlying fitted linear decision function; "
                "sigmoid calibration affects probabilities, not the learned feature weights."
            )
        if method.startswith("shap"):
            return "SHAP values are computed for the Logistic Regression linear model with a zero TF-IDF baseline."
        return "Coefficient attributions multiply the input TF-IDF value by the fitted class coefficient."
