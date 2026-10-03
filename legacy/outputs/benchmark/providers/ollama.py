"""Ollama local chat adapter with native tool calls and JSON-only fallback.

No model download or pull operation is implemented here.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any


class OllamaError(RuntimeError):
    pass


class OllamaProvider:
    provider = "ollama"

    def __init__(self, model_id: str, host: str | None = None, timeout_seconds: int = 600):
        self.model_id = model_id
        self.host = (host or os.environ.get("OLLAMA_HOST") or "http://127.0.0.1:11434").rstrip("/")
        self.timeout_seconds = timeout_seconds

    def _request(self, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        request = urllib.request.Request(
            self.host + path,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST" if data is not None else "GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                return json.load(response)
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            raise OllamaError(f"Ollama request failed: {type(exc).__name__}: {exc}") from exc

    def installed_models(self) -> list[str]:
        return [item["name"] for item in self._request("/api/tags").get("models", [])]

    def preflight(self) -> dict[str, Any]:
        installed = self.installed_models()
        if self.model_id not in installed:
            raise OllamaError(f"Model {self.model_id!r} is not installed; no download attempted")
        started = time.monotonic()
        response = self._request("/api/chat", {
            "model": self.model_id,
            "stream": False,
            "messages": [
                {"role": "system", "content": "You are testing a tool-call interface. Call the supplied probe tool once with value 'ok'."},
                {"role": "user", "content": "Call probe now."},
            ],
            "tools": [{"type": "function", "function": {"name": "probe", "description": "Connectivity probe", "parameters": {"type": "object", "properties": {"value": {"type": "string"}}, "required": ["value"], "additionalProperties": False}}}],
            "think": False,
            "options": {"temperature": 0, "num_predict": 64, "num_ctx": 2048},
        })
        message = response.get("message", {})
        return {
            "model_id": self.model_id,
            "installed": True,
            "latency_ms": round((time.monotonic() - started) * 1000),
            "native_tool_calls": len(message.get("tool_calls") or []),
            "content_preview": str(message.get("content", ""))[:120],
            "prompt_eval_count": response.get("prompt_eval_count"),
            "eval_count": response.get("eval_count"),
        }

    def generate(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
        options: dict[str, Any] = {
            "temperature": config.get("temperature", 0),
            "num_predict": config.get("max_output_tokens", 2048),
            "num_ctx": config.get("num_ctx", 24000),
        }
        if config.get("seed") is not None:
            options["seed"] = config["seed"]
        body = {
            "model": self.model_id,
            "stream": False,
            "messages": messages,
            "tools": tools,
            "think": config.get("think", False),
            "options": options,
            "keep_alive": config.get("keep_alive", "15m"),
        }
        started = time.monotonic()
        response = self._request("/api/chat", body)
        latency_ms = round((time.monotonic() - started) * 1000)
        usage = {
            "input_tokens": response.get("prompt_eval_count"),
            "output_tokens": response.get("eval_count"),
            "prompt_eval_count": response.get("prompt_eval_count"),
            "eval_count": response.get("eval_count"),
            "prompt_eval_duration_ns": response.get("prompt_eval_duration"),
            "eval_duration_ns": response.get("eval_duration"),
            "load_duration_ns": response.get("load_duration"),
            "total_duration_ns": response.get("total_duration"),
            "memory_peak_bytes": None,
            "cost_estimate_usd": 0.0,
        }
        return {
            "message": response.get("message", {"role": "assistant", "content": ""}),
            "usage": usage,
            "latency_ms": latency_ms,
            "raw": {"done_reason": response.get("done_reason"), "model": response.get("model")},
            "tool_transport": "native" if response.get("message", {}).get("tool_calls") else "json_fallback_or_none",
        }
