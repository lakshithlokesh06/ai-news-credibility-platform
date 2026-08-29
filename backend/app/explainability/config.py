from app.models.article import ArticleLabel

CLASSICAL_LIMITATIONS = [
    "Feature attribution explains how this trained model used text patterns; it does not verify factual claims.",
    "Influential terms are not automatically true or false.",
    "Attributions reflect the model artifact and dataset used for this training run.",
]

TRANSFORMER_LIMITATIONS = [
    "SHAP text attribution explains model behavior for this input; it does not verify factual claims.",
    "Transformer explanations are approximate and can be slower than prediction.",
    "Influential tokens reflect learned dataset patterns and may be sensitive to wording.",
]


class ExplanationError(ValueError):
    def __init__(self, message: str, error_type: str = "explanation_error") -> None:
        super().__init__(message)
        self.error_type = error_type


def opposite_label(label: ArticleLabel) -> ArticleLabel:
    return ArticleLabel.FAKE if label == ArticleLabel.REAL else ArticleLabel.REAL
