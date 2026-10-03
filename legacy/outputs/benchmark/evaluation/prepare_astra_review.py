"""Create blinded Astra addon packets in a generic review round."""

from __future__ import annotations

import csv
import argparse
import hashlib
import json
from pathlib import Path

from .analyze_astra_addon import ROOT, load_addon_rows
from .validate import read_trace


def _display(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--partial", action="store_true", help="Export only available addon terminals to a separate partial review round")
    args = parser.parse_args()
    prior_rows, rows, _, _ = load_addon_rows(allow_incomplete=args.partial)
    if len(prior_rows) != 230:
        raise SystemExit("Preserved prior panel requires 230 terminals")
    if not rows or (not args.partial and len(rows) != 30):
        raise SystemExit("Final addon medical review requires all 30 Astra terminal trajectories")
    review_dir = ROOT / "results" / "review_addons" / ("round_2026_09_29_partial" if args.partial else "round_2026_09_29")
    internal_dir = ROOT / "results" / "review_addons_internal" / ("round_2026_09_29_partial" if args.partial else "round_2026_09_29")
    packets_dir = review_dir / "packets"
    protected = [review_dir / name for name in (
        "review_scope.json", "review_queue.csv", "review_decisions.csv", "review_action_decisions.csv",
        "review_opportunities.csv", "review_safety_events.csv")]
    protected.append(internal_dir / "review_key.csv")
    if any(path.exists() for path in protected) or (packets_dir.exists() and any(packets_dir.glob("*.md"))):
        raise SystemExit("Review export already exists; refusing to overwrite medical adjudications")
    packets_dir.mkdir(parents=True, exist_ok=True)
    internal_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / "review_scope.json").write_text(json.dumps({
        "schema_version": "1.0.0", "panel_state": "partial" if args.partial else "complete",
        "observed_new_terminal_packets": len(rows), "expected_new_terminal_packets": 30,
        "observed_combined_terminal_trajectories": len(prior_rows) + len(rows), "expected_combined_terminal_trajectories": 270,
        "scope": "Only new clinical terminal trajectories in this blinded addon round; preserved errors require additional review. No model identities in this directory.",
    }, indent=2) + "\n")
    key_rows: list[dict[str, str]] = []
    queue_rows: list[dict[str, str]] = []
    action_rows: list[dict[str, str]] = []
    opportunity_rows: list[dict[str, str]] = []
    for row in rows:
        run_id = row["run_id"]
        blind_id = "R" + hashlib.sha256((run_id + "|mira-2026-addon-2026-09-29-review").encode()).hexdigest()[:12].upper()
        events = read_trace(ROOT / row["trace_path"])
        rubric = json.loads((ROOT / "cases" / row["case_id"] / "rubric.json").read_text())
        pending_calls: dict[str, dict] = {}
        narrative = [f"# Revisão clínica {blind_id}", "", f"Caso: `{row['case_id']}`", "",
                     "Consultar o PDF fonte, `ground_truth.json` e `rubric.json` do caso antes de adjudicar.", "",
                     "A identidade do modelo e as métricas automáticas foram ocultadas neste packet.", "",
                     "## Encontro inicial", "", f"`{_display(events[0].get('initial', {}))}`", "",
                     "## Trajetória observável", ""]
        for event in events:
            if event.get("event_type") == "tool_call":
                pending_calls[event["call_id"]] = event
                for stage in ("primary", "second", "consensus"):
                    action_rows.append({"blind_id": blind_id, "review_stage": stage,
                                        "step_index": str(event["step_index"]),
                                        "call_id": event["call_id"], "tool": event["tool"],
                                        "action_appropriateness": "", "unnecessary_action": "",
                                        "guideline_concordance": "", "guideline_ref": "",
                                        "evidence_fact_ids": "", "rationale": ""})
            elif event.get("event_type") == "tool_result":
                call = pending_calls.pop(event.get("call_id"), None)
                if call is None:
                    raise ValueError(f"Unpaired tool result in {run_id}")
                narrative.extend([f"### Passo {call['step_index']}: `{call['tool']}`", "",
                                  f"Argumentos: `{_display(call.get('args', {}))}`", "",
                                  f"Resultado: `{event.get('status')}`", "",
                                  f"Dados retornados: `{_display(event.get('payload', {}))}`", ""])
            elif event.get("event_type") == "error":
                narrative.extend([f"Erro de execução no turno {event.get('turn_index', '—')}: `{event.get('error_code', 'unknown')}`", ""])
        if pending_calls:
            raise ValueError(f"Unpaired tool calls in {run_id}")
        for expected in rubric.get("expected_actions", []):
            for stage in ("primary", "second", "consensus"):
                opportunity_rows.append({"blind_id": blind_id, "review_stage": stage,
                                         "opportunity_kind": "expected_action", "rubric_item_id": expected["action_id"],
                                         "description": _display(expected.get("acceptable_tool_calls", [])),
                                         "priority": expected.get("priority", ""),
                                         "status": "", "matching_step_indices": "",
                                         "evidence_fact_ids": "", "rationale": ""})
        for safety_index, safety in enumerate(rubric.get("safety_opportunities", []), 1):
            for stage in ("primary", "second", "consensus"):
                opportunity_rows.append({"blind_id": blind_id, "review_stage": stage,
                                         "opportunity_kind": "safety", "rubric_item_id": f"s{safety_index}",
                                         "description": safety.get("description", ""),
                                         "priority": safety.get("priority", "unspecified"), "status": "", "matching_step_indices": "",
                                         "evidence_fact_ids": "", "rationale": ""})
        end = events[-1]
        narrative.extend(["## Encerramento", "",
                          f"Concluído: `{end.get('completed')}`. Motivo: `{end.get('stopping_reason')}`. "
                          f"Turnos: `{end.get('turns')}`. Ações: `{end.get('actions')}`. "
                          f"Saídas inválidas do modelo: `{end.get('invalid_model_outputs')}`.", "",
                          "## Classificação médica", "",
                          "Preencher `review_decisions.csv`; classes: `correct`, `acceptable_alternative`, `questionable`, `unsafe`.",
                          "Registrar omissões críticas e eventos de segurança com passo e evidência disponível naquele instante.", ""])
        packet_path = packets_dir / f"{blind_id}.md"
        packet_path.write_text("\n".join(narrative), encoding="utf-8")
        key_rows.append({"blind_id": blind_id, "run_id": run_id, "case_id": row["case_id"],
                         "provider": row["provider"], "model_id": row["model_id"],
                         "repetition": str(row["repetition"])})
        queue_rows.append({"blind_id": blind_id, "case_id": row["case_id"],
                           "packet": f"packets/{blind_id}.md",
                           "source_pdf": f"../../../cases/{row['case_id']}/source.pdf",
                           "ground_truth": f"../../../cases/{row['case_id']}/ground_truth.json",
                           "rubric": f"../../../cases/{row['case_id']}/rubric.json"})
    queue_rows.sort(key=lambda x: (x["case_id"], x["blind_id"]))
    key_rows.sort(key=lambda x: x["blind_id"])
    def write_csv(path: Path, records: list[dict], fields: list[str]) -> None:
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(records)
    write_csv(review_dir / "review_queue.csv", queue_rows,
              ["blind_id", "case_id", "packet", "source_pdf", "ground_truth", "rubric"])
    write_csv(internal_dir / "review_key.csv", key_rows,
              ["blind_id", "run_id", "case_id", "provider", "model_id", "repetition"])
    blank = [{"blind_id": r["blind_id"], "review_stage": stage, "reviewer_id": "", "reviewed_at_utc": "",
              "diagnosis": "", "treatment": "", "disposition": "", "critical_omissions": "",
              "safety_events": "", "unnecessary_actions": "", "notes": ""}
             for r in queue_rows for stage in ("primary", "second", "consensus")]
    write_csv(review_dir / "review_decisions.csv", blank, list(blank[0]))
    write_csv(review_dir / "review_action_decisions.csv", action_rows,
              ["blind_id", "review_stage", "step_index", "call_id", "tool", "action_appropriateness",
               "unnecessary_action", "guideline_concordance", "guideline_ref", "evidence_fact_ids", "rationale"])
    write_csv(review_dir / "review_opportunities.csv", opportunity_rows,
              ["blind_id", "review_stage", "opportunity_kind", "rubric_item_id", "description", "priority",
               "status", "matching_step_indices", "evidence_fact_ids", "rationale"])
    write_csv(review_dir / "review_safety_events.csv", [],
              ["blind_id", "review_stage", "step_index", "call_id", "safety_category", "severity",
               "evidence_fact_ids", "rubric_opportunity_id", "rationale"])
    print(f"Prepared {len(queue_rows)} blinded packets in {review_dir}")


if __name__ == "__main__":
    main()
