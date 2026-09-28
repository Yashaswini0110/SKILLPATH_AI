"""Optional NVIDIA NIM complete() for grounded assistant answers.

Default is no network call. When enabled, this rephrases retrieved
passages only. It must not add skills, scores, or employee PII that
the passages do not already contain. The LLM is not the ranker.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request

DEFAULT_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_MODEL = "openai/gpt-oss-20b"
DEFAULT_TIMEOUT = 60.0

SYSTEM_PROMPT = (
    "You rephrase a grounded learning-assistant draft. "
    "Use only the draft and the passages. "
    "If they do not contain the answer, say you do not have it. "
    "Do not add skills, scores, courses, projects, or personal data "
    "that are not already written. "
    "Reply with one or two short paragraphs. No preamble."
)

logger = logging.getLogger("skillpath.llm")


def complete(
    prompt: str,
    *,
    enabled: bool = False,
    api_key: str = "",
    base_url: str = DEFAULT_BASE_URL,
    model: str = DEFAULT_MODEL,
    timeout: float = DEFAULT_TIMEOUT,
) -> str | None:
    if not enabled or not api_key or not prompt.strip():
        return None
    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 256,
        "stream": False,
        "reasoning_effort": "low",
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        logger.warning(
            "LLM complete() failed (%s); keeping the stored-fact answer",
            type(exc).__name__,
        )
        return None
    text = _choice_text(body)
    return text or None


def grounded_prompt(question: str, passages: list[str], draft: str = "") -> str:
    body = "\n\n".join(f"- {item}" for item in passages if item.strip())
    draft_block = f"Draft:\n{draft.strip()}\n\n" if draft.strip() else ""
    return (
        "Rephrase the draft using only the passages. "
        "If the passages do not contain the answer, say you do not have it. "
        "Do not add skills, scores, or personal data that are not written below.\n\n"
        f"Question: {question}\n\n"
        f"{draft_block}"
        f"Passages:\n{body}"
    )


def _choice_text(body: object) -> str:
    if not isinstance(body, dict):
        return ""
    choices = body.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    first = choices[0]
    if not isinstance(first, dict):
        return ""
    message = first.get("message")
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    if isinstance(content, list):
        content = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        )
    if not isinstance(content, str):
        return ""
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`").strip()
    return stripped
