"""Protocol v5 order desk and physician-facing checks (opt-in; v1 to v4 paths are untouched).

What it adds on top of the v3.6 desk (the exam behaviour the user preferred):
  * every investigation order carries a justification (`hypothesis`: the working diagnosis the test addresses; `decision`: what the result would change). An order without one
    comes back, free of cost, asking for it; time-critical first-line tests are exempt when the urgency alarm is on. The justification is logged apart from the tool event, so the
    blind reviewers never see the physician's hypothesis.
  * the desk talks back: a request that is not on record gets a plain desk note (name it precisely and say why, or treat it as not performed); results that differ from the request
    in assay, contrast, scope or guidance carry a note (see exam_notes).
  * a loop guard: the same order refused, held or unanswered three times is not executed again and the physician is told to change course.
  * speech/action sync: if the final message says "I am ordering X" for something that was refused, held or not on record, the physician is asked once to rewrite the message.
"""
import json,re
from .tools import schemas
from .runner_v3 import V3Tools
from .exam_policy import classify,overlap
from .exam_notes import desk_note_missing
from .semantics import norm

JUSTIFICATION={'type':'object','description':'Why this order: the working diagnosis it addresses and what the result would change.',
               'properties':{'hypothesis':{'type':'string','description':'the working diagnosis or concern this test addresses'},
                             'decision':{'type':'string','description':'what a positive or a negative result would change in your plan'}},
               'required':['hypothesis','decision']}
INVESTIGATIONS=('request_blood_test','request_urine_test','request_bedside_test','request_radiology','request_microbiology','request_other_investigation')

def schemas_v5():
    out=[]
    for s in schemas():
        s=json.loads(json.dumps(s))
        if s['function']['name'] in INVESTIGATIONS:
            p=s['function']['parameters'];p['properties']['justification']=JUSTIFICATION;p['required']=list(p.get('required',[]))+['justification']
        out.append(s)
    return out

V5_RULES=('\n- Every investigation request must include `justification` with `hypothesis` (the working diagnosis it addresses) and `decision` (what the result would change). Request tests only when you already have a plausible '
          'hypothesis from the history and examination; an order without a justification is returned to you at no cost.\n'
          '- The order desk answers each request. Read its notes: a result may differ from what you asked (assay, contrast, scope, guidance), and a test that is not on record comes back with a desk note; then re-request '
          'with a precise name and a reason, or treat it as not performed. Do not repeat an order the desk has already refused or answered.\n'
          '- Never tell the patient you are ordering a test that the desk refused, held or did not find; say what you will do instead.\n'
          '- Message format: plain text without markdown, at most 110 words. React to what the patient just said in your own words (do not start every message the same way); ask at most three questions, numbered only when there is more than one; '
          'mention an order only if it was actually performed.')

ORDER_CLAUSE=re.compile(r"\b(?:i am|i'm|i will|i'll|we will|we are|we'll|let me)\s+(?:now\s+|also\s+|immediately\s+|urgently\s+|going to\s+)?(?:order|ordering|request|requesting|arrang\w+|get|getting|obtain\w*|send|sending|perform\w*|start\w*)\b[^.?!\n]{0,160}",re.I)

def speech_mismatch(text,refused):
    """Names in `refused` that the message claims to be ordering (token overlap with the clause), [] when the speech matches the action."""
    out=[]
    for m in ORDER_CLAUSE.finditer(text or ''):
        for n in refused:
            if overlap(m.group(0),n)>=0.5 and n not in out:out.append(n)
    return out

SYNC_NOTE=("[Desk note] Your last message tells the patient you are ordering {names}, but that order was not performed ({why}). Rewrite your message to the patient so it is accurate: say what you will do instead. "
           "Do not call the same test again unless you now justify it and it is allowed.")

EXPOSURE_ASKED=re.compile(r"\b(ticks?|insects?|mosquito\w*|bites?|animals?|pets?|livestock|exposures?|exposed|contact with|farm|garden|hobb\w+|occupation|work (?:with|around|as|in))\b",re.I)
EXPOSURE_NOTE=("Admission paused once: you have not asked about exposures. Before admitting, ask the patient briefly about occupation and hobbies, travel, contact with animals, insects or ticks (bites), unusual foods, and "
               "new medicines or supplements, then read the answer. If this is an emergency or the history is already complete, admit again.")
STAGNATION_NOTE=("[Desk] {n} consecutive requests returned nothing new. Before another order, step back: reconsider the whole picture (re-read the history and results, think of explanations outside the family of tests you have "
                 "been trying, and ask the patient about anything not yet asked), or admit with your best-supported hypothesis.")

class V5Tools(V3Tools):
    def __init__(self,*a,emit=None,urgent=False,**k):
        super().__init__(*a,**k)
        self.emit=emit or (lambda e:None);self.urgent=urgent;self.require_justification=True;self._depth=0;self.sig_misses={};self.turn_status={}
        self.v5={'justification_rejects':0,'desk_notes':0,'loop_guards':0,'orders_with_justification':0,'stagnation_nudges':0,'exposure_pauses':0};self.no_new=0;self.exposure_asked=False;self.exposure_paused=False
    def begin_turn(self):self.turn_status={}
    def note_doctor_text(self,text):
        if EXPOSURE_ASKED.search(text or ''):self.exposure_asked=True
    def admission_blocked(self):
        base=super().admission_blocked()
        if base:return base
        if not self.exposure_asked and not self.exposure_paused and not self.urgent:
            self.exposure_paused=True;self.v5['exposure_pauses']+=1;self.emit({'event':'exposure_pause'});return EXPOSURE_NOTE
        return ''
    @staticmethod
    def names_of(name,args):
        raw=[args.get('study_name')] if name=='request_radiology' else (args.get('test_names') or [])
        return [n for n in raw if isinstance(n,str) and n.strip()]
    def locked(self):return self.exchanges<self.min_exchanges or not self.exam_done
    def refused_names(self):
        return [n for n,s in self.turn_status.items() if s=='refused']
    def execute(self,name,args):
        if self._depth or name not in self.INVESTIGATIONS or not isinstance(args,dict):
            self._depth+=1
            try:return super().execute(name,args)
            finally:self._depth-=1
        just=args.pop('justification',None);names=self.names_of(name,args);turn_key=[n for n in names]
        if self.require_justification and not self.locked():
            exempt=self.urgent and names and all(classify(n)[2] for n in names)
            ok=isinstance(just,dict) and len(str(just.get('hypothesis','')).split())>=2 and len(str(just.get('decision','')).split())>=3
            if not ok and not exempt:
                self.v5['justification_rejects']+=1;self.emit({'event':'exam_justification_rejected','tool':name,'tests':names})
                for n in names:self.turn_status[n]='refused'
                return ("Order not placed (no cost): justify it. Include `justification` with `hypothesis` (the working diagnosis this test addresses) and `decision` (what a positive or negative result would change), "
                        "then request again. Order tests when you already have a plausible hypothesis.")
        if just:
            self.v5['orders_with_justification']+=1
            self.emit({'event':'exam_justification','tool':name,'tests':names,'hypothesis':str(just.get('hypothesis',''))[:300] if isinstance(just,dict) else str(just)[:300],'decision':str(just.get('decision',''))[:300] if isinstance(just,dict) else ''})
        sig=(name,tuple(sorted(norm(n) for n in names)))
        if names and self.sig_misses.get(sig,0)>=3 and not self.locked():
            self.v5['loop_guards']+=1;self.emit({'event':'loop_guard','tool':name,'tests':names,'repeats':self.sig_misses[sig]})
            for n in names:self.turn_status[n]='refused'
            return ("Loop guard: you have requested this same order several times and nothing new came back. Do not request it again. Change course: re-specify it precisely with a different name only if you can say why, "
                    "choose another test, talk to the patient, or admit if the evidence is enough.")
        self._depth+=1
        try:out=super().execute(name,args)
        finally:self._depth-=1
        return self.after(name,names,sig,out)
    def after(self,name,names,sig,out):
        text=out if isinstance(out,str) else json.dumps(out)
        try:obj,end=json.JSONDecoder().raw_decode(text.lstrip());rest=text.lstrip()[end:]
        except ValueError:obj,rest=None,''
        got=[]
        if isinstance(obj,dict):
            got=[f.get('requested') for f in obj.get('findings',[]) if isinstance(f,dict)]
            for n in (obj.get('atomic_scope_results') or []):
                try:sub=json.loads(n.get('output','')) if isinstance(n,dict) else {}
                except (ValueError,TypeError):sub={}
                got+=[f.get('requested') for f in sub.get('findings',[]) if isinstance(f,dict)]
        delivered=bool(got)
        for n in names:
            queued=("Queued: '"+n+"'") in text
            if any(isinstance(g,str) and norm(g)==norm(n) for g in got):self.turn_status[n]='performed'
            elif not queued and not text.lstrip().startswith('Order placed'):self.turn_status[n]='refused'
        self.sig_misses[sig]=0 if delivered else self.sig_misses.get(sig,0)+1
        self.no_new=0 if delivered else self.no_new+1
        nudge=''
        if self.require_justification and self.no_new>=4 and self.v5['stagnation_nudges']<3 and not self.urgent:
            self.v5['stagnation_nudges']+=1;self.emit({'event':'stagnation_nudge','consecutive':self.no_new});nudge='\n'+STAGNATION_NOTE.format(n=self.no_new);self.no_new=0
        if isinstance(obj,dict) and obj.get('unavailable_at_current_stage'):  # name nothing that exists only later: the doctor learns the time rule, not what the record holds
            obj['unavailable_at_current_stage']=[{'requested':x.get('requested'),'note':'Not obtainable in this encounter: a result of this kind only exists at a later stage of care (follow-up, later days) or retrospectively.'} for x in obj['unavailable_at_current_stage'] if isinstance(x,dict)]
            self.v5['temporal_unavailable']=self.v5.get('temporal_unavailable',0)+len(obj['unavailable_at_current_stage'])
            return json.dumps(obj,ensure_ascii=False)+rest+nudge
        if isinstance(obj,dict) and obj.get('not_available_in_this_case') and 'desk_note' not in obj:
            obj['desk_note']=desk_note_missing(obj['not_available_in_this_case']);self.v5['desk_notes']+=1
            return json.dumps(obj,ensure_ascii=False)+rest+nudge
        return (out+nudge) if nudge else out
