from collections.abc import Iterable
from dataclasses import dataclass

from app.models.article import ArticleLabel
from app.schemas.ml import ExplanationConfig, InfluentialItem


@dataclass(frozen=True)
class RawAttribution:
    text: str
    score_for_real: float
    score_for_fake: float
    start_offset: int | None = None
    end_offset: int | None = None
    source_tokens: tuple[str, ...] | None = None


def ranked_items(
    attributions: Iterable[RawAttribution],
    *,
    direction: ArticleLabel,
    config: ExplanationConfig,
) -> list[InfluentialItem]:
    if direction == ArticleLabel.REAL and not config.include_real_support:
        return []
    if direction == ArticleLabel.FAKE and not config.include_fake_support:
        return []

    scored: list[tuple[RawAttribution, float]] = []
    for attribution in attributions:
        score = (
            attribution.score_for_real
            if direction == ArticleLabel.REAL
            else attribution.score_for_fake
        )
        if score <= 0:
            continue
        scored.append((attribution, score))

    scored.sort(key=lambda item: abs(item[1]), reverse=True)
    return [
        InfluentialItem(
            text=attribution.text,
            attribution_score=round(float(score), 6),
            attribution_magnitude=round(abs(float(score)), 6),
            direction=direction,
            rank=index + 1,
            start_offset=attribution.start_offset,
            end_offset=attribution.end_offset,
            source_tokens=list(attribution.source_tokens) if attribution.source_tokens else None,
        )
        for index, (attribution, score) in enumerate(scored[: config.max_items])
    ]
