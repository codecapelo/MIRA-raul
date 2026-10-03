"""Add Astra to the preserved 230-run panel without rewriting prior analyses.

The default export requires 30 Astra clinical terminals and retains Luna at
20 terminals. --partial writes distinct filenames during the Astra run.
Clinical safety and diagnostic equivalence still require physician review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path

from .analyze_extension import (
    ROOT, BINARY_FIELDS, EXPECTED_CASES, EXPECTED_MODELS, _case_mean,
    _check_trace_contract, _computed_openai_cost, _interval, _sha,
    analyze as analyze_existing, load_rows as load_existing,
    verify_freeze as verify_existing,
)
from .metrics import score_run
from .validate import load_json, read_trace, validate_trace
from tools.schemas import ollama_tools

MODEL = "gpt-6-astra"
MANIFEST = ROOT / "docs" / "protocol_astra_extension_2026-09-29.json"
ARCHIVED_PANEL = ROOT / "results" / "extension_2026-09-28" / "summaries" / "partial_combined_analysis.json"
OUT = ROOT / "results" / "extension_astra_2026-09-29" / "summaries"
RESULTS = ROOT / "results" / "extension_astra_2026-09-29"


def verify_addon() -> dict:
    verify_existing()
    base = load_json(ROOT / "docs" / "protocol_freeze_manifest.json")
    corpus = load_json(ROOT / "docs" / "corpus_freeze_manifest.json")
    manifest = load_json(MANIFEST)
    if (manifest.get("extension_version") != "mvp10_extension_astra_2026-09-29"
            or manifest.get("base_protocol_version") != base["protocol_version"]
            or manifest.get("base_protocol_manifest_sha256") != _sha(ROOT / "docs" / "protocol_freeze_manifest.json")
            or manifest.get("corpus_version") != corpus["corpus_version"]
            or manifest.get("case_order") != EXPECTED_CASES
            or manifest.get("repetitions") != 3
            or manifest.get("results_directory") != str(RESULTS.relative_to(ROOT))
            or set(manifest.get("models", {})) != {MODEL}):
        raise ValueError("Astra addon is not the frozen v5 clinical protocol")
    definition = manifest["models"][MODEL]
    if (definition.get("provider") != "openai" or definition.get("effort") != "high"
            or definition.get("model_observed", "non-null") is not None
            or definition.get("progress_path") != str((RESULTS / "summaries" / "astra_progress.jsonl").relative_to(ROOT))):
        raise ValueError("Astra provider, requested effort, or observed identity changed")
    for key in ("max_actions", "max_model_turns", "max_wall_seconds", "repeated_unproductive_call_limit"):
        if manifest.get(key) != base[key]:
            raise ValueError(f"Astra clinical limit changed: {key}")
    for item in manifest.get("files", []):
        path = ROOT / item["path"]
        if not path.is_file() or _sha(path) != item["sha256"]:
            raise ValueError(f"Frozen Astra file changed: {item['path']}")
    wrapper = manifest.get("diagnostic_wrapper", {})
    if wrapper:
        path = ROOT / wrapper["path"]
        if not path.is_file() or _sha(path) != wrapper["sha256"]:
            raise ValueError("Astra diagnostic wrapper changed from its declared snapshot")
    pricing = manifest.get("pricing", {}).get(MODEL, {})
    if (pricing.get("verified") is not True
            or pricing.get("source_url") != "https://developers.openai.com/api/docs/models/gpt-6-astra"
            or any(pricing.get(field) != value for field, value in (
                ("input_per_million", 10.0), ("cached_input_per_million", 1.0),
                ("cache_write_input_per_million", 12.5), ("output_per_million", 50.0),
                ("long_context_threshold", 272000),
                ("input_includes_cached", True), ("output_includes_reasoning", True)))):
        raise ValueError("Astra tariff or token semantics differ from the verified manifest")
    return manifest


def _load_index(manifest: dict, model: str = MODEL) -> dict[str, dict]:
    path = ROOT / manifest["models"][model]["progress_path"]
    if not path.exists():
        return {}
    rows: dict[str, dict] = {}
    for line in path.read_text().splitlines():
        entry = json.loads(line)
        if (entry.get("model_id") != model or entry.get("extension_version") != manifest["extension_version"]
                or not isinstance(entry.get("run_id"), str) or entry["run_id"] in rows):
            raise ValueError("Invalid or duplicate Astra progress index row")
        rows[entry["run_id"]] = entry
    return rows


def _check_index(entry: dict, events: list[dict], path: Path, manifest: dict, model: str = MODEL) -> None:
    first, end = events[0], events[-1]
    expected = {"extension_version": manifest["extension_version"], "corpus_version": manifest["corpus_version"],
                "protocol_version": manifest["base_protocol_version"], "model_id": model,
                "model_requested": model, "model_observed": None, "provider": "openai",
                "reasoning_effort": "high", "case_id": first["case_id"],
                "repetition": first["manifest"]["repetition"],
                "trace_path": str(path.relative_to(ROOT)), "stopping_reason": end.get("stopping_reason")}
    if any(entry.get(key) != value for key, value in expected.items()):
        raise ValueError(f"Astra index/trace mismatch: {path.name}")
    if first.get("provider") != "openai" or first.get("model_id") != model or path.stem != first.get("run_id"):
        raise ValueError(f"Astra trace identity mismatch: {path.name}")


def _contract(events: list[dict], manifest: dict) -> None:
    base = load_json(ROOT / "docs" / "protocol_freeze_manifest.json")
    corpus = load_json(ROOT / "docs" / "corpus_freeze_manifest.json")
    packet_hashes = {item["path"].split("/")[1]: item["sha256"] for item in corpus["files"]
                     if item["path"].endswith("/case_packet.json")}
    prompt_hash = next(item["sha256"] for item in base["files"] if item["path"] == "prompts/physician_agent.md")
    schema_hash = hashlib.sha256(json.dumps(ollama_tools(), sort_keys=True).encode()).hexdigest()
    _check_trace_contract(events, base, packet_hashes, prompt_hash, schema_hash)


def load_addon_rows(*, allow_incomplete: bool = False) -> tuple[list[dict], list[dict], dict, dict]:
    manifest = verify_addon()
    archived = load_json(ARCHIVED_PANEL)
    if (archived.get("observed_terminal_trajectories") != 230 or archived.get("panel_state") != "partial"
            or archived.get("corpus_version") != manifest["corpus_version"]
            or archived.get("protocol_version") != manifest["base_protocol_version"]
            or set(archived.get("models", {})) != set(EXPECTED_MODELS)):
        raise ValueError("Preserved eight-model panel is not the 230-run source")
    prior_rows = load_existing(allow_incomplete=True)
    if len(prior_rows) != 230:
        raise ValueError(f"Preserved prior panel changed from 230 terminals: {len(prior_rows)}")
    fresh = analyze_existing(prior_rows)
    for key in ("corpus_version", "protocol_version"):
        if fresh[key] != archived[key]:
            raise ValueError(f"Prior panel changed: {key}")
    for model in EXPECTED_MODELS:
        if fresh["models"][model] != archived["models"][model]:
            raise ValueError(f"Prior model scores or usage changed: {model}")
    if fresh["evaluation"]["scorer_sha256"] != archived["evaluation"]["scorer_sha256"]:
        raise ValueError("Frozen scorer hash changed")
    index = _load_index(manifest)
    new_rows: list[dict] = []
    raw = RESULTS / "raw"
    for path in sorted(raw.glob("*.jsonl")):
        events = read_trace(path)
        if not events or events[-1].get("event_type") != "run_ended":
            if allow_incomplete:
                continue
            raise ValueError(f"Astra raw trace is nonterminal: {path.name}")
        valid = validate_trace(events)
        if not valid["valid"]:
            raise ValueError(f"Astra invalid trace: {path.name}: {valid['errors']}")
        first, end = events[0], events[-1]
        if first.get("case_id") not in EXPECTED_CASES or first.get("manifest", {}).get("repetition") not in (1, 2, 3):
            raise ValueError(f"Astra case/repetition outside frozen design: {path.name}")
        entry = index.get(first.get("run_id"))
        if entry is None:
            if allow_incomplete:  # Append-only trace can precede the index flush.
                continue
            raise ValueError(f"Astra trace missing progress entry: {path.name}")
        _check_index(entry, events, path, manifest)
        _contract(events, manifest)
        if end.get("stopping_reason") == "provider_or_runner_error":
            raise ValueError(f"Astra provider error remained in clinical raw/: {path.name}")
        responses = [item for item in events if item.get("event_type") == "model_response"]
        if not responses:
            raise ValueError(f"Astra trace has no response evidence: {path.name}")
        for response in responses:
            meta = response.get("provider_metadata", {})
            if (meta.get("model_requested") != MODEL or meta.get("effort_requested") != "high"
                    or meta.get("models_reported") not in (None, [])):
                raise ValueError(f"Astra model/effort evidence mismatch: {path.name}")
        case = ROOT / "cases" / first["case_id"]
        row = score_run(events, load_json(case / "ground_truth.json"), load_json(case / "rubric.json"))
        row.update({"repetition": first["manifest"]["repetition"], "arm_origin": manifest["extension_version"],
                    "trace_path": str(path.relative_to(ROOT)),
                    "identity_evidence": "requested_and_inference_accepted_not_observed",
                    "cost_usage_events": [item.get("payload", {}) for item in events if item.get("event_type") == "usage"],
                    "cost_response_count": len(responses)})
        new_rows.append(row)
    all_ids = [item["run_id"] for item in prior_rows + new_rows]
    keys = [(item["model_id"], item["case_id"], item["repetition"]) for item in prior_rows + new_rows]
    if len(all_ids) != len(set(all_ids)) or len(keys) != len(set(keys)):
        raise ValueError("Duplicate run ID or model/case/repetition across preserved panel and Astra")
    if len(new_rows) > 30:
        raise ValueError("More than 30 Astra terminals")
    return prior_rows, new_rows, manifest, archived


def _score_astra(rows: list[dict], manifest: dict, model: str = MODEL) -> dict:
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        groups[row["case_id"]].append(row)
    complete = all({row["repetition"] for row in groups[case]} == {1, 2, 3} for case in EXPECTED_CASES)
    entry = {"observed_runs": len(rows), "expected_runs": 30, "complete_panel": complete,
             "cases": {case: {"runs": len(groups[case]), "completed": sum(bool(r["completed"]) for r in groups[case]),
                              "concept_matches": sum(r["benchmark_target_concept_match"] is True for r in groups[case]),
                              "tool_calls": [r["tool_calls"] for r in groups[case]],
                              "stopping_reasons": [r["stopping_reason"] for r in groups[case]]}
                       for case in EXPECTED_CASES}, "metrics": {}}
    for field in BINARY_FIELDS:
        values = [_case_mean(groups[case], field) for case in EXPECTED_CASES if groups[case]]
        values = [value for value in values if value is not None]
        entry["metrics"][field] = {"case_mean": sum(values)/len(values) if values else None,
                                    "case_cluster_bootstrap_95": _interval(values) if complete and len(values) == 10 else None,
                                    "evaluable_cases": len(values), "provisional": field != "completed"}
    entry["total_tool_calls"] = sum(r["tool_calls"] for r in rows)
    entry["median_run_seconds"] = statistics.median(r["total_duration_ms"]/1000 for r in rows) if rows else None
    emitted = [r for r in rows if r["diagnosis_emitted"]]
    entry["diagnosis_emitted_runs"] = len(emitted)
    entry["target_match_given_diagnosis"] = (sum(r["benchmark_target_concept_match"] is True for r in emitted)/len(emitted)
                                               if emitted else None)
    def mean_field(field: str) -> float | None:
        values = [float(r[field]) for r in rows if r.get(field) is not None]
        return sum(values)/len(values) if values else None
    def sum_usage(field: str) -> float | None:
        values = [float(r["usage"][field]) for r in rows if r.get("usage", {}).get(field) is not None]
        return sum(values) if values else None
    entry["process"] = {
        "mean_lab_requests": mean_field("lab_requests"), "mean_imaging_requests": mean_field("imaging_requests"),
        "mean_procedure_orders": mean_field("procedure_orders"), "mean_medication_orders": mean_field("medication_orders"),
        "mean_steps_to_benchmark_diagnosis": mean_field("steps_to_first_benchmark_target"),
        "invalid_tool_calls": sum(r["invalid_tool_calls"] for r in rows),
        "failed_tool_calls": sum(r["invalid_or_failed_tool_calls"] for r in rows),
        "reported_input_tokens": sum_usage("input_tokens"), "reported_cached_input_tokens": sum_usage("cached_input_tokens"),
        "reported_cache_creation_input_tokens": sum_usage("cache_creation_input_tokens"),
        "reported_output_tokens": sum_usage("output_tokens"), "reported_reasoning_tokens": sum_usage("reasoning_tokens"),
        "reported_cost_equivalent_usd": sum_usage("cost_estimate_usd"),
        "mean_local_tokens_per_second": mean_field("local_tokens_per_second")}
    entry["observed_match_count"] = sum(r["benchmark_target_concept_match"] is True for r in rows)
    entry["observed_run_target_rate"] = entry["observed_match_count"]/len(rows) if rows else None
    entry["computed_cost_proxy"] = _computed_openai_cost(rows, manifest, model)
    entry["identity_evidence"] = "requested_and_inference_accepted_not_observed"
    return entry


def _astra_errors(manifest: dict, index: dict[str, dict], terminal_ids: set[str],
                  model: str = MODEL, results: Path = RESULTS) -> dict:
    attempts = []
    for path in sorted((results / "incomplete").glob("*.jsonl")):
        events = read_trace(path)
        if not events or not validate_trace(events)["valid"]:
            raise ValueError(f"Invalid preserved Astra provider-error trace: {path.name}")
        first, end = events[0], events[-1]
        entry = index.get(first["run_id"])
        if entry is None:
            raise ValueError(f"Preserved Astra error missing index: {path.name}")
        _check_index(entry, events, path, manifest, model)
        _contract(events, manifest)
        if (first["run_id"] in terminal_ids or end.get("stopping_reason") != "provider_or_runner_error"
                or end.get("completed") is not False):
            raise ValueError(f"Preserved Astra error overlaps clinical terminal: {path.name}")
        frames = [item.get("payload", {}) for item in events if item.get("event_type") == "usage"]
        proxy = _computed_openai_cost([{"run_id": first["run_id"], "cost_usage_events": frames}], manifest, model)
        attempts.append({"path": str(path.relative_to(ROOT)), "sha256": _sha(path), "run_id": first["run_id"],
                         "case_id": first["case_id"], "repetition": first["manifest"]["repetition"],
                         "usage_events": len(frames), "known_prefix_api_proxy": proxy,
                         "last_failed_call_usage_known": False, "cause": "not established from generic provider/runner error"})
    if len({item["run_id"] for item in attempts}) != len(attempts):
        raise ValueError("Duplicate Astra preserved error")
    return {"attempts": attempts, "attempt_count": len(attempts),
            "included_in_clinical_denominator": False,
            "coverage": "Verified preserved Astra errors only; known usage prefix is not total failed-attempt cost."}


def analyze(*, allow_incomplete: bool = False) -> dict:
    prior_rows, new_rows, manifest, archived = load_addon_rows(allow_incomplete=allow_incomplete)
    if not allow_incomplete and len(new_rows) != 30:
        raise ValueError(f"Final Astra analysis requires 30 Astra terminals, got {len(new_rows)}")
    baseline_models = {model: archived["models"][model] for model in EXPECTED_MODELS}
    astra = _score_astra(new_rows, manifest)
    if not allow_incomplete and not astra["complete_panel"]:
        raise ValueError("Final Astra analysis requires 10 cases x 3 distinct repetitions")
    rows = prior_rows + new_rows
    index = _load_index(manifest)
    result = {"schema_version": "1.0.0", "addon_version": manifest["extension_version"],
              "corpus_version": manifest["corpus_version"], "protocol_version": manifest["base_protocol_version"],
              "evaluation": {"version": "evaluation-v2", "diagnosis_ruleset_version": archived["evaluation"]["diagnosis_ruleset_version"],
                             "diagnosis_ruleset_sha256": archived["evaluation"]["diagnosis_ruleset_sha256"],
                             "scorer_sha256": archived["evaluation"]["scorer_sha256"],
                             "analyzer_sha256": _sha(Path(__file__))},
              "expected_trajectories": 270, "observed_terminal_trajectories": len(rows),
              "preserved_prior_trajectories": 230, "astra_observed_trajectories": len(new_rows),
              "luna_observed_trajectories": 20, "luna_planned_trajectories": 30,
              "baseline_source": {"path": str(ARCHIVED_PANEL.relative_to(ROOT)), "sha256": _sha(ARCHIVED_PANEL),
                                  "all_eight_model_fields_equal": True},
              "astra_manifest": {"path": str(MANIFEST.relative_to(ROOT)), "sha256": _sha(MANIFEST)},
              "models": {**baseline_models, MODEL: astra}, "paired_differences": {},
              "astra_operational_errors": _astra_errors(manifest, index, {r["run_id"] for r in rows}),
              "physician_review_state": "pending", "panel_state": "astra_complete_prior_luna_partial" if astra["complete_panel"] else "astra_partial_prior_luna_partial",
              "interpretation": "Exploratory public-case lexical process measures, not adjudicated clinical accuracy or safety. Model plus subscription CLI transport and execution date; Luna remains 20/30."}
    if astra["complete_panel"]:
        by_model_case: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
        for row in rows:
            by_model_case[row["model_id"]][row["case_id"]].append(row)
        for field in ("completed", "benchmark_target_concept_match"):
            for model in EXPECTED_MODELS:
                if model == "gpt-6-luna":  # 20/30, no imputation or pairwise inference.
                    continue
                if not baseline_models[model]["complete_panel"]:
                    continue
                differences = [_case_mean(by_model_case[MODEL][case], field) - _case_mean(by_model_case[model][case], field)
                               for case in EXPECTED_CASES]
                result["paired_differences"][f"{field}: {MODEL} minus {model}"] = {
                    "mean": sum(differences)/10, "case_cluster_bootstrap_95": _interval(differences),
                    "case_differences": differences, "provisional": field != "completed",
                    "comparison_scope": "Astra and a complete 30-run prior arm only; excludes incomplete Luna"}
    return result


def markdown(report: dict) -> str:
    def pct(value: float | None) -> str:
        return "—" if value is None else f"{100*value:.1f}%"
    lines = ["# Astra high — comparação aditiva com o painel preservado", "",
             f"Trajetórias clínicas terminais: **{report['observed_terminal_trajectories']}/270 planejadas**; painel anterior preservado **230**, Astra **{report['astra_observed_trajectories']}/30**, Luna anterior **20/30**.", "",
             "| Modelo | Runs observadas | Conclusão entre observadas | Alvo provisório, média por caso | Alvo bruto entre observadas | Custo CLI equivalente USD | Proxy API USD |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for model in (*EXPECTED_MODELS, MODEL):
        item = report["models"][model]
        observed = item["observed_runs"]
        completion = sum(case["completed"] for case in item["cases"].values()) / observed if observed else None
        process = item["process"]
        reported = process["reported_cost_equivalent_usd"] if model in {"claude-opus-5-5", "claude-sonnet-5-5"} else None
        proxy = item.get("computed_cost_proxy", {}).get("computed_api_equivalent_usd")
        cost = lambda value: "—" if value is None else f"{value:.6f}"
        lines.append(f"| {model} | {observed}/30 | {pct(completion)} | {pct(item['metrics']['benchmark_target_concept_match']['case_mean'])} | {pct(item['observed_run_target_rate'])} | {cost(reported)} | {cost(proxy)} |")
    lines.extend(["", "Ausência de diagnóstico EHR aceito conta como erro no match provisório; equivalência lexical não substitui adjudicação médica. Os dez casos públicos podem ter contaminado treino. O braço Luna foi interrompido a pedido do usuário e mantém dez combinações ausentes; não foram imputadas como falhas e não recebe comparação pareada com Astra.", "",
                  "## Por caso", "",
                  "Cada célula: match do alvo/runs observadas. Traço significa caso sem run terminal, não resultado negativo.", "",
                  "| Caso | " + " | ".join((*EXPECTED_MODELS, MODEL)) + " |",
                  "|---|" + "---:|" * (len(EXPECTED_MODELS)+1)])
    for case in EXPECTED_CASES:
        values = []
        for model in (*EXPECTED_MODELS, MODEL):
            item = report["models"][model]["cases"][case]
            values.append(f"{item['concept_matches']}/{item['runs']}" if item["runs"] else "—")
        lines.append("| " + case + " | " + " | ".join(values) + " |")
    lines.extend(["", "## Comparações pareadas exploratórias", "",
                  "Somente Astra versus braços completos de 30 runs, após Astra alcançar 10 casos × 3. Diferenças são médias por caso com bootstrap descritivo; multiplicidade não ajustada. Luna parcial fica fora.", ""])
    if report["paired_differences"]:
        lines.extend(["| Comparação | Diferença média | IC bootstrap 95% |", "|---|---:|---:|"])
        for label, result in report["paired_differences"].items():
            ci = result["case_cluster_bootstrap_95"]
            lines.append(f"| {label} | {100*result['mean']:.1f} pp | [{100*ci[0]:.1f}, {100*ci[1]:.1f}] pp |")
    else:
        lines.append("Astra ainda não completou 30 trajetórias; nenhuma diferença pareada foi calculada.")
    lines.extend(["", "## Custo e procedência", "",
                  f"Astra usa tarifa Standard da [página oficial](https://developers.openai.com/api/docs/models/gpt-6-astra): entrada US$10/M, cache lido US$1/M, cache escrito US$12,50/M e saída US$50/M. Trata-se de proxy hipotético de API, não cobrança da assinatura. Raciocínio é subconjunto da saída e cache lido da entrada; chamadas acima de 272 mil tokens são excluídas do proxy curto com motivo no JSON.",
                  f"Astra: {report['models'][MODEL]['computed_cost_proxy']['evaluable_runs']}/{report['astra_observed_trajectories']} runs com proxy calculável. O custo de tentativas com erro contém apenas uso conhecido do prefixo; a chamada final falha pode ter uso não reportado. Erros Astra preservados: {report['astra_operational_errors']['attempt_count']}.",
                  f"Base anterior verificada byte a byte por métricas de oito modelos contra `{report['baseline_source']['path']}` (SHA-256 `{report['baseline_source']['sha256']}`). Manifest Astra `{report['astra_manifest']['path']}` (SHA-256 `{report['astra_manifest']['sha256']}`). Scorer e regras diagnósticas não mudaram.",
                  "A identidade Astra foi solicitada e a inferência aceita, mas a CLI de assinatura não expõe slug servido. Esforço high é solicitado. Diferenças incluem transporte e data; não demonstram efeito isolado dos pesos do modelo. Assinatura compartilha cota com outras tarefas e não há conversão verificável quota↔tokens/custo proxy.",
                  "Revisão médica permanece pendente para segurança, tratamentos, ações desnecessárias e alternativas aceitáveis. Não há score clínico composto nem comparação direta numérica com MIRA.", ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--partial", action="store_true", help="Write separate partial Astra filenames during active runs")
    args = parser.parse_args()
    report = analyze(allow_incomplete=args.partial)
    OUT.mkdir(parents=True, exist_ok=True)
    json_name = "partial_astra_comparative_analysis.json" if args.partial else "astra_comparative_analysis.json"
    md_name = "PARTIAL_ASTRA_COMPARATIVE_REPORT.md" if args.partial else "ASTRA_COMPARATIVE_REPORT.md"
    (OUT / json_name).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / md_name).write_text(markdown(report), encoding="utf-8")
    print(f"Astra addon analyzed {report['astra_observed_trajectories']}/30, combined {report['observed_terminal_trajectories']}/270 planned; {report['panel_state']}")


if __name__ == "__main__":
    main()
