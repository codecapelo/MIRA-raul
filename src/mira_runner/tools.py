import json,re
from .semantics import compatible,result_value,identity
NAMES=['request_physical_exam','request_blood_test','request_urine_test','request_bedside_test','request_radiology','request_microbiology','request_other_investigation','admission']
def schemas():
    result=[]
    for n in NAMES:
        props={}; required=[]
        if n=='admission': props={k:{'type':'string'} for k in ['diagnosis','reasoning']}; required=list(props)
        elif n=='request_radiology': props={k:{'type':'string'} for k in ['study_name','modality','region']}
        elif n!='request_physical_exam': props={'test_names':{'type':'array','items':{'type':'string'}}}; required=['test_names']
        result.append({'type':'function','function':{'name':n,'description':'Finalize case' if n=='admission' else 'Retrieve available published case findings; missing findings are unavailable.','parameters':{'type':'object','properties':props,'required':required,'additionalProperties':False}}})
    return result

class ToolArgumentsError(ValueError):pass

def norm(x): return re.sub('[^a-z0-9]+',' ',str(x).lower()).strip()
class CaseTools:
    def __init__(self,observations,matcher=None): self.observations=observations; self.returned=set(); self.errors=0; self.matcher=matcher
    def validate(self,name,args):
        if name not in NAMES: raise ToolArgumentsError('Unknown tool')
        if not isinstance(args,dict): raise ToolArgumentsError('Arguments must be a JSON object')
        allowed=next(x['function']['parameters']['properties'] for x in schemas() if x['function']['name']==name)
        if set(args)-set(allowed):raise ToolArgumentsError('Unexpected argument keys')
        if name not in ['admission','request_physical_exam','request_radiology']:
            if not isinstance(args.get('test_names'),list) or not all(isinstance(x,str) for x in args['test_names']):raise ToolArgumentsError('test_names must be a string array')
        if name=='request_radiology' and any(not isinstance(v,(str,type(None))) for v in args.values()):raise ToolArgumentsError('Radiology arguments must be strings')
    def execute(self,name,args):
        self.validate(name,args)
        if name=='admission':
            if not all(isinstance(args.get(k),str) and args[k].strip() for k in ['diagnosis','reasoning']): raise ToolArgumentsError('Empty admission diagnosis/reasoning')
            return 'Case admitted.'
        domains={'request_physical_exam':['physical_exam','exam','physical','vitals'],'request_blood_test':['blood','lab','laboratory'],'request_urine_test':['urine'],'request_bedside_test':['bedside','ecg'],'request_radiology':['radiology','imaging'],'request_microbiology':['microbiology'],'request_other_investigation':['other','tissue','csf','genetic','other_fluid','procedure_result','other_test']}
        def routed(o):
            route=o.get('routing_tool')
            if route==name or (route is None and o['domain'] in domains[name]):return True
            # Explicit clinically valid shared routes; original_domain/fact_id
            # never participates in eligibility.
            test=identity(o['name'])
            if name=='request_radiology' and o.get('modality')=='echocardiography':return True
            if name=='request_urine_test' and test=='urine culture':return True
            if name=='request_blood_test' and test in ['peripheral blood film','t spot tb']:return True
            if name=='request_microbiology' and test=='t spot tb':return True
            if name=='request_other_investigation' and test=='peripheral blood film':return True
            return False
        pool=[o for o in self.observations if routed(o) and not o.get('unavailable_for_immediate_care')]
        if name=='request_physical_exam':
            pool=[o for o in pool if o.get('available_at','time_zero') in ['time_zero','admission','baseline','initial','presentation'] and not o.get('prerequisites')]
            selected=[{'name':o['name'],'value':o['value']} for o in pool]
            self.returned.update(o['fact_id'] for o in pool)
        else:
            requested=args.get('test_names',[args.get('study_name','')])
            selected=[]
            for query in requested:
                # The LLM sees only clinically compatible candidates, and every
                # returned identifier is revalidated against the specific query.
                eligible=[o for o in pool if compatible(query,o)]
                exact=[o for o in eligible if identity(query)==identity(o['name'])]
                matched=exact
                if not exact and eligible:
                    ids=self.matcher([query],eligible) if self.matcher else [o['fact_id'] for o in eligible]
                    matched=[o for o in eligible if o['fact_id'] in ids and compatible(query,o)]
                for o in matched:
                    item={'name':o['name'],'value':result_value(query,o)}
                    if item not in selected:selected.append(item)
                    self.returned.add(o['fact_id'])
        if not selected:return 'Requested findings are not available in this published case.'
        return json.dumps(selected,ensure_ascii=False)
