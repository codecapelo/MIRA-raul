"""One timeline per encounter, from its trace: every step with the clock (seconds since the encounter started), the latency of the call, and the actor.

The panel plays it back at 1x to 60x with a stopwatch. All steps share one card format; only the actor (and its color) changes: GLM-5 (or another physician model), the simulated patient,
the order desk (exam matcher), the JEF triage, Sonnet 5.5, Opus 5.5 and the judge. Gaps longer than GAP_S seconds between consecutive events (a run that was interrupted and resumed) are
cut to PAUSE_S and the removed time is reported, so the clock never counts hours of waiting.
  from replay_events import build;  events,meta=build(trace_path)
"""
import json,re

GAP_S=120;PAUSE_S=4
ACTORS={'claude-sonnet-5-5':'sonnet','claude-opus-5-5':'opus','claude-haiku-5-5':'haiku'}
LABEL={'glm':'GLM-5','sonnet':'Sonnet 5.5','opus':'Opus 5.5','haiku':'Haiku 5.5','patient':'Paciente (simulado)','sys':'Pedidos e exames','jef':'JEF','judge':'Juiz (Gemini 3.1 Pro)'}
TOOLPT={'request_blood_test':'exame de sangue','request_urine_test':'exame de urina','request_bedside_test':'exame à beira do leito','request_radiology':'imagem','request_microbiology':'microbiologia','request_other_investigation':'outro exame','request_physical_exam':'exame físico','admission':'admissão'}

def parse(t):
    m=re.search(r'\{.*\}',t or '',re.S)
    try:return json.loads(m.group(0),strict=False)
    except Exception:return {}

def actor_of(model):
    return ACTORS.get(model) or ('glm' if 'glm' in (model or '') else 'sys')

def clip(s,n=900):
    s=str(s or '');return s if len(s)<=n else s[:n]+' …'

def tool_text(e):
    out=e.get('output') or '';a=e.get('arguments') or {};names=a.get('test_names') or [a.get('study_name')] or []
    names=', '.join(x for x in names if x) or json.dumps(a,ensure_ascii=False)[:160]
    if out.startswith('Investigation locked'):return 'bloqueado','Pedido: '+names+'\n'+out
    body=out.split('\nApproximate')[0].split('Held (not ordered)')[0].strip();extra=out[len(body):].strip()
    lines=[]
    try:o=json.loads(body)
    except json.JSONDecodeError:o=None
    if isinstance(o,dict):
        for x in o.get('findings',[]):lines.append(f"{x.get('name')}: {clip(x.get('value'),600)}"+(' (reencaminhado para a ferramenta certa)' if x.get('rerouted') else ''))
        for n in o.get('not_available_in_this_case',[]):lines.append(f'{n}: não disponível neste caso')
        for x in o.get('already_ordered_earlier',[]):lines.append(f"{x.get('name')}: já pedido antes")
        for x in o.get('ambiguous_request',[]):lines.append(f"{x.get('requested')}: pedido inespecífico, o associador pede para detalhar")
        for x in o.get('wrong_tool',[]):lines.append(f"{x.get('requested','')}: ferramenta errada, use {x.get('use_tool')}")
        for x in o.get('requires_prior_procedure',[]):lines.append(f"{x.get('requested','')}: exige antes {x.get('needs_prior_procedure')}")
    elif body:lines.append(clip(body,500))
    found=isinstance(o,dict) and bool(o.get('findings'))
    kind='resultado' if found else 'na fila' if 'Queued:' in out else 'repetido' if 'already requested this turn' in out else 'retido' if 'Held (not ordered)' in out else 'sem resultado'
    return kind,'Pedido: '+names+'\n'+'\n'.join(lines)+(('\n'+extra) if extra else '')

def build(path):
    ev=[json.loads(l) for l in open(path)];ev.sort(key=lambda e:float(e['time']))
    t_start=float(next(e['time'] for e in ev if e['event']=='protocol_config') if any(e['event']=='protocol_config' for e in ev) else ev[0]['time'])
    # time stamps at which work happened, to find long gaps
    stamps=sorted({float(e['time']) for e in ev}|{float(e['time'])-float(e.get('latency_s') or 0) for e in ev if e['event']=='cli_call'})
    cuts=[];off=0.0;prev=None;pauses=[]
    for x in stamps:
        if prev is not None and x-prev>GAP_S:off+=(x-prev)-PAUSE_S;pauses.append({'after_s':round(prev-t_start-sum(p['removed_s'] for p in pauses),1),'removed_s':round((x-prev)-PAUSE_S)})
        cuts.append((x,off));prev=x
    def tc(x):
        o=0.0
        for s,f in cuts:
            if s<=x+1e-9:o=f
            else:break
        return max(x-t_start-o,0.0)
    reqs={e['request_id']:e for e in ev if e['event']=='request'}
    out=[];last_t=0.0;last_rev='sonnet';seen={}
    def add(actor,model,kind,title,text,t,t0=None,detail=None,chips=None,t0c=None):
        nonlocal last_t
        t=round(tc(t),2) if t is not None else last_t;t0=t0c if t0c is not None else (round(tc(t0),2) if t0 is not None else t)
        out.append({'t':t,'t0':min(t0,t),'actor':actor,'model':model,'kind':kind,'title':title,'text':text,'detail':detail or [],'chips':chips or []});last_t=max(last_t,t)
    final=next((e for e in ev if e['event']=='case_complete'),None)
    res=final['result'] if final else {};tokens=(res.get('cascade_path') or '').split('>')
    for e in ev:
        k=e['event'];tm=float(e['time'])
        if k=='cli_call':
            role=e.get('role');msg=e['response']['message'];lat=float(e.get('latency_s') or 0);a=actor_of(e['model']);txt=(msg.get('content') or '').strip()
            if role=='consult_map':
                j=parse(txt);d=[f"{i+1}) {x.get('diagnosis')} — confirmar com: {x.get('confirm_with','')}" for i,x in enumerate(j.get('differentials') or [])]
                dec=[f"{x.get('tool','').replace('request_','')}: {', '.join(x.get('test_names') or [])}" for x in j.get('decisive_investigations') or []]
                add(a,e['model'],'map','Mapa da consulta (só com a queixa e o exame inicial)',f"Urgência: {j.get('urgency','')} ({j.get('urgency_reason','')})",tm,tm-lat,[['Diferenciais','\n'.join(d)],['Exames decisivos','\n'.join(dec)],['Perguntas-chave','\n'.join(j.get('key_questions') or [])]],[j.get('urgency','')])
            elif role=='doctor':
                calls=[c['function']['name'] for c in msg.get('tool_calls') or []]
                add(a,e['model'],'doctor','Médico',txt,tm,tm-lat,[],[TOOLPT.get(c,c) for c in calls])
            elif role=='patient':add('patient',e['model'],'patient','Paciente',txt,tm,tm-lat)
            elif role=='patient_review':add('patient',e['model'],'patient','Paciente responde ao revisor',txt,tm,tm-lat)
            elif role=='review_claude':
                j=parse(txt);last_rev=a
                if 'decision' in j:
                    title='Árbitro';body=f"Decisão: {j.get('decision')}\nDiagnóstico: {j.get('diagnosis','')}";det=[['Raciocínio',j.get('reasoning','')]]
                elif 'features' in j:
                    title='Leitura guiada pelos achados';body=f"Diagnóstico: {j.get('diagnosis','')}\nConfiança: {j.get('confidence','')}"
                    det=[['Achados distintivos','\n'.join(f"- {f.get('feature')} → {', '.join((f.get('candidates') or f.get('characteristic_of') or [])[:4])}" for f in j.get('features') or [])],['Não explicado',' | '.join(j.get('unexplained') or [])],['Raciocínio',j.get('reasoning','')]]
                else:
                    title='Leitura às cegas (não vê a proposta)';body=f"Diagnóstico: {j.get('diagnosis','')}\nConfiança: {j.get('confidence','')}";det=[['Raciocínio',j.get('reasoning','')]]
                seen[title]=seen.get(title,0)+1
                if seen[title]>1:title+=' (2ª leitura, depois da rodada)'
                elif title!='Árbitro':title+=' (1ª leitura)'
                if j.get('missing_questions') or j.get('missing_tests') or j.get('questions') or j.get('tests'):
                    qs=j.get('missing_questions') or j.get('questions') or [];ts=j.get('missing_tests') or j.get('tests') or []
                    det.append(['Pediu','\n'.join(['pergunta: '+q for q in qs]+['exame: '+', '.join(t.get('test_names') or []) for t in ts if isinstance(t,dict)])])
                add(a,e['model'],'review',title,body,tm,tm-lat,[d for d in det if d[1]])
        elif k=='response' and e.get('role')=='doctor':
            rq=reqs.get(e.get('request_id'));t0=float(rq['time']) if rq else tm;m=e['response']['choices'][0]['message']
            calls=[c['function']['name'] for c in m.get('tool_calls') or []]
            add(actor_of(e['response'].get('model')),e['response'].get('model'),'doctor','Médico',(m.get('content') or '').strip(),tm,t0,[],[TOOLPT.get(c,c) for c in calls])
        elif k=='response' and e.get('role')=='patient':
            rq=reqs.get(e.get('request_id'));t0=float(rq['time']) if rq else tm;m=e['response']['choices'][0]['message'];add('patient',e['response'].get('model'),'patient','Paciente',(m.get('content') or '').strip(),tm,t0)
        elif k=='response' and e.get('role')=='judge':
            rq=reqs.get(e.get('request_id'));t0=float(rq['time']) if rq else tm;j=parse(e['response']['choices'][0]['message'].get('content') or '')
            add('judge',e['response'].get('model'),'judge','Juiz',('correto' if j.get('decision') else 'errado'),tm,t0,[['Justificativa do juiz',j.get('reasoning','')]],['correto' if j.get('decision') else 'errado'])
        elif k=='tool':
            nm=e['name']
            if nm=='admission':
                a=e.get('arguments') or {}
                if e.get('admit_blocked') or e.get('nudge'):add('sys',None,'sys','Admissão recusada' if e.get('admit_blocked') else 'Lembrete de exame decisivo antes de admitir',clip(e.get('output'),500),tm,None,t0c=last_t)
                else:add('glm',None,'admission','Admissão: proposta do médico',f"Diagnóstico: {a.get('diagnosis','')}",tm,tm,[['Raciocínio',a.get('reasoning','')]])
                continue
            kind,body=tool_text(e);add('sys',None,'order',TOOLPT.get(nm,nm).capitalize(),body,tm,None,[],[kind],t0c=last_t)
        elif k=='cascade_step' and e['key']=='verify':
            v=e['value']
            if v.get('failed'):add('jef',None,'jef','Triagem do JEF','falhou',tm,tm)
            else:add('jef',v.get('model'),'jef','Triagem do JEF: a proposta se sustenta?',f"sustentado {v['supported']:.2f} · causa específica {v['specific']:.2f} · alternativas não excluídas {v['alternatives']:.2f} · escore combinado {v['combined']:.2f}",tm,tm,[],['aceitou a proposta' if 'jef_accept' in tokens else 'chamou a revisão'])
        elif k=='cascade_step' and e['key']=='same_prop_blind':add('jef',None,'jef','JEF: o revisor concorda com a proposta?',f"mesma doença (0 a 1): {e['value'].get('same',0):.2f}",tm,tm)
        elif k=='followup_result':
            det=[];qs=e.get('questions') or [];ts=e.get('tests') or []
            if qs:det.append(['Perguntas ao paciente','\n'.join('- '+q for q in qs)])
            if ts:det.append(['Exames pedidos',' | '.join(', '.join(t.get('test_names') or []) for t in ts)])
            add(last_rev,None,'followup','Rodada do revisor: perguntas e exames',clip(e.get('text'),1500),tm,None,det,t0c=last_t)
    if final:
        r=res;add('sys',None,'result','Resultado',f"Diagnóstico final: {r.get('dx_agent','')}\nReferência: {r.get('dx_reference','')}",float(final['time']),float(final['time']),[['Caminho',' › '.join(tokens).replace('claude-','').replace('-5-5','')]],['correto' if str(r.get('judge_correct'))=='True' else 'errado'])
    out.sort(key=lambda x:(x['t'],x['t0']))
    total=out[-1]['t'] if out else 0
    adm=next((x['t'] for x in out if x['kind']=='admission'),None)
    spent={}
    for x in out:
        if x['kind'] in('doctor','patient','review','judge','map'):spent[x['actor']]=round(spent.get(x['actor'],0)+x['t']-x['t0'],1)
    return out,{'total_s':total,'admission_s':adm,'paused':pauses,'busy_s':spent,'n':len(out)}
