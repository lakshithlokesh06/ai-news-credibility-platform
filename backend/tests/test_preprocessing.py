import pytest

from app.schemas.preprocessing import PreprocessingConfig, TextCompositionConfig
from app.services.preprocessing import (
    EmptyTextError,
    compose_article_text,
    preprocess_for_classical_ml,
    preprocess_for_transformer,
)


def test_classical_preprocessing_is_conservative_but_configurable() -> None:
    processed = preprocess_for_classical_ml(
        "  <p>Café NEWS!!! Visit https://example.com/story</p>  ",
        PreprocessingConfig(lowercase=True),
    )

    assert processed == "café news!!! visit <url>"


def test_classical_preprocessing_can_remove_urls() -> None:
    processed = preprocess_for_classical_ml(
        "A headline https://example.com keeps punctuation.",
        PreprocessingConfig(remove_urls=True, normalize_urls=False),
    )

    assert processed == "A headline keeps punctuation."


def test_transformer_preprocessing_preserves_case_punctuation_and_urls() -> None:
    processed = preprocess_for_transformer(
        "<article>Breaking NEWS!!! See https://example.com/story</article>"
    )

    assert processed == "Breaking NEWS!!! See https://example.com/story"


def test_preprocessing_rejects_empty_text() -> None:
    with pytest.raises(EmptyTextError):
        preprocess_for_transformer("<p>   </p>")


def test_article_text_composition_modes() -> None:
    assert compose_article_text(title="Title", content="Body") == "Title\n\nBody"
    assert (
        compose_article_text(
            title="Title",
            content="Body",
            config=TextCompositionConfig(mode="title_only"),
        )
        == "Title"
    )
    assert (
        compose_article_text(
            title="Title",
            content="Body",
            config=TextCompositionConfig(mode="content_only"),
        )
        == "Body"
    )

