"""Build the v6 case copies: original case + items recovered from the article (presentation phase, verified quote, labelled unreviewed) + gatekeeper.json. The source cases/ folder is never modified.

  python3 scripts/build_v6_cases.py --cases case_001 case_004 --cases-dir <cases> --audit-dir <dir with case_XXX.json audits> --licenses-dir <dir> --out <dir>

The PDF path is read from the audit file. Output for closed (NEJM) cases must stay in a Git-ignored folder.
"""
import argparse,json,subprocess,sys
from pathlib import Path
BASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(BASE/'src'))
from mira_v6.recovered import build_case

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--cases',nargs='+',required=True);ap.add_argument('--cases-dir',type=Path,required=True)
    ap.add_argument('--audit-dir',type=Path,action='append',required=True);ap.add_argument('--licenses-dir',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    for c in a.cases:
        audit=next((d/f'{c}.json' for d in a.audit_dir if (d/f'{c}.json').exists()),None);lic=a.licenses_dir/f'{c}.json'
        pdf=json.loads(audit.read_text())['pdf'] if audit else (json.loads(lic.read_text())['pdf'] if lic.exists() else None)
        text=subprocess.run(['pdftotext','-q','-layout',str(pdf),'-'],capture_output=True,text=True,timeout=120).stdout if pdf else ''
        res=build_case(a.cases_dir/c,a.out/c,audit,lic if lic.exists() else None,text);print(c,json.dumps(res),flush=True)
if __name__=='__main__':main()
