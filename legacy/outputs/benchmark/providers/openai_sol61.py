"""GPT-6.1 Sol high through the official ChatGPT-authenticated Codex CLI.

This is a subscription CLI action-emulation transport, not the OpenAI API and
not native Responses API function calling. It does not inspect any credential.
The clinical benchmark harness, not Codex, executes the EHR calls.
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any


class OpenAIAccountError(RuntimeError):
    pass


class OpenAIProvider:
    provider = 'openai'
    model_id = 'gpt-6.1-sol'
    transport = 'codex_chatgpt_subscription_cli_json_action'

    def __init__(self, model_id: str = 'gpt-6.1-sol', effort: str = 'high', cli: str = '/opt/homebrew/bin/codex'):
        if model_id != self.model_id or effort != 'high':
            raise ValueError('This arm is pinned to GPT-6.1 Sol high')
        self.effort = effort
        self.cli = cli
        self.schema_path = Path(__file__).with_name('action_schema.json')

    def preflight(self) -> dict[str, Any]:
        if not Path(self.cli).is_file():
            raise OpenAIAccountError('Official Codex CLI unavailable')
        p = subprocess.run([self.cli,'login','status'],capture_output=True,text=True,timeout=15)
        if p.returncode or 'Logged in using ChatGPT' not in (p.stdout + p.stderr):
            raise OpenAIAccountError('Codex CLI is not authenticated with ChatGPT')
        return {'authenticated':True,'transport':self.transport,'model_requested':self.model_id,'effort_requested':self.effort}

    def generate(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]], config: dict[str, Any] | None = None) -> dict[str, Any]:
        self.preflight()
        config=config or {}
        if config.get('model',self.model_id)!=self.model_id or config.get('effort',self.effort)!='high':
            raise ValueError('Model and effort are frozen for this arm')
        prompt=(
            'You are in a retrospective closed-book clinical benchmark. The task protocol and physician instruction are in the SYSTEM messages below. '
            'You must choose exactly ONE next EHR action. Return a JSON object with content and tool_calls matching the output schema. '
            'tool_calls must contain exactly one object with name and arguments_json, where arguments_json is a JSON-encoded object of tool arguments. Do not use your own shell, files, web browser, connectors, or other tools. '
            'The EHR harness executes the action and supplies the next result; never invent a result. No live patient is being treated.\n\n'
            'EHR tool definitions:\n'+json.dumps(tools,ensure_ascii=False,separators=(',',':'))+
            '\n\nConversation so far, where tool results are authoritative:\n'+json.dumps(messages,ensure_ascii=False,separators=(',',':'))+
            '\n\nReturn the next action only as JSON.'
        )
        cmd=[self.cli,'exec','-m',self.model_id,'-c',"model_reasoning_effort='high'",'-s','read-only','--skip-git-repo-check','--ephemeral','--ignore-user-config','--ignore-rules','--json','--output-schema',str(self.schema_path),prompt]
        start=time.monotonic()
        p=subprocess.run(cmd,input='',capture_output=True,text=True,timeout=int(config.get('timeout_seconds',600)))
        latency_ms=round((time.monotonic()-start)*1000)
        if p.returncode:
            # stderr can carry account data: keep only status, not its contents.
            raise OpenAIAccountError(f'Codex CLI inference failed with exit code {p.returncode}')
        final=None; usage={}; errors=0
        for line in p.stdout.splitlines():
            try: event=json.loads(line)
            except json.JSONDecodeError: continue
            if event.get('type')=='item.completed':
                item=event.get('item') or {}
                if item.get('type')=='agent_message': final=item.get('text')
                elif item.get('type')=='error': errors+=1
            elif event.get('type')=='turn.completed': usage=event.get('usage') or {}
        if final is None:
            raise OpenAIAccountError('Codex CLI returned no final action')
        try: action=json.loads(final)
        except json.JSONDecodeError as exc: raise OpenAIAccountError('Codex CLI action is not JSON') from exc
        calls=action.get('tool_calls')
        if not isinstance(calls,list) or len(calls)!=1:
            raise OpenAIAccountError('Codex CLI action must have exactly one EHR call')
        call=calls[0]
        if not isinstance(call,dict):
            raise OpenAIAccountError('Codex CLI action arguments invalid')
        try: args=json.loads(call.get('arguments_json',''))
        except (TypeError,ValueError) as exc: raise OpenAIAccountError('Codex CLI arguments_json is invalid') from exc
        if not isinstance(args,dict):
            raise OpenAIAccountError('Codex CLI action arguments are not an object')
        return {'message':{'role':'assistant','content':str(action.get('content','')),'tool_calls':[{'function':{'name':str(call.get('name','')),'arguments':args}}]},'usage':usage,'latency_ms':latency_ms,'raw':{'transport':self.transport,'model_requested':self.model_id,'effort_requested':self.effort,'cli_error_events':errors},'tool_transport':'json_emulated'}
