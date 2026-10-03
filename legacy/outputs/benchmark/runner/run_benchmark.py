"""Resume-capable local Ollama run scheduler. Never downloads models."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from providers.ollama import OllamaProvider
from runner.run_case import ROOT, run_case
from runner.run_frontier import _verify_corpus, _verify_protocol


DEFAULT_MODELS = ["qwen3.5:9b-mlx", "qwen3:8b", "llama3.1:8b"]
DEFAULT_CASES = [f"case_{i:03d}" for i in range(1, 11)]


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    parser.add_argument("--cases", nargs="+", default=DEFAULT_CASES)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--max-actions", type=int, default=40)
    parser.add_argument("--max-turns", type=int, default=60)
    parser.add_argument("--max-wall-seconds", type=int, default=3600)
    parser.add_argument("--num-ctx", type=int, default=24000)
    parser.add_argument("--index", type=Path, default=ROOT / "results" / "local_run_index.jsonl")
    args = parser.parse_args()
    corpus = _verify_corpus()
    protocol = _verify_protocol()
    args.index.parent.mkdir(parents=True, exist_ok=True)
    completed: set[tuple[str, str, int]] = set()
    if args.index.exists():
        for line in args.index.read_text(encoding="utf-8").splitlines():
            try:
                record = json.loads(line)
                if (record.get("corpus_version") == corpus
                        and record.get("protocol_version") == protocol
                        and record.get("stopping_reason") != "provider_or_runner_error"):
                    completed.add((record["model_id"], record["case_id"], record["repetition"]))
            except (json.JSONDecodeError, KeyError):
                continue
    installed = set(OllamaProvider(args.models[0]).installed_models())
    missing = [model for model in args.models if model not in installed]
    if missing:
        raise SystemExit(f"Not installed; no download attempted: {missing}")
    with args.index.open("a", encoding="utf-8") as index:
        for model_id in args.models:
            provider = OllamaProvider(model_id)
            preflight = provider.preflight()
            print(json.dumps({"event": "preflight", "utc": _utc(), **preflight}), flush=True)
            for case_id in args.cases:
                if not (ROOT / "cases" / case_id / "case_packet.json").is_file():
                    raise SystemExit(f"Missing case packet: {case_id}")
                for repetition in range(1, args.repetitions + 1):
                    key = (model_id, case_id, repetition)
                    if key in completed:
                        print(json.dumps({"event": "skip_existing", "model_id": model_id, "case_id": case_id, "repetition": repetition}), flush=True)
                        continue
                    print(json.dumps({"event": "run_start", "utc": _utc(), "model_id": model_id, "case_id": case_id, "repetition": repetition}), flush=True)
                    _verify_corpus()
                    result = run_case(provider, case_id, repetition,
                                      max_actions=args.max_actions, max_turns=args.max_turns,
                                      max_wall_seconds=args.max_wall_seconds, num_ctx=args.num_ctx)
                    index.write(json.dumps({"indexed_at": _utc(), "corpus_version": corpus,
                                            "protocol_version": protocol, **result}, ensure_ascii=False) + "\n")
                    index.flush()
                    if result["stopping_reason"] != "provider_or_runner_error":
                        completed.add(key)
                    print(json.dumps({"event": "run_end", **result}, ensure_ascii=False), flush=True)
                    if result["stopping_reason"] == "provider_or_runner_error":
                        raise SystemExit("Local provider error; stopped for inspection")


if __name__ == "__main__":
    main()
