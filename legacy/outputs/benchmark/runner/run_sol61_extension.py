"""Resume-capable extension of the frozen v5 clinical protocol.

New traces and indices live outside the completed 150-run base panel. Each
model holds a process lock; terminal case/repetition combinations are never
repeated. Provider failures are retained under incomplete/ for inspection.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path

from runner.run_case import ROOT, run_case
from runner.run_frontier import _utc, _verify_corpus, _verify_protocol

MANIFEST = ROOT / "docs" / "protocol_sol61_extension_2026-09-29.json"


def verify() -> dict:
    corpus, protocol = _verify_corpus(), _verify_protocol()
    manifest = json.loads(MANIFEST.read_text())
    if manifest["corpus_version"] != corpus or manifest["base_protocol_version"] != protocol:
        raise SystemExit("Extension does not match frozen base corpus/protocol")
    for entry in manifest["files"]:
        path = ROOT / entry["path"]
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise SystemExit(f"Extension file changed after freeze: {entry['path']}")
    return manifest


def _load_terminal(raw: Path, model: str) -> dict:
    terminal = {}
    for path in raw.glob("*.jsonl"):
        events = [json.loads(line) for line in path.read_text().splitlines() if line]
        if not events or events[0].get("model_id") != model:
            continue
        end = events[-1]
        if end.get("event_type") != "run_ended":
            raise SystemExit(f"Nonterminal trace needs inspection: {path.name}")
        if end.get("stopping_reason") == "provider_or_runner_error":
            raise SystemExit(f"Failed trace must be preserved under incomplete/: {path.name}")
        key = (end["case_id"], end["repetition"])
        if key in terminal:
            raise SystemExit(f"Duplicate terminal combination: {key}")
        terminal[key] = (path, end)
    return terminal


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=["gpt-6.1-sol"], required=True)
    parser.add_argument("--max-runs", type=int, default=30)
    args = parser.parse_args()
    manifest = verify()
    spec = manifest["models"][args.model]
    directory = ROOT / manifest["results_directory"]
    raw = directory / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    lock_path = directory / f"{args.model}.lock"
    with lock_path.open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit(f"An execution is already active for {args.model}")
        lock.seek(0)
        lock.truncate()
        lock.write(json.dumps({"pid": os.getpid(), "model_id": args.model, "started_at": _utc()}))
        lock.flush()

        from providers.openai_sol61 import OpenAIProvider
        provider = OpenAIProvider(args.model, effort="high")
        print(json.dumps({"event": "preflight", "utc": _utc(), **provider.preflight()}), flush=True)
        progress = ROOT / spec["progress_path"]
        progress.parent.mkdir(parents=True, exist_ok=True)
        indexed, attempts = {}, {}
        if progress.exists():
            for line in progress.read_text().splitlines():
                row = json.loads(line)
                if (row.get("model_id") != args.model
                        or row.get("extension_version") != manifest["extension_version"]):
                    raise SystemExit("Incompatible extension progress index")
                indexed[row["run_id"]] = row
                key = (row["case_id"], row["repetition"])
                attempts[key] = max(attempts.get(key, 0), row["attempt"])
        terminal = _load_terminal(raw, args.model)
        terminal_ids = {end["run_id"] for _, end in terminal.values()}
        for row in indexed.values():
            if row["stopping_reason"] != "provider_or_runner_error" and row["run_id"] not in terminal_ids:
                raise SystemExit("A terminal indexed trace is missing; inspect rather than repeating it")

        def index_row(result: dict, path: Path, attempt: int, *, recovered: bool = False) -> dict:
            events = [json.loads(line) for line in path.read_text().splitlines() if line]
            reported = {model for event in events if event.get("event_type") == "model_response"
                        for model in event.get("provider_metadata", {}).get("models_reported", [])}
            return {"extension_version": manifest["extension_version"],
                    "corpus_version": manifest["corpus_version"],
                    "protocol_version": manifest["base_protocol_version"],
                    "reasoning_effort": "high", "model_requested": args.model,
                    "model_observed": next(iter(reported)) if len(reported) == 1 else None,
                    "attempt": attempt, "indexed_at": _utc(),
                    "trace_path": str(path.relative_to(ROOT)), "recovered_index": recovered,
                    **{k: v for k, v in result.items() if k not in {
                        "event_schema", "seq", "event_type", "utc", "monotonic_ms"}}}

        count = 0
        with progress.open("a") as stream:
            # Recover a trace written before a scheduler crash at the index step.
            for key, (path, end) in terminal.items():
                if end["run_id"] not in indexed:
                    row = index_row(end, path, attempts.get(key, 0) + 1, recovered=True)
                    stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                    stream.flush()
            for case_id in manifest["case_order"]:
                for repetition in range(1, manifest["repetitions"] + 1):
                    key = (case_id, repetition)
                    if key in terminal:
                        continue
                    if count >= args.max_runs:
                        return
                    verify()
                    attempt = attempts.get(key, 0) + 1
                    print(json.dumps({"event": "run_start", "utc": _utc(), "model_id": args.model,
                                      "case_id": case_id, "repetition": repetition, "attempt": attempt}), flush=True)
                    result = run_case(provider, case_id, repetition, out_dir=raw,
                                      max_actions=manifest["max_actions"],
                                      max_turns=manifest["max_model_turns"],
                                      max_wall_seconds=manifest["max_wall_seconds"])
                    path = raw / f"{result['run_id']}.jsonl"
                    failed = result["stopping_reason"] == "provider_or_runner_error"
                    if failed:
                        incomplete = directory / "incomplete"
                        incomplete.mkdir(exist_ok=True)
                        destination = incomplete / path.name
                        path.rename(destination)
                        path = destination
                    row = index_row(result, path, attempt)
                    stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                    stream.flush()
                    print(json.dumps({"event": "run_end", **row}, ensure_ascii=False), flush=True)
                    count += 1
                    if failed:
                        raise SystemExit("Provider error; trace preserved, inspect before resume")


if __name__ == "__main__":
    main()
