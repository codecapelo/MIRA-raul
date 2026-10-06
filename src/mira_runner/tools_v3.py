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
NO_SPECIMEN_DOMAINS={'blood','lab','laboratory','radiology','physical_exam','bedside','ecg'}
def specimen_ok(query,o):
    """A request that names a specimen (stool, urine, pleural fluid...) is never answered by a record of another specimen, nor by a blood/imaging record that names none."""
    q=specimen(query)-{'fluid'};n=specimen(o['name'])-{'fluid'}
    if q and n:return bool(q&n)
    if q and not n and not specimen(o['name']) and o.get('domain') in NO_SPECIMEN_DOMAINS:return False
    return True
COMPOUND_RE=re.compile(r'\s+/\s+|\s+\+\s+')
def split_compound(requested):
    out=[]
    for r in requested:
        for part in COMPOUND_RE.split(str(r)):
            part=part.strip()
            if part and part not in out:out.append(part)
    return out
OTHER_TOOLS=('request_blood_test','request_urine_test','request_bedside_test','request_radiology','request_microbiology','request_other_investigation')

def prereq_groups(o):
    """Procedure prerequisites in the case metadata, e.g. 'after_procedure:laparotomy' or 'after_any_procedure:laparoscopy|laparotomy'."""
    out=[]
    for p in o.get('prerequisites') or []:
        if isinstance(p,str):
            for pre in ('after_procedure:','after_any_procedure:'):
                if p.startswith(pre):out.append([t.replace('_',' ') for t in p[len(pre):].split('|')])
    return out

class V3CaseTools(CaseTools):
    def __init__(self,observations,matcher=None,enforce_prereqs=False,strict=None):
        super().__init__(observations,matcher);self.reported=set();self.enforce=enforce_prereqs;self.prereq_blocks=0;self.strict=strict;self.stats={'same':0,'component':0,'panel_part':0,'too_generic':0,'none':0,'wrong_tool_hint':0,'specimen_blocked':0,'component_isolated':0,'component_unisolated':0}
        self.names={o['fact_id']:o['name'].lower() for o in observations}
    def unmet(self,o):
        done=[self.names[i] for i in self.returned if i in self.names]
        return [g for g in prereq_groups(o) if not any(t in n for t in g for n in done)]
    def execute(self,name,args):
        if name in ('admission','request_physical_exam'):return super().execute(name,args)
        self.validate(name,args)
        pool=self.pool_for(name);requested=args.get('test_names',[args.get('study_name','')])
        if self.strict is not None:return self.execute_strict(name,pool,requested)
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

    @staticmethod
    def isolate(text,fragments,answer=''):
        """The requested part of a bundled result. Verbatim fragments of the record that carry a number are used as they are; otherwise a short statement is accepted only if every number in it occurs in the record. Anything else is refused (fail closed)."""
        squash=lambda x:' '.join(str(x).split()).lower();base=squash(text);ok=[]
        for f in fragments:
            if squash(f) and squash(f) in base and f.strip() not in ok:ok.append(f.strip())
        verbatim='; '.join(ok)
        if verbatim and re.search(r'\d',verbatim):return verbatim
        nums=lambda x:set(re.findall(r'\d+(?:[.,]\d+)?',str(x)))
        answer=' '.join(str(answer or '').split())
        if answer and len(answer)<=300 and nums(answer)<=nums(text):return answer
        return ''

    def execute_strict(self,name,pool,requested):
        """Protocol v3.3: one relation per request decided by the strict matcher; generic -> specific, other specimens and different tests are never released."""
        decided={};pending=[];missing=[];generic=[];extracts={};unisolated=[]
        requested=split_compound(requested)  # a request that lists several tests ("A / B", "A + B") is decided test by test
        for query in requested:
            def compat(o):  # a single-analyte record is eligible when its NAME is the requested analyte, even if the result text does not repeat the name
                return compatible(query,o) or bool(requested_analytes(query)&requested_analytes(o['name']))
            eligible=[o for o in pool if compat(o)]
            ok=[o for o in eligible if specimen_ok(query,o)]
            self.stats['specimen_blocked']+=len(eligible)-len(ok)
            exact=[o for o in pool if identity(query)==identity(o['name']) and specimen_ok(query,o)]
            if exact:decided[query]=(exact,'same');continue
            if requested_analytes(query):
                comp=[o for o in ok if specimen(query)==specimen(o['name'])]  # compatible() already required the analyte in the result text
                if comp:decided[query]=(comp,'component');continue
            if ok:pending.append((query,ok))
            else:missing.append(query)
        if pending:
            cand={o['fact_id']:o for _,el in pending for o in el}
            dec=self.strict([q for q,_ in pending],list(cand.values()))
            for q,el in pending:
                d=dec.get(q) or {'relation':'none','keys':[]};ids={o['fact_id'] for o in el}&set(d['keys'])
                if d['relation'] in ('same','component','panel_part') and ids:decided[q]=([o for o in el if o['fact_id'] in ids],d['relation']);extracts[q]=(d.get('extract') or [],d.get('answer') or '')
                elif d['relation']=='too_generic':generic.append(q);self.stats['too_generic']+=1
                else:missing.append(q);self.stats['none']+=1
        findings=[];already=[];needs=[]
        for query in requested:
            if query not in decided:continue
            matched,rel=decided[query];self.stats[rel]+=1
            if self.enforce:
                blocked=[(o,self.unmet(o)) for o in matched];matched=[o for o,u in blocked if not u]
                for o,u in blocked:
                    if u:
                        item={'requested':query,'needs_prior_procedure':' or '.join(' / '.join(g) for g in u)}
                        if item not in needs:needs.append(item);self.prereq_blocks+=1
                if not matched:continue
            for o in matched:
                value=result_value(query,o)
                if rel=='component' and len(matched)==1 and not requested_analytes(query):  # release only the requested part of a bundle
                    part=self.isolate(o['value'],*(extracts.get(query) or ([],'')))
                    if part:value=part;self.stats['component_isolated']+=1
                    else:  # fail closed: never release the rest of the bundle
                        self.stats['component_unisolated']+=1
                        if query not in unisolated:unisolated.append(query)
                        continue
                key=(o['fact_id'],value)
                if key in self.reported:
                    item={'requested':query,'name':o['name']}
                    if item not in already:already.append(item)
                    continue
                self.reported.add(key);self.returned.add(o['fact_id'])
                item={'requested':query,'name':o['name'],'value':value}
                if rel=='panel_part':item['note']='Only these components of the requested panel are reported in this case.'
                if item not in findings:findings.append(item)
        if self.enforce:
            for q in list(missing):  # a procedure-gated tissue sample at a site that needs a procedure first
                if TISSUE_RE.search(norm(q)):
                    procs=[o['name'] for o in self.observations if o.get('routing_tool')=='request_other_investigation' and PROC_RE.search(o['name'].lower()) and not TISSUE_RE.search(o['name'].lower()) and not o.get('prerequisites')]
                    if procs:
                        needs.append({'requested':q,'needs_prior_procedure':' or '.join(procs[:3]),'note':'tissue sampling at this site requires a procedure first; request the procedure'});self.prereq_blocks+=1;missing.remove(q)
        missing+=[q for q in unisolated if q not in missing and not any(f['requested']==q for f in findings)]
        wrong=[]
        if self.enforce and missing:  # the same strict decision against the other tools' records says which tool holds it
            tools={o['fact_id']:t for t in OTHER_TOOLS if t!=name for o in self.pool_for(t)};others={o['fact_id']:o for t in OTHER_TOOLS if t!=name for o in self.pool_for(t)}
            pend=[(q,[o for o in others.values() if (compatible(q,o) or requested_analytes(q)&requested_analytes(o['name'])) and specimen_ok(q,o)]) for q in missing];pend=[(q,el) for q,el in pend if el]
            if pend:
                dec=self.strict([q for q,_ in pend],list({o['fact_id']:o for _,el in pend for o in el}.values()))
                for q,el in pend:
                    d=dec.get(q) or {'relation':'none','keys':[]};ids=[k for k in d['keys'] if k in {o['fact_id'] for o in el}]
                    if d['relation'] in ('same','component','panel_part') and ids:wrong.append({'requested':q,'use_tool':tools[ids[0]]});missing.remove(q);self.stats['wrong_tool_hint']+=1
        out={}
        if findings:out['findings']=findings
        if already:out['already_ordered_earlier']=already
        if wrong:out['wrong_tool']=wrong
        if needs:out['requires_prior_procedure']=needs
        if generic:out['ambiguous_request']=[{'requested':q,'note':'Too nonspecific to be performed. Please specify exactly which test you want: the specimen or site and the target (antigen, organism, analyte) or the imaging modality and region.'} for q in generic]
        if missing:out['not_available_in_this_case']=missing
        return json.dumps(out,ensure_ascii=False)

