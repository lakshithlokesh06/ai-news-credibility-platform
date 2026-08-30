from app.schemas.monitoring import MonitoringConfig

PROFILE_VERSION = "monitoring-v1"
TEXT_LENGTH_BINS = [0, 100, 250, 500, 1000, 2000, 5000, 10000]
TITLE_LENGTH_BINS = [0, 20, 50, 100, 200, 500, 1000]
CONFIDENCE_BINS = [0.0, 0.6, 0.7, 0.8, 0.9, 1.000001]

DEFAULT_MONITORING_CONFIG = MonitoringConfig()

MONITORING_LIMITATIONS = [
    "Monitoring uses saved analysis history and does not verify factual claims.",
    "Unlabeled analysis history cannot measure production accuracy, precision, recall, F1, or ROC-AUC.",
    "Drift can indicate changed input or prediction behavior, but it does not automatically mean the model has failed.",
    "No detected drift does not guarantee correctness.",
    "Confidence is a model score, not accuracy.",
]


class MonitoringError(ValueError):
    def __init__(self, message: str, error_type: str = "monitoring_error") -> None:
        super().__init__(message)
        self.error_type = error_type
