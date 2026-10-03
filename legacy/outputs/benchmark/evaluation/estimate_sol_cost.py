"""Post-hoc API-price proxy for subscription-based GPT-6 Sol runs.

This is separate from the frozen clinical evaluator. It reads terminal traces,
never changes them, and adds a clearly labelled cost addendum to REPORT.md.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .validate import read_trace

ROOT = Path(__file__).resolve().parents[1]
PRICING_URL = "https://developers.openai.com/api/docs/models/gpt-6-sol"
RATES_PER_MILLION = {"uncached_input": 2.0, "cached_input": 0.20,
                     "cache_write_input": 2.50, "output": 10.0}
REPORT_MARKER = "\n## Custo estimado do GPT-6 Sol — análise posterior\n"


def calculate() -> dict:
    runs = []
    seen = set()
    for path in sorted((ROOT / "results" / "raw").glob("*.jsonl")):
        events = read_trace(path)
        if not events or events[0].get("model_id") != "gpt-6-sol":
            continue
        if events[-1].get("event_type") != "run_ended" or events[-1].get("stopping_reason") == "provider_or_runner_error":
            raise ValueError(f"Nonterminal or failed Sol trace: {path}")
        key = (events[0]["case_id"], events[0]["manifest"]["repetition"])
        if key in seen:
            raise ValueError(f"Duplicate Sol case/repetition: {key}")
        seen.add(key)
        usage = [e["payload"] for e in events if e.get("event_type") == "usage"]
        if not usage:
            raise ValueError(f"No usage events in {path}")
        runs.append((key, usage))
    if seen != {(f"case_{i:03d}", j) for i in range(1, 11) for j in (1, 2, 3)}:
        raise ValueError("Expected exactly 10 cases x 3 Sol runs")

    all_usage = [u for _, usage in runs for u in usage]
    required = ("input_tokens", "cached_input_tokens", "output_tokens")
    if any(any(not isinstance(u.get(k), int) for k in required) for u in all_usage):
        raise ValueError("Missing integer token count")
    if any(u["cached_input_tokens"] > u["input_tokens"] for u in all_usage):
        raise ValueError("Cached input cannot exceed total input")
    maximum_call_input = max(u["input_tokens"] for u in all_usage)
    if maximum_call_input > 272000:
        raise ValueError("Long-context price tier requires a different calculation")
    input_total = sum(u["input_tokens"] for u in all_usage)
    cached = sum(u["cached_input_tokens"] for u in all_usage)
    output = sum(u["output_tokens"] for u in all_usage)
    reasoning = sum(u.get("reasoning_output_tokens", 0) for u in all_usage)
    uncached = input_total - cached
    reported_writes = sum(u.get("cache_write_input_tokens", 0) for u in all_usage)
    if reasoning > output:
        raise ValueError("Reasoning tokens already included in output")
    if reported_writes > uncached:
        raise ValueError("Cache writes exceed noncached input")

    def price(cache_writes: int) -> float:
        return (((uncached - cache_writes) * RATES_PER_MILLION["uncached_input"]
                 + cached * RATES_PER_MILLION["cached_input"]
                 + cache_writes * RATES_PER_MILLION["cache_write_input"]
                 + output * RATES_PER_MILLION["output"]) / 1_000_000)

    return {
        "schema_version": "1.0.0",
        "type": "post_hoc_api_equivalent_not_subscription_charge",
        "model_id": "gpt-6-sol", "effort": "high", "run_count": len(runs),
        "usage_event_count": len(all_usage), "input_tokens_including_cached": input_total,
        "cached_input_tokens": cached, "uncached_input_tokens": uncached,
        "output_tokens_including_reasoning": output, "reasoning_output_tokens_subset": reasoning,
        "cache_write_input_tokens_reported": reported_writes,
        "maximum_input_tokens_per_call": maximum_call_input,
        "pricing_usd_per_million_tokens": RATES_PER_MILLION,
        "api_equivalent_using_reported_cache_writes_usd": price(reported_writes),
        "api_equivalent_sensitivity_all_uncached_as_cache_writes_usd": price(uncached),
        "actual_subscription_charge_usd": None,
        "pricing_url": PRICING_URL, "pricing_checked_date": "2026-09-26",
        "limitations": [
            "Codex CLI used a ChatGPT subscription, not OpenAI API billing.",
            "A direct Responses API adapter may have different context and cache usage.",
            "The CLI reports zero cache-write tokens; the upper scenario treats every noncached input token as a cache write.",
            "Reasoning tokens are a subset of output and are not charged twice.",
        ],
    }


def markdown(data: dict) -> str:
    base = data["api_equivalent_using_reported_cache_writes_usd"]
    high = data["api_equivalent_sensitivity_all_uncached_as_cache_writes_usd"]
    return f"""# Estimativa de custo do GPT-6 Sol high

Análise posterior aos {data['run_count']} runs completos do corpus congelado. Os traces foram executados pelo Codex CLI autenticado pela assinatura ChatGPT; **o valor abaixo não é cobrança observada**. O custo efetivo atribuível ao benchmark na assinatura não é mensurável pelos traces e não deve ser apresentado como US$ 0.

| Medida | Valor |
|---|---:|
| Eventos de uso | {data['usage_event_count']} |
| Entrada total, incluindo cache | {data['input_tokens_including_cached']:,} |
| Entrada lida do cache, subconjunto da anterior | {data['cached_input_tokens']:,} |
| Entrada não cacheada | {data['uncached_input_tokens']:,} |
| Saída total, incluindo raciocínio | {data['output_tokens_including_reasoning']:,} |
| Raciocínio, subconjunto da saída | {data['reasoning_output_tokens_subset']:,} |
| Maior entrada por chamada | {data['maximum_input_tokens_per_call']:,} |
| **Equivalente hipotético API Standard** | **US$ {base:.2f}** |
| Sensibilidade: toda entrada não cacheada cobrada como gravação de cache | US$ {high:.2f} |
| Média equivalente por run | US$ {base / data['run_count']:.3f} |
| Cobrança real da assinatura | Não disponível |

Tarifas da [página oficial do GPT-6 Sol]({PRICING_URL}), consultadas em 26-09-2026: US$ 2,00/milhão de tokens de entrada comum, US$ 0,20/milhão lidos do cache, US$ 2,50/milhão de gravação de cache, US$ 10,00/milhão de saída. Todas as chamadas ficaram abaixo de 272 mil tokens de entrada, portanto foi usada a faixa curta Standard. `high` não recebe multiplicador separado: o esforço de raciocínio aparece no volume de tokens de saída.

Fórmula da estimativa principal: `({data['uncached_input_tokens']:,} × 2 + {data['cached_input_tokens']:,} × 0,20 + {data['output_tokens_including_reasoning']:,} × 10) / 1.000.000 = US$ {base:.4f}`. Os eventos reportaram {data['cache_write_input_tokens_reported']} tokens de gravação; a faixa de sensibilidade até US$ {high:.2f} cobre a hipótese de esses tokens terem sido classificados como entrada comum no transporte por assinatura. Não somamos os tokens de raciocínio novamente, pois já integram a saída.

O histórico foi reempacotado a cada ação EHR pelo Codex CLI. Assim, uma implementação nativa pela API pode consumir tokens e cache diferentes. O custo do Claude no relatório é estimativa fornecida pela própria CLI, calculada por outra contabilização; os dois valores não são uma comparação econômica controlada. [Assinatura Codex e cobrança API são separadas](https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex).
"""


def main() -> None:
    data = calculate()
    out = ROOT / "results" / "summaries"
    (out / "SOL_COST.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    (out / "SOL_COST.md").write_text(markdown(data))
    report_path = out / "REPORT.md"
    report = report_path.read_text()
    report = report.split(REPORT_MARKER, 1)[0].rstrip() + "\n"
    rows = report.splitlines()
    for i, row in enumerate(rows):
        if row.startswith("| gpt-6-sol |") and str(data["input_tokens_including_cached"]) in row:
            rows[i] = re.sub(r"\| — \|$", f"| {data['api_equivalent_using_reported_cache_writes_usd']:.2f}* |", row)
            break
    else:
        raise ValueError("Sol cost row not found in generated report")
    report = "\n".join(rows).replace(
        "O Sol não fornece custo equivalente e `—` significa indisponível.",
        "O Sol não reporta custo; `4.66*` é proxy API Standard calculada dos tokens, não cobrança da assinatura.",
    ).rstrip()
    report += REPORT_MARKER + "\n" + (
        f"**US$ {data['api_equivalent_using_reported_cache_writes_usd']:.2f}** para 30 runs "
        f"(sensibilidade **US$ {data['api_equivalent_using_reported_cache_writes_usd']:.2f}–{data['api_equivalent_sensitivity_all_uncached_as_cache_writes_usd']:.2f}**; "
        "cobrança real pela assinatura: indisponível). Fórmula, tarifas oficiais e limites em "
        "[SOL_COST.md](SOL_COST.md).\n"
    )
    report_path.write_text(report)
    print(f"Sol API equivalent: USD {data['api_equivalent_using_reported_cache_writes_usd']:.4f} for {data['run_count']} runs")


if __name__ == "__main__":
    main()
