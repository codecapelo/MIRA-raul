#!/usr/bin/env python3
"""Offline report generator. All inputs read-only; no network/model calls."""
import argparse,csv,hashlib,json,math,sqlite3,statistics
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
MODELS=['openai/gpt-oss-120b','z-ai/glm-4.5-air','z-ai/glm-5','qwen/qwen3.5-397b-a17b','openai/gpt-5.2']
CATEGORY=dict(zip([f'case_{i:03}' for i in range(1,11)],['cardiovascular','cardiovascular','urologic','respiratory_oncology','respiratory_oncology','endocrine_infectious','hematology','neurologic','gastrointestinal','obstetric']))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def judge(s):
 s=str(s).lower().strip();return True if s in ('true','1','correct','yes') else False if s in ('false','0','incorrect','no') else None
def wilson(k,n):
 if not n:return None
 z=1.959963984540054;p=k/n;d=1+z*z/n;c=(p+z*z/(2*n))/d;h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d;return [c-h,c+h]
def quant(v,p):
 v=sorted(v);x=(len(v)-1)*p;i=int(x);return v[i]+(v[min(i+1,len(v)-1)]-v[i])*(x-i)
def stat(v):return {'n':len(v),'median':statistics.median(v),'q1':quant(v,.25),'q3':quant(v,.75)} if v else {'n':0,'median':None,'q1':None,'q3':None}
def operational_failure(row):
 return row.get('status')=='operational_failure' or (not str(row.get('dx_agent','')).strip() and ('notjudged' in str(row.get('judge_rationale','')).lower().replace('_','').replace(' ','') or str(row.get('judge_correct','')).strip()==''))
def score(rows):
 failures=sum(operational_failure(r) for r in rows);v=[judge(r.get('judge_correct')) for r in rows if not operational_failure(r) and judge(r.get('judge_correct')) is not None]
 return {'attempts':len(rows),'completed':len(rows),'operational_failures':failures,'diagnoses_submitted':sum(bool(str(r.get('dx_agent','')).strip()) for r in rows),'judged':len(v),'correct':sum(v),'judge_accuracy':sum(v)/len(v) if v else None,'wilson95':wilson(sum(v),len(v)),'conservative_success_all_terminal_attempts':sum(v)/len(rows) if rows else None}
def write(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def main(root):
 report=root/'reports';report.mkdir(exist_ok=True);p=root/'results/run1.csv';raw=list(csv.DictReader(p.open())) if p.exists() else [];rows=[];seen=set();duplicates=[];hashes={str(p.relative_to(root)):sha(p)} if p.exists() else {}
 for r in raw:
  key=(r['case_id'],r['model'])
  if key in seen:duplicates.append(key);continue
  rows.append(r);seen.add(key)
 calls={};malformed=[]
 for log in sorted(set((root/'logs/raw').glob('**/*.jsonl')) | set((root/'logs/incomplete').glob('**/*.jsonl'))):
  hashes[str(log.relative_to(root))]=sha(log)
  for lineno,line in enumerate(log.read_text().splitlines(),1):
   try:e=json.loads(line)
   except json.JSONDecodeError:malformed.append({'file':str(log),'line':lineno});continue
   rid=e.get('request_id')
   if e.get('event')=='request':calls.setdefault(rid,{}).update({'model':e['payload']['model'],'role':e.get('role'),'case_id':log.stem})
   elif e.get('event')=='response':calls.setdefault(rid,{}).update({'usage':e.get('response',{}).get('usage',{})})
 ledger=[];db=root/'logs/budget.sqlite'
 if db.exists():
  con=sqlite3.connect(f'file:{db}?mode=ro',uri=True);con.row_factory=sqlite3.Row;ledger=[dict(r) for r in con.execute('SELECT * FROM calls')];con.close()
  for e in ledger:
   c=calls.setdefault(e['id'],{});m=json.loads(e.get('metadata') or '{}');c.update({'ledger_cost':e['cost'],'ledger_state':e['state']});c.setdefault('role',m.get('role'));c.setdefault('model',m.get('model'))
 actors=defaultdict(lambda:{'calls':0,'known_cost_usd':Decimal(0),'unknown_cost_calls':0,'prompt_tokens':0,'completion_tokens':0,'reasoning_tokens':0})
 for c in calls.values():
  a=actors[c.get('role') or 'unknown'];u=c.get('usage',{});a['calls']+=1;cost=c.get('ledger_cost') if c.get('ledger_cost') is not None else u.get('cost')
  if cost is None:a['unknown_cost_calls']+=1
  else:a['known_cost_usd']+=Decimal(str(cost))
  for k in ('prompt_tokens','completion_tokens'):a[k]+=int(u.get(k,0) or 0)
  a['reasoning_tokens']+=int(u.get('completion_tokens_details',{}).get('reasoning_tokens',0) or 0)
 for a in actors.values():a['known_cost_usd']=str(a['known_cost_usd'])
 model_results=[];projection=[]
 for m in MODELS:
  rr=[r for r in rows if r['model']==m];s={'model':m,'expected':10,**score(rr)};s['categories']={c:score([r for r in rr if CATEGORY.get(r['case_id'])==c]) for c in sorted(set(CATEGORY.values()))};s['usage']={k:stat([float(r[k]) for r in rr if r.get(k)]) for k in ('prompt_tokens','completion_tokens','reasoning_tokens','latency_s')};model_results.append(s)
  pilot=[r for r in rr if r['case_id']=='case_001'];costs=[Decimal(r['cost_usd']) for r in pilot if r.get('cost_usd')];total=sum(costs,Decimal(0));projection.append({'model':m,'pilot_completed':len(pilot),'pilot_terminal_attempts':len(pilot),'pilot_operational_failures':sum(operational_failure(r) for r in pilot),'pilot_judged':score(pilot)['judged'],'pilot_providers':sorted({r.get('provider','unknown') for r in pilot}),'pilot_cost_usd':str(total) if costs else None,'projected_10x1_usd':str(total*10/len(costs)) if costs else None,'projected_10x5_usd':str(total*50/len(costs)) if costs else None})
 old=root/'legacy/outputs/benchmark/results/frontier_addons_2026-09-29/summaries/frontier_addons_analysis.json';historical={}
 if old.exists():
  d=json.loads(old.read_text());historical={'path':str(old),'sha256':sha(old),'expected_trajectories':d['expected_trajectories'],'observed_terminal_trajectories':d['observed_terminal_trajectories'],'models_original':d['models'],'evaluation_original':d['evaluation'],'physician_review_state_original':d['physician_review_state']}
 expected=[(c.name,m) for c in sorted((root/'cases').glob('case_*')) for m in MODELS]
 result={'schema_version':'1.0.0','completed_rows':len(rows),'terminal_attempts':len(rows),'operational_failures':sum(operational_failure(r) for r in rows),'judged_rows':sum(not operational_failure(r) and judge(r.get('judge_correct')) is not None for r in rows),'expected_rows':len(expected),'missing_pairs':[k for k in expected if k not in seen],'duplicates':duplicates,'malformed_raw_log_lines':malformed,'models':model_results,'actor_breakdown_including_incomplete':dict(actors),'ledger_known_cost_usd':str(sum((Decimal(e['cost']) for e in ledger if e['cost'] is not None),Decimal(0))),'csv_known_cost_usd':str(sum((Decimal(r['cost_usd']) for r in rows if r.get('cost_usd')),Decimal(0))),'unsettled_calls':[{'id':e['id'],'state':e['state'],'reserved':e['reserved'],'known_cost':e['cost']} for e in ledger if e['state']!='settled'],'legacy_lexical_comparison':historical,'physician_review':'pending','input_sha256':hashes,'category_note':'Manually assigned broad descriptive groups, not upstream strata.'}
 write(report/'run1_summary.json',result);proj={'models':projection,'pilot_expected':5,'pilot_completed':sum(x['pilot_completed'] for x in projection),'known_all_calls_usd':result['ledger_known_cost_usd'],'unsettled_calls':result['unsettled_calls'],'assumption':'Linear extrapolation from case001 with patient/judge/matcher included; complexity differs. Projection is not execution authorization.'};write(report/'cost_projection.json',proj)
 if proj['pilot_completed']==5 and not (report/'pilot_cost_projection.json').exists():write(report/'pilot_cost_projection.json',proj)
 lines=['# Run1: julgamento LLM, revisão médica pendente','',f"Tentativas terminais {len(rows)}/{len(expected)}, incluindo {result['operational_failures']} falhas operacionais; julgamentos clínicos válidos: {result['judged_rows']}. Ausências explicitadas no JSON.",'','| Modelo | Tentativas terminais | Falhas operacionais | Corretos/julgados | Wilson 95% |','|---|---:|---:|---:|---|']
 for s in model_results:
  ci=s['wilson95'];lines.append(f"| {s['model']} | {s['attempts']}/10 | {s['operational_failures']} | {s['correct']}/{s['judged']} | {f'{ci[0]:.1%}–{ci[1]:.1%}' if ci else 'indisponível'} |")
 lines+=['',f"Custo conhecido ledger: US$ {result['ledger_known_cost_usd']}; CSV terminal: US$ {result['csv_known_cost_usd']}. Custos de tentativas incompletas aparecem no detalhamento por ator. Chamadas não liquidadas impedem presumir total final.",'','Mediana/IQR de tokens e latência, intervalos por categoria e pares ausentes estão no JSON. Tokens de raciocínio são subconjunto da conclusão; não somar novamente. Grupos clínicos descritivos possuem denominadores pequenos.','', 'O juiz LLM avalia equivalência diagnóstica. A análise antiga é lexical, com outros modelos, transporte, ferramentas e três repetições. Não há comparação de superioridade clínica. Revisão médica cega pendente. Repetições não são pacientes independentes.']
 if historical:lines+=['',f"Histórico imutável: {historical['observed_terminal_trajectories']}/{historical['expected_trajectories']} trajetórias, métricas originais de todos os modelos preservadas no JSON. Fonte `{old}`, SHA-256 `{historical['sha256']}`."]
 lines+=['', '## Custo e consumo por modelo', '', 'Custos por modelo abaixo somam tentativas terminais, inclusive falhas operacionais, incluindo todos os atores. O custo global por ator inclui também tentativas incompletas; por isso pode exceder esta soma.', '', '| Modelo | Episódios | Custo total US$ | Custo médio US$ | Tokens totais mediana [Q1; Q3] | Prompt mediana [Q1; Q3] | Conclusão mediana [Q1; Q3] | Raciocínio mediana [Q1; Q3] |', '|---|---:|---:|---:|---|---|---|---|']
 def fmtstat(v):return 'indisponível' if not v['n'] else f"{v['median']:,.0f} [{v['q1']:,.0f}; {v['q3']:,.0f}]"
 for model in MODELS:
  rr=[r for r in rows if r['model']==model];cc=[Decimal(r['cost_usd']) for r in rr if r.get('cost_usd')];total=sum(cc,Decimal(0));usage=next(x['usage'] for x in model_results if x['model']==model);totals=stat([float(r['prompt_tokens'])+float(r['completion_tokens']) for r in rr if r.get('prompt_tokens') and r.get('completion_tokens')]);mean=f"{total/len(cc):.6f}" if cc else 'indisponível'
  lines.append(f"| {model} | {len(rr)} | {total:.6f} | {mean} | {fmtstat(totals)} | {fmtstat(usage['prompt_tokens'])} | {fmtstat(usage['completion_tokens'])} | {fmtstat(usage['reasoning_tokens'])} |")
 lines+=['', '## Categorias e casos', '', 'Falhas operacionais são tentativas terminais, sem diagnóstico/julgamento; não viram decisão falsa do juiz. Cada linha tem seu próprio denominador; Wilson é calculado sobre julgamentos válidos. Categorias amplas foram atribuídas manualmente e não correspondem aos estratos do artigo.', '', '| Modelo | Categoria | Tentativas | Corretos/julgados | Wilson 95% |', '|---|---|---:|---:|---|']
 def fmtci(ci):return f"{ci[0]:.1%}–{ci[1]:.1%}" if ci else 'indisponível'
 for model in model_results:
  for cat,val in model['categories'].items():lines.append(f"| {model['model']} | {cat} | {val['completed']} | {val['correct']}/{val['judged']} | {fmtci(val['wilson95'])} |")
 lines+=['', '| Caso | Categoria | Tentativas | Corretos/julgados entre modelos | Wilson 95% |', '|---|---|---:|---:|---|']
 for cid,cat in CATEGORY.items():
  val=score([r for r in rows if r['case_id']==cid]);lines.append(f"| {cid} | {cat} | {val['completed']}/5 | {val['correct']}/{val['judged']} | {fmtci(val['wilson95'])} |")
 lines+=['', 'Os intervalos por caso agrupam cinco configurações diferentes, sendo apenas descritivos; os modelos compartilham o mesmo caso e não são cinco pacientes independentes.', '', '## Comparação histórica lexical', '', '| Modelo histórico | Trajetórias observadas/previstas | Conceitos publicados encontrados/observados | Média lexical por caso |', '|---|---:|---:|---:|']
 for name,val in historical.get('models_original',{}).items():
  matches=sum(c.get('concept_matches',0) for c in val.get('cases',{}).values());metric=val.get('metrics',{}).get('published_diagnosis_concept_match',{}).get('case_mean');mean=f"{metric:.1%}" if metric is not None else 'indisponível';lines.append(f"| {name} | {val.get('observed_runs','?')}/{val.get('expected_runs','?')} | {matches}/{val.get('observed_runs','?')} | {mean} |")
 lines+=['', 'Valores históricos são transcritos do relatório congelado, sem reexecução do avaliador lexical. Média por caso e proporção por trajetória podem diferir com repetições ausentes. Juiz LLM e correspondência lexical são medidas distintas: não inferir superioridade ou acurácia clínica.']
 fidelity=root/'reports/patient_fidelity_case001_gptoss.md'
 if fidelity.exists():
  lines+=['', '## Fidelidade do paciente simulado', '', '**Falha documentada em GPT-OSS/case_001:** o paciente inventou características de dor, horário/intensidade, frequência de diálise e negativa de alergia; o médico usou elementos inventados na justificativa de STEMI. Zero erros de ferramenta não garante fidelidade narrativa. O erro e seu custo foram preservados; não foi excluído nem reexecutado.', '', 'A conclusão deste episódio reflete contaminação da narrativa simulada e extrapolação do médico. A fidelidade dos demais modelos requer análise própria. Evidência detalhada: [patient_fidelity_case001_gptoss.md](patient_fidelity_case001_gptoss.md). Revisão documental; revisão médica assinada pendente.'];result['patient_fidelity_warning']={'path':str(fidelity),'sha256':sha(fidelity),'case_id':'case_001','model':'openai/gpt-oss-120b','observed_failure':True};write(report/'run1_summary.json',result)
 (report/'run1_summary.md').write_text('\n'.join(lines)+'\n');(report/'summary.md').write_text('\n'.join(lines)+'\n')
 costlines=['# Custos observados e projeção','',f"Piloto: {proj['pilot_completed']}/5 tentativas terminais, um caso por modelo, inclusive falhas operacionais. Valores reais provenientes do CSV; custos conhecidos de todas as chamadas provenientes do ledger.",'', '| Modelo | Provedor observado | Piloto real US$ | 10 casos × 1 execução US$ | 10 casos × 5 execuções US$ |','|---|---|---:|---:|---:|']
 for item in projection:
  display=lambda key: f"{Decimal(item[key]):.6f}" if item[key] is not None else 'pendente'
  costlines.append(f"| {item['model']} | {', '.join(item['pilot_providers']) or 'pendente'} | {display('pilot_cost_usd')} | {display('projected_10x1_usd')} | {display('projected_10x5_usd')} |")
 costlines+=['',f"Custo total conhecido, incluindo tentativas arquivadas/incompletas: US$ {result['ledger_known_cost_usd']}. Total das tentativas terminais: US$ {result['csv_known_cost_usd']}.",'', '| Ator | Chamadas | Custo conhecido US$ | Chamadas sem custo resolvido |','|---|---:|---:|---:|']
 for role,a in sorted(actors.items()):costlines.append(f"| {role} | {a['calls']} | {a['known_cost_usd']} | {a['unknown_cost_calls']} |")
 costlines+=['',f"Chamadas não liquidadas: {len(result['unsettled_calls'])}; detalhes e reservas no JSON. Logs atuais e logs/incomplete são agregados por request_id, sem duplicar chamadas presentes nos dois locais.",'', 'Projeção linear baseada nas cinco tentativas terminais do caso 001, incluindo falhas sem diagnóstico; não exige cinco diagnósticos nem representa custo de sucesso clínico. Inclui médico, paciente, juiz e matcher quando usados. Casos mais complexos e alterações de preço/provedor modificam o custo. Projeções futuras não incorporam novamente custos históricos de tentativas incompletas e não autorizam novas execuções. Provedor observado vem do CSV de cada episódio.']
 (report/'cost_projection.md').write_text('\n'.join(costlines)+'\n')
 print(json.dumps({'completed':len(rows),'expected':len(expected),'reports':str(report)}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);main(p.parse_args().root)
