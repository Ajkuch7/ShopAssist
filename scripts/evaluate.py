"""Evaluate scripted conversations against one or more Ollama models."""

import argparse
import sys
from pathlib import Path
from unittest.mock import patch

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from tests.test_scenarios import FAKE_POLICY, FAKE_PRODUCTS, SCENARIOS, classify_result, run_scenario, tool_selection_accuracy


RESULTS_PATH = Path(__file__).resolve().parents[1] / "results" / "model_comparison.md"


def _fake_products(description, max_price=None, category=None, k=3):
    return FAKE_PRODUCTS[:k]


def _fake_policy(question, k=3):
    return FAKE_POLICY[:k]


def evaluate_model(model_name: str) -> list[tuple[str, str, int, bool]]:
    """Run every scenario for one model and return result rows."""

    rows: list[tuple[str, str, int, bool]] = []
    with patch("app.tools.products.search_products_semantic", _fake_products), patch("app.tools.policy.search_policy", _fake_policy):
        for scenario in SCENARIOS:
            turns = run_scenario(scenario, model_name=model_name)
            rows.append((scenario.name, classify_result(scenario, turns), len(turns), tool_selection_accuracy(scenario, turns)))
    return rows


def _model_report(model_name: str, rows: list[tuple[str, str, int, bool]]) -> str:
    passes = sum(result == "pass" for _, result, _, _ in rows)
    failures = len(rows) - passes
    wrongly_approved = sum(result == "wrongly approved" for _, result, _, _ in rows)
    wrongly_denied = sum(result == "wrongly denied" for _, result, _, _ in rows)
    resolutions = [messages for _, result, messages, _ in rows if result == "pass"]
    average_messages = sum(resolutions) / len(resolutions) if resolutions else 0
    tool_accuracy = sum(accurate for _, _, _, accurate in rows) / len(rows) * 100
    lines = [
        f"## Model: `{model_name}`",
        "",
        "| Scenario | Result | Messages | Tools |",
        "|---|---:|---:|---:|",
    ]
    lines.extend(f"| {name} | {result} | {messages} | {'pass' if accurate else 'fail'} |" for name, result, messages, accurate in rows)
    lines.extend([
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Pass | {passes} |",
        f"| Fail | {failures} |",
        f"| Wrongly approved | {wrongly_approved} |",
        f"| Wrongly denied | {wrongly_denied} |",
        f"| Average messages per resolution | {average_messages:.2f} |",
        f"| Tool-selection accuracy | {tool_accuracy:.1f}% |",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", nargs="+", help="One or more Ollama model names to compare")
    args = parser.parse_args()
    models = args.model or [get_settings().models.chat]
    reports = []
    for model_name in models:
        rows = evaluate_model(model_name)
        reports.append(_model_report(model_name, rows))
        print(f"\nModel: {model_name}")
        for name, result, messages, accurate in rows:
            print(f"{result:18} | messages={messages:2} | tools={'pass' if accurate else 'fail':4} | {name}")
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text("# ShopAssist model comparison\n\n" + "\n".join(reports), encoding="utf-8")
    print(f"\nSaved results to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
