"""Phase 26 latency checks against the PRD targets."""

from __future__ import annotations

import math
import os
import time
import urllib.error
import urllib.request

import pytest
from fastapi.testclient import TestClient

from tests.pipeline import (
    gap_analysis,
    learning_path,
    recommend_courses,
    set_target_role,
    start_learner,
    upload_sample_resume,
)

pytestmark = pytest.mark.performance

API_P95_SECONDS = 0.5
EXTRACTION_SECONDS = 10.0
GAP_SECONDS = 2.0
PATH_SECONDS = 3.0
RECOMMENDATION_SECONDS = 1.0
PAGE_LOAD_SECONDS = 2.0
API_SAMPLES = 20


def _p95(samples: list[float]) -> float:
    ranked = sorted(samples)
    index = min(len(ranked) - 1, max(0, math.ceil(0.95 * len(ranked)) - 1))
    return ranked[index]


def _timed(call) -> float:
    started = time.perf_counter()
    call()
    return time.perf_counter() - started


def test_catalog_list_p95_under_500ms(client: TestClient, unique_email: str) -> None:
    headers = start_learner(client, unique_email)
    warmup = client.get("/api/v1/skills", headers=headers)
    assert warmup.status_code == 200
    samples = [
        _timed(lambda: client.get("/api/v1/skills", headers=headers))
        for _ in range(API_SAMPLES)
    ]
    assert _p95(samples) < API_P95_SECONDS, f"skills p95={_p95(samples):.3f}s"


def test_skill_extraction_under_10s(client: TestClient, unique_email: str) -> None:
    headers = start_learner(client, unique_email)
    elapsed = _timed(lambda: upload_sample_resume(client, headers))
    assert elapsed < EXTRACTION_SECONDS, f"extraction={elapsed:.3f}s"


def test_gap_analysis_under_2s(client: TestClient, unique_email: str) -> None:
    headers = start_learner(client, unique_email)
    upload_sample_resume(client, headers)
    set_target_role(client, headers)
    elapsed = _timed(lambda: gap_analysis(client, headers))
    assert elapsed < GAP_SECONDS, f"gap={elapsed:.3f}s"


def test_recommendation_under_1s(client: TestClient, unique_email: str) -> None:
    headers = start_learner(client, unique_email)
    upload_sample_resume(client, headers)
    set_target_role(client, headers)
    elapsed = _timed(lambda: recommend_courses(client, headers))
    assert elapsed < RECOMMENDATION_SECONDS, f"recommendation={elapsed:.3f}s"


def test_path_generation_under_3s(client: TestClient, unique_email: str) -> None:
    headers = start_learner(client, unique_email)
    upload_sample_resume(client, headers)
    set_target_role(client, headers)
    elapsed = _timed(lambda: learning_path(client, headers))
    assert elapsed < PATH_SECONDS, f"path={elapsed:.3f}s"


def test_page_load_under_2s_when_frontend_is_up() -> None:
    url = os.environ.get("FRONTEND_URL", "http://localhost:5173/")
    try:
        started = time.perf_counter()
        with urllib.request.urlopen(url, timeout=5) as response:
            response.read()
            status = response.status
        elapsed = time.perf_counter() - started
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        pytest.skip(f"frontend not reachable at {url}: {exc}")
    assert status == 200
    assert elapsed < PAGE_LOAD_SECONDS, f"page load={elapsed:.3f}s"
