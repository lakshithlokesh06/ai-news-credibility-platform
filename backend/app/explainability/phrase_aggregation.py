from app.models.article import ArticleLabel
from app.explainability.normalization import RawAttribution

SPECIAL_TOKENS = {"[CLS]", "[SEP]", "[PAD]", "<s>", "</s>", "<pad>"}


def _clean_token(token: str) -> str:
    return token.replace("##", "").replace("Ġ", "").replace("▁", "").strip()


def aggregate_transformer_tokens(
    tokens: list[str],
    real_scores: list[float],
    fake_scores: list[float],
    offsets: list[tuple[int, int]] | None = None,
) -> list[RawAttribution]:
    attributions: list[RawAttribution] = []
    current_text = ""
    current_real = 0.0
    current_fake = 0.0
    current_tokens: list[str] = []
    current_start: int | None = None
    current_end: int | None = None

    def flush() -> None:
        nonlocal current_text, current_real, current_fake, current_tokens, current_start, current_end
        cleaned = current_text.strip()
        if cleaned:
            attributions.append(
                RawAttribution(
                    text=cleaned,
                    score_for_real=current_real,
                    score_for_fake=current_fake,
                    start_offset=current_start,
                    end_offset=current_end,
                    source_tokens=tuple(current_tokens),
                )
            )
        current_text = ""
        current_real = 0.0
        current_fake = 0.0
        current_tokens = []
        current_start = None
        current_end = None

    for index, token in enumerate(tokens):
        if token in SPECIAL_TOKENS:
            flush()
            continue
        cleaned = _clean_token(token)
        if not cleaned:
            flush()
            continue
        start: int | None = None
        end: int | None = None
        if offsets and index < len(offsets):
            start, end = offsets[index]
            if start == end == 0:
                start = None
                end = None

        is_subword = token.startswith("##")
        if current_text and is_subword:
            current_text += cleaned
            current_real += real_scores[index]
            current_fake += fake_scores[index]
            current_tokens.append(token)
            if end is not None:
                current_end = end
            continue

        flush()
        current_text = cleaned
        current_real = real_scores[index]
        current_fake = fake_scores[index]
        current_tokens = [token]
        current_start = start
        current_end = end

    flush()
    return attributions


def score_direction(score_for_real: float, score_for_fake: float) -> ArticleLabel | None:
    if score_for_real <= 0 and score_for_fake <= 0:
        return None
    return ArticleLabel.REAL if score_for_real >= score_for_fake else ArticleLabel.FAKE
