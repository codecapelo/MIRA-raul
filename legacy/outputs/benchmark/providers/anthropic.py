"""Claude Code subscription transport for the account based Anthropic arm.

This adapter never reads OAuth material. It invokes the official ``claude`` CLI,
which handles its own subscription authentication. The benchmark harness owns
the EHR and tools; Claude Code's built-in tools and browser are disabled.

The transport is *structured JSON action emulation*, not native Anthropic API
tool use. Keep it as a separately labelled arm in every analysis.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from typing import Any


class AnthropicAccessUnavailable(RuntimeError):
    """The official Claude Code subscription CLI cannot run in this session."""


class AnthropicProtocolError(RuntimeError):
    """Claude CLI returned an invalid or unusable benchmark response."""


_ACTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "content": {"type": "string"},
        "tool_calls": {
            "type": "array",
            "maxItems": 1,
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "arguments": {"type": "object"},
                },
                "required": ["name", "arguments"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["content", "tool_calls"],
    "additionalProperties": False,
}


def _load_json(text: str) -> dict[str, Any]:
    """Accept the CLI's structured_output or a single JSON result string."""
    try:
        outer = json.loads(text)
    except json.JSONDecodeError as exc:
        raise AnthropicProtocolError("Claude CLI output is not JSON") from exc
    if not isinstance(outer, dict):
        raise AnthropicProtocolError("Claude CLI output must be an object")
    return outer


def _status(cli: str) -> dict[str, Any]:
    completed = subprocess.run(
        [cli, "auth", "status", "--json"],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    if completed.returncode:
        return {"loggedIn": False}
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {"loggedIn": False}


class AnthropicProvider:
    """Official Claude Code CLI subscription adapter.

    Contract: ``generate(messages, tools, config)`` returns an Ollama-like
    ``message`` with at most one tool call, plus usage, latency and sanitized
    transport metadata. No API key, session token, OAuth code or cookie is read.
    """

    def __init__(self, model: str = "claude-opus-5-5", effort: str = "high") -> None:
        self.provider = "anthropic"
        self.model = model
        self.model_id = model
        self.effort = effort
        self.cli = shutil.which("claude")

    def preflight(self) -> dict[str, Any]:
        if not self.cli:
            raise AnthropicAccessUnavailable("Official Claude Code CLI is not installed")
        status = _status(self.cli)
        if not status.get("loggedIn"):
            raise AnthropicAccessUnavailable(
                "Claude Code CLI has no authenticated subscription session; "
                "run 'claude auth login --claudeai' interactively"
            )
        return {
            "authenticated": True,
            "transport": "claude_code_subscription_cli_json_action",
            "model_requested": self.model,
            "effort_requested": self.effort,
        }

    def generate(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.preflight()
        config = config or {}
        model = config.get("model", self.model)
        effort = config.get("effort", self.effort)
        if model != "claude-opus-5-5":
            raise ValueError("This benchmark arm is pinned to claude-opus-5-5")
        if effort != "high":
            raise ValueError("This benchmark arm is pinned to high effort")
        timeout = int(config.get("timeout_seconds", 600))

        system_parts = [str(m.get("content", "")) for m in messages if m.get("role") == "system"]
        conversation = [m for m in messages if m.get("role") != "system"]
        system_prompt = "\n\n".join(system_parts) + (
            "\n\nYou are inside a closed-book clinical benchmark. "
            "The only allowed clinical actions are the listed EHR tools. "
            "Do not use your own browser, shell, files, external connectors, "
            "or Claude Code skills to obtain case information. "
            "Return one JSON object matching the specified schema. "
            "Use exactly one tool call for the next action or zero only if the "
            "benchmark protocol explicitly allows a plain-text response."
        )
        prompt = (
            "EHR tool definitions (read-only descriptions; the harness executes actions):\n"
            + json.dumps(tools, ensure_ascii=False, separators=(",", ":"))
            + "\n\nConversation so far (JSON; tool results are authoritative case data):\n"
            + json.dumps(conversation, ensure_ascii=False, separators=(",", ":"))
            + "\n\nChoose the next action. Return only the specified JSON object."
        )
        command = [
            self.cli,
            "--print",
            "--output-format",
            "json",
            "--model",
            model,
            "--effort",
            effort,
            "--system-prompt",
            system_prompt,
            "--json-schema",
            json.dumps(_ACTION_SCHEMA, separators=(",", ":")),
            "--tools",
            "",
            "--no-chrome",
            "--no-session-persistence",
            "--safe-mode",
        ]
        start = time.monotonic()
        completed = subprocess.run(
            command,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        latency_ms = round((time.monotonic() - start) * 1000)
        if completed.returncode:
            # CLI stderr and result text can contain account data. Persist only
            # status and a broad error class, never the raw response.
            try:
                failed = _load_json(completed.stdout)
            except AnthropicProtocolError:
                failed = {}
            status = failed.get("api_error_status")
            result_text = str(failed.get("result", "")).lower()
            category = (
                "rate_or_usage_limit" if status == 429 or "usage limit" in result_text
                else "unsupported_model_or_version" if status == 400 and "model" in result_text
                else "authentication" if status in {401, 403}
                else "other"
            )
            raise AnthropicProtocolError(
                f"Claude Code CLI failed: category={category}, "
                f"api_error_status={status}, exit_code={completed.returncode}"
            )
        envelope = _load_json(completed.stdout)
        if envelope.get("is_error"):
            raise AnthropicProtocolError("Claude Code CLI reported an inference error")
        action = envelope.get("structured_output")
        if not isinstance(action, dict):
            result = envelope.get("result", "")
            action = _load_json(result) if isinstance(result, str) else result
        if not isinstance(action, dict):
            raise AnthropicProtocolError("Claude action is not an object")
        calls = action.get("tool_calls")
        if not isinstance(calls, list) or len(calls) > 1:
            raise AnthropicProtocolError("Claude action must have zero or one tool call")
        normalized = []
        for call in calls:
            if not isinstance(call, dict) or not isinstance(call.get("arguments"), dict):
                raise AnthropicProtocolError("Claude tool arguments must be an object")
            normalized.append(
                {"function": {"name": str(call.get("name", "")), "arguments": call["arguments"]}}
            )
        usage = envelope.get("usage") if isinstance(envelope.get("usage"), dict) else {}
        # The CLI may report a subscription-account cost estimate; it is not
        # equivalent to a charge on an Anthropic API billing account.
        # Expose the action as JSON text so the common runner correctly records
        # json_emulated rather than treating this as native API tool calling.
        if normalized:
            function = normalized[0]["function"]
            message_content = json.dumps(
                {"tool": function["name"], "args": function["arguments"]},
                ensure_ascii=False,
            )
        else:
            message_content = str(action.get("content", ""))
        return {
            "message": {"role": "assistant", "content": message_content, "tool_calls": []},
            "usage": usage,
            "latency_ms": latency_ms,
            "raw": {
                "transport": "claude_code_subscription_cli_json_action",
                "tool_transport": "json_emulated",
                "subtype": envelope.get("subtype"),
                "model_requested": model,
                "models_reported": sorted(envelope["modelUsage"].keys())
                if isinstance(envelope.get("modelUsage"), dict) else [],
                "effort_requested": effort,
                "cost_estimate_usd": envelope.get("total_cost_usd"),
                "assistant_note": str(action.get("content", "")),
                "temperature_accepted": False,
                "seed_accepted": False,
                "max_output_tokens_accepted": False,
            },
        }


__all__ = ["AnthropicProvider", "AnthropicAccessUnavailable", "AnthropicProtocolError"]
