"""Provider-independent sequential clinical case runner.

Run as ``python -m runner.run_case`` from the benchmark directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.ehr_sandbox import EHRCase
from tools.schemas import TOOL_SPECS, ollama_tools


ROOT = Path(__file__).resolve().parents[1]


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_object(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if text.startswith("```json") and text.endswith("```"):
        text = text[7:-3].strip()
    elif text.startswith("```") and text.endswith("```"):
        text = text[3:-3].strip()
    try:
        parsed = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _extract_calls(message: dict[str, Any]) -> tuple[list[tuple[str, dict[str, Any]]], str]:
    native = message.get("tool_calls") or []
    calls = []
    for item in native:
        function = item.get("function", {}) if isinstance(item, dict) else {}
        name = function.get("name")
        args = function.get("arguments")
        if isinstance(args, str):
            args = _json_object(args)
        if isinstance(name, str) and isinstance(args, dict):
            calls.append((name, args))
    if calls:
        return calls, "native"
    content = message.get("content", "")
    parsed = _json_object(content if isinstance(content, str) else "")
    if parsed:
        name = parsed.get("tool") or parsed.get("name")
        args = parsed.get("args") or parsed.get("arguments") or parsed.get("parameters")
        if isinstance(name, str) and isinstance(args, dict):
            return [(name, args)], "json_emulated"
    return [], "none"


class Trace:
    def __init__(self, path: Path, run_id: str, case_id: str, provider: str, model_id: str):
        path.parent.mkdir(parents=True, exist_ok=True)
        self._file = path.open("w", encoding="utf-8")
        self.run_id = run_id
        self.case_id = case_id
        self.provider = provider
        self.model_id = model_id
        self.seq = 0
        self.start = time.monotonic()

    def emit(self, event_type: str, **fields: Any) -> None:
        self.seq += 1
        event = {
            "event_schema": "1.0.0",
            "run_id": self.run_id,
            "seq": self.seq,
            "event_type": event_type,
            "utc": _utc(),
            "monotonic_ms": round((time.monotonic() - self.start) * 1000),
            "case_id": self.case_id,
            "provider": self.provider,
            "model_id": self.model_id,
            **fields,
        }
        self._file.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")
        self._file.flush()

    def close(self) -> None:
        self._file.close()


def run_case(provider: Any, case_id: str, repetition: int, *, max_actions: int = 40,
             max_turns: int = 60, max_wall_seconds: int = 3600, seed: int | None = None,
             out_dir: Path | None = None, num_ctx: int = 24000) -> dict[str, Any]:
    case_path = ROOT / "cases" / case_id / "case_packet.json"
    prompt_path = ROOT / "prompts" / "physician_agent.md"
    packet = json.loads(case_path.read_text(encoding="utf-8"))
    ehr = EHRCase(packet)
    prompt = prompt_path.read_text(encoding="utf-8")
    run_id = str(uuid.uuid4())
    output = out_dir or ROOT / "results" / "raw"
    trace = Trace(output / f"{run_id}.jsonl", run_id, case_id, provider.provider, provider.model_id)
    config = {"temperature": 0, "max_output_tokens": 2048, "num_ctx": num_ctx,
              "seed": seed if seed is not None else repetition}
    system = prompt + "\n\nInterface rule: Emit exactly one tool call per response. Available tool names: " + ", ".join(TOOL_SPECS) + ". In a native function call, its arguments object contains only that function's parameters (no tool/name/args wrapper). If native tool calls are unavailable, emit only one JSON object with keys tool and args. Never include prose around that JSON."
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system},
        {"role": "user", "content": "Initial encounter data:\n" + json.dumps(ehr.public_initial(), ensure_ascii=False) + "\nRequest further data or act through a tool. No source metadata or test catalog is provided."},
    ]
    manifest = {"case_packet_sha256": _sha(case_path), "prompt_sha256": _sha(prompt_path),
                "tool_schema_sha256": hashlib.sha256(json.dumps(ollama_tools(), sort_keys=True).encode()).hexdigest(),
                "repetition": repetition, "config": config, "tool_count": len(TOOL_SPECS),
                "max_actions": max_actions, "max_model_turns": max_turns,
                "max_wall_seconds": max_wall_seconds,
                "repeated_unproductive_call_limit": 3}
    trace.emit("run_started", manifest=manifest, initial=ehr.public_initial())
    started = time.monotonic()
    turns = 0
    invalid_model_outputs = 0
    provider_usage: list[dict[str, Any]] = []
    previous_action_signature: str | None = None
    identical_action_streak = 0
    stopping_reason = "unknown"
    error = None
    try:
        while True:
            if ehr.ended:
                stopping_reason = "completed"
                break
            if turns >= max_turns:
                stopping_reason = "max_model_turns"
                break
            if ehr.action_count >= max_actions:
                stopping_reason = "max_actions"
                break
            if time.monotonic() - started > max_wall_seconds:
                stopping_reason = "max_wall_seconds"
                break
            turns += 1
            trace.emit("model_request", turn_index=turns, payload_sha256=hashlib.sha256(json.dumps(messages, sort_keys=True).encode()).hexdigest(), message_count=len(messages))
            response = provider.generate(messages, ollama_tools(), config)
            message = response.get("message", {})
            usage = response.get("usage", {})
            provider_usage.append(usage)
            calls, transport = _extract_calls(message)
            trace.emit("model_response", turn_index=turns, duration_ms=response.get("latency_ms"),
                       content=message.get("content", ""), tool_transport=transport,
                       tool_calls_count=len(calls), provider_metadata=response.get("raw", {}))
            trace.emit("usage", turn_index=turns, payload=usage)
            if not calls:
                invalid_model_outputs += 1
                signature = "no_call:" + str(message.get("content", ""))
                identical_action_streak = identical_action_streak + 1 if signature == previous_action_signature else 1
                previous_action_signature = signature
                messages.append({"role": "assistant", "content": str(message.get("content", ""))})
                messages.append({"role": "user", "content": "Invalid tool-call output. Use exactly one of these tool names: " + ", ".join(TOOL_SPECS) + ". In native tool calls, put only the tool parameters in arguments. No clinical information is added."})
                trace.emit("error", turn_index=turns, error_code="no_valid_tool_call")
                if identical_action_streak >= 3:
                    stopping_reason = "repeated_unproductive_call"
                    break
                continue
            # Models occasionally return several simultaneous tool calls. Execute
            # in order and log every action, but never add hidden information.
            if transport == "native":
                messages.append(message)
            else:
                messages.append({"role": "assistant", "content": str(message.get("content", ""))})
            for name, args in calls:
                if ehr.action_count >= max_actions:
                    break
                call_id = str(uuid.uuid4())
                trace.emit("tool_call", turn_index=turns, step_index=ehr.step + 1, call_id=call_id, tool=name, args=args)
                tool_started = time.monotonic()
                result = ehr.call(name, args, call_id)
                # The EHR is deterministic. An identical consecutive request,
                # including plan_reason, cannot yield new information.
                signature = json.dumps({"tool": name, "args": args}, sort_keys=True)
                identical_action_streak = identical_action_streak + 1 if signature == previous_action_signature else 1
                previous_action_signature = signature
                trace.emit("tool_result", turn_index=turns, step_index=ehr.step, call_id=call_id, tool=name,
                           status=result["status"], error_code=result["error_code"],
                           duration_ms=round((time.monotonic() - tool_started) * 1000), payload=result["data"])
                if transport == "native":
                    messages.append({"role": "tool", "tool_name": name, "content": json.dumps(result, ensure_ascii=False)})
                else:
                    messages.append({"role": "user", "content": "Tool result:\n" + json.dumps(result, ensure_ascii=False) + "\nContinue with exactly one tool call."})
                if ehr.ended:
                    break
                if identical_action_streak >= 3:
                    stopping_reason = "repeated_unproductive_call"
                    break
            if stopping_reason == "repeated_unproductive_call":
                break
    except Exception as exc:  # Persist a failed run rather than losing its trace.
        stopping_reason = "provider_or_runner_error"
        # Exception text from subprocess timeouts can include the full prompt.
        # Keep only its type in traces and progress logs.
        error = f"{type(exc).__name__}: provider or runner call failed"
        trace.emit("error", error_code="provider_or_runner_error", error=error)
    summary = {"run_id": run_id, "case_id": case_id, "provider": provider.provider,
               "model_id": provider.model_id, "repetition": repetition,
               "stopping_reason": stopping_reason, "completed": ehr.ended,
               "turns": turns, "actions": ehr.action_count, "seen_fact_count": len(ehr.seen_fact_ids),
               "invalid_model_outputs": invalid_model_outputs,
               "elapsed_ms": round((time.monotonic() - started) * 1000),
               "usage": {
                   "input_tokens": sum(u.get("input_tokens") or 0 for u in provider_usage),
                   "cached_input_tokens": sum(u.get("cached_input_tokens") or u.get("cache_read_input_tokens") or 0 for u in provider_usage),
                   "cache_creation_input_tokens": sum(u.get("cache_creation_input_tokens") or 0 for u in provider_usage),
                   "output_tokens": sum(u.get("output_tokens") or 0 for u in provider_usage),
               },
               "review_state": "pending", "error": error}
    trace.emit("run_ended", **summary)
    trace.close()
    return summary


def _provider(name: str, model: str) -> Any:
    if name == "ollama":
        from providers.ollama import OllamaProvider
        return OllamaProvider(model)
    if name == "openai":
        from providers.openai import OpenAIProvider
        return OpenAIProvider(model)
    if name == "anthropic":
        from providers.anthropic import AnthropicProvider
        return AnthropicProvider(model)
    raise ValueError(f"Unsupported provider: {name}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["ollama", "openai", "anthropic"], required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--case", required=True)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--max-actions", type=int, default=40)
    parser.add_argument("--max-turns", type=int, default=60)
    parser.add_argument("--max-wall-seconds", type=int, default=3600)
    parser.add_argument("--num-ctx", type=int, default=24000)
    args = parser.parse_args()
    provider = _provider(args.provider, args.model)
    if args.provider == "ollama":
        print(json.dumps({"preflight": provider.preflight()}, ensure_ascii=False), flush=True)
    for repetition in range(1, args.repetitions + 1):
        result = run_case(provider, args.case, repetition, max_actions=args.max_actions,
                          max_turns=args.max_turns, max_wall_seconds=args.max_wall_seconds,
                          num_ctx=args.num_ctx)
        print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
