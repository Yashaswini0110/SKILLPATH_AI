"""Write Phase 27 evaluation results. Synthetic labels only."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from ml.evaluation.run import evaluate, render_markdown  # noqa: E402


def main() -> None:
    report = evaluate(ROOT)
    text = render_markdown(report)
    out = ROOT / "docs" / "research" / "evaluation-results.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(text)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
