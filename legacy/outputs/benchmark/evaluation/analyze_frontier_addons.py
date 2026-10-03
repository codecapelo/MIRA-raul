"""Compare the preserved 230-run panel with one or two frozen frontier addons.

The first addon is Astra. A second addon is accepted only by explicit path to
its own frozen manifest. This code never starts inference or edits prior output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from .analyze_astra_addon import (
    ROOT, MODEL as ASTRA, MANIFEST as ASTRA_MANIFEST, RESULTS as ASTRA_RESULTS,
    _astra_errors, _check_index, _contract, _load_index, _score_astra,
    load_addon_rows,
)
from .analyze_extension import EXPECTED_CASES, EXPECTED_MODELS, _case_mean, _interval, _sha
from .metrics import score_run
from .validate import load_json, read_trace, validate_trace

OUT = ROOT / "results" / "frontier_addons_2026-09-29" / "summaries"


def verify_optional_manifest(path: Path) -> tuple[dict, str, Path]:
    path = path.resolve()
    if path.parent != (ROOT / "docs").resolve() or path == ASTRA_MANIFEST.resolve():
        raise ValueError("Additional frozen manifest must be a distinct file in benchmark/docs")
    manifest = load_json(path)
    base = load_json(ROOT / "docs" / "protocol_freeze_manifest.json")
    corpus = load_json(ROOT / "docs" / "corpus_freeze_manifest.json")
    models = manifest.get("models", {})
    if not isinstance(models, dict) or len(models) != 1:
        raise ValueError("Second addon manifest must contain exactly one model")
    model = next(iter(models))
    if (model in {*EXPECTED_MODELS, ASTRA}
            or manifest.get("base_protocol_version") != base["protocol_version"]
            or manifest.get("base_protocol_manifest_sha256") != _sha(ROOT / "docs" / "protocol_freeze_manifest.json")
            or manifest.get("corpus_version") != corpus["corpus_version"]
            or manifest.get("case_order") != EXPECTED_CASES or manifest.get("repetitions") != 3
            or not isinstance(manifest.get("extension_version"), str)
            or manifest["extension_version"] == load_json(ASTRA_MANIFEST)["extension_version"]):
        raise ValueError("Second addon is not a distinct freeze of the same clinical protocol")
    for key in ("max_actions", "max_model_turns", "max_wall_seconds", "repeated_unproductive_call_limit"):
        if manifest.get(key) != base[key]:
            raise ValueError(f"Second addon stopping limit differs: {key}")
    definition = models[model]
    directory = manifest.get("results_directory")
    directory_parts = Path(directory).parts if isinstance(directory, str) else ()
    progress = definition.get("progress_path")
    if (len(directory_parts) != 2 or directory_parts[0] != "results" or not directory_parts[1].startswith("extension_")
            or directory in {"results/extension_2026-09-28", "results/extension_terra_2026-09-28", str(ASTRA_RESULTS.relative_to(ROOT))}
            or definition.get("provider") != "openai" or definition.get("effort") != "high"
            or definition.get("model_observed", "non-null") is not None
            or not isinstance(progress, str)
            or Path(progress).parent != Path(directory) / "summaries"
            or not Path(progress).name.endswith("_progress.jsonl")):
        raise ValueError("Second addon provider, observed identity, or results directory invalid")
    results = ROOT / directory
    if not isinstance(manifest.get("files"), list) or not manifest["files"]:
        raise ValueError("Second addon frozen runtime files missing")
    frozen_paths = {item.get("path") for item in manifest["files"]}
    if definition.get("adapter") not in frozen_paths:
        raise ValueError("Second addon adapter is not included in its freeze")
    for item in manifest["files"]:
        source = ROOT / item["path"]
        if not source.is_file() or _sha(source) != item["sha256"]:
            raise ValueError(f"Second addon frozen file changed: {item['path']}")
    wrapper = manifest.get("diagnostic_wrapper", {})
    if wrapper:
        source = ROOT / wrapper["path"]
        if not source.is_file() or _sha(source) != wrapper["sha256"]:
            raise ValueError("Second addon diagnostic wrapper changed")
    pricing = manifest.get("pricing", {}).get(model, {})
    if pricing:
        fields = ("input_per_million", "cached_input_per_million", "cache_write_input_per_million", "output_per_million")
        if (pricing.get("verified") is not True or not str(pricing.get("source_url", "")).startswith("https://developers.openai.com/")
                or not all(isinstance(pricing.get(key), (int, float)) and pricing[key] >= 0 for key in fields)
                or pricing.get("input_includes_cached") is not True or pricing.get("output_includes_reasoning") is not True):
            raise ValueError("Second addon tariff declared without verifiable source/token semantics")
    if model == "gpt-6.1-sol":
        expected = {"source_url": "https://developers.openai.com/api/docs/models/gpt-6.1-sol",
                    "input_per_million": 2.0, "cached_input_per_million": 0.1,
                    "cache_write_input_per_million": 2.5, "output_per_million": 10.0,
                    "long_context_threshold": 272000}
        if pricing.get("verified") is not True or any(pricing.get(key) != value for key, value in expected.items()):
            raise ValueError("GPT-6.1 Sol frozen tariff differs from its official model page")
    return manifest, model, results


def load_optional_rows(manifest: dict, model: str, results: Path, *, allow_incomplete: bool) -> list[dict]:
    index = _load_index(manifest, model)
    if not index and not allow_incomplete:
        raise ValueError(f"No progress index for second addon {model}")
    rows = []
    for path in sorted((results / "raw").glob("*.jsonl")):
        events = read_trace(path)
        if not events or events[-1].get("event_type") != "run_ended":
            if allow_incomplete:
                continue
            raise ValueError(f"Nonterminal second-addon raw trace: {path.name}")
        valid = validate_trace(events)
        if not valid["valid"]:
            raise ValueError(f"Invalid second-addon trace: {path.name}: {valid['errors']}")
        first, end = events[0], events[-1]
        if first.get("case_id") not in EXPECTED_CASES or first.get("manifest", {}).get("repetition") not in (1, 2, 3):
            raise ValueError(f"Second addon case/repetition outside design: {path.name}")
        entry = index.get(first.get("run_id"))
        if entry is None:
            if allow_incomplete:
                continue
            raise ValueError(f"Second-addon trace missing index: {path.name}")
        _check_index(entry, events, path, manifest, model)
        _contract(events, manifest)
        if end.get("stopping_reason") == "provider_or_runner_error":
            raise ValueError(f"Second-addon provider error remained in raw/: {path.name}")
        responses = [item for item in events if item.get("event_type") == "model_response"]
        if not responses:
            raise ValueError(f"Second-addon trace has no response: {path.name}")
        for response in responses:
            metadata = response.get("provider_metadata", {})
            if (metadata.get("model_requested") != model or metadata.get("effort_requested") != "high"
                    or metadata.get("models_reported") not in (None, [])):
                raise ValueError(f"Second-addon requested model/effort mismatch: {path.name}")
        case = ROOT / "cases" / first["case_id"]
        row = score_run(events, load_json(case / "ground_truth.json"), load_json(case / "rubric.json"))
        row.update({"repetition": first["manifest"]["repetition"], "arm_origin": manifest["extension_version"],
                    "trace_path": str(path.relative_to(ROOT)), "identity_evidence": "requested_and_inference_accepted_not_observed",
                    "cost_usage_events": [item.get("payload", {}) for item in events if item.get("event_type") == "usage"],
                    "cost_response_count": len(responses)})
        rows.append(row)
    if len(rows) > 30:
        raise ValueError("More than 30 second-addon terminals")
    return rows


def analyze(*, additional_manifest: Path | None = None, allow_incomplete: bool = False) -> tuple[dict, list[dict]]:
    prior_rows, astra_rows, astra_manifest, archived = load_addon_rows(allow_incomplete=allow_incomplete)
    addons: dict[str, tuple[list[dict], dict, Path, Path]] = {
        ASTRA: (astra_rows, astra_manifest, ASTRA_RESULTS, ASTRA_MANIFEST)}
    if additional_manifest is not None:
        manifest, model, results = verify_optional_manifest(additional_manifest)
        addons[model] = (load_optional_rows(manifest, model, results, allow_incomplete=allow_incomplete),
                         manifest, results, additional_manifest.resolve())
    all_rows = prior_rows + [row for items, _, _, _ in addons.values() for row in items]
    run_ids = [item["run_id"] for item in all_rows]
    keys = [(item["model_id"], item["case_id"], item["repetition"]) for item in all_rows]
    if len(run_ids) != len(set(run_ids)) or len(keys) != len(set(keys)):
        raise ValueError("Duplicate run ID or model/case/repetition in combined addon panel")
    if not allow_incomplete and any(len(items) != 30 for items, _, _, _ in addons.values()):
        raise ValueError("Final addon analysis requires 30 terminals for each new arm")
    model_entries = {model: archived["models"][model] for model in EXPECTED_MODELS}
    for model, (items, manifest, _, _) in addons.items():
        entry = _score_astra(items, manifest, model)
        if not allow_incomplete and not entry["complete_panel"]:
            raise ValueError(f"Final addon analysis requires 10 cases x 3 for {model}")
        model_entries[model] = entry
    result = {"schema_version": "1.0.0", "analysis_version": "frontier-addons-2026-09-29-v1",
              "corpus_version": archived["corpus_version"], "protocol_version": archived["protocol_version"],
              "evaluation": {"version": "evaluation-v2", "scorer_sha256": archived["evaluation"]["scorer_sha256"],
                             "diagnosis_ruleset_version": archived["evaluation"]["diagnosis_ruleset_version"],
                             "diagnosis_ruleset_sha256": archived["evaluation"]["diagnosis_ruleset_sha256"],
                             "analyzer_sha256": _sha(Path(__file__))},
              "expected_trajectories": 230 + 30*len(addons) + 10,
              "observed_terminal_trajectories": len(all_rows), "luna_observed_trajectories": 20,
              "luna_planned_trajectories": 30,
              "preserved_baseline": {"path": str((ROOT / "results/extension_2026-09-28/summaries/partial_combined_analysis.json").relative_to(ROOT)),
                                     "sha256": _sha(ROOT / "results/extension_2026-09-28/summaries/partial_combined_analysis.json"),
                                     "all_eight_model_fields_equal": True, "terminal_count": 230},
              "addon_manifests": [{"model_id": model, "path": str(path.relative_to(ROOT)), "sha256": _sha(path),
                                   "observed_terminal_runs": len(items), "expected_terminal_runs": 30,
                                   "cli_version": manifest["models"][model].get("cli_version"),
                                   "cli_path": manifest["models"][model].get("cli_path"),
                                   "high_access_verified": manifest["models"][model].get("access_verified_high",
                                                                                         manifest["models"][model].get("access_verified")),
                                   "identity_evidence": "requested_and_inference_accepted_not_observed"}
                                  for model, (items, manifest, _, path) in addons.items()],
              "models": model_entries, "paired_differences": {},
              "addon_operational_errors": {model: _astra_errors(manifest, _load_index(manifest, model), set(run_ids), model, results)
                                           for model, (_, manifest, results, _) in addons.items()},
              "physician_review_state": "pending",
              "interpretation": "Exploratory public-case lexical and process measures; not physician-adjudicated accuracy or safety. Luna stays 20/30 without imputation. Each addon includes model plus subscription CLI transport and date."}
    complete_models = [model for model in model_entries if model != "gpt-6-luna" and model_entries[model]["complete_panel"]]
    grouped: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for row in all_rows:
        grouped[row["model_id"]][row["case_id"]].append(row)
    if all(model_entries[model]["complete_panel"] for model in addons):
        for field in ("completed", "benchmark_target_concept_match"):
            for model in addons:
                for comparator in complete_models:
                    if comparator == model or (comparator in addons and list(addons).index(comparator) >= list(addons).index(model)):
                        continue
                    differences = [_case_mean(grouped[model][case], field) - _case_mean(grouped[comparator][case], field)
                                   for case in EXPECTED_CASES]
                    result["paired_differences"][f"{field}: {model} minus {comparator}"] = {
                        "mean": sum(differences)/10, "case_cluster_bootstrap_95": _interval(differences),
                        "case_differences": differences, "provisional": field != "completed",
                        "scope": "New complete addon compared with complete 30-run arm; Luna excluded"}
    result["panel_state"] = ("addons_complete_prior_luna_partial" if all(model_entries[model]["complete_panel"] for model in addons)
                             else "addons_partial_prior_luna_partial")
    return result, [row for model in addons for row in addons[model][0]]


def markdown(report: dict) -> str:
    models = list(report["models"])
    def pct(value: float | None) -> str:
        return "—" if value is None else f"{100*value:.1f}%"
    def cost(value: float | None) -> str:
        return "—" if value is None else f"{value:.6f}"
    observed_addons = sum(item["observed_terminal_runs"] for item in report["addon_manifests"])
    lines = ["# Modelos de fronteira adicionais — comparação exploratória", "",
             f"Painel preservado: **230** terminais. Novos braços: **{observed_addons}/{30*len(report['addon_manifests'])}** terminais. Total: **{report['observed_terminal_trajectories']}/{report['expected_trajectories']}** planejadas; Luna anterior permanece **20/30**.", "",
             "| Modelo | Terminais | Conclusão entre terminais | Alvo, média por caso | Alvo bruto observado | CLI equivalente USD | Proxy API USD |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for model in models:
        entry = report["models"][model]
        n = entry["observed_runs"]
        completion = sum(c["completed"] for c in entry["cases"].values()) / n if n else None
        reported = entry["process"]["reported_cost_equivalent_usd"] if model in {"claude-opus-5-5", "claude-sonnet-5-5"} else None
        proxy = entry.get("computed_cost_proxy", {}).get("computed_api_equivalent_usd")
        lines.append(f"| {model} | {n}/30 | {pct(completion)} | {pct(entry['metrics']['benchmark_target_concept_match']['case_mean'])} | {pct(entry['observed_run_target_rate'])} | {cost(reported)} | {cost(proxy)} |")
    lines.extend(["", "As células Luna faltantes não são imputadas. Os matches são triagem lexical determinística, não acurácia clínica adjudicada. Custos API são proxies hipotéticos separados de estimativas CLI e da cobrança desconhecida da assinatura. Não somar raciocínio à saída novamente. Os casos públicos podem ter contaminado treino.", "",
                  "## Casos", "", "Célula = match do alvo/runs terminais observadas; `—` = ausência, sem imputação.", "",
                  "| Caso | " + " | ".join(models) + " |", "|---|" + "---:|"*len(models)])
    for case in EXPECTED_CASES:
        cells = []
        for model in models:
            item = report["models"][model]["cases"][case]
            cells.append(f"{item['concept_matches']}/{item['runs']}" if item["runs"] else "—")
        lines.append("| " + case + " | " + " | ".join(cells) + " |")
    lines.extend(["", "## Diferenças pareadas exploratórias", "",
                  "Só após cada novo braço completar 10 casos × 3. Comparadores também precisam estar completos; Luna parcial é excluído. Bootstrap descritivo por caso (10 mil reamostragens), sem ajuste de multiplicidade.", ""])
    if report["paired_differences"]:
        lines.extend(["| Comparação | Diferença média | IC bootstrap 95% |", "|---|---:|---:|"])
        for label, item in report["paired_differences"].items():
            ci = item["case_cluster_bootstrap_95"]
            lines.append(f"| {label} | {100*item['mean']:.1f} pp | [{100*ci[0]:.1f}, {100*ci[1]:.1f}] pp |")
    else:
        lines.append("Nenhum conjunto pareado de novos braços foi completado; nenhuma inferência pareada foi gerada.")
    lines.extend(["", "## Proveniência e limites", "",
                  f"O JSON anterior de 230 terminais teve todos os campos dos oito modelos conferidos: SHA-256 `{report['preserved_baseline']['sha256']}`. Scorer e regras diagnósticas continuam evaluation-v2."])
    for source in report["addon_manifests"]:
        model = source["model_id"]
        entry = report["models"][model]
        proxy = entry["computed_cost_proxy"]
        rate = proxy.get("pricing", {})
        lines.append(f"- `{model}`: manifest `{source['path']}` SHA-256 `{source['sha256']}`; {source['observed_terminal_runs']}/30 terminais; CLI declarada `{source['cli_version'] or 'desconhecida'}`; acesso high verificado no manifest: `{source['high_access_verified']}`; proxy API {cost(proxy.get('computed_api_equivalent_usd'))} USD em {proxy['evaluable_runs']} runs. Fonte tarifária: {rate.get('source_url') or 'indisponível'}. Erros operacionais preservados: {report['addon_operational_errors'][model]['attempt_count']}.")
    lines.extend(["", "A identidade servida pelos CLIs Codex de assinatura não é exposta; apenas modelo solicitado e inferência aceita são registrados. Esforço high é pedido. Comparações incluem transporte e data, não isolam pesos do modelo. Custo de prefixos com erro é apenas o uso conhecido; última chamada pode não ter reportado tokens. Cota da assinatura é compartilhada e não há fórmula verificável de conversão para tokens/proxy de API. Revisão médica de diagnóstico, conduta e segurança está pendente; nenhum LLM é juiz único de segurança.", ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--additional-manifest", type=Path, help="Optional second frozen addon manifest in docs/")
    parser.add_argument("--partial", action="store_true", help="Export separate partial files while an addon is running")
    args = parser.parse_args()
    report, _ = analyze(additional_manifest=args.additional_manifest, allow_incomplete=args.partial)
    OUT.mkdir(parents=True, exist_ok=True)
    stem = "partial_frontier_addons" if args.partial else "frontier_addons"
    (OUT / f"{stem}_analysis.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / ("PARTIAL_FRONTIER_ADDONS_REPORT.md" if args.partial else "FRONTIER_ADDONS_REPORT.md")).write_text(markdown(report), encoding="utf-8")
    print(f"Analyzed {report['observed_terminal_trajectories']}/{report['expected_trajectories']} planned; {report['panel_state']}")


if __name__ == "__main__":
    main()
