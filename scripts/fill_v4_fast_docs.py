"""Render final fast4 documentation from verified aggregate reports only.

No inference or ledger mutations. Default: preview outside the repository.
Copy this script beside templates_v4_fast_docs, or supply --templates.
"""
import argparse
import json
import re
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

START = '<!-- V4_FAST4_FINAL_START -->'
END = '<!-- V4_FAST4_FINAL_END -->'


def fmt(value):
    if value is None:
        raise ValueError('A final metric is absent; refusing to fabricate it')
    return f'{float(value):,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')


def billing_description(bill):
    """Separate observed usage/metadata from account-attributed rejection cost."""
    calls = int(bill['calls'])
    received = int(bill['responded_calls_with_usage'])
    rejected = int(bill['zero_cost_rejections_without_usage'])
    metadata = int(bill['generation_metadata_present'])
    matched = int(bill['generation_cost_matches'])
    mismatched = int(bill['generation_cost_mismatches'])
    missing = len(bill['missing_generation_ids'])
    records = bill['rejected_calls']
    if calls != received + rejected or int(bill['settled_calls']) != calls:
        raise ValueError('Incomplete or inconsistent billing call counts')
    if rejected != len(records):
        raise ValueError('Missing rejection attribution records')
    for record in records:
        if (Decimal(str(record['attributed_cost_usd'])) != 0
                or record['provider_usage_cost_received'] is not False
                or not record.get('evidence_sha256')):
            raise ValueError('Rejection requires explicit zero-cost account evidence')
    if metadata != matched + mismatched or metadata + missing != received:
        raise ValueError('Metadata counts do not cover the observed usage responses')
    if (mismatched or missing or not bill['account_reconciled']
            or Decimal(str(bill['difference_ledger_minus_account_usd'])) != 0):
        raise ValueError('Financial reconciliation is not final and exact')
    status = ('conta e ledger conciliados; custos das respostas com usage.cost '
              'confirmados pelos metadados de geração')
    if rejected:
        status += f'; {rejected} '+('rejeição sem usage.cost atribuída' if rejected==1 else 'rejeições sem usage.cost atribuídas')+' a zero por evidência de conta'
    counts = (f'{metadata} metadados recebidos para {received} respostas com usage.cost; '
              f'{matched} custos de geração coincidentes; {rejected} '+('rejeição' if rejected==1 else 'rejeições')+' '
              f'sem usage.cost com zero atribuído; {missing} IDs de geração ausentes')
    return status, counts


def current_readme(original, block):
    # Remove the obsolete top-level status only, retaining historical checkpoints.
    original = re.sub(r'^> \*\*Checkpoint da otimização rápida[^\n]*(?:\n>[^\n]*)*\n(?:\n)?',
                      '', original, flags=re.M)
    pattern = r'<!-- V4_CURRENT_START -->[\s\S]*?<!-- V4_CURRENT_END -->'
    if len(re.findall(pattern, original)) != 1:
        raise ValueError('README needs exactly one V4_CURRENT block')
    return re.sub(pattern, lambda _: '<!-- V4_CURRENT_START -->\n' + block
                  + '\n<!-- V4_CURRENT_END -->', original, count=1)


def add_block(original, block, prepend=False):
    wrapped = START + '\n' + block.rstrip() + '\n' + END
    pattern = re.escape(START) + r'[\s\S]*?' + re.escape(END)
    matches = len(re.findall(pattern, original))
    if matches > 1:
        raise ValueError('Duplicate final documentation blocks')
    if matches:
        return re.sub(pattern, lambda _: wrapped, original, count=1)
    if prepend:
        heading, separator, rest = original.partition('\n')
        return heading + separator + '\n' + wrapped + '\n\n' + rest
    return original.rstrip() + '\n\n' + wrapped + '\n'


def final_values(summary, bill, date):
    if (not summary['selected_study_complete']
            or summary['partial_public_only'] or summary['partial_closed_only']
            or summary['clinical_commit'] != 'b3d7d005a324db538b98882f6599cc33f2692eb5'):
        raise ValueError('Require the complete frozen fast4 study')
    if (summary['public']['terminal_count'] != 10
            or summary['closed']['terminal_count'] != 10
            or summary['public']['judge_accepted'] != 10):
        raise ValueError('Require 20 unique terminals and the public 10/10 gate')
    if not (summary['financial']['snapshot_is_final_verified']
            and summary['financial']['exact_match']):
        raise ValueError('Summary financial snapshot is not final')
    status, counts = billing_description(bill)
    if Decimal(str(summary['ledger']['cost_usd'])) != Decimal(str(bill['ledger_usage_cost_usd'])):
        raise ValueError('Summary and billing snapshots disagree')
    if Decimal(str(summary['ledger']['reserved_or_uncertain_upper_bound_usd'])) != 0:
        raise ValueError('Unresolved ledger reservations or uncertain costs')
    values = {}
    for prefix, cohort in [('PUBLIC', summary['public']), ('CLOSED', summary['closed'])]:
        for key, field in [('TERMINALS', 'terminal_count'), ('ACCEPTED', 'judge_accepted'),
                           ('PROPOSAL_ACCEPTED', 'proposal_accepted'), ('PROPOSAL_JUDGED', 'proposal_judged'),
                           ('OPERATIONAL', 'operational_terminals'), ('API_USD', 'openrouter_all_actors_usd'),
                           ('DEPLOY_API_USD', 'deployment_openrouter_usd')]:
            if cohort[field] is None:
                raise ValueError(f'Missing final {prefix}_{key}')
            values[prefix + '_' + key] = str(cohort[field])
        for short, field in [('TTFT', 'first_doctor_content_s'), ('FIRST_FULL', 'first_doctor_completed_s'),
                             ('ACTIVE', 'active_call_union_s'), ('WALL', 'wall_s')]:
            for quantile, key in [('P50', 'median'), ('P95', 'p95')]:
                values[f'{prefix}_{short}_{quantile}_S'] = fmt(cohort[field][key])
        astra = cohort['roles']['fast_review_astra']['latency_s']
        for quantile, key in [('P50', 'median'), ('P95', 'p95')]:
            values[f'{prefix}_ASTRA_{quantile}_S'] = fmt(astra[key])
        cli = cohort['subscription_input_tokens_per_case']
        values[prefix + '_CLI_INPUT_P50_IQR'] = f"{fmt(cli['median'])} / {fmt(cli['q1'])}–{fmt(cli['q3'])} (Q1–Q3)"
        values[prefix + '_CLI_CACHE_INPUT_OUTPUT'] = (
            f"{cohort['subscription_cache_input_tokens_total']} / {cohort['subscription_input_tokens_total']} / "
            f"{int(cohort['subscription_output_tokens_per_case']['sum'])}")
        values[prefix + '_WILSON95'] = '–'.join(fmt(100 * x) + '%' for x in cohort['wilson_95_all_terminals'])
        values[prefix + '_EXAM_UNITS_SOURCES'] = f"{cohort['relative_exam_units']} / {cohort['charged_sources']}"
        values[prefix + '_UNAVAILABLE_DUPLICATES'] = f"{cohort['unavailable_attempts']} / {cohort['duplicate_attempts']}"
    values.update({
        'FINAL_DATE_LOCAL': date,
        'GLOBAL_LEDGER_USD': str(summary['ledger']['cost_usd']),
        'GLOBAL_ACCOUNT_DELTA_USD': str(bill['account_delta_usd']),
        'GLOBAL_BILLING_DIFFERENCE_USD': str(bill['difference_ledger_minus_account_usd']),
        'GLOBAL_CAP_REMAINING_USD': str(summary['ledger']['remaining_cap_conservative_usd']),
        'BILLING_STATUS': status,
        'GENERATION_RECONCILIATION_COUNTS': counts,
        'PENDING_UNCERTAIN_COUNT': '0',
        'ACTOR_COST_REPORT_PATH': '[v4_fast_summary.json](v4_fast_summary.json)',
        'FINAL_FIDELITY_REPORT_PATH': '[piloto público](v4_fast4_fidelity_pilot.md), [oito públicos restantes](v4_fast4_fidelity_remaining_public.md) e [agregado fechado](v4_fast4_closed_fidelity_aggregate.json)',
        'PUBLIC_MANIFEST_PATH': '[v4_fast_public_trace_manifest.json](v4_fast_public_trace_manifest.json)',
        'CLOSED_AGGREGATE_MANIFEST_PATH': 'v4_fast_preregistration_digests.json e v4_fast_public_trace_manifest.json (digests opacos; manifestos integrais preservados localmente)',
        'HISTORICAL_HASH_STATUS': '978/978 arquivos canônicos e 888/888 presentes no worktree sem divergência; 90 arquivos históricos ignorados ausentes no worktree',
        'FINAL_VALIDATION_STATUS': '338 testes aprovados: 321 antes da inferência e 17 verificações offline de consolidação/artifact/documentação; JavaScript validado por Node; ver v4_fast_final_validation.json',
        'PR_URL': 'https://github.com/codecapelo/MIRA-raul/pull/7',
    })
    return values


def closed_fidelity_paragraph(audit):
    if audit['status'] != 'complete_post_terminal_source_audit' or audit['audited_terminal_encounters'] != 10:
        raise ValueError('Closed fidelity aggregate must be terminal and complete')
    patient, exams, source = audit['patient_answers'], audit['exam_results'], audit['source_integrity']
    return (
        f"Auditoria agregada dos fechados: {patient['total_answers']} respostas do paciente; "
        f"{patient['confirmed_answers_with_unreported_negative_assertions']} continham negativos sem fonte e "
        f"{patient['pending_ambiguous_answers']} permaneceram ambíguas. "
        f"{exams['distinct_excerpts_checked']} trechos distintos de exames e "
        f"{source['source_files_verified']} arquivos-fonte foram verificados. "
        f"Divergências de identidade: {source['mismatches']}; candidatos de divergência literal de exames: "
        f"{exams['literal_source_match_review_candidates']}. Estes números refletem o escopo auditado: "
        'não houve adjudicação clínica exaustiva das afirmações narrativas positivas ou do raciocínio médico. '
        'Ausência de divergência literal não demonstra segurança, adequação do manejo ou acurácia clínica. '
        'Nenhum achado da auditoria foi usado para reajustar a condição ou reclassificar resultados.')


def render_documents(base, templates, summary, bill, audit, date):
    values = final_values(summary, bill, date)
    validation = json.loads((base / 'reports/v4_fast_final_validation.json').read_text())
    if (validation['status'] != 'passed' or validation['clinical_pre_inference_tests'] != 321
            or validation['frozen_clinical_commit'] != summary['clinical_commit']
            or validation['clinical_code_changed_after_inference'] is not False
            or validation['javascript_scope_and_replay_checks'] != 'passed'):
        raise ValueError('Final validation report is incomplete or inconsistent')
    values['FINAL_VALIDATION_STATUS'] = (
        f"{validation['release_python_tests']} testes Python aprovados, incluindo 321 antes da inferência; "
        f"{validation['offline_consolidation_artifact_tests']} verificações offline de consolidação/artifact/documentação; "
        'JavaScript validado por Node; ver v4_fast_final_validation.json')
    def fill(text):
        text = re.sub(r'\{\{([A-Z0-9_]+)\}\}', lambda m: values[m[1]], text)
        if '{{' in text:
            raise ValueError('Unfilled template placeholder')
        return text
    def template(name):
        return fill((templates / name).read_text())
    public = summary['public']
    api = Decimal(str(public['openrouter_all_actors_usd']))
    old = Decimal('0.35023969')
    slow = Decimal('0.11515425')
    comparison = (
        f"Comparação descritiva nos dez públicos: Claude v3.6 158,46s / US$0.35023969; "
        f"v4 anterior 515,93s / US$0.11515425; fast4 {fmt(public['active_call_union_s']['median'])}s / US${api}. "
        f"Variação da API: {fmt(100 * (api / old - 1))}% versus v3.6 e "
        f"{fmt(100 * (api / slow - 1))}% versus v4 lenta. Entrada CLI mediana "
        f"{fmt(public['subscription_input_tokens_per_case']['median'])} versus 183.706,5 na v4 lenta "
        'e 34.522,5 na v3.6. Contextos, cache e transportes diferem; os tempos históricos não isolam efeito causal.')
    closed_note = closed_fidelity_paragraph(audit)
    closed_wall = summary['closed']['wall_s']
    closed_active = summary['closed']['active_call_union_s']
    pause_note = (
        f"Nos fechados, o tempo de parede manteve a cauda de pausas: P95 {fmt(closed_wall['p95'])}s "
        f"e máximo {fmt(closed_wall['max'])}s, incluindo interrupção pelo limite da chave e pausa solicitada. "
        f"A união dos intervalos de chamadas foi P50 {fmt(closed_active['median'])}s / "
        f"P95 {fmt(closed_active['p95'])}s. As pausas não foram apagadas; tempo ativo e tempo decorrido "
        'respondem a perguntas distintas, e nenhum deles isoladamente mede a qualidade da interação.')
    readme = template('README.block.md') + '\n\n' + comparison + '\n\n' + pause_note + '\n\n' + closed_note + '\n'
    readme += ('\nAuditoria dos públicos: pré-requisito repetido indevidamente, teste específico representado por basal, '
               'bloqueio de investigação urgente e afirmação inventada usada no raciocínio. Hash íntegro e juiz positivo '
               'não garantem fidelidade ou conduta correta; correções propostas ainda não testadas nesta condição.\n')
    outputs = {'README.md': current_readme((base / 'README.md').read_text(), readme)}
    for name in ('PROTOCOL', 'AGENTS', 'CHANGELOG'):
        outputs[name + '.md'] = add_block((base / (name + '.md')).read_text(), template(name + '.block.md'), name == 'CHANGELOG')
    specific = re.sub(r'\*\*RASCUNHO:[\s\S]*?Data final', 'Data final', template('reports/v4_fast4_summary.md'), count=1)
    specific += '\n\n' + pause_note + '\n'
    specific += '\n\n## Fidelidade fechada agregada\n\n' + closed_note + '\n'
    specific += ('\nOs manifestos originais integrais e metadados de geração por chamada permanecem locais para auditoria, '
                 'ignorados no Git quando contêm identificadores privados. Os exports públicos expõem digests opacos e '
                 'contagens em v4_fast_preregistration_digests.json. A conciliação consulta o ledger somente em leitura; '
                 'não altera custos históricos.\n')
    specific += ('\n## Auditoria pública adicional e próximas correções\n\n'
                 'Todos os públicos foram auditados. Nos oito restantes: 24 inputs reconstruídos, 30 outputs exatos, '
                 '35 achados de fonte; 20 grupos conservadores de enunciados sem fonte em 12 respostas de 7 casos. '
                 'Não são a mesma unidade das cinco afirmações específicas do piloto. Houve pré-requisito inadequado '
                 'repetido, basal representando teste específico, MRI urgente adiada e histórico de dispositivo não relatado '
                 'usado no raciocínio. Protocolos, contraste e momento não são atestados por equivalência nominal.\n\n'
                 'Propostas seguintes, não validadas nesta condição: paciente estruturado com desconhecidos explícitos; '
                 'correspondência de espécime, protocolo e momento; triagem de urgência antes de gates de história e custo; '
                 'detecção de ciclos de pré-requisitos; julgamento médico cego de diagnóstico e manejo. '
                 'Nenhum código clínico foi alterado ou caso reexecutado após observar fechados.\n')
    outputs['reports/v4_fast4_summary.md'] = specific
    projection = (
        f"## v4 rápida fast4 — consolidação em {date}\n\nDez públicos: US${api} todos os atores; "
        f"dez fechados: US${summary['closed']['openrouter_all_actors_usd']}. A assinatura tem custo monetário desconhecido. "
        'A API de implantação exclui paciente simulado e juízes, discriminados no resumo. Exames usam unidades artificiais '
        '1/5/15 deduplicadas por fonte, sem dólar clínico.\n\n'
        f"Projeção linear para 50 encontros públicos: US${api * 5}; para 50 do mix das duas coortes: "
        f"US${(api + Decimal(str(summary['closed']['openrouter_all_actors_usd']))) * Decimal('2.5')}. "
        'Estimativas sem autorização de execução, sem assinatura, sem garantia de acerto ou preço. '
        f"Global v4 US${summary['ledger']['cost_usd']} conciliado, pilotos e falhas incluídos; "
        f"restante do teto US$5: US${summary['ledger']['remaining_cap_conservative_usd']}. Projeções anteriores permanecem históricas.")
    outputs['reports/cost_projection.md'] = add_block((base / 'reports/cost_projection.md').read_text(), projection)
    general = (
        f"## Atualização v4 rápida — {date}\n\nFast4 públicos {public['judge_accepted']}/10, "
        f"fechados {summary['closed']['judge_accepted']}/10 pelo juiz, separados; condição b3d7d00, sem retuning fechado. "
        f"Global v4 US${summary['ledger']['cost_usd']}. {values['BILLING_STATUS']}. "
        '[Resumo específico](v4_fast4_summary.md), [métricas e atores](v4_fast_summary.json), '
        '[artifact animado](v4_comparison.html). Histórico e negativos preservados; revisão médica pendente.')
    outputs['reports/summary.md'] = add_block((base / 'reports/summary.md').read_text(), general)
    for name in ('README.md','AGENTS.md','PROTOCOL.md','CHANGELOG.md'):
        outputs[name]=re.sub(r'\]\((v4_[^)]*)\)',r'](reports/\1)',outputs[name])
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--templates', type=Path, default=Path(__file__).resolve().parent / 'templates_v4_fast_docs')
    parser.add_argument('--output', type=Path, help='Preview directory; does not modify --base')
    parser.add_argument('--apply', action='store_true', help='Explicitly write completed documents into --base')
    parser.add_argument('--final-date-local', help='Stable America/Fortaleza timestamp for repeatable rendering')
    args = parser.parse_args()
    if args.apply and args.output:
        parser.error('--apply and --output are mutually exclusive')
    base = args.base.resolve()
    destination = base if args.apply else (args.output or Path(__file__).resolve().parent / 'rendered_v4_fast_docs').resolve()
    if destination == base and not args.apply:
        parser.error('Writing into --base requires --apply')
    def report(name):
        return json.loads((base / 'reports' / name).read_text())
    date = args.final_date_local or datetime.now(ZoneInfo('America/Fortaleza')).strftime('%d/%m/%Y %H:%M:%S')
    outputs = render_documents(base, args.templates, report('v4_fast_summary.json'),
                               report('v4_fast_billing_reconciliation.json'),
                               report('v4_fast4_closed_fidelity_aggregate.json'), date)
    # Validate/render every input before making any documentation mutation.
    for relative, content in outputs.items():
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
    print(json.dumps({'documentation_updated': args.apply, 'preview': not args.apply,
                      'files': len(outputs), 'output': str(destination),
                      'placeholder_count_remaining': 0, 'closed_individual_content_written': False}))


if __name__ == '__main__':
    main()
