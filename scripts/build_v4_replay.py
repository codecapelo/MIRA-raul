from pathlib import Path
import json,hashlib,time,argparse
ap=argparse.ArgumentParser(description='Refresh only public replay data in the v4 artifact')
ap.add_argument('--base',type=Path,default=Path(__file__).resolve().parents[1])
ap.add_argument('--artifact',type=Path)
a=ap.parse_args()
BASE=a.base.resolve()
LABEL={'consult_map':'Mapa inicial','doctor':'Médico simulado','patient':'Paciente simulado','patient_review':'Paciente responde ao revisor','review_codex':'Revisão cega','working_final_review':'Astra · hipótese de trabalho','matcher':'Associador de exames','judge':'Juiz final · só metadados','judge_proposal':'Juiz da proposta · só metadados'}
def clip(v,n=520):
 s=v if isinstance(v,str) else json.dumps(v,ensure_ascii=False)
 return (s[:n]+' […] [trecho truncado]' if len(s)>n else s),len(s)>n

def build(p):
 raw=p.read_bytes();lines=raw.splitlines();ev=[];tail_omitted=False
 for index,line in enumerate(lines):
  if not line.strip():continue
  try:ev.append(json.loads(line))
  except json.JSONDecodeError:
   if index==len(lines)-1:tail_omitted=True
   else:raise
 if not ev:raise ValueError('No complete public events: '+p.name)
 start=float(next(e['time'] for e in ev if e['event']=='protocol_config'));end=max(float(e['time']) for e in ev);out=[]
 def add(e,i,title,kind='instant',begin=None,preview='',estimated=False,cost=None,units=None,pending=False):
  t=float(e['time']);txt,trunc=clip(preview)
  out.append({'id':f'L{i}','line':i,'title':title,'actor':e.get('role','sistema'),'model':e.get('model'),'kind':kind,'start':t if begin is None else float(begin),'end':t,'duration_s':0 if begin is None else round(t-float(begin),6),'estimated_start':estimated,'preview':txt,'truncated':trunc,'cost_usd':cost,'units':units,'pending':pending})
 reqs={e['request_id']:(i,e) for i,e in enumerate(ev,1) if e['event']=='request'};paired=set();released_seen={}
 for i,e in enumerate(ev,1):
  k=e['event'];role=e.get('role','');tm=float(e['time'])
  if k=='protocol_config':add(e,i,'Início do protocolo','protocol',preview='Configuração da condição registrada; execução do teste, não tempo assistencial.')
  elif k=='cli_call':
   msg=e.get('response',{}).get('message',{});text=msg.get('content') or '';calls=msg.get('tool_calls') or []
   if calls:text+='\nAções JSON: '+', '.join(c.get('function',{}).get('name','') for c in calls)
   latency=float(e.get('latency_s') or 0)
   add(e,i,LABEL.get(role,role),'cli',tm-latency,text,True)
   out[-1]['duration_s']=latency;out[-1]['end']=tm
  elif k=='response':
   req=reqs.get(e.get('request_id'));paired.add(e.get('request_id'));begin=float(req[1]['time']) if req else tm
   resp=e.get('response') or {};usage=resp.get('usage') or {};cost=usage.get('cost')
   preview='Texto e referência do juiz omitidos. Somente horário, duração e custo API.' if role.startswith('judge') else 'Solicitação e resposta API pareadas pelo request_id; conteúdo de entrada omitido.'
   add(e,i,'API · '+LABEL.get(role,role),'api',begin,preview,cost=cost)
   out[-1]['request_line']=req[0] if req else None;out[-1]['model']=resp.get('model')
   out[-1]['exact_start']=bool(req)
  elif k=='exam_cost':
   # Accounting evidence is not a tool.output; do not reconstruct queued findings.
   actor=e.get('actor') or 'sistema';tool=e.get('tool') or 'não informado'
   charges=[{'name':c.get('name','fonte sem nome'),'relative_units':c.get('relative_units'),'actor':c.get('actor')} for c in (e.get('charges') or []) if isinstance(c,dict)]
   note='Estes eventos podem repetir em retomada; o total canônico case_complete não é a soma destes registros.'
   preview=note+'\nRegistro contábil instantâneo; não é tool.output e não reconstrói resultados liberados pela fila.\nAtor: '+str(actor)+' | ferramenta: '+str(tool)+'\nUnidades neste registro: '+str(e.get('relative_units'))+' | acumulado registrado: '+str(e.get('cumulative_relative_units'))
   if charges:preview+='\nFontes: '+'; '.join(str(c['name'])+' ('+str(c['relative_units'])+' unidades)' for c in charges)
   add(e,i,'Contabilidade de exames · '+str(tool),'accounting',preview=preview,units=e.get('relative_units'))
   out[-1]['actor']=actor;out[-1]['tool']=tool;out[-1]['charges']=charges;out[-1]['cumulative_relative_units']=e.get('cumulative_relative_units');out[-1]['accounting_note']=note
  elif k=='tool':
   name=e.get('name','');output=e.get('output') or ''
   if name=='admission':
    arguments=e.get('arguments') or {};text='Proposta: '+str(arguments.get('diagnosis',''))+'\n'+str(output)
    add(e,i,'Admissão · proposta/retorno','admission',preview=text)
   else:add(e,i,'Ferramenta · '+name,'tool',preview=output)
  elif k=='released_results':
   text=e.get('text','');digest=hashlib.sha256(text.encode()).hexdigest()
   if digest!=e.get('content_sha256'):raise ValueError('Released-results audit hash mismatch')
   slot=(e.get('turn'),e.get('exchanges'),e.get('delivery'))
   if slot in released_seen:
    if released_seen[slot]!=digest:raise ValueError('Released-results audit delivery changed')
    continue
   released_seen[slot]=digest
   add(e,i,'Resultados liberados ao médico','tool',preview=text)
   out[-1]['content_sha256']=digest;out[-1]['delivery']=e.get('delivery')
   out[-1]['turn']=e.get('turn');out[-1]['exchanges']=e.get('exchanges')
   out[-1]['source_basis']='Texto exato registrado ao entregar release(); não reconstruído de exam_cost'
  elif k=='followup_result':add(e,i,'Rodada complementar obtida','followup',preview=e.get('text',''))
  elif k=='working_final_review':add(e,i,'Hipótese de trabalho registrada','working',preview=e.get('diagnosis','')+'\n'+e.get('reasoning',''))
  elif k=='case_complete':
   r=e.get('result',{});add(e,i,'Terminal case_complete','terminal',preview='Diagnóstico do agente: '+str(r.get('dx_agent',''))+'\nJuiz LLM: '+('positivo' if r.get('judge_correct') is True else 'negativo' if r.get('judge_correct') is False else 'não informado'))
   out[-1]['cost_usd']=r.get('cost_usd');out[-1]['units']=(r.get('exam_cost_relative') or {}).get('relative_units');out[-1]['cost_basis']='total canônico do encontro, não somar às chamadas'
 for request_id,(i,e) in reqs.items():
  if request_id not in paired:
   add(dict(e,time=end),i,'API · '+LABEL.get(e.get('role'),e.get('role'))+' · sem resposta registrada','api_pending',float(e['time']),'Solicitação registrada sem resposta neste snapshot. Não assumir custo zero.',pending=True)
   out[-1]['duration_s']=None
 intervals=sorted((max(start,e['start']),e['end']) for e in out)
 merged=[]
 for a,b in intervals:
  if merged and a<=merged[-1][1]:merged[-1][1]=max(merged[-1][1],b)
  else:merged.append([a,b])
 gaps=[]
 for (_,a),(b,_) in zip(merged,merged[1:]):
  if b-a>120:
   gaps.append({'start':a,'end':b,'duration_s':b-a})
   out.append({'id':f'gap_{len(gaps)}','line':None,'title':'Intervalo sem chamada registrada','actor':'intervalo','model':None,'kind':'gap','start':a,'end':b,'duration_s':b-a,'estimated_start':False,'preview':'Há intervalo entre eventos, inclusive retomada após cota em alguns casos. O trace não permite atribuir toda essa duração a inferência. Compressão opcional muda só a reprodução; o relógio real é preservado.','truncated':False,'cost_usd':None,'units':None,'pending':False})
 out.sort(key=lambda e:(e['start'],e['end'],e['line'] or 0))
 return {'case_id':p.stem,'source':str(p.relative_to(BASE)),'sha256':hashlib.sha256(raw).hexdigest(),'start':start,'end':end,'duration_s':end-start,'terminal_observed':any(e['event']=='case_complete' for e in ev),'raw_event_count':len(ev),'incomplete_tail_omitted':tail_omitted,'events':out,'gaps':gaps}
trials=[]
for tid,path,label in [('original','runs/v4/sol/run1/logs/raw/gpt-6.1-sol','v4 original'),('working','runs/v4/sol_working/run1/logs/raw/gpt-6.1-sol','Candidata · hipótese de trabalho Astra')]:
 cases=[build(p) for p in sorted((BASE/path).glob('case_*.jsonl')) if p.stem in {f'case_{i:03}' for i in range(1,11)}]
 trials.append({'id':tid,'label':label,'status':'original congelada' if tid=='original' else ('10 encontros completos; ver escore no relatório' if len(cases)==10 and all(c['terminal_observed'] for c in cases) else 'snapshot parcial; validação pendente'),'cases':cases})
replay={'schema_version':1,'timezone':'America/Fortaleza','snapshot_unix':time.time(),'gap_threshold_s':120,'compressed_gap_display_s':4,'trials':trials,'notes':['Os relógios mostram execução do teste, não duração clínica de atendimento.','Eventos CLI registram fim e latência; início calculado por subtração é estimado. API usa request e response do mesmo ID.','Conteúdo de entrada, referência, critérios e justificativas dos juízes não são exportados. Trechos clínicos públicos são truncados explicitamente.','Custo de chamadas API e custo total terminal são bases distintas; não somar ambos. Custo monetário da assinatura desconhecido.','Eventos exam_cost são registros contábeis instantâneos, podem repetir em retomada e não substituem tool.output. Total canônico case_complete não é a soma destes registros.']}

import re
html_path=(a.artifact or BASE/'reports/v4_comparison.html').resolve()
html=html_path.read_text()
m=re.search(r'(<script id="mira-data" type="application/json">)([\s\S]*?)(</script>)',html)
if not m: raise SystemExit('DATA JSON not found; no file modified')
data=json.loads(m.group(2))
data['replay']=replay
encoded=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
updated=html[:m.start(2)]+encoded+html[m.end(2):]
if len(updated.encode())>=1_000_000: raise SystemExit('Artifact exceeds 1 MB; no file modified')
html_path.write_text(updated)
print(json.dumps({'file':str(html_path),'bytes':len(updated.encode()),'trials':[{'id':t['id'],'cases':len(t['cases']),'terminals_observed':sum(c['terminal_observed'] for c in t['cases'])} for t in trials],'other_data_preserved':True},ensure_ascii=False))
