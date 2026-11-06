"""Rebuilds the post-admission review pipeline of one encounter from its trace: what each reviewer saw, asked, received and decided.
Traces written since v3.5 carry the exact reviewer round in `followup_result` events; older traces are reconstructed by replaying the recorded strict-matcher decisions.
Used by the encounter viewer (artifact); `build(trace_path, case_dir, None)` returns (steps, final_result)."""
import json,re,sys
sys.path.insert(0,'src')
from mira_runner.tools_v3 import V3CaseTools
from mira_runner.matcher_v3 import strict_match
from mira_runner.cascade import Cascade,clean_requests,SWEEP_Q

def parse(t):
    m=re.search(r'\{.*\}',t or '',re.S)
    try:return json.loads(m.group(0))
    except Exception:return {}
class Fake:
    def __init__(self,content):self.content=content
    def call(self,*a,**k):return {'content':self.content}
class Log:
    def append(self,e):pass
class Replay:
    """strict-matcher stand-in that returns the decisions that were recorded in the trace, in order"""
    def __init__(self,ev):
        reqs={e['request_id']:e for e in ev if e['event']=='request' and e['role']=='matcher'};self.items=[]
        for e in ev:
            if e['event']=='response' and e['role']=='matcher' and e['request_id'] in reqs:
                u=reqs[e['request_id']]['payload']['messages'][1]['content']
                try:qs=json.loads(u.split('REQUESTED_TESTS:\n')[1].split('\n\nCANDIDATE_RECORDS')[0])
                except Exception:continue
                self.items.append([qs,e['response']['choices'][0]['message'].get('content') or '',False])
    def __call__(self,queries,cands):
        for it in self.items:
            if not it[2] and sorted(it[0])==sorted(queries):
                it[2]=True;return strict_match(Fake(it[1]),Log(),'replay',queries,cands)
        return {q:{'relation':'none','keys':[],'extract':[],'answer':'','reason':'sem decisão gravada'} for q in queries}

def fmt_output(tool,name,out):
    try:o=json.loads(out)
    except Exception:return f"{name}: {str(out)[:300]}"
    if not isinstance(o,dict):return f"{name}: {str(o)[:300]}"
    lines=[]
    for x in o.get('findings',[]):lines.append(f"ENCONTRADO — {x.get('name')}: {str(x.get('value'))[:600]}"+(f" ({x['note']})" if x.get('note') else ''))
    for x in o.get('already_ordered_earlier',[]):lines.append(f"já pedido antes — {x.get('name')}")
    for x in o.get('wrong_tool',[]):lines.append(f"ferramenta errada, use {x.get('use_tool')}")
    for x in o.get('requires_prior_procedure',[]):lines.append(f"exige procedimento antes: {x.get('needs_prior_procedure')}")
    for x in o.get('ambiguous_request',[]):lines.append("INESPECÍFICO — o associador pede para especificar o exame")
    if o.get('not_available_in_this_case'):lines.append("não disponível neste caso")
    return f"{name}: "+' | '.join(lines or ['sem resposta'])

def followup_lines(tools,tests):
    ctx={'tools':type('T',(),{'inner':tools})(),'stats':{'review_exchanges':0},'client':None,'log':Log(),'patient_messages':[],'patient_model':''}
    text=Cascade(None).follow_up(ctx,[],tests);lines=[]
    for ln in text.split('\n'):
        m=re.match(r"Reviewer test (\w+) '(.*?)': (.*)$",ln,re.S)
        if m:lines.append(fmt_output(m.group(1),m.group(2),m.group(3)))
        elif ln.startswith('(re-sent'):lines.append('   '+ln)
        elif ln.startswith('Reviewer procedure first'):lines.append(ln[:400])
    return lines

def build(path_trace,case_dir,csv_row):
    ev=[json.loads(l) for l in open(path_trace)];inv=json.load(open(case_dir/'investigations.json'))['observations']
    final=[e for e in ev if e['event']=='case_complete'][0]['result'];path=final['cascade_path'];tokens=path.split('>')
    steps=[]
    # the doctor's proposal
    adm=None
    for e in ev:
        if e['event']=='tool' and e['name']=='admission':adm=e.get('arguments') or {}
    steps.append({'t':'1 · Proposta do GLM-5 (admissão do médico)','b':[('Diagnóstico',(adm or {}).get('diagnosis') or final.get('proposal_dx')),('Raciocínio',(adm or {}).get('reasoning',''))]})
    # rebuild the tool state of the doctor phase, then replay the reviewers' rounds on it
    tools=V3CaseTools(inv,None,True,Replay(ev))
    for e in ev:
        if e['event']=='tool' and e['name'] not in('admission','request_physical_exam'):
            try:tools.execute(e['name'],e.get('arguments') or {})
            except Exception:pass
        if e['event']=='cascade_step' and e['key']=='verify':break
    jv=next((e['value'] for e in ev if e['event']=='cascade_step' and e['key']=='verify'),None)
    if jv and not jv.get('failed'):
        acc='jef_accept' in tokens
        steps.append({'t':'2 · Triagem do JEF','pill':('aceitou a proposta sem revisão' if acc else 'chamou a revisão','ok' if acc else 'warn'),'b':[('Escores',f"sustentado {jv['supported']:.2f} · causa específica {jv['specific']:.2f} · alternativas não excluídas {jv['alternatives']:.2f} · falta exame definitivo {jv.get('missing_definitive',0):.2f} → combinado {jv['combined']:.2f} (corte de aceite 0,86)")]})
    if 'jef_accept' in tokens:
        steps.append({'t':'3 · Decisão final','b':[('Sem revisão: a proposta do GLM-5 virou o diagnóstico final.','')],'final':True});return steps,final
    reads=[e for e in ev if e['event']=='cli_call' and e['role']=='review_claude'];pats=[e for e in ev if e['event']=='cli_call' and e['role']=='patient_review']
    n=3;ri=0;pi=0;prev=None
    def read_block(j,label):
        b=[('Diagnóstico',j.get('diagnosis') or j.get('decision') or ''),('Confiança',str(j.get('confiança') or j.get('confidence','')))]
        if j.get('reasoning'):b.append(('Raciocínio',j['reasoning']))
        return b
    exact=[e for e in ev if e['event']=='followup_result']
    def followup(j,round_no,sweep):
        qs,ts=clean_requests(j.get('missing_questions'),j.get('missing_tests'))
        qtext=list(qs)+([SWEEP_Q] if sweep else [])
        ans=pats[pi]['response']['message']['content'] if pi<len(pats) else ''
        if round_no-1<len(exact):  # exact record: use it as it was received
            txt=exact[round_no-1]['text'];lines=[fmt_output(m.group(1),m.group(2),m.group(3)) for m in (re.match(r"Reviewer test (\w+) '(.*?)': (.*)$",l,re.S) for l in txt.split('\n')) if m]
            qtext=exact[round_no-1].get('questions') or qtext
            a=re.search(r'Patient answers to the reviewer: (.*?)(?:\nReviewer |\Z)',txt,re.S)
            ans=a.group(1).strip() if a else ans
        else:lines=followup_lines(tools,ts) if ts else []
        b=[]
        if qtext:b.append(('Perguntas ao paciente','\n'.join('- '+q for q in qtext)))
        if ans:b.append(('Resposta do paciente',ans))
        if lines:b.append(('Exames que o revisor pediu e o que voltou','\n'.join('• '+l for l in lines)))
        return b
    def blind_name(m):return 'Sonnet 5.5' 
    # first blind read
    if ri<len(reads):
        j=parse(reads[ri]['response']['message']['content']);ri+=1
        steps.append({'t':f'{n} · Sonnet 5.5 às cegas: 1ª leitura (não vê a proposta)','pill':('confiança '+str(j.get('confidence','')),'neutral'),'b':read_block(j,''),'asks':True});n+=1;prev=j
        if any(t.startswith('followup') for t in tokens):
            sweep=any('sweep' in t for t in tokens);b=followup(prev,1,sweep);pi+=1 if (b and any(x[0]=='Resposta do paciente' for x in b)) else 0
            steps.append({'t':f'{n} · Rodada de perguntas e exames do revisor'+(' (inclui a varredura padrão de exposições)' if sweep else ''),'b':b});n+=1
            if ri<len(reads):
                j=parse(reads[ri]['response']['message']['content']);ri+=1;steps.append({'t':f'{n} · Sonnet 5.5 às cegas: 2ª leitura, com as respostas','pill':('confiança '+str(j.get('confidence','')),'neutral'),'b':read_block(j,'')});n+=1;prev=j
        sm=next((e['value'] for e in ev if e['event']=='cascade_step' and e['key']=='same_prop_blind'),None)
        if sm and 'same' in sm:steps.append({'t':f'{n} · JEF: o Sonnet concorda com a proposta?','b':[('Mesma doença (0 a 1)',f"{sm['same']:.2f}")]});n+=1
    if any(t.startswith('escalate:') for t in tokens):
        for k in range(2):
            if ri>=len(reads):break
            j=parse(reads[ri]['response']['message']['content']);ri+=1
            b=[('Diagnóstico',j.get('diagnosis','')),('Confiança',str(j.get('confidence','')))]
            if j.get('features'):b.append(('Achados distintivos e doenças que os caracterizam','\n'.join('- '+f.get('feature','')+' → '+', '.join((f.get('candidates') or f.get('characteristic_of') or [])[:4]) for f in j['features'][:6])))
            if j.get('unexplained'):b.append(('Não explicado',' | '.join(j['unexplained'])))
            if j.get('reasoning'):b.append(('Raciocínio',j['reasoning']))
            steps.append({'t':f'{n} · Opus 5.5, leitura guiada pelos achados ({"1ª, com pedidos" if k==0 else "2ª, depois da rodada própria"})','pill':('escalada: confiança do Sonnet abaixo de 0,5' if k==0 else 'leitura final','warn'),'b':b});n+=1
            if k==0 and any(t=='followup2' for t in tokens):
                b2=followup(j,2,False);pi+=1 if any(x[0]=='Resposta do paciente' for x in b2) else 0
                steps.append({'t':f'{n} · Rodada própria do Opus: perguntas e exames','b':b2});n+=1
            else:break
    elif any(t.startswith('adjudicate:') for t in tokens):
        if ri<len(reads):
            j=parse(reads[ri]['response']['message']['content']);ri+=1
            steps.append({'t':f'{n} · Árbitro (Sonnet 5.5): vê a proposta e a leitura às cegas','pill':({'accept_proposal':'ficou com a proposta do GLM-5','accept_reviewer':'ficou com a leitura às cegas','own':'diagnóstico próprio'}.get(j.get('decision'),str(j.get('decision',''))),'neutral'),'b':[('Decisão',{'accept_proposal':'ficar com a proposta do GLM-5','accept_reviewer':'ficar com a leitura às cegas','own':'diagnóstico próprio'}.get(j.get('decision'),str(j.get('decision','')))),('Diagnóstico',j.get('diagnosis','')),('Raciocínio',j.get('reasoning',''))]});n+=1
    last=tokens[-1]
    why={'accept_blind':'aceitou o revisor às cegas (concorda com a proposta e tem confiança suficiente)','accept_escalation':'aceitou a leitura do Opus (confiança de pelo menos 0,5, sem árbitro)','chose_blind':'o árbitro ficou com a leitura às cegas','chose_proposal':'o árbitro ficou com a proposta do GLM-5','own':'diagnóstico próprio do árbitro'}.get(last,last)
    steps.append({'t':f'{n} · Decisão final','pill':('correto' if str(final['judge_correct'])=='True' else 'errado','ok' if str(final['judge_correct'])=='True' else 'bad'),'b':[('Como foi decidido',why),('Diagnóstico final',final['dx_agent']),('Referência',final['dx_reference'])],'final':True})
    return steps,final
