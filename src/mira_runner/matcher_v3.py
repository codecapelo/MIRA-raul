"""Strict exam matcher (protocol v3.3, `--strict-exams`).

The upstream matcher prompt lets one request map to "multiple candidates when clinically appropriate", which in practice returned
a specific test for a generic request (serum IgE -> allergen-specific IgE), a serology for a stool request, a culture for a
urinalysis, an angiography for a cardiac CT. This matcher decides one relation per requested test and fails closed:

  same        the candidate is the very test/procedure requested (synonyms, abbreviations and non-changing descriptors allowed)
  component   one analyte/part that a bundled candidate explicitly reports in its result text
  panel_part  a defined panel (e.g. CMP) of which the candidate reports only some components
  too_generic a category or workup, not a defined test ("parasitic infection panel", "infectious workup")
  none        everything else: broader-than-candidate (generic -> specific), another specimen, organism, antigen, analyte,
              site, modality, procedure or assay, and screening vs confirmatory tests

One call handles all requests of one tool call. Decisions are validated against the candidate keys; anything malformed is `none`.
"""
import json

RELATIONS=('same','component','panel_part','too_generic','none')
STRICT_PROMPT=("""You are the order desk of a hospital laboratory and imaging service. A physician requests tests; you may release a result only when the case record contains THAT test.

For every requested test decide exactly one relation to the candidate records (each has a key, a name and what it reports):
- "same": a candidate is the very test or procedure requested. Synonyms, abbreviations, other languages and descriptors that do not change what is done are fine (CBC = full blood count; CT abdomen with contrast = abdominal CT; 12-lead ECG = electrocardiogram).
- "component": the request names ONE analyte or part that a bundled candidate explicitly reports in its "reported" text (e.g. platelet count inside a blood count). The analyte must literally appear in "reported".
- "panel_part": the request is a defined standard panel (comprehensive metabolic panel, liver panel, coagulation studies) and a candidate reports only some of its components.
- "too_generic": the request is too nonspecific to be performed, and the physician must be asked to specify it. This covers (a) a category, workup or screen ("parasitic infection panel", "infectious disease workup", "allergy testing", "autoimmune panel", "tumor markers", "stool studies", "rule out infection") and (b) a test class that needs a target, specimen or site that the request leaves out ("specific IgE" without the antigen, "antibody test" or "serology" without the organism, "culture" without the specimen, "biopsy" without the site, "PCR" without the target, "imaging" without modality and region). Decide this from the wording of the request alone, never from what the candidates contain. Standard defined panels and tests that are complete as named (blood count, metabolic panel, liver panel, coagulation studies, urinalysis, total IgE, chest CT) are NOT too generic.
- "none": any other case. Always "none" when:
  * the request is BROADER than the candidate (generic -> specific): "serum IgE" vs "IgE specific for one named antigen"; "cardiac CT" vs "coronary angiography"; "antibody test" vs "antibody to a named organism"; "biopsy" vs "biopsy of a named site".
  * the specimen differs (stool vs blood vs urine vs CSF vs pleural fluid), or the organism, antigen, analyte, anatomical site, imaging modality, procedure or assay differs (BNP vs NT-proBNP; urinalysis vs urine culture; crossmatch vs direct antiglobulin test; thoracoscopy vs bronchoscopy; transesophageal echo vs surgical exploration; lactate vs lactate dehydrogenase).
  * the candidate is a screening test and the request a confirmatory one, or the reverse.
  * the candidate would merely be clinically useful or related. Usefulness is never a reason to release a result.
When in doubt, answer "none".

Release only what was requested. Give one key unless the request explicitly names several different tests. For "component" also give "extract" (the words copied verbatim from that candidate's "reported" text that carry the requested result, WITH its value, unit or finding, never the analyte name alone) and "answer" (one short statement of the result of ONLY the requested part, using only the numbers and findings of the record, for example "Giardia stool antigen: negative" when the record says both antigens are negative). Other results of the bundle were not requested and must not be released.

Return JSON only: {"decisions":[{"request":"<the request, verbatim>","relation":"same|component|panel_part|too_generic|none","keys":["<candidate key>", ...],"extract":["<verbatim fragment>", ...],"answer":"<short statement>","reason":"<at most 20 words>"}]}. Give "keys" only for same, component and panel_part; use [] otherwise. "extract" and "answer" only for component, else [] and "". One decision per requested test, in order.""")

def strict_match(client,log,model,queries,candidates,role='matcher',params=None,**kwargs):
    """Returns {query: {'relation':..., 'keys':[...], 'reason':str}} for every query; unreadable output means 'none' for all."""
    cand=[{'key':o['fact_id'],'name':o['name'],'reported':str(o.get('value',''))[:500]} for o in candidates]
    user='REQUESTED_TESTS:\n'+json.dumps(list(queries),ensure_ascii=False)+'\n\nCANDIDATE_RECORDS:\n'+json.dumps(cand,ensure_ascii=False)
    sp=set(((getattr(client,'config',None) or {}).get('models',{}).get(model) or {}).get('supported_parameters') or [])  # only send what the pinned provider accepts
    extra={'max_tokens':4000}
    if 'response_format' in sp:extra['response_format']={'type':'json_object'}
    if model.startswith('z-ai/') and 'reasoning' in sp:extra['reasoning']={'enabled':False}  # as the upstream matcher: no hidden reasoning, deterministic
    reply=client.call(model,[{'role':'system','content':STRICT_PROMPT},{'role':'user','content':user}],log,role,params if params is not None else {'temperature':0},**(extra | kwargs))
    out={q:{'relation':'none','keys':[],'reason':'unreadable matcher output'} for q in queries}
    try:
        text=(reply.get('content') or '').strip().removeprefix('```json').removeprefix('```').removesuffix('```').strip()
        decisions=json.loads(text)['decisions']
    except (json.JSONDecodeError,TypeError,KeyError,AttributeError):
        log.append({'event':'backend_error','role':role,'reason':'settled malformed strict matcher output','fallback':'none'});return out
    allowed={o['fact_id'] for o in candidates}
    for d in decisions if isinstance(decisions,list) else []:
        if not isinstance(d,dict) or d.get('request') not in out:continue
        rel=d.get('relation') if d.get('relation') in RELATIONS else 'none'
        keys=[k for k in (d.get('keys') or []) if k in allowed] if rel in ('same','component','panel_part') else []
        if rel in ('same','component','panel_part') and not keys:rel='none'
        ext=d.get('extract');ext=[ext] if isinstance(ext,str) else ext
        out[d['request']]={'relation':rel,'keys':keys,'extract':[x for x in (ext or []) if isinstance(x,str) and x.strip()][:4] if rel=='component' else [],'answer':str(d.get('answer') or '')[:300] if rel=='component' else '','reason':str(d.get('reason',''))[:200]}
    return out
