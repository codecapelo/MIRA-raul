"""Add the GLM 5.3 Flash doctor phase (the frozen v6.3 doctor phases) to the local dialogue page, with the proposals marked right or wrong.

  python3 scripts/dialogos_glm_section.py --base <data worktree> --html runs/v5/dialogos_v63_local.html [--arms-json v63_now.json]

What it does (local, read-only on the traces; no request is sent):
- for each of the 8 v6.3 cases it takes the doctor-patient exchange already rendered in the page (`case_XXX__opus63`: the Opus arm IS the source encounter of the frozen doctor phase) up to the first reviewer card, and publishes it as its own section `case_XXX__glm63`, with a card on top that shows the doctor's proposal (before any reviewer), the reference diagnosis, the proposal judge's decision and rationale, and the path (calls, exchanges, orders, doctor cost and time);
- adds `glm63__resumo`: right/wrong proposals of the 8 frozen phases, how many reviewer arms ended accepted, and every GLM 5.3 run on those cases (right / wrong / no verdict);
- adds a nav group. Running it again replaces its own sections and keeps a backup of the original page next to it (`*.before_glm63.html`).
The page is git-ignored and holds closed-case text: it stays local.
"""
import argparse,html,json,re,sys
from collections import defaultdict
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent/'src')]
from run_v63_reviewers import SOURCES
from mira_v6.frozen_doctor import DOCTOR_DIR
import doctor_cost_analysis as dca

CASES=['case_001','case_002','case_003','case_004','case_005','case_011','case_017','case_018']
CLOSED={'case_011','case_017','case_018'}
ARM_KEYS=['opus','sonnet','sol62','astra62','kimi','both']
E=lambda s:html.escape(str(s),quote=True)

def mark(v):return '<span class="ok">✓ certa</span>' if v is True else ('<span class="bad">✕ errada</span>' if v is False else '<span>sem veredito</span>')

def source_facts(base,case):
    p=Path(base)/'runs/v5/v6_qwen'/SOURCES[case]/'run1/logs/raw'/DOCTOR_DIR/f'{case}.jsonl'
    ev=[json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    res=next(e['result'] for e in ev if e['event']=='case_complete')
    snap_i=next(i for i,e in enumerate(ev) if e['event']=='proposal_snapshot');snap=ev[snap_i]
    req={e['request_id']:e for e in ev if e['event']=='request'}
    docs=[e for e in ev[:snap_i] if e['event']=='response' and e.get('role')=='doctor']
    cost=sum(float(((e['response'].get('usage') or {}).get('cost')) or 0) for e in docs)
    wait=sum(float(e['time'])-float(req[e['request_id']]['time']) for e in docs if e['request_id'] in req)
    jp=None
    for e in ev:
        if e['event']=='response' and e.get('role')=='judge_proposal':
            try:jp=json.loads(e['response']['choices'][0]['message'].get('content') or '{}')
            except Exception:jp={}
    prop=snap.get('diagnosis') or res.get('proposal_dx') or ''
    return {'variant':SOURCES[case],'proposal':prop,'reference':res.get('dx_reference') or '','proposal_correct':res.get('proposal_correct') if isinstance(res.get('proposal_correct'),bool) else None,
            'final_correct':res.get('judge_correct') if isinstance(res.get('judge_correct'),bool) else None,'judge_reasoning':(jp or {}).get('reasoning',''),'judge_decision':(jp or {}).get('decision'),
            'calls':len(docs),'exchanges':res.get('patient_exchanges'),'orders':res.get('investigation_orders'),'cost':cost,'wait_s':wait}

def doctor_phase_html(section_html):
    a=section_html.index('</div>',section_html.index('<div class="top">'))+6
    k=section_html.index('class="card rev');st=section_html.rfind('<div',0,k)
    return section_html[a:st]

def verdict_card(case,f,accepted):
    pc=f['proposal_correct'];tag='ok' if pc else 'bad'
    dec={True:'aceitou',False:'rejeitou',None:'sem decisão'}[f['judge_decision'] if isinstance(f['judge_decision'],bool) else None]
    arms=(f'{accepted[0]} de {accepted[1]} braços de revisor terminaram com o diagnóstico final aceito' if accepted else '')
    return (f'<div class="card final"><div class="ch"><span class="ico">⚖️</span><b>Proposta do médico (antes de qualquer revisor)</b><span class="tag {tag}">proposta: {"certa" if pc else ("errada" if pc is False else "sem veredito")}</span></div>'
            f'<div class="kv"><span class="k">proposta do GLM 5.3 Flash (registrada na admissão)</span><p class="dx">{E(f["proposal"])}</p></div>'
            f'<div class="kv"><span class="k">diagnóstico de referência</span><p>{E(f["reference"])}</p></div>'
            f'<div class="kv"><span class="k">juiz da proposta (Gemini 3.1 Pro): {dec}</span><p>{E(f["judge_reasoning"]) or "sem justificativa registrada"}</p></div>'
            f'<div class="kv"><span class="k">percurso até a proposta</span><p>{f["calls"]} chamadas do médico · {f["exchanges"]} falas do paciente · {f["orders"]} pedidos de exame · US$ {f["cost"]:.4f} · ≈ {f["wait_s"]:.0f} s esperando o modelo</p></div>'
            f'<p class="note">Os revisores não veem esta proposta nem o juiz. {E(arms)}. A conversa abaixo é a fase do médico que foi congelada e reaproveitada nos seis braços de revisor da v6.3.</p></div>')

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__.split('\n')[0]);ap.add_argument('--base',type=Path,required=True);ap.add_argument('--html',type=Path,required=True);ap.add_argument('--arms-json',type=Path);a=ap.parse_args(argv)
    s=a.html.read_text(encoding='utf-8')
    bak=a.html.with_name(a.html.stem+'.before_glm63.html')
    if not bak.exists():bak.write_text(s,encoding='utf-8')
    # remove a previous run of this script
    s=re.sub(r'<section id="(?:glm63__resumo|case_\d+__glm63)".*?</section>\n?','',s,flags=re.S);s=re.sub(r'<div class="grp" data-glm63>.*?</div>(?=<div class="grp"|</nav>)','',s,flags=re.S)
    arms={}
    if a.arms_json and a.arms_json.exists():arms=json.loads(a.arms_json.read_text())
    facts={c:source_facts(a.base,c) for c in CASES}
    acc={}
    for c in CASES:
        got=[arms.get(k,{}).get('per_case',{}).get(f'{c}#1',{}).get('judge') for k in ARM_KEYS];acc[c]=(sum(1 for g in got if g),len([g for g in got if g is not None])) if arms else None
    # all GLM 5.3 runs on these cases
    led=dca.ledgers(a.base);rows=dca.collect(a.base,led,'z-ai/glm-5.3-flash');runs=defaultdict(dict)
    for r in rows:runs[(r['root'],r['variant'],r['case'])]['calls']=runs[(r['root'],r['variant'],r['case'])].get('calls',0)+1
    for (root,var,case) in list(runs):
        p=Path(a.base)/'runs/v5'/root/var/'run1/logs/raw'/DOCTOR_DIR/f'{case}.jsonl'
        if not p.exists():
            q=next((Path(a.base)/'runs/v5'/root/var/'run1/logs/raw').glob(f'*/{case}.jsonl'),None);p=q
        res=next((json.loads(l)['result'] for l in p.read_text().splitlines() if '"case_complete"' in l and json.loads(l)['event']=='case_complete'),None) if p else None
        runs[(root,var,case)]['pc']=res.get('proposal_correct') if res and isinstance(res.get('proposal_correct'),bool) else None;runs[(root,var,case)]['term']=bool(res)
    sections=[];nav=['<div class="grp" data-glm63><b>Médico GLM 5.3 · propostas</b><a href="#glm63__resumo" data-c="glm63__resumo"><span>certas e erradas</span></a>']
    for c in CASES:
        m=re.search(rf'<section id="{c}__opus63".*?</section>',s,flags=re.S)
        if not m:print('sem seção opus63 para',c);continue
        f=facts[c];top=(f'<div class="top"><h2>Caso {c[-3:]}</h2><span class="tag arm">GLM 5.3 Flash · médico congelado da v6.3</span><span class="tag">{"fechado" if c in CLOSED else "público"}</span>'
                        f'<span class="tag {"ok" if f["proposal_correct"] else "bad"}">proposta: {"certa" if f["proposal_correct"] else "errada"}</span><span class="stat">{f["exchanges"]} falas do paciente · {f["orders"]} pedidos de exame · {f["calls"]} chamadas do médico</span></div>')
        sections.append(f'<section id="{c}__glm63" class="case" hidden>{top}\n{verdict_card(c,f,acc[c])}\n{doctor_phase_html(m.group(0))}</section>\n'.replace(f'id="{c}__glm63"',f'id="{c}__glm63"'))
        nav.append(f'<a href="#{c}__glm63" data-c="{c}__glm63"><span>Caso {c[-3:]}</span><i class="{"ok" if f["proposal_correct"] else "bad"}">{"✓" if f["proposal_correct"] else "✕"}</i></a>')
    nav.append('</div>')
    # summary
    tr=[]
    for c in CASES:
        f=facts[c];allr=[(v,d) for (root,v,cc),d in sorted(runs.items()) if cc==c and d.get('term')]
        okn=sum(1 for _,d in allr if d['pc'] is True);nn=sum(1 for _,d in allr if d['pc'] in (True,False))
        chips=' '.join(f'<span class="{"ok" if d["pc"] else ("bad" if d["pc"] is False else "")}" title="{E(v)}">{"✓" if d["pc"] else ("✕" if d["pc"] is False else "·")}</span>' for v,d in allr)
        tr.append(f'<tr><td><a href="#{c}__glm63">{c[-3:]}</a><br><span class="stat">{"fechado" if c in CLOSED else "público"}</span></td><td>{mark(f["proposal_correct"])}</td><td>{E(f["proposal"])}</td><td>{E(f["reference"])}</td>'
                  f'<td>{(str(acc[c][0])+" de "+str(acc[c][1])) if acc[c] else "—"}</td><td>{f["calls"]} / {f["exchanges"]} / {f["orders"]}</td><td>{okn} de {nn}<br><span style="letter-spacing:2px">{chips}</span></td></tr>')
    right=sum(1 for c in CASES if facts[c]['proposal_correct'])
    summ=(f'<section id="glm63__resumo" class="case" hidden><div class="top"><h2>Médico GLM 5.3 Flash: propostas certas e erradas</h2><span class="tag arm">fase do médico congelada da v6.3</span><span class="tag {"ok" if right>=6 else "bad"}">{right} de {len(CASES)} propostas certas</span></div>'
          f'<p class="intro">A proposta é o diagnóstico que o médico registra ao admitir, <b>antes de qualquer revisor</b>, julgado contra a referência pelo Gemini 3.1 Pro (juiz de proposta). Esta é a fase do médico que os seis revisores da v6.3 receberam igual: o que muda entre os braços vem só do revisor. Clique no número do caso para ver a conversa inteira.</p>'
          f'<table class="cmp"><thead><tr><th>Caso</th><th>Proposta</th><th>O que o médico propôs</th><th>Referência</th><th>Revisores com final aceito (dos que terminaram)</th><th>Chamadas / falas / exames</th><th>Todas as rodadas do GLM 5.3 neste caso</th></tr></thead><tbody>{"".join(tr)}</tbody></table>'
          f'<p class="note">Última coluna: cada símbolo é um encontro do GLM 5.3 como médico em gerações diferentes do pipeline (✓ proposta certa, ✕ errada, · sem veredito do juiz); passe o mouse para ver a variante. São casos conhecidos, uma execução por encontro, juiz LLM e sem revisão médica: não mede conhecimento clínico nem generaliza.</p></section>\n')
    sections.insert(0,summ)
    a_=s.index('<section id="v63__resumo"');b_=s.index('</section>',a_)+len('</section>')
    s=s[:b_]+'\n'+''.join(sections)+s[b_:]
    n=s.index('<nav>')+len('<nav>');s=s[:n]+''.join(nav)+s[n:]
    a.html.write_text(s,encoding='utf-8');print('ok',a.html,len(s),'bytes; secoes novas',len(sections),'; backup',bak.name)
    print({c:(facts[c]['proposal_correct'],acc[c]) for c in CASES})

if __name__=='__main__':main()
