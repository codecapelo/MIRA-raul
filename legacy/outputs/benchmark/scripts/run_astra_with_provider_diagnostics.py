"""Passive, external exception diagnostics for frozen subscription adapters.

Does not change prompts, generation configuration, results, stopping or retries.
Run only after the previous scheduler has exited; its original lock still applies.
"""
from __future__ import annotations

import argparse
import importlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_CONSTANT_CATEGORIES = {
    "Official Codex CLI unavailable": "cli_unavailable",
    "Codex CLI is not authenticated with ChatGPT": "auth_status_failed",
    "Codex CLI returned no final action": "no_final_action",
    "Codex CLI action is not JSON": "action_json_invalid",
    "Codex CLI action must have exactly one EHR call": "action_count_invalid",
    "Codex CLI action arguments invalid": "action_argument_item_invalid",
    "Codex CLI arguments_json is invalid": "arguments_json_invalid",
    "Codex CLI action arguments are not an object": "arguments_not_object",
    "Model and effort are frozen for this arm": "frozen_config_mismatch",
}


def _category(exc: Exception) -> str:
    if type(exc).__name__ == "TimeoutExpired":
        return "timeout"
    # No message text is persisted. Only exact allowlisted constants or a
    # numeric CLI exit code may contribute to the category.
    message = str(exc)
    if message in _CONSTANT_CATEGORIES:
        return _CONSTANT_CATEGORIES[message]
    match = re.fullmatch(r"Codex CLI inference failed with exit code (-?\d+)", message)
    if match:
        return "cli_exit_" + match.group(1)
    return "unknown_adapter_exception"


def _record(path: Path, model: str, exception_class: str, category: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({
                "utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "model": model,
                "class": exception_class,
                "category": category,
            }) + "\n")
            stream.flush()
    except Exception:
        # Diagnostic I/O must not alter the original provider result/exception.
        pass


def _wrap_generate(provider_class: type, model: str, log_path: Path) -> None:
    original = provider_class.generate

    def diagnostic_generate(self: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            return original(self, *args, **kwargs)
        except Exception as exc:
            _record(log_path, model, type(exc).__name__, _category(exc))
            raise

    provider_class.generate = diagnostic_generate


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=["gpt-6-astra"], required=True)
    args, runner_args = parser.parse_known_args()
    if args.model == "gpt-6-astra":
        adapter_name = "providers.openai_astra"
        runner_name = "runner.run_astra_extension"
    else:
        adapter_name = "providers.openai_luna"
        runner_name = "runner.run_extension"
    adapter = importlib.import_module(adapter_name)
    runner = importlib.import_module(runner_name)
    log_path = ROOT / "results" / "provider_diagnostics_2026-09-29" / (args.model + ".jsonl")
    _wrap_generate(adapter.OpenAIProvider, args.model, log_path)
    _record(log_path, args.model, "instrumentation", "start")
    # All scheduler arguments/configuration remain under the frozen runner.
    sys.argv = [str(Path(runner.__file__)), "--model", args.model, *runner_args]
    runner.main()


if __name__ == "__main__":
    main()
