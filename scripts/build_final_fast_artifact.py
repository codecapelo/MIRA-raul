"""Build a final standalone candidate AFTER validated fast4 public+closed completion.

Read only the aggregate published report and explicitly public replay paths.
Writes /private/tmp only. Never opens closed traces, case facts or private IDs.
All displayed numbers come from the supplied completed consolidation report.
"""
import argparse
from datetime import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo

PUBLIC_IDS = [f'case_{i:03}' for i in range(1, 11)]
AGGREGATE_KEYS = {'terminal_count','judged','judge_accepted','judge_rejected','operational_terminals',
    'doctor_rescues','proposal_accepted','proposal_judged','openrouter_all_actors_usd',
    'deployment_openrouter_usd','wall_s','active_call_union_s','first_doctor_completed_s',
    'first_doctor_content_s','first_doctor_any_delta_s','relative_exam_units','charged_sources',
    'subscription_input_tokens_per_case','subscription_output_tokens_per_case',
    'subscription_input_tokens_total','subscription_cache_input_tokens_total',
    'failed_calls_with_unknown_subscription_usage','failed_subscription_calls_with_recorded_latency','failed_subscription_calls_without_recorded_latency','active_call_time_incomplete','stream_failures_received_metadata',
    'wilson_95_all_terminals','subscription_monetary_cost_usd'}
CASE_KEYS = {'case_id','judge_correct','proposal_correct','openrouter_usd','wall_s','active_call_union_s',
    'first_doctor_completed_s','first_doctor_content_s','first_doctor_any_delta_s',
    'relative_exam_units','charged_sources','subscription_input_tokens','subscription_output_tokens','trace_sha256'}


def validate_summary(report):
    if report.get('partial_closed_only') is True or report.get('selected_study_complete') is False:
        raise ValueError('Blocked checkpoint cannot be a final artifact')
    if report.get('partial_public_only') is not False or report.get('variant') != 'fast4':
        raise ValueError('Requires final selected fast4 consolidation')
    public, closed = report.get('public'), report.get('closed')
    if not isinstance(public,dict) or not isinstance(closed,dict):
        raise ValueError('Both complete cohorts required')
    if public.get('terminal_count') != 10 or public.get('judge_accepted') != 10 or closed.get('terminal_count') != 10:
        raise ValueError('Public gate and twenty terminal encounters required')
    rows = public.get('cases',[])
    if sorted(row.get('case_id','') for row in rows) != PUBLIC_IDS:
        raise ValueError('Only ten public case identities permitted')
    if len(set(row['case_id'] for row in rows)) != 10:
        raise ValueError('Duplicate public identity')
    # Reject leaked closed rows rather than silently accepting a bad report.
    if 'cases' in closed or any(key in closed for key in ('diagnoses','inputs','case_ids','individual_hashes')):
        raise ValueError('Closed report must contain aggregates only')
    for cohort in (public,closed):
        if cohort.get('judged',0)+cohort.get('operational_terminals',0) != cohort['terminal_count']:
            raise ValueError('Cohort denominators inconsistent')
        if cohort.get('judge_accepted',0)+cohort.get('judge_rejected',0) != cohort.get('judged',0):
            raise ValueError('Judgment counts inconsistent')
    if report.get('human_review') != 'pending' or report.get('judge_uncertainty_fields_scored') is not False:
        raise ValueError('Validation boundaries required')


def safe_aggregate(value):
    return {key:value[key] for key in sorted(AGGREGATE_KEYS) if key in value}


def select_data(report, summary_sha):
    validate_summary(report)
    public = safe_aggregate(report['public'])
    public['cases'] = [{key:row[key] for key in sorted(CASE_KEYS) if key in row} for row in report['public']['cases']]
    previous = {variant: safe_aggregate(value) for variant,value in report.get('preserved_previous_public_conditions',{}).items()}
    return {'variant':report['variant'],'public':public,'closed':safe_aggregate(report['closed']),
        'previous_public':previous,'comparison_descriptive':{label:{key:data[key] for key in ('active_call_union_s_recomputed',
            'first_doctor_completed_s_recomputed','subscription_input_tokens_per_case') if key in data}
            for label,data in report.get('comparison_descriptive',{}).items() if label in ('v36','v4_original','v4_working')},
        'global_ledger_usd':report['ledger']['cost_usd'],'remaining_global_cap_usd':report['ledger']['remaining_cap_conservative_usd'],
        'cap_usd':report['ledger']['cap_usd'],
        'financial':{key:report.get('financial',{}).get(key) for key in ('status','account_delta_usd',
            'received_usage_ledger_usd','ledger_above_account_usd','exact_match','snapshot_is_final_verified')},
        'created_unix_time':report['created_unix_time'],'clinical_commit':report['clinical_commit'],
        'frozen_condition_sha256':report['frozen_condition_sha256'],'summary_sha256':summary_sha,
        'human_review':'pending','closed_export_policy':'Agregados somente; sem casos, fatos, diagnósticos ou hashes individuais',
        'subscription_monetary_cost_usd':None}


OVERVIEW = '''<section id="achados" class="panel" role="tabpanel" aria-labelledby="tab-achados">
<div class="section-intro"><h2>Conversa leve; revisão Sol/Astra nos pontos de decisão.</h2><p>A condição escolhida usa Flash-Lite para a conversa e Sol/Astra para revisão. Os dez públicos liberaram a avaliação dos dez fechados com a mesma condição congelada. Todos os números abaixo são observações desta execução.</p></div>
<div id="fast-final-metrics" class="grid metrics"></div><div class="callout"><p><strong>O significado do escore:</strong> decisão do juiz LLM sobre o diagnóstico. Os públicos participaram do desenvolvimento, e os fechados têm uso histórico: nenhum grupo constitui validação externa intocada. Confiança, incertezas e próximos passos não são julgados por esse escore. Revisão médica pendente.</p></div>
<div class="grid two"><article class="card"><span class="tag">Dez públicos · condição escolhida</span><h3 style="margin-top:12px">Rapidez e recursos</h3><div id="fast-public-details"></div></article><article class="card"><span class="tag">Dez fechados · apenas agregados</span><h3 style="margin-top:12px">Validação após o gate público</h3><div id="fast-closed-details"></div><p class="small">Mesmos código, configuração e parâmetros congelados. Nenhuma informação individual fechada foi incluída neste artifact.</p></article></div>
<div class="callout good"><p><strong>Como mudou:</strong> anamnese curta no modelo econômico, revisão independente Sol, parecer final de Astra, custos de exames compartilhados e seguimento dirigido pelos achados realmente obtidos. O gasto OpenRouter é medido; o custo monetário da assinatura permanece desconhecido.</p></div>
<article class="card" style="margin:20px 0"><span class="tag">Auditoria dos dez públicos · limites observados</span><h3 style="margin-top:12px">Acertar a hipótese não garante um percurso clínico fiel.</h3><p>O paciente simulado ainda afirmou negativos ou históricos ausentes da fonte; em um público, uma afirmação inventada sobre seguimento de dispositivo também apareceu no raciocínio final. Resultados literais e hashes íntegros não eliminam esse problema.</p><p>Foram observados pré-requisito repetido inadequadamente, exame específico representado por resultado basal e investigação urgente adiada por regras de história/custo. Protocolos, contraste e momento de coleta continuam exigindo verificação além do nome do exame.</p><p><strong>Correções propostas para a próxima condição, ainda não validadas nesta rodada:</strong> paciente com fatos estruturados e desconhecidos explícitos; correspondência obrigatória de protocolo/espécime/momento; triagem de gravidade antes de limites de história/custo; detecção de ciclos de pré-requisitos; revisão médica cega do diagnóstico e da conduta. A condição testada e seus resultados permanecem preservados.</p><p class="small">Cobertura: dez públicos auditados contra os arquivos locais de paciente/investigações; cinco afirmações específicas sem fonte no piloto001–002 e vinte grupos conservadores de enunciados no restante. Essas unidades de contagem diferem e não são somadas. Não houve nova extração dos artigos-fonte nem validação clínica independente.</p></article><details><summary>Achados e resultados preservados da v4 anterior</summary>__OLD_OVERVIEW__</details></section>'''

COMPARISON = '''<article class="card" style="margin:20px 0"><span class="tag">Histórico preservado · denominadores explícitos</span><h3 style="margin-top:12px">Tempo, gasto e diagnóstico nos públicos</h3><div class="table-scroll"><table><thead><tr><th>Condição</th><th>Terminais</th><th>Final · juiz</th><th>OpenRouter · todos atores</th><th>Chamadas ativas · mediana</th><th>Primeira fala completa · mediana</th><th>Entrada da assinatura · mediana</th></tr></thead><tbody id="fast-public-comparison"></tbody></table></div><p class="small" style="margin-top:12px">fast1 é a condição concluída rejeitada pelo gate; fast2 e fast3 são pilotos preservados, com dois terminais cada. Um piloto não equivale a dez casos. Tempos incluem caudas longas; chamadas ativas são a união dos intervalos, enquanto o tempo entre início e terminal inclui pausas de retomada. Comparação descritiva, sem atribuição causal ou superioridade clínica.</p><p id="fast-api-difference" class="small"></p></article>'''

CASES = '''<article class="card" style="margin:20px 0"><span class="tag">Condição escolhida · somente casos públicos</span><h3 style="margin-top:12px">Os dez encontros rápidos</h3><div class="table-scroll"><table><thead><tr><th>Caso público</th><th>Final · juiz</th><th>Chamadas ativas</th><th>Início até terminal</th><th>Primeiro conteúdo</th><th>OpenRouter</th><th>Unidades artificiais</th></tr></thead><tbody id="fast-public-cases"></tbody></table></div><p class="small">Clique no caso para abrir sua reprodução. Os fechados são apresentados exclusivamente como agregados.</p></article>'''

FINAL_JS = r'''<script>
(()=>{
const F=DATA.fastFinal,P=F.public,C=F.closed;
const dur=s=>s===null||s===undefined?'não medido':s>=3600?Math.floor(s/3600)+'h '+Math.floor((s%3600)/60)+'min':s<60?Number(s).toLocaleString('pt-BR',{maximumFractionDigits:1})+' s':Math.floor(Math.round(s)/60)+'min '+(Math.round(s)%60)+'s';
const median=v=>v&&typeof v.median==='number'?v.median:null;
const num=v=>v===null||v===undefined?'não informado':Number(v).toLocaleString('pt-BR',{maximumFractionDigits:0});
const accepted=c=>c.judge_accepted+'/'+c.terminal_count;
const cards=[['Juiz · públicos / fechados',accepted(P)+' · '+accepted(C),'Coortes separadas; públicos de desenvolvimento e fechados históricos.'],['Chamadas ativas · mediana',dur(median(P.active_call_union_s))+(P.active_call_time_incomplete?' · limite inferior':''),'Exclui intervalos sem chamada; inclui caudas longas.'],['Primeiro conteúdo do médico',dur(median(P.first_doctor_content_s)),'Desde início do encontro; chegada de conteúdo registrada por SSE.'],['OpenRouter · dez públicos','US$ '+money(P.openrouter_all_actors_usd,5),'Todos os atores. Assinatura separada.']];
const metrics=document.getElementById('fast-final-metrics');cards.forEach(([label,value,note])=>{const card=el('article',undefined,'card metric');card.append(el('small',label),el('strong',value),el('p',note));metrics.append(card)});
function details(id,c){const target=document.getElementById(id);[['Final pelo juiz',accepted(c)],['Terminais operacionais',num(c.operational_terminals)],['Proposta pelo juiz',c.proposal_accepted+'/'+c.proposal_judged+' julgadas'],['Tempo entre início e terminal · mediana',dur(median(c.wall_s))],['Tempo entre início e terminal · P95 / máximo',dur(c.wall_s.p95)+' / '+dur(c.wall_s.max)],['Chamadas ativas · mediana',dur(median(c.active_call_union_s))+(c.active_call_time_incomplete?' · limite inferior: falha sem duração registrada':'')],['Chamadas ativas · P95',dur(c.active_call_union_s.p95)],['Primeira fala completa · mediana',dur(median(c.first_doctor_completed_s))],['Tokens de entrada da assinatura · mediana',num(median(c.subscription_input_tokens_per_case))],['Exames artificiais',num(c.relative_exam_units)+' unidades / '+num(c.charged_sources)+' fontes'],['OpenRouter · todos os atores','US$ '+money(c.openrouter_all_actors_usd)]].forEach(([key,value])=>{const p=el('p');p.append(el('b',key+': '),el('span',value));target.append(p)})};details('fast-public-details',P);details('fast-closed-details',C);
function oldTime(id,key){const old=F.comparison_descriptive[id]||{};return median(old[key])};
const rows=[['Claude v3.6 · dez públicos',10,DATA.v36.public_final,DATA.v36.public_openrouter_usd,oldTime('v36','active_call_union_s_recomputed'),oldTime('v36','first_doctor_completed_s_recomputed'),oldTime('v36','subscription_input_tokens_per_case')],['v4 · revisão final Astra',10,DATA.v4Working.judge_correct,DATA.v4Working.openrouter_usd,oldTime('v4_working','active_call_union_s_recomputed'),oldTime('v4_working','first_doctor_completed_s_recomputed'),oldTime('v4_working','subscription_input_tokens_per_case')]];
for(const [variant,c] of Object.entries(F.previous_public)){rows.push([variant+(c.terminal_count<10?' · piloto preservado':' · condição anterior'),c.terminal_count,c.judge_accepted,c.openrouter_all_actors_usd,median(c.active_call_union_s),median(c.first_doctor_completed_s),median(c.subscription_input_tokens_per_case)])};rows.push([F.variant+' · condição escolhida',P.terminal_count,P.judge_accepted,P.openrouter_all_actors_usd,median(P.active_call_union_s),median(P.first_doctor_completed_s),median(P.subscription_input_tokens_per_case)]);
const body=document.getElementById('fast-public-comparison');rows.forEach(([name,n,correct,cost,active,first,tokens])=>{const tr=el('tr');[name,String(n),correct+'/'+n,'US$ '+money(cost),dur(active),dur(first),num(tokens)].forEach(value=>tr.append(el('td',value)));body.append(tr)});
const diff=100*(1-Number(P.openrouter_all_actors_usd)/Number(DATA.v36.public_openrouter_usd));document.getElementById('fast-api-difference').textContent='Diferença no gasto OpenRouter versus dez públicos v3.6: '+Math.abs(diff).toLocaleString('pt-BR',{maximumFractionDigits:1})+'% '+(diff>=0?'menor':'maior')+'. Frente à v4 anterior mais lenta, o gasto OpenRouter ficou '+(100*(Number(P.openrouter_all_actors_usd)/Number(DATA.v4Working.openrouter_usd)-1)).toLocaleString('pt-BR',{maximumFractionDigits:1})+'% maior, porque a conversa passou para API paga. O custo monetário da assinatura é desconhecido; estes números não medem custo total.';
const caseBody=document.getElementById('fast-public-cases');P.cases.forEach(c=>{const tr=el('tr'),td=el('td'),button=el('button',c.case_id.replace('case_','Caso '),'case-link');button.addEventListener('click',()=>{showTab('reproducao');const trial=document.getElementById('replay-trial');trial.value='fast_'+F.variant;trial.dispatchEvent(new Event('change'));const picker=document.getElementById('replay-case');picker.value=c.case_id;picker.dispatchEvent(new Event('change'));document.getElementById('reproducao').scrollIntoView({behavior:'smooth'})});td.append(button);tr.append(td);[c.judge_correct?'positivo':'negativo',dur(c.active_call_union_s),dur(c.wall_s),dur(c.first_doctor_content_s),'US$ '+money(c.openrouter_usd),num(c.relative_exam_units)].forEach(value=>tr.append(el('td',value)));caseBody.append(tr)});
const footer=document.querySelector('.footer');if(footer){const p=el('p');p.textContent='Orçamento global registrado: US$ '+money(F.global_ledger_usd)+' / US$ '+money(F.cap_usd,2)+'. Financeiro: '+(F.financial.exact_match?(F.financial.snapshot_is_final_verified?'conta conciliada':'snapshot coincidente; leitura final requer conferência'):'diferença preservada ou leitura final pendente')+'. Hash do relatório agregado: '+F.summary_sha256+'. Revisão médica pendente.';footer.append(p)};
})();
</script>'''


def build(base, summary, artifact, output, helper_path=None):
    report=json.loads(summary.read_text()); validate_summary(report)
    fidelity_path=base/'reports/v4_fast4_closed_fidelity_aggregate.json'
    fidelity=json.loads(fidelity_path.read_text())
    if fidelity.get('audited_terminal_encounters')!=10:
        raise ValueError('Completed aggregate fidelity audit required')
    answers=fidelity['patient_answers']; exam_audit=fidelity['exam_results']
    closed_fidelity_notice=(f'<p><strong>Auditoria das falas:</strong> entre {int(answers["total_answers"])} respostas do paciente simulado, '
        f'{int(answers["confirmed_answers_with_unreported_negative_assertions"])} acrescentaram negativas clínicas ausentes da fonte; '
        f'{int(answers["pending_ambiguous_answers"])} permaneceram ambíguas. '
        f'{int(exam_audit["distinct_excerpts_checked"])} trechos de exames foram verificados sem divergência encontrada nas verificações aplicadas. '
        'Afirmações positivas e raciocínio médico não foram adjudicados exaustivamente; isto não estabelece fidelidade clínica completa.</p><p>O tempo máximo entre início e terminal inclui a interrupção pelo limite da chave e a pausa autorizada. Esse intervalo permanece nas métricas de parede; chamadas ativas somam apenas os intervalos registrados de execução.</p>')
    helper_path = Path(helper_path) if helper_path else Path(__file__).resolve().with_name('update_fast_artifact.py')
    spec=importlib.util.spec_from_file_location('public_fast_replay_helper',helper_path)
    helper=importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
    stage=output.with_name(output.stem+'_replay_stage.html'); stage.write_text(artifact.read_text())
    variants=list(report.get('preserved_previous_public_conditions',{}))+[report['variant']]
    for variant in variants:
        if not re.fullmatch(r'fast[1-4]',variant): raise ValueError('Unexpected public condition')
        extended,_=helper.build_candidate(base,stage,variant,allow_partial=variant!=report['variant'])
        stage.write_text(extended)
    html=stage.read_text(); match=re.search(r'(<script id="mira-data" type="application/json">)([\s\S]*?)(</script>)',html)
    data=json.loads(match.group(2))
    if 'fastFinal' in data:
        raise ValueError('Use preserved base artifact; final extension already present')
    data['fastFinal']=select_data(report,hashlib.sha256(summary.read_bytes()).hexdigest())
    chosen=next(t for t in data['replay']['trials'] if t['id']=='fast_'+report['variant'])
    if len(chosen['cases'])!=10 or not all(c['terminal_observed'] for c in chosen['cases']):
        raise ValueError('Chosen public replay not fully terminal')
    expected={r['case_id']:r['trace_sha256'] for r in report['public']['cases']}
    if any(expected[c['case_id']]!=c['sha256'] for c in chosen['cases']): raise ValueError('Public replay/report hash mismatch')
    for trial in data['replay']['trials']:
        if any(c['case_id'] not in PUBLIC_IDS or 'fast_private' in c['source'] for c in trial['cases']):
            raise ValueError('Private replay forbidden')
    when=datetime.fromtimestamp(report['created_unix_time'],ZoneInfo('America/Fortaleza')).strftime('%d/%m/%Y %H:%M:%S')
    data['title']='MIRA v4 · interação otimizada'; data['snapshot_date']=when+' · Fortaleza'
    html=html[:match.start(2)]+json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')+html[match.end(2):]
    # Preserve earlier overview in a collapsed record; all historical panels/data remain.
    pattern=r'(<section id="achados"[^>]*>)([\s\S]*?)(</section>)'; old=re.search(pattern,html)
    if not old: raise ValueError('Overview section missing')
    html=html[:old.start()]+OVERVIEW.replace('__OLD_OVERVIEW__',old.group(2)).replace('<div id="fast-closed-details"></div>', '<div id="fast-closed-details"></div>'+closed_fidelity_notice)+html[old.end():]
    html=html.replace('<title>MIRA · v4 em perspectiva</title>','<title>MIRA v4 · interação otimizada</title>')
    html=html.replace('<h1>v4 em perspectiva</h1>','<h1>v4 · interação otimizada</h1>')
    html=re.sub(r'<span class="pill">Snapshot · [^<]+</span>','<span class="pill">Snapshot · '+when+' · Fortaleza</span>',html,count=1)
    html=html.replace('<span class="pill">10 casos públicos conhecidos</span>','<span class="pill">10 públicos + 10 fechados · condição escolhida</span>',1)
    html=html.replace('O que mudou no sistema, o que os dez casos mostram e quais comparações ainda não são sustentadas pela evidência.','Conversa econômica, revisão Sol/Astra, horários reais registrados e histórico completo das condições testadas.',1)
    html=html.replace('<!-- FINAL_THREE_START -->',COMPARISON+'<!-- FINAL_THREE_START -->',1)
    html=re.sub(r'(<section id="casos"[^>]*>)',lambda m:m.group(1)+CASES,html,count=1)
    if html.count('});populateTrials();') != 1:
        raise ValueError('Expected one scoped replay initialization')
    html=html.replace("});populateTrials();", "});populateTrials('fast_'+DATA.fastFinal.variant);",1)
    # A replay cannot display the complete response before its observed end.
    html=html.replace("el('div',e.preview||'Sem conteúdo de saída neste evento.','replay-preview')", "el('div',((e.kind==='api'||e.kind==='cli')&&now<e.end)?'Chamada em andamento. A resposta completa só é exibida após o horário registrado de conclusão.':(e.preview||'Sem conteúdo de saída neste evento.'),'replay-preview')")
    html=html.replace("el('p',resource(e),'replay-resource')", "el('p',resource(e)+(e.diagnostic_status==='proposal_before_expert_review'?' · PROPOSTA anterior às revisões; não é a hipótese final selecionada.':''),'replay-resource')")
    html=html.replace('</body></html>',FINAL_JS+'</body></html>')
    html=html.replace('MIRA · síntese exploratória, 08-10-2026.', 'MIRA · síntese exploratória, '+datetime.fromtimestamp(report['created_unix_time'],ZoneInfo('America/Fortaleza')).strftime('%d-%m-%Y')+'.')
    html=html.replace('Ele não integrou os dez encontros apresentados e não preenche retrospectivamente seus resultados ausentes.', 'Esse registro não integrou os dez encontros antigos; na condição fast4, os retornos exatos da fila foram registrados e auditados. Não há preenchimento retroativo de registros ausentes.')
    html=html.replace('após esta avaliação, foi acrescentado','após a avaliação v4 anterior, foi acrescentado')
    html=html.replace('A conta global inclui também o estudo offline e a candidata;', 'Este snapshot financeiro anterior ao fast1–4 inclui somente o estudo original, offline e a candidata lenta;')
    html=html.replace('\"title\":\"fast_review_sol_post_followup\"','\"title\":\"Sol · revisão complementar\"')
    output.write_text(html); stage.unlink()
    return {'candidate':str(output),'bytes':len(html.encode()),'selected_variant':report['variant'],
        'public_replay_trials':[{ 'id':t['id'],'cases':len(t['cases'])} for t in data['replay']['trials']],
        'closed_data':'aggregates only','repository_modified':False,'private_files_opened':False}


def main():
    p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True)
    p.add_argument('--summary',type=Path);p.add_argument('--artifact',type=Path)
    p.add_argument('--helper',type=Path,help='Replay helper; default sibling update_fast_artifact.py')
    p.add_argument('--output',type=Path,default=Path('/private/tmp/mira_v4_fast_final_candidate.html'))
    a=p.parse_args(); base=a.base.resolve(); output=a.output.resolve()
    if not output.is_relative_to(Path('/private/tmp')): raise ValueError('Candidate must remain in /private/tmp')
    archived=base/'reports/v4_comparison_before_fast.html'
    template=a.artifact or (archived if archived.exists() else base/'reports/v4_comparison.html')
    result=build(base,a.summary or base/'reports/v4_fast_summary.json',template,output,a.helper)
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(json.dumps({'artifact_build_failed':type(exc).__name__,'no_inference':True,'no_repository_edits':True}))
        raise SystemExit(1) from None
