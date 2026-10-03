import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
pins={'openai/gpt-oss-120b':'dekallm/bf16','z-ai/glm-4.5-air':'novita/bf16','z-ai/glm-5':'streamlake/fp8','qwen/qwen3.5-397b-a17b':'parasail/fp8','openai/gpt-5.2':'openai','google/gemini-3.1-flash-lite-preview':'google-ai-studio'}
models={}
for model,pin in pins.items():
    data=json.loads((root/'reports/endpoints'/ (model.replace('/','__')+'.json')).read_text())['data']
    e=next(e for e in data['endpoints'] if e['tag']==pin)
    models[model]={'provider':pin,'provider_name':e['provider_name'],'pricing_verified':True,'context_tokens':0,'context_limit':e['context_length'],'max_tokens':24576,'usd_per_million':{k:float(e['pricing'][v])*1000000 for k,v in [('input','prompt'),('output','completion')]},'supports_logprobs':'logprobs' in e['supported_parameters'],'supported_parameters':e['supported_parameters']}
(root/'config').mkdir(exist_ok=True)
(root/'config/run1.json').write_text(json.dumps({'budget_usd':'18.50','models':models},indent=2))
