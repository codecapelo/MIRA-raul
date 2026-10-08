"""v4 subscription cascade: every proposal receives a blind second opinion.

No JEF credential or API is used. Agreement is judged through the same audited,
closed-book subscription transport; it is not a correctness or safety score.
"""
from .cascade import Cascade

class SubscriptionCascade(Cascade):
    def __init__(self):
        super().__init__(None,reviewers=('gpt-6.1-sol','gpt-6-astra','gpt-6-astra'),
                         triage='none',rescue=True,sweep=True,low_conf=0.5,agree_accept=False)
    def step(self,ctx,key,fn):
        if key=='verify':
            return super().step(ctx,key,lambda:{'combined':0,'disabled':True,'reason':'v4 always uses blind review; no JEF'})
        return super().step(ctx,key,fn)
    def same(self,ctx,key,a,b):
        def compare():
            out=self.llm_json(ctx,'gpt-6.1-sol',
                'Compare two proposed diagnoses for identity only. Do not judge correctness and do not introduce facts. '
                'Different mechanisms or specific causes are different diagnoses. '
                'Put ONE JSON object serialized as a string in content: {"same":bool,"reason":str}.',
                'Diagnosis A: '+a+'\nDiagnosis B: '+b)
            if not isinstance(out.get('same'),bool):raise ValueError('invalid agreement')
            return {'same':1.0 if out['same'] else 0.0,'source':'codex_subscription_identity_comparison'}
        v=self.step(ctx,key,compare)
        return None if v.get('failed') else v['same']
