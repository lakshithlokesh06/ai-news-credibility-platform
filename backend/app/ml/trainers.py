from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC

from app.models.training import ClassicalModelType
from app.schemas.ml import ModelHyperparameters


def create_classifier(model_type: ClassicalModelType, config: ModelHyperparameters):
    if model_type == ClassicalModelType.LOGISTIC_REGRESSION:
        return (
            LogisticRegression(
                C=config.c,
                max_iter=config.max_iter,
                class_weight=config.class_weight,
                random_state=0,
            ),
            "predict_proba",
        )

    if model_type == ClassicalModelType.LINEAR_SVM:
        estimator = LinearSVC(
            C=config.c,
            max_iter=config.max_iter,
            class_weight=config.class_weight,
            random_state=0,
        )
        return (
            CalibratedClassifierCV(
                estimator=estimator,
                method="sigmoid",
                cv=config.calibration_cv,
            ),
            f"sigmoid_calibration_cv_{config.calibration_cv}",
        )

    raise ValueError(f"Unsupported model type: {model_type}")

