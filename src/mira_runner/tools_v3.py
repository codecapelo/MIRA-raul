"""v3 investigation tool: per-test answers instead of one anonymous bundle.

Every requested test gets an explicit status by name: reported (with the finding), already ordered earlier
(not repeated), or not available. Analyte requests that are literally present in a bundled observation
(e.g. total bilirubin inside 'Hemolysis studies') are returned deterministically instead of depending on the
LLM matcher; a specimen guard keeps urine/fluid requests from matching serum values. v1/v2 CaseTools is unchanged.
"""
import json,re
from .semantics import compatible,identity,norm,requested_analytes,result_value
from .tools import CaseTools

SPECIMENS={'urine','pleural','csf','ascitic','drain','synovial','stool','sputum','fluid','peritoneal'}
def specimen(text):return frozenset(set(norm(text).split())&SPECIMENS)

class V3CaseTools(CaseTools):
    def __init__(self,observations,matcher=None):
        super().__init__(observations,matcher);self.reported=set()
    def execute(self,name,args):
        if name in ('admission','request_physical_exam'):return super().execute(name,args)
        self.validate(name,args)
        pool=self.pool_for(name);requested=args.get('test_names',[args.get('study_name','')])
        findings=[];already=[];missing=[]
        for query in requested:
            eligible=[o for o in pool if compatible(query,o)]
            exact=[o for o in eligible if identity(query)==identity(o['name'])]
            matched=exact
            if not exact and requested_analytes(query):
                # compatible() already required the analyte to be literally present in the value
                matched=[o for o in eligible if specimen(query)==specimen(o['name'])]
            if not matched and eligible:
                ids=self.matcher([query],eligible) if self.matcher else [o['fact_id'] for o in eligible]
                matched=[o for o in eligible if o['fact_id'] in ids and compatible(query,o)]
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
        if missing:out['not_available_in_this_case']=missing
        return json.dumps(out,ensure_ascii=False)
