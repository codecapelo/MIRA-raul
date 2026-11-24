"""Repetitions and uncertainty for the case-level outcomes of one or more conditions. No model call, no cost.

  python3 scripts/repetition_report.py --condition v5=runs/v5/v5z/run1,runs/v5/v5full1/run1 --cases-dir cases --json out.json
  python3 scripts/repetition_report.py --condition A=pathA1,pathA2,pathA3 --condition B=pathB1,pathB2,pathB3 --cases-dir cases     # also a paired comparison A vs B

A condition is the list of run roots (one run = one execution of every case). The unit of analysis is the CASE, not the encounter: repetitions of the same case are dependent, so intervals come from resampling cases.
Reported per condition: repetitions per case (and a check that they match), mean accuracy with a case-bootstrap 95% interval, per-run accuracy with Wilson intervals, pass@k (any repetition correct), majority vote, how many cases were
always right, always wrong or unstable, and the within-case flip rate between runs. Comparison of two conditions: paired difference of per-case accuracy with a case-bootstrap interval and an exact sign test on the cases that differ.
Closed (NEJM) cases enter the aggregates only; per-case rows are written for public cases only.
"""
import argparse,importlib.util,json,math,random,sys
from collections import defaultdict
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]

def wilson(k,n,z=1.96):
    if not n:return None
    p=k/n;d=1+z*z/n;c=p+z*z/(2*n);m=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n));return [round((c-m)/d,4),round((c+m)/d,4)]

def pctile(sorted_vals,q):
    if not sorted_vals:return None
    i=min(len(sorted_vals)-1,max(0,int(round(q*(len(sorted_vals)-1)))));return round(sorted_vals[i],4)

def case_means(outcomes):
    """{case:[True/False/None,...]} -> {case:mean of the judged repetitions} (cases with no judged repetition are dropped)."""
    out={}
    for c,v in outcomes.items():
        j=[x for x in v if isinstance(x,bool)]
        if j:out[c]=sum(j)/len(j)
    return out

def boot_ci(values,boot=4000,seed=20261114):
    """95% percentile interval of the mean of `values`, resampling items with replacement."""
    if not values:return None
    rng=random.Random(seed);n=len(values);means=sorted(sum(values[rng.randrange(n)] for _ in range(n))/n for _ in range(boot))
    return [pctile(means,0.025),pctile(means,0.975)]

def analyze(outcomes,boot=4000,seed=20261114):
    """outcomes: {case_id:[bool|None per repetition]} for one condition. None = terminal without a judge verdict (counted, not scored)."""
    reps={c:len(v) for c,v in outcomes.items()};k=sorted(set(reps.values()))
    means=case_means(outcomes);vals=[means[c] for c in sorted(means)]
    runs=max(reps.values()) if reps else 0
    per_run=[]
    for r in range(runs):
        col=[v[r] for v in outcomes.values() if len(v)>r];j=[x for x in col if isinstance(x,bool)]
        per_run.append({'run':r+1,'cases':len(col),'judged':len(j),'correct':sum(j),'accuracy':round(sum(j)/len(j),4) if j else None,'wilson95':wilson(sum(j),len(j))})
    always=[c for c,m in means.items() if m==1.0];never=[c for c,m in means.items() if m==0.0];mixed=[c for c in means if 0<means[c]<1]
    multi=[v for v in outcomes.values() if len([x for x in v if isinstance(x,bool)])>=2]
    flips=pairs=0
    for v in multi:
        j=[x for x in v if isinstance(x,bool)]
        for a in range(len(j)):
            for b in range(a+1,len(j)):pairs+=1;flips+=j[a]!=j[b]
    anyc=sum(any(x is True for x in v) for v in outcomes.values() if any(isinstance(x,bool) for x in v))
    maj=sum(1 for v in outcomes.values() if (lambda j:len(j)>0 and sum(j)*2>len(j))([x for x in v if isinstance(x,bool)]))
    ncases=len(means)
    return {'cases':len(outcomes),'cases_scored':ncases,'repetitions_per_case':k,'repetitions_match':len(k)<=1,'mean_accuracy':round(sum(vals)/ncases,4) if ncases else None,'case_bootstrap95':boot_ci(vals,boot,seed),
            'per_run':per_run,'pass_at_k':{'k':runs,'cases_with_any_correct':anyc,'rate':round(anyc/ncases,4) if ncases else None},'majority_correct':{'cases':maj,'rate':round(maj/ncases,4) if ncases else None,'rule':'strictly more than half of the judged repetitions'},
            'always_correct':len(always),'always_wrong':len(never),'unstable':len(mixed),'within_case_flip_rate':round(flips/pairs,4) if pairs else None,
            'warnings':([] if len(k)<=1 else ['cases have different numbers of repetitions: '+str(k)])+([] if runs>=2 else ['a single repetition: no run-to-run variation can be measured'])}

def sign_test_p(better,worse):
    """Two-sided exact binomial (p=0.5) on the cases that differ."""
    n=better+worse
    if not n:return 1.0
    k=min(better,worse);p=sum(math.comb(n,i) for i in range(k+1))/2**n;return round(min(1.0,2*p),4)

def compare(a,b,boot=4000,seed=20261114):
    """Paired comparison of two conditions on the cases present and scored in both. Positive difference = A better than B."""
    ma,mb=case_means(a),case_means(b);shared=sorted(set(ma)&set(mb));d=[ma[c]-mb[c] for c in shared]
    better=sum(x>0 for x in d);worse=sum(x<0 for x in d)
    return {'shared_cases':len(shared),'only_in_a':sorted(set(ma)-set(mb)),'only_in_b':sorted(set(mb)-set(ma)),'mean_difference_a_minus_b':round(sum(d)/len(d),4) if d else None,'case_bootstrap95':boot_ci(d,boot,seed),
            'cases_a_better':better,'cases_b_better':worse,'cases_equal':len(d)-better-worse,'sign_test_p':sign_test_p(better,worse),'note':'cases are the unit; with few cases an interval that spans zero means no difference can be claimed'}

def load_outcomes(run_roots,case_dirs):
    spec=importlib.util.spec_from_file_location('rule_metrics',BASE/'scripts/rule_metrics.py');rm=importlib.util.module_from_spec(spec);sys.modules['rule_metrics']=rm;spec.loader.exec_module(rm)
    out=defaultdict(list)
    for i,root in enumerate(run_roots):
        rows,_=rm.collect([(f'run{i+1}',root)],case_dirs)
        for r in rows:
            if r.get('terminal'):out[r['case_id']].append(r['judge_correct'] if isinstance(r.get('judge_correct'),bool) else None)
    return dict(out)

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__.split('\n')[0]);ap.add_argument('--condition',action='append',required=True,help='NAME=root1,root2,... (one root per repetition)')
    ap.add_argument('--cases-dir',action='append',type=Path,required=True);ap.add_argument('--json',type=Path);ap.add_argument('--boot',type=int,default=4000);a=ap.parse_args(argv)
    conds={}
    for spec in a.condition:
        name,_,paths=spec.partition('=');conds[name]=load_outcomes([Path(p) for p in paths.split(',') if p],a.cases_dir)
    result={'conditions':{},'comparisons':[]}
    for name,o in conds.items():
        pub={c:v for c,v in o.items() if int(c.split('_')[1])<11};clo={c:v for c,v in o.items() if int(c.split('_')[1])>=11}
        result['conditions'][name]={'all':analyze(o,a.boot),'public':analyze(pub,a.boot) if pub else None,'closed_aggregate':analyze(clo,a.boot) if clo else None,
                                    'public_cases':{c:v for c,v in sorted(pub.items())}}
    names=list(conds)
    for i in range(len(names)):
        for j in range(i+1,len(names)):result['comparisons'].append({'a':names[i],'b':names[j],**compare(conds[names[i]],conds[names[j]],a.boot)})
    text=json.dumps(result,ensure_ascii=False,indent=1)
    if a.json:a.json.write_text(text+'\n')
    for n,c in result['conditions'].items():
        x=c['all'];print(f"{n}: {x['cases_scored']} cases, reps per case {x['repetitions_per_case']}, mean accuracy {x['mean_accuracy']} (case bootstrap {x['case_bootstrap95']}), always right {x['always_correct']}, always wrong {x['always_wrong']}, unstable {x['unstable']}, flip rate {x['within_case_flip_rate']}",flush=True)
        for w in x['warnings']:print('  warning:',w)
    for c in result['comparisons']:print(f"{c['a']} vs {c['b']}: shared {c['shared_cases']}, diff {c['mean_difference_a_minus_b']} {c['case_bootstrap95']}, A better {c['cases_a_better']}, B better {c['cases_b_better']}, sign test p={c['sign_test_p']}")
if __name__=='__main__':main()
