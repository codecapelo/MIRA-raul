"""Exploratory, case-clustered analysis of terminal v3 trajectories.

Run only after all three schedulers have stopped. No clinical safety judgment is
made by this script; published-diagnosis concept matches are lexical screens.
"""

from __future__ import annotations

import json
import hashlib
import random
import statistics
from collections import defaultdict
from pathlib import Path

from .metrics import score_run
from .validate import load_json, read_trace, validate_trace

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_CASES = [f"case_{i:03d}" for i in range(1, 11)]
EXPECTED_MODELS = ["qwen3.5:9b-mlx", "qwen3:8b", "llama3.1:8b", "gpt-6-sol", "claude-opus-5-5"]
BINARY_FIELDS = (
    "completed", "published_diagnosis_exact_match",
    "published_diagnosis_concept_match", "published_diagnosis_top3_concept",
    "benchmark_target_concept_match", "benchmark_target_top3_concept",
    "disposition_published_exact_match",
)


def _interval(values: list[float], draws: int = 10000, seed: int = 20260925) -> list[float]:
    rng = random.Random(seed)
    n = len(values)
    samples = sorted(sum(values[rng.randrange(n)] for _ in range(n)) / n for _ in range(draws))
    return [samples[int(.025 * (draws - 1))], samples[int(.975 * (draws - 1))]]


def _case_mean(rows: list[dict], field: str) -> float | None:
    values = [float(row[field]) for row in rows if row.get(field) is not None]
    return sum(values) / len(values) if values else None


def load_rows(*, allow_incomplete: bool = False) -> list[dict]:
    rows = []
    expected_protocol = load_json(ROOT / "docs" / "protocol_freeze_manifest.json")
    expected_corpus = load_json(ROOT / "docs" / "corpus_freeze_manifest.json")
    packet_hashes = {item["path"].split("/")[1]: item["sha256"] for item in expected_corpus["files"]
                     if item["path"].endswith("/case_packet.json")}
    prompt_hash = next(item["sha256"] for item in expected_protocol["files"]
                       if item["path"] == "prompts/physician_agent.md")
    index: dict[str, dict] = {}
    for index_path in (ROOT / "results" / "local_run_index.jsonl",
                       ROOT / "results" / "summaries" / "openai_progress.jsonl",
                       ROOT / "results" / "summaries" / "anthropic_progress.jsonl"):
        for line in index_path.read_text().splitlines():
            entry = json.loads(line)
            run_id = entry["run_id"]
            if run_id in index:
                raise ValueError(f"Duplicate run ID in progress indices: {run_id}")
            index[run_id] = entry
    for path in sorted((ROOT / "results" / "raw").glob("*.jsonl")):
        events = read_trace(path)
        if not events or events[-1].get("event_type") != "run_ended":
            if allow_incomplete:
                continue
            raise ValueError(f"Nonterminal trace in primary panel: {path.name}")
        check = validate_trace(events)
        if not check["valid"]:
            raise ValueError(f"Invalid trace {path.name}: {check['errors']}")
        manifest = events[0]["manifest"]
        case_id = events[0]["case_id"]
        indexed = index.get(events[0]["run_id"])
        if (manifest.get("case_packet_sha256") != packet_hashes.get(case_id)
                or manifest.get("prompt_sha256") != prompt_hash
                or not indexed
                or indexed.get("corpus_version") != expected_corpus["corpus_version"]
                or indexed.get("protocol_version") != expected_protocol["protocol_version"]
                or indexed.get("case_id") != case_id
                or indexed.get("model_id") != events[0]["model_id"]
                or indexed.get("repetition") != manifest.get("repetition")):
            raise ValueError(f"Trace {path.name} uses a different corpus or protocol freeze")
        if events[-1].get("stopping_reason") == "provider_or_runner_error":
            raise ValueError(f"Provider-error attempt must be archived before analysis: {path.name}")
        case_dir = ROOT / "cases" / case_id
        row = score_run(events, load_json(case_dir / "ground_truth.json"),
                        load_json(case_dir / "rubric.json"))
        row["repetition"] = events[0]["manifest"]["repetition"]
        rows.append(row)
    return rows


def analyze(rows: list[dict]) -> dict:
    by_model_case: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    seen: set[tuple[str, str, int]] = set()
    for row in rows:
        key = (row["model_id"], row["case_id"], row["repetition"])
        if row["model_id"] not in EXPECTED_MODELS or row["case_id"] not in EXPECTED_CASES or row["repetition"] not in (1, 2, 3):
            raise ValueError(f"Unexpected model/case/repetition: {key}")
        if key in seen:
            raise ValueError(f"Duplicate trajectory for model/case/repetition: {key}")
        seen.add(key)
        by_model_case[row["model_id"]][row["case_id"]].append(row)
    ruleset_path = ROOT / "evaluation" / "diagnosis_aliases.json"
    result = {"schema_version": "1.0.0", "corpus_version": load_json(ROOT / "docs" / "corpus_freeze_manifest.json")["corpus_version"],
              "protocol_version": load_json(ROOT / "docs" / "protocol_freeze_manifest.json")["protocol_version"],
              "evaluation": {"version": "evaluation-v2",
                             "diagnosis_ruleset_version": load_json(ruleset_path)["ruleset_version"],
                             "diagnosis_ruleset_sha256": hashlib.sha256(ruleset_path.read_bytes()).hexdigest(),
                             "scorer_sha256": hashlib.sha256((ROOT / "evaluation" / "metrics.py").read_bytes()).hexdigest(),
                             "analyzer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
              "expected_trajectories": 150, "observed_terminal_trajectories": len(rows),
              "physician_review_state": "pending", "models": {}, "paired_differences": {},
              "interpretation": "Exploratory public-case lexical and process measures only; no definitive clinical accuracy or safety estimate."}
    for model in EXPECTED_MODELS:
        groups = by_model_case.get(model, {})
        observed = sum(len(group) for group in groups.values())
        complete_panel = all({r["repetition"] for r in groups.get(case_id, [])} == {1, 2, 3}
                             for case_id in EXPECTED_CASES)
        entry = {"observed_runs": observed, "expected_runs": 30, "complete_panel": complete_panel,
                 "cases": {case_id: {"runs": len(groups.get(case_id, [])),
                                     "completed": sum(bool(r["completed"]) for r in groups.get(case_id, [])),
                                     "concept_matches": sum(r["benchmark_target_concept_match"] is True for r in groups.get(case_id, [])),
                                     "tool_calls": [r["tool_calls"] for r in groups.get(case_id, [])],
                                     "stopping_reasons": [r["stopping_reason"] for r in groups.get(case_id, [])]}
                           for case_id in EXPECTED_CASES}, "metrics": {}}
        for field in BINARY_FIELDS:
            case_values = [_case_mean(groups[case_id], field) for case_id in EXPECTED_CASES if groups.get(case_id)]
            case_values = [v for v in case_values if v is not None]
            entry["metrics"][field] = {
                "case_mean": sum(case_values) / len(case_values) if case_values else None,
                "case_cluster_bootstrap_95": _interval(case_values) if complete_panel and len(case_values) == 10 else None,
                "evaluable_cases": len(case_values),
                "provisional": field != "completed",
            }
        entry["total_tool_calls"] = sum(r["tool_calls"] for group in groups.values() for r in group)
        entry["median_run_seconds"] = (statistics.median(r["total_duration_ms"] / 1000
                                                         for group in groups.values() for r in group)
                                        if observed else None)
        model_rows = [r for group in groups.values() for r in group]
        emitted = [r for r in model_rows if r["diagnosis_emitted"]]
        entry["diagnosis_emitted_runs"] = len(emitted)
        entry["target_match_given_diagnosis"] = (
            sum(r["benchmark_target_concept_match"] is True for r in emitted) / len(emitted)
            if emitted else None)
        def mean_field(field: str) -> float | None:
            values = [float(r[field]) for r in model_rows if r.get(field) is not None]
            return sum(values) / len(values) if values else None
        def sum_usage(field: str) -> float | None:
            values = [float(r["usage"][field]) for r in model_rows
                      if r.get("usage", {}).get(field) is not None]
            return sum(values) if values else None
        entry["process"] = {
            "mean_lab_requests": mean_field("lab_requests"),
            "mean_imaging_requests": mean_field("imaging_requests"),
            "mean_procedure_orders": mean_field("procedure_orders"),
            "mean_medication_orders": mean_field("medication_orders"),
            "mean_steps_to_benchmark_diagnosis": mean_field("steps_to_first_benchmark_target"),
            "invalid_tool_calls": sum(r["invalid_tool_calls"] for r in model_rows),
            "failed_tool_calls": sum(r["invalid_or_failed_tool_calls"] for r in model_rows),
            "reported_input_tokens": sum_usage("input_tokens"),
            "reported_cached_input_tokens": sum_usage("cached_input_tokens"),
            "reported_cache_creation_input_tokens": sum_usage("cache_creation_input_tokens"),
            "reported_output_tokens": sum_usage("output_tokens"),
            "reported_reasoning_tokens": sum_usage("reasoning_tokens"),
            "reported_cost_equivalent_usd": sum_usage("cost_estimate_usd"),
            "mean_local_tokens_per_second": mean_field("local_tokens_per_second"),
        }
        result["models"][model] = entry
    if all(result["models"][m]["complete_panel"] for m in EXPECTED_MODELS):
        for field in ("completed", "benchmark_target_concept_match"):
            for i, first in enumerate(EXPECTED_MODELS):
                for second in EXPECTED_MODELS[i + 1:]:
                    differences = []
                    for case_id in EXPECTED_CASES:
                        a = _case_mean(by_model_case[first][case_id], field)
                        b = _case_mean(by_model_case[second][case_id], field)
                        if a is not None and b is not None:
                            differences.append(a - b)
                    if len(differences) == 10:
                        result["paired_differences"][f"{field}: {first} minus {second}"] = {
                            "mean": sum(differences) / 10,
                            "case_cluster_bootstrap_95": _interval(differences),
                            "case_differences": differences,
                            "provisional": field != "completed",
                        }
    return result


def markdown(report: dict) -> str:
    lines = ["# Análise exploratória — painel MIRA-2026", "",
             f"Corpus: `{report['corpus_version']}` · Protocolo: `{report['protocol_version']}`.", "",
             f"Avaliação: `{report['evaluation']['version']}` · Regras diagnósticas: `{report['evaluation']['diagnosis_ruleset_version']}` (SHA-256 `{report['evaluation']['diagnosis_ruleset_sha256']}`).", "",
             f"Trajetórias terminais: **{report['observed_terminal_trajectories']}/150**. Revisão médica: **pendente**.", "",
             "| Modelo | Runs | Conclusão | Alvo do encontro, média por caso | Diagnóstico publicado, média por caso | Top-3 alvo, média por caso | Chamadas | Mediana duração |",
             "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for model in EXPECTED_MODELS:
        m = report["models"][model]
        def pct(field: str) -> str:
            value = m["metrics"][field]["case_mean"]
            ci = m["metrics"][field]["case_cluster_bootstrap_95"]
            if value is None:
                return "—"
            return f"{100 * value:.1f}%" + (f" [{100 * ci[0]:.1f}, {100 * ci[1]:.1f}]" if ci else "")
        duration = m["median_run_seconds"]
        lines.append(f"| {model} | {m['observed_runs']}/30 | {pct('completed')} | {pct('benchmark_target_concept_match')} | {pct('published_diagnosis_concept_match')} | {pct('benchmark_target_top3_concept')} | {m['total_tool_calls']} | {duration:.1f} s |" if duration is not None else f"| {model} | 0/30 | — | — | — | — | 0 | — |")
    lines.extend(["", "Ausência de diagnóstico final **aceito pelo EHR** conta como erro nas três colunas diagnósticas acima. Cada caso recebe o mesmo peso; no painel completo de três runs por caso, a média por caso equivale à proporção das 30 runs. Os valores são triagens lexicais, não acurácia clínica adjudicada.",
                  "", "| Modelo | Diagnósticos aceitos pelo EHR | Match do alvo entre aceitos |", "|---|---:|---:|"])
    for model in EXPECTED_MODELS:
        m = report["models"][model]
        conditional = m["target_match_given_diagnosis"]
        lines.append(f"| {model} | {m['diagnosis_emitted_runs']}/{m['observed_runs']} | {100 * conditional:.1f}% |" if conditional is not None
                     else f"| {model} | 0/{m['observed_runs']} | — |")
    lines.extend(["", "## Triagem lexical por caso", "",
                  "Cada célula mostra `match do alvo/3 (runs concluídas/3)`. Match não equivale à avaliação médica.", "",
                  "| Caso | " + " | ".join(EXPECTED_MODELS) + " |",
                  "|---|" + "---:|" * len(EXPECTED_MODELS)])
    for case_id in EXPECTED_CASES:
        cells = []
        for model in EXPECTED_MODELS:
            case = report["models"][model]["cases"][case_id]
            cells.append(f"{case['concept_matches']}/3 ({case['completed']}/3)")
        lines.append("| " + case_id + " | " + " | ".join(cells) + " |")
    lines.extend(["", "## Uso de ferramentas e recursos", "",
                  "| Modelo | Labs/run | Imagens/run | Procedimentos/run | Medicações/run | Chamadas inválidas | Chamadas falhas | Tokens de saída reportados | Tokens/s local |",
                  "|---|---:|---:|---:|---:|---:|---:|---:|---:|"])
    for model in EXPECTED_MODELS:
        p = report["models"][model]["process"]
        def number(value: float | None, digits: int = 1) -> str:
            return "—" if value is None else f"{value:.{digits}f}"
        lines.append(f"| {model} | {number(p['mean_lab_requests'])} | {number(p['mean_imaging_requests'])} | {number(p['mean_procedure_orders'])} | {number(p['mean_medication_orders'])} | {p['invalid_tool_calls']} | {p['failed_tool_calls']} | {number(p['reported_output_tokens'], 0)} | {number(p['mean_local_tokens_per_second'])} |")
    lines.extend(["", "| Modelo | Input reportado | Cache lido | Cache criado | Raciocínio reportado | Custo equivalente USD |",
                  "|---|---:|---:|---:|---:|---:|"])
    for model in EXPECTED_MODELS:
        p = report["models"][model]["process"]
        lines.append(f"| {model} | {number(p['reported_input_tokens'], 0)} | {number(p['reported_cached_input_tokens'], 0)} | {number(p['reported_cache_creation_input_tokens'], 0)} | {number(p['reported_reasoning_tokens'], 0)} | {number(p['reported_cost_equivalent_usd'], 2)} |")
    lines.extend(["", "As CLIs reportam tokens de entrada/cache com semânticas distintas; não usar as colunas como medida padronizada de eficiência entre fornecedores. Custo do Claude é estimativa equivalente fornecida pela CLI, não cobrança da assinatura. O Sol não fornece custo equivalente e `—` significa indisponível. Recursos locais não incluem energia. A classificação clínica de ações desnecessárias, diretrizes, medicações e segurança permanece pendente."])
    lines.extend(["", "Intervalos entre colchetes: bootstrap descritivo por dez casos (10 mil reamostragens), mostrado somente com 3 runs por caso. O pareamento preserva as três runs dentro de cada caso.",
                  "", "**Limites:** equivalência diagnóstica acima é uma triagem lexical determinística, não acurácia clínica adjudicada. No caso 003, o alvo do encontro é ruptura do reservatório antes da sepse pós-operatória; a coluna publicada mantém o diagnóstico final do relato. Condutas alternativas, segurança, adequação de pedidos e concordância com diretrizes aguardam médico. Casos públicos podem ter contaminado treinamento; a ordem de execução não foi randomizada e os transportes de ferramentas diferem entre Ollama e CLIs de assinatura. No braço Sol, a instrução de não usar arquivos/web e o modo `read-only` não comprovam isolamento estrito das ferramentas internas; ver `docs/safety.md`.",
                  "", "Os traces completos, os gabaritos e os rubrics permitem revisão cega por caso. Não se calculou score composto nem comparação numérica direta com MIRA.", ""])
    return "\n".join(lines)


def main() -> None:
    report = analyze(load_rows())
    out = ROOT / "results" / "summaries"
    out.mkdir(parents=True, exist_ok=True)
    (out / "exploratory_analysis.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    (out / "REPORT.md").write_text(markdown(report))
    print(f"Analyzed {report['observed_terminal_trajectories']}/150 terminal trajectories")


if __name__ == "__main__":
    main()
