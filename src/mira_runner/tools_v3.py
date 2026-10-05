"""v3 investigation tool: per-test answers instead of one anonymous bundle.

Every requested test gets an explicit status by name: reported (with the finding), already ordered earlier
(not repeated), or not available. Analyte requests that are literally present in a bundled observation
(e.g. total bilirubin inside 'Hemolysis studies') are returned deterministically instead of depending on the
LLM matcher; a specimen guard keeps urine/fluid requests from matching serum values. v1/v2 CaseTools is unchanged.
"""
import json,re
from .semantics import compatible,identity,norm,requested_analytes,result_value
from .tools import CaseTools

PROC_RE=re.compile(r'laparo|thoraco|explor|surg|endoscop|bronchoscop|centesis')
TISSUE_RE=re.compile(r'biops|patholog|histolog|cytolog|resect|tissue|specimen')
SPECIMENS={'urine','pleural','csf','ascitic','drain','synovial','stool','sputum','fluid','peritoneal'}
def specimen(text):return frozenset(set(norm(text).split())&SPECIMENS)

def prereq_groups(o):
    """Procedure prerequisites in the case metadata, e.g. 'after_procedure:laparotomy' or 'after_any_procedure:laparoscopy|laparotomy'."""
    out=[]
    for p in o.get('prerequisites') or []:
        if isinstance(p,str):
            for pre in ('after_procedure:','after_any_procedure:'):
                if p.startswith(pre):out.append([t.replace('_',' ') for t in p[len(pre):].split('|')])
    return out

class V3CaseTools(CaseTools):
    def __init__(self,observations,matcher=None,enforce_prereqs=False):
        super().__init__(observations,matcher);self.reported=set();self.enforce=enforce_prereqs;self.prereq_blocks=0
        self.names={o['fact_id']:o['name'].lower() for o in observations}
    def unmet(self,o):
        done=[self.names[i] for i in self.returned if i in self.names]
        return [g for g in prereq_groups(o) if not any(t in n for t in g for n in done)]
    def execute(self,name,args):
        if name in ('admission','request_physical_exam'):return super().execute(name,args)
        self.validate(name,args)
        pool=self.pool_for(name);requested=args.get('test_names',[args.get('study_name','')])
        findings=[];already=[];missing=[];needs=[]
        for query in requested:
            eligible=[o for o in pool if compatible(query,o)]
            exact=[o for o in eligible if identity(query)==identity(o['name'])]
            matched=exact
            if not exact and requested_analytes(query):
                # compatible() already required the analyte to be literally present in the value
                matched=[o for o in eligible if specimen(query)==specimen(o['name'])]
            if not matched and self.enforce and len(norm(query))>=6:  # a procedure named inside a longer observation name ('Diagnostic laparoscopy' in 'Diagnostic laparoscopy / Exploratory laparotomy')
                matched=[o for o in eligible if norm(query) in norm(o['name']) or norm(o['name']) in norm(query)]
            if not matched and eligible:
                ids=self.matcher([query],eligible) if self.matcher else [o['fact_id'] for o in eligible]
                matched=[o for o in eligible if o['fact_id'] in ids and compatible(query,o)]
            if self.enforce and matched:
                blocked=[(o,self.unmet(o)) for o in matched];matched=[o for o,u in blocked if not u]
                for o,u in blocked:
                    if u:
                        item={'requested':query,'needs_prior_procedure':' or '.join(' / '.join(g) for g in u)}
                        if item not in needs:needs.append(item);self.prereq_blocks+=1
                if not matched:continue
            if not matched and self.enforce and TISSUE_RE.search(norm(query)):
                procs=[o['name'] for o in self.observations if o.get('routing_tool')=='request_other_investigation' and PROC_RE.search(o['name'].lower()) and not TISSUE_RE.search(o['name'].lower()) and not o.get('prerequisites')]
                if procs:
                    needs.append({'requested':query,'needs_prior_procedure':' or '.join(procs[:3]),'note':'tissue sampling at this site requires a procedure first; request the procedure'});self.prereq_blocks+=1;continue
            if not matched:missing.append(query);continue
            for o in matched:
                value=result_value(query,o);key=(o['fact_id'],value)
                if key in self.reported:
                    item={'requested':query,'name':o['name']}
                    if item not in already:already.append(item)
                    continue
                self.reported.add(key);self.returned.add(o['fact_id'])
                item={'requested':query,'name':o['name'],'value':value}
                if item not in findings:findings.append(item)
        out={}
        if findings:out['findings']=findings
        if already:out['already_ordered_earlier']=already
        if missing and self.enforce:  # a request sent to the wrong tool: say which tool holds it (no content is revealed)
            wrong=[]
            for q in list(missing):
                for tool in ('request_blood_test','request_urine_test','request_bedside_test','request_radiology','request_microbiology','request_other_investigation'):
                    if tool==name:continue
                    if any(len(norm(q))>=5 and (identity(q)==identity(o['name']) or norm(q) in norm(o['name']) or norm(o['name']) in norm(q)) for o in self.pool_for(tool)):
                        wrong.append({'requested':q,'use_tool':tool});missing.remove(q);break
            if wrong:out['wrong_tool']=wrong
        if needs:out['requires_prior_procedure']=needs
        if missing:out['not_available_in_this_case']=missing
        return json.dumps(out,ensure_ascii=False)
