"""Record evaluator and raw-trace hashes after a complete panel, without changing traces."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from .analyze_panel import EXPECTED_MODELS, ROOT, analyze, load_rows
from .validate import read_trace


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    rows = load_rows()
    report = analyze(rows)
    if len(rows) != 150 or not all(report["models"][model]["complete_panel"] for model in EXPECTED_MODELS):
        raise SystemExit("Cannot freeze an incomplete panel")
    utc = datetime.now(timezone.utc).isoformat()
    eval_files = [
        "evaluation/metrics.py", "evaluation/diagnosis_concepts.py",
        "evaluation/diagnosis_aliases.json", "evaluation/validate.py",
        "evaluation/analyze_panel.py", "evaluation/prepare_review.py",
        "evaluation/adjudication.md",
    ]
    evaluation = {
        "evaluation_version": "evaluation-v2", "frozen_at_utc": utc,
        "corpus_version": report["corpus_version"], "protocol_version": report["protocol_version"],
        "files": [{"path": name, "sha256": sha256(ROOT / name)} for name in eval_files],
    }
    traces = []
    for path in sorted((ROOT / "results" / "raw").glob("*.jsonl")):
        events = read_trace(path)
        traces.append({"path": str(path.relative_to(ROOT)), "sha256": sha256(path),
                       "run_id": events[0]["run_id"], "case_id": events[0]["case_id"],
                       "model_id": events[0]["model_id"],
                       "repetition": events[0]["manifest"]["repetition"],
                       "stopping_reason": events[-1]["stopping_reason"],
                       "events": len(events)})
    trace_manifest = {
        "schema_version": "1.0.0", "frozen_at_utc": utc,
        "corpus_version": report["corpus_version"], "protocol_version": report["protocol_version"],
        "evaluation_version": "evaluation-v2", "trajectory_count": len(traces), "traces": traces,
    }
    (ROOT / "docs" / "evaluation_freeze_manifest.json").write_text(json.dumps(evaluation, ensure_ascii=False, indent=2) + "\n")
    (ROOT / "results" / "trace_manifest.json").write_text(json.dumps(trace_manifest, ensure_ascii=False, indent=2) + "\n")
    print("Frozen evaluator and 150 raw-trace hashes")


if __name__ == "__main__":
    main()
