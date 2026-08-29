from app.models.article import ArticleLabel
from app.ml.transformer_dataset import ID2LABEL


def softmax_probabilities(logits: list[float]) -> dict[str, float]:
    import math

    if not logits:
        raise ValueError("Logits are required.")
    maximum = max(logits)
    exponentials = [math.exp(value - maximum) for value in logits]
    denominator = sum(exponentials)
    if denominator == 0:
        raise ValueError("Cannot normalize logits.")
    return {
        ID2LABEL[index]: round(exponential / denominator, 6)
        for index, exponential in enumerate(exponentials)
    }


def prediction_from_logits(logits: list[float]) -> tuple[ArticleLabel, dict[str, float], float]:
    probabilities = softmax_probabilities(logits)
    predicted_label = max(probabilities, key=probabilities.get)
    confidence = probabilities[predicted_label]
    return ArticleLabel(predicted_label), probabilities, confidence

