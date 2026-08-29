from typing import Any


def ensure_shap_available():
    try:
        import shap
    except ImportError as exc:
        raise RuntimeError("SHAP is required for this explanation method.") from exc
    return shap


def compute_linear_shap_values(classifier: Any, features: Any) -> list[float]:
    import numpy as np

    shap = ensure_shap_available()
    dense_features = features.toarray() if hasattr(features, "toarray") else np.asarray(features)
    background = np.zeros((1, dense_features.shape[1]))
    explainer = shap.LinearExplainer(classifier, background)
    explanation = explainer(dense_features)
    values = explanation.values
    if values.ndim == 3:
        values = values[0, :, -1]
    elif values.ndim == 2:
        values = values[0]
    return [float(value) for value in values]


def create_text_explainer(predict_function: Any, tokenizer: Any, output_names: list[str]):
    shap = ensure_shap_available()
    masker = shap.maskers.Text(tokenizer)
    return shap.Explainer(predict_function, masker, output_names=output_names)
