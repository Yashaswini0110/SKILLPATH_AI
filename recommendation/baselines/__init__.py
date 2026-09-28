from recommendation.baselines.content import content_score
from recommendation.baselines.popularity import popularity_score
from recommendation.baselines.semantic import (
    gap_summary,
    get_encoder,
    resource_text,
    semantic_score,
)
from recommendation.baselines.vectors import cosine_similarity

__all__ = [
    "content_score",
    "cosine_similarity",
    "gap_summary",
    "get_encoder",
    "popularity_score",
    "resource_text",
    "semantic_score",
]
