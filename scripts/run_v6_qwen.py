"""Qwen4 Max in a reviewer slot of the v6 arm (doctor chosen with --doctor, default GLM 5.3 Flash; Gatekeeper v6 desk, v5 pipeline otherwise).

  python3 scripts/run_v6_qwen.py --base <worktree with cases, upstream and the v5 code> --slot first --smoke --execute     # one tiny call: provider, reasoning text, cost
  python3 scripts/run_v6_qwen.py --base <...> --slot first --cases case_011 --execute

Slots: `first` = Qwen4 Max (OpenRouter, Alibaba, reasoning effort high, thinking kept in the response event) in the place of Sonnet 5.5, Opus 5.5 high by subscription as the final reviewer;
`final` = Sonnet 5.5 first, Qwen4 Max last; `both` = Qwen4 Max in both slots (the only reviewer, no Claude reviewer); `opus` = Opus 5.5 high (subscription) in both slots (the only reviewer); `kimi` = Kimi K3.1 Pro (OpenRouter, Moonshot AI first-party mxfp4, reasoning high) in both slots. Everything else is v6 unchanged (patient Sonnet 5.5, associador, strict matcher, judge, prompts, protocol, desk). The Fable 5.2 slot of v6 is Opus 5.5 here (user decision), so this arm differs from v6 in the reviewer models only.
Own ledger and cap (<base>/runs/v5/v6_qwen/budget.sqlite, default cap USD 0.60, raised only by the user). One execution per case; terminal encounters are skipped; no automatic retries. Traces under runs/v5 (Git-ignored); closed-case content never reaches the terminal.
Sampling for Qwen4 Max is the provider default.
"""
import argparse,fcntl,json,os,re,subprocess,sys
from decimal import Decimal
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent/'src')]
import run_v6 as r6
import run_v6_doctor as d6

QWEN='qwen/qwen4-max'
ROUTE={'provider':'alibaba','provider_name':'Alibaba','pricing_verified':True,'context_tokens':0,'context_limit':1000000,'max_tokens':16000,'usd_per_million':{'input':1.425,'output':4.275},'supports_logprobs':False,
       'supported_parameters':['reasoning','reasoning_effort','include_reasoning','temperature','seed','tools','tool_choice','max_tokens','top_p','response_format','stream'],
       'note':'Alibaba only endpoint (qwen/qwen4-max-20261115), quantization not reported; price checked on the OpenRouter endpoint listing 17-11-2026'}
KIMI='moonshotai/kimi-k3.1-pro'
ROUTE_KIMI={'provider':'moonshotai/mxfp4','provider_name':'Moonshot AI','pricing_verified':True,'context_tokens':0,'context_limit':1048576,'max_tokens':16000,'usd_per_million':{'input':2.0,'output':10.0},'supports_logprobs':False,
            'supported_parameters':['reasoning','include_reasoning','temperature','seed','tools','tool_choice','max_tokens','top_p','response_format','stream'],
            'note':'Moonshot AI first-party endpoint (tag moonshotai/mxfp4, mxfp4), price checked on the OpenRouter endpoint listing 17-11-2026; no fallback'}
REVIEW_MODELS={QWEN,KIMI}
SLOTS={'first':{'first':QWEN,'final':'claude-opus-5-5'},'final':{'first':'claude-sonnet-5-5','final':QWEN},'both':{'first':QWEN,'final':QWEN},'opus':{'first':'claude-opus-5-5','final':'claude-opus-5-5'},'kimi':{'first':KIMI,'final':KIMI}}
REASONING={'effort':'high'};MAX_TOKENS=16000;DEFAULT_CAP=Decimal('0.60')

def install_reviewers(first,final):
    from mira_runner import cli_client,fast_v4
    for m in (first,final):
        if m.startswith('claude-'):cli_client.CLI_MODELS.setdefault(m,m.removeprefix('claude-').replace('.','-'));cli_client.SUBSCRIPTION_MODELS.add(m)
    fast_v4.SOL=first;fast_v4.ASTRA=final

def unwrap_content(content):
    """The reviewer prompts (written for the CLI emulation) ask for ONE JSON object inside a "content" field. Qwen4 Max sometimes follows that literally over the API and returns {"content": "<json string>"} instead of the bare object (case 004, second review). Deterministic unwrap, no new inference; anything else is left untouched."""
    try:o=json.loads(content or '')
    except Exception:return content
    return o['content'] if isinstance(o,dict) and set(o)=={'content'} and isinstance(o['content'],str) else content

def patch_client(v5):
    orig=v5.V5Client.call
    def call(self,model,messages,log,role,params=None,**kwargs):
        if model in REVIEW_MODELS:params={**(params or {}),'reasoning':dict(REASONING)};kwargs={**kwargs,'max_tokens':MAX_TOKENS}
        msg=orig(self,model,messages,log,role,params,**kwargs)
        return {**msg,'content':unwrap_content(msg.get('content'))} if model in REVIEW_MODELS and role.startswith('fast_review') else msg
    v5.V5Client.call=call

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path,required=True);ap.add_argument('--slot',required=True,choices=sorted(SLOTS));ap.add_argument('--doctor',default='glm',choices=sorted(r6.DOCTORS));ap.add_argument('--cases',nargs='*',default=[]);ap.add_argument('--smoke',action='store_true');ap.add_argument('--desk',choices=['v6','v61'],default='v6',help='v61 = truthful later-stage notice + followup results released to reviewers after admission + final-stage rule (src/mira_v6/desk_v61.py)')
    ap.add_argument('--suffix',default='q1');ap.add_argument('--cap',type=Decimal,default=DEFAULT_CAP);ap.add_argument('--cpt-dir',type=Path,default=HERE.parent/'data/cpt');ap.add_argument('--execute',action='store_true');ap.add_argument('--allow-commit-transition',action='store_true');a=ap.parse_args()
    if not a.smoke and not a.cases:raise SystemExit('--cases or --smoke required')
    variant=f'{a.doctor}_{a.slot}_{a.suffix}'
    if a.desk=='v61' and 'v61' not in a.suffix:raise SystemExit('--desk v61 needs a suffix containing v61 (own variant name, own traces)')
    if not re.fullmatch(r'[a-z][a-z0-9_-]{0,31}',variant):raise ValueError('variant must be a lowercase slug')
    rev=SLOTS[a.slot];doctor=r6.DOCTORS[a.doctor];base=a.base.resolve();sys.path[:0]=[str(base/'scripts'),str(base/'src')]
    import run_v5 as v5
    from mira_runner.budget import Ledger
    from mira_v6 import desk
    from mira_v6.costing import PriceTable
    parent=base/'runs/v5/v6_qwen';root=parent/variant/'run1';cases_dir=base/r6.ARM['cases']
    done={json.loads(l)['result']['case_id'] for p in (root/'logs/raw').glob('*/*.jsonl') for l in p.read_text().splitlines() if '"case_complete"' in l} if (root/'logs/raw').exists() else set()
    pending=[c for c in a.cases if c not in done]
    missing=[c for c in pending if not (cases_dir/c/'gatekeeper.json').exists()]
    if missing:raise RuntimeError('v6 case copies missing: '+','.join(missing))
    if not a.execute:print(json.dumps({'variant':variant,'reviewers':rev,'pending':pending,'terminal_skipped':sorted(done),'smoke':a.smoke,'cap_usd':str(a.cap),'requests_not_sent':True}));return
    v5.CAP=a.cap;r6.CAP=a.cap;v5.DOCTOR=doctor;v5.ALLOWED=v5.ALLOWED|{doctor}|REVIEW_MODELS|set(rev.values())
    desk.install()
    if a.desk=='v61':
        from mira_v6 import desk_v61;desk_v61.install();desk_v61.install_final_rule()
    install_reviewers(rev['first'],rev['final']);patch_client(v5);desk.CONTEXT['price_table']=PriceTable.from_dir(a.cpt_dir)
    config=json.loads((base/'config/v5.json').read_text());config['budget_usd']=str(a.cap);config['models'][QWEN]=dict(ROUTE);config['models'][KIMI]=dict(ROUTE_KIMI)
    if doctor in d6.ROUTES:config['models'][doctor]=d6.route_config(doctor)
    parent.mkdir(parents=True,exist_ok=True)
    with (parent/('run_'+variant+'.lock')).open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        key=Path(os.environ.get('OPENROUTER_KEY_FILE',str(base/'.secrets/openrouter.key'))).read_text().strip()
        if not key:raise RuntimeError('empty OpenRouter key')
        shared=parent/'budget.sqlite'
        if not shared.exists():Ledger(shared,str(a.cap)).db.close()
        bpath=parent/'credits_before.json'
        if not bpath.exists():bpath.write_text(json.dumps(v5.snapshot(key),indent=2)+'\n')
        baseline=json.loads(bpath.read_text());commit=subprocess.check_output(['git','-C',str(base),'rev-parse','HEAD'],text=True).strip()
        root.mkdir(parents=True,exist_ok=True);(root/'logs').mkdir(exist_ok=True);(root/'config').mkdir(exist_ok=True)
        v5.link(root/'upstream',base/'upstream',True);v5.link(root/'config/judge_overrides_v3.json',base/'config/judge_overrides_v3.json');v5.link(root/'logs/budget.sqlite',shared)
        if subprocess.run(['git','-C',str(base),'check-ignore','--quiet','--',str((root/'x').relative_to(base))],capture_output=True).returncode:raise RuntimeError('runs/v5/v6_qwen must be Git-ignored')
        if a.smoke:smoke(v5,Ledger,shared,root,config,key,a.cap,baseline,rev['first']);return
        for case in pending:
            v5.guard(v5.snapshot(key),baseline,v5.ledger_total(shared));desk.CONTEXT['case_dir']=str(cases_dir/case)
            r=r6.work(v5,base,root,shared,cases_dir/case,config,key,commit,a.allow_commit_transition,doctor)
            after=v5.guard(v5.snapshot(key),baseline,v5.ledger_total(shared));v=r.get('v5',{})
            print(json.dumps({'slot':a.slot,'case_id':r['case_id'],'judge_correct':r['judge_correct'],'proposal_correct':r.get('proposal_correct'),'openrouter_usd':r.get('cost_usd'),'patient_api_equiv_usd':v.get('patient_api_equiv_usd'),
                              'turns':r.get('n_turns'),'exchanges':r.get('patient_exchanges'),'remaining_cap_usd':after['remaining_cap_usd']}),flush=True)

def smoke(v5,Ledger,shared,root,config,key,cap,baseline,model=QWEN):
    """One tiny non-clinical call through the same client, route and parameters: checks the provider, that the thinking text comes back, and the real cost."""
    from mira_runner.client import AuditLog
    from mira_runner.cli_client import CODEX_EFFORT
    log=AuditLog(root/'logs/raw'/'smoke'/'smoke.jsonl','smoke');ledger=Ledger(shared,str(cap))
    try:
        client=v5.V5Client(ledger,config,key,codex_effort=CODEX_EFFORT,codex_transport_options={'diagnostics':True})
        msg=client.call(model,[{'role':'system','content':'Answer with one JSON object {"answer":str}.'},{'role':'user','content':'Which is larger, 17 times 23 or 400? Give the product.'}],log,'smoke',{},max_tokens=8192)
        ev=[e for e in log.events() if e['event']=='response'][-1]['response'];u=ev.get('usage',{})
        print(json.dumps({'smoke':True,'asked_model':model,'provider':ev.get('provider'),'model':ev.get('model'),'has_reasoning_text':bool(msg.get('reasoning')),'reasoning_chars':len(msg.get('reasoning') or ''),'has_reasoning_details':bool(msg.get('reasoning_details')),
                          'content_chars':len(msg.get('content') or ''),'prompt_tokens':u.get('prompt_tokens'),'completion_tokens':u.get('completion_tokens'),'reasoning_tokens':(u.get('completion_tokens_details') or {}).get('reasoning_tokens'),'cost_usd':u.get('cost')}),flush=True)
    finally:ledger.db.close()

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(json.dumps({'execution_failed':type(exc).__name__,'detail':str(exc)[:160],'requests_not_retried':True}),flush=True);raise SystemExit(1) from None
