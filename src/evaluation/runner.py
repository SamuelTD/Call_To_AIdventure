"""Validate or execute the versioned AI evaluation dataset.

Validation is offline and safe for CI. ``--live`` invokes the configured
generation provider only for choice cases and may incur cost.
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from agents.runtime_config import AIRuntimeConfig
from agents.schemas import ChoiceOutput


ROOT = Path(__file__).resolve().parents[2]


def git_revision() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def validate_dataset(dataset: dict) -> list[str]:
    errors: list[str] = []
    ids: set[str] = set()
    if dataset.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    for index, case in enumerate(dataset.get("cases", [])):
        case_id = case.get("id")
        if not case_id or case_id in ids:
            errors.append(f"case {index}: id must be present and unique")
        ids.add(case_id)
        if case.get("task") not in {"choices", "rag_source", "api_boundary"}:
            errors.append(f"{case_id}: unsupported task")
    if not ids:
        errors.append("dataset must contain cases")
    return errors


def run_live_choice(case: dict) -> dict:
    from agents.llm_runtime import choicer_chain, choicer_chain_fr

    chain = choicer_chain_fr if case.get("language") == "fr" else choicer_chain
    started = time.perf_counter()
    result = chain.invoke({key: case[key] for key in (
        "player_summary", "context", "rag_context", "last_choices"
    )})
    parsed = result if isinstance(result, ChoiceOutput) else ChoiceOutput.model_validate(result)
    return {
        "passed": True,
        "latency_seconds": round(time.perf_counter() - started, 3),
        "output": parsed.model_dump(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=ROOT / "evaluation" / "dataset.json")
    parser.add_argument("--output", type=Path, default=ROOT / "evaluation" / "report.json")
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()

    dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
    errors = validate_dataset(dataset)
    config = AIRuntimeConfig.from_env(require_generation_key=args.live)
    results = []
    if not errors:
        for case in dataset["cases"]:
            if args.live and case["task"] == "choices":
                try:
                    result = run_live_choice(case)
                except Exception as exc:
                    result = {"passed": False, "error_type": type(exc).__name__}
            else:
                result = {"passed": True, "status": "validated_offline"}
            results.append({"id": case["id"], "task": case["task"], **result})

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_revision": dataset.get("revision"),
        "git_revision": git_revision(),
        "python": platform.python_version(),
        "configuration": config.safe_metadata(),
        "mode": "live" if args.live else "offline-validation",
        "thresholds": {"schema_validity_rate": 1.0, "case_pass_rate": 0.9},
        "validation_errors": errors,
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    passed = not errors and all(item["passed"] for item in results)
    print(f"Evaluation {'passed' if passed else 'failed'}: {args.output}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
