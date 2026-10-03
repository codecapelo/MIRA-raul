import json,re
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

def norm(x): return re.sub('[^a-z0-9]+',' ',str(x).lower()).strip()
class CaseTools:
    def __init__(self,observations,matcher=None): self.observations=observations; self.returned=set(); self.errors=0; self.matcher=matcher
    def execute(self,name,args):
        if name not in NAMES: raise ValueError('Unknown tool')
        if not isinstance(args,dict): raise ValueError('Arguments must be a JSON object')
        if name not in ['admission','request_physical_exam','request_radiology']:
            if not isinstance(args.get('test_names'),list) or not all(isinstance(x,str) for x in args['test_names']):raise ValueError('test_names must be a string array')
        if name=='request_radiology' and any(not isinstance(v,(str,type(None))) for v in args.values()):raise ValueError('Radiology arguments must be strings')
        if name=='admission':
            if not all(isinstance(args.get(k),str) and args[k].strip() for k in ['diagnosis','reasoning']): raise ValueError('Empty admission diagnosis/reasoning')
            return 'Case admitted.'
        domains={'request_physical_exam':['physical_exam','exam','physical','vitals'],'request_blood_test':['blood','lab','laboratory'],'request_urine_test':['urine'],'request_bedside_test':['bedside','ecg','imaging'],'request_radiology':['radiology','imaging'],'request_microbiology':['microbiology'],'request_other_investigation':['other','tissue','csf','genetic','other_fluid','procedure_result','other_test']}
        pool=[o for o in self.observations if o['domain'] in domains[name] and not o.get('unavailable_for_immediate_care')]
        if name=='request_bedside_test':pool=[o for o in pool if o['domain']!='imaging' or 'echo' in norm(o['name'])]
        requested=args.get('test_names',[args.get('study_name','')])
        if name=='request_physical_exam': selected=pool
        else:
            # Case labels are not placed in the doctor prompt. Only a requested test's
            # exact normalized name is resolved, avoiding broad accidental disclosure.
            selected=[o for o in pool if norm(o['name']) in [norm(q) for q in requested]]
        unresolved=[q for q in requested if norm(q) not in [norm(o['name']) for o in selected]]
        if unresolved and pool and self.matcher and name!='request_physical_exam':
            ids=self.matcher(unresolved,pool)
            selected += [o for o in pool if o['fact_id'] in ids and o not in selected]
        if not selected: return 'Requested findings are not available in this published case.'
        self.returned.update(o['fact_id'] for o in selected)
        return json.dumps([{'name':o['name'],'value':o['value']} for o in selected],ensure_ascii=False)
