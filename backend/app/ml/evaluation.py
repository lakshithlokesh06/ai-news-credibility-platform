import math
from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    precision_score,
    recall_score,
    roc_auc_score,
)

LABEL_ORDER = ["REAL", "FAKE"]


def _clean_metric(value: float | int | None) -> float | int | None:
    if value is None:
        return None
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return round(float(value), 6)


def evaluate_classifier(
    classifier: Any,
    features: Any,
    labels: list[str],
) -> dict[str, Any]:
    predictions = list(classifier.predict(features))
    probabilities = classifier.predict_proba(features) if hasattr(classifier, "predict_proba") else None

    roc_auc: float | None = None
    if probabilities is not None and len(set(labels)) == 2:
        class_index = list(classifier.classes_).index("FAKE")
        roc_auc = float(roc_auc_score(labels, probabilities[:, class_index]))

    class_precision, class_recall, class_f1, class_support = precision_recall_fscore_support(
        labels,
        predictions,
        labels=LABEL_ORDER,
        zero_division=np.nan,
    )
    class_metrics = {
        label: {
            "precision": _clean_metric(class_precision[index]),
            "recall": _clean_metric(class_recall[index]),
            "f1": _clean_metric(class_f1[index]),
            "support": int(class_support[index]),
        }
        for index, label in enumerate(LABEL_ORDER)
    }

    support = {label: int(class_support[index]) for index, label in enumerate(LABEL_ORDER)}
    return {
        "accuracy": _clean_metric(float(accuracy_score(labels, predictions))),
        "precision": _clean_metric(float(precision_score(labels, predictions, pos_label="FAKE", zero_division=np.nan))),
        "recall": _clean_metric(float(recall_score(labels, predictions, pos_label="FAKE", zero_division=np.nan))),
        "f1": _clean_metric(float(f1_score(labels, predictions, pos_label="FAKE", zero_division=np.nan))),
        "roc_auc": _clean_metric(roc_auc),
        "confusion_matrix": confusion_matrix(labels, predictions, labels=LABEL_ORDER).astype(int).tolist(),
        "class_metrics": class_metrics,
        "support": support,
    }

