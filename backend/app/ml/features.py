from sklearn.feature_extraction.text import TfidfVectorizer

from app.schemas.ml import TfidfConfig


def create_tfidf_vectorizer(config: TfidfConfig) -> TfidfVectorizer:
    return TfidfVectorizer(
        max_features=config.max_features,
        ngram_range=config.ngram_range,
        min_df=config.min_df,
        max_df=config.max_df,
        sublinear_tf=config.sublinear_tf,
        lowercase=config.lowercase,
    )

