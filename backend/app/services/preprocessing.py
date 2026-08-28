import html
import re
import unicodedata

from app.schemas.preprocessing import PreprocessingConfig, TextCompositionConfig

HTML_TAG_RE = re.compile(r"<[^>]+>")
URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
WHITESPACE_RE = re.compile(r"\s+")


class EmptyTextError(ValueError):
    pass


def _ensure_non_empty(value: str) -> str:
    if not value.strip():
        raise EmptyTextError("Text is empty after preprocessing.")
    return value


def preprocess_for_classical_ml(
    text: str,
    config: PreprocessingConfig | None = None,
) -> str:
    config = config or PreprocessingConfig()
    processed = text

    if config.normalize_unicode:
        processed = unicodedata.normalize("NFKC", processed)
    if config.strip_html:
        processed = html.unescape(HTML_TAG_RE.sub(" ", processed))
    if config.remove_urls:
        processed = URL_RE.sub(" ", processed)
    elif config.normalize_urls:
        processed = URL_RE.sub(" <URL> ", processed)
    if config.normalize_punctuation_spacing:
        processed = re.sub(r"\s+([,.;:!?])", r"\1", processed)
        processed = re.sub(r"([,.;:!?])(?=[^\s,.;:!?])", r"\1 ", processed)
    if config.normalize_whitespace:
        processed = WHITESPACE_RE.sub(" ", processed).strip()
    if config.lowercase:
        processed = processed.lower()

    return _ensure_non_empty(processed)


def preprocess_for_transformer(text: str) -> str:
    processed = unicodedata.normalize("NFKC", text)
    processed = html.unescape(HTML_TAG_RE.sub(" ", processed))
    processed = WHITESPACE_RE.sub(" ", processed).strip()
    return _ensure_non_empty(processed)


def compose_article_text(
    *,
    title: str | None,
    content: str | None,
    config: TextCompositionConfig | None = None,
) -> str:
    config = config or TextCompositionConfig()
    clean_title = title.strip() if title else ""
    clean_content = content.strip() if content else ""

    if config.mode == "title_only":
        return _ensure_non_empty(clean_title)
    if config.mode == "content_only":
        return _ensure_non_empty(clean_content)

    parts = [part for part in [clean_title, clean_content] if part]
    return _ensure_non_empty(config.separator.join(parts))
