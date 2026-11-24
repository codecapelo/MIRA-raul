"""Grade stored final diagnoses 1 to 5 with a justification for every score (src/mira_v6/judge_likert.py). Never reruns an encounter: reads `dx_agent` from case_complete and the reference from the case folder.

  python3 scripts/likert_run.py --arm v5=<run root>:<cases dir>:openai --arm gemini=<run root>:<cases dir>:claude ... --cases case_004 ... --out likert.json --key-file <openrouter key>

Judges: Gemini 3.1 Pro through OpenRouter for every encounter (a family that wrote neither the doctor text nor the reviewers' final text) plus a second judge from a family DIFFERENT from the one that wrote the final diagnosis:
authors `openai` (Sol/Astra) -> Claude Sonnet 5.5 high by subscription; authors `claude` (Sonnet/Fable) -> GPT through the Codex subscription (gpt-6.1-sol, medium).
OpenRouter cost of the first judge is outside the v6 ledger: reconcile it with the account delta. Closed-case reference and diagnosis text are read in memory only; `--out` must stay outside Git when it holds closed cases.
"""
import argparse,json,sys
from pathlib import Path
BASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(BASE/'src'))
from mira_v6 import judge_likert as jl

def complete(root,case):
    for p in Path(root,'logs/raw').glob(f'*/{case}.jsonl'):
        for l in p.read_text().splitlines():
            if '"case_complete"' in l:return json.loads(l)['result']
    return None

def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--arm',action='append',required=True,help='NAME=root:cases_dir:authors(openai|claude)');ap.add_argument('--cases',nargs='+',required=True)
    ap.add_argument('--out',type=Path,required=True);ap.add_argument('--key-file',type=Path,required=True);ap.add_argument('--primary',default='google/gemini-3.1-pro-preview');a=ap.parse_args(argv)
    primary=jl.judge  # noqa: F841 (kept for clarity)
    call_primary=jl.openrouter(a.primary,a.key_file);call_claude=jl.claude_cli('claude-sonnet-5-5','high');call_codex=jl.codex_cli('gpt-6.1-sol','medium')
    out=json.loads(a.out.read_text()) if a.out.exists() else {}
    for spec in a.arm:
        name,_,rest=spec.partition('=');root,cdir,authors=rest.split(':')
        for case in a.cases:
            key=f'{name}|{case}'
            if key in out:continue
            res=complete(root,case)
            if not res or not res.get('dx_agent'):continue
            ref=json.loads((Path(cdir)/case/'reference.json').read_text())['correct_diagnosis'];row={'arm':name,'case':case,'authors':authors,'model':res.get('model')}
            try:row['primary']=jl.judge(call_primary,ref,res['dx_agent'])
            except Exception as exc:row['primary']=None;row['primary_error']=type(exc).__name__+': '+str(exc)[:120]
            row['primary_model']=a.primary
            second=call_claude if authors=='openai' else call_codex;row['second_model']='claude-sonnet-5-5' if authors=='openai' else 'gpt-6.1-sol'
            try:row['second']=jl.judge(second,ref,res['dx_agent'])
            except Exception as exc:row['second']=None;row['second_error']=type(exc).__name__
            out[key]=row;a.out.write_text(json.dumps(out,ensure_ascii=False,indent=1))
            print(key,(row['primary'] or {}).get('score'),(row['second'] or {}).get('score'),flush=True)
    rows=list(out.values());print(f'{len(rows)} graded')
if __name__=='__main__':main()
