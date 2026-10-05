import json, os, re
from typing import Any, Dict, List, Optional
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
load_dotenv()
OLLAMA_BASE_URL=os.getenv('OLLAMA_BASE_URL','http://127.0.0.1:11434').rstrip('/')
OLLAMA_MODEL=os.getenv('OLLAMA_MODEL','llama3:latest')
OLLAMA_API_KEY=os.getenv('OLLAMA_API_KEY','').strip()
OLLAMA_TIMEOUT=float(os.getenv('OLLAMA_TIMEOUT','300'))
CORS_ORIGINS=[x.strip() for x in os.getenv('CORS_ORIGINS','http://localhost:5173').split(',') if x.strip()]
app=FastAPI(title='Lunor App Studio API', version='1.0.0')
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS or ['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
class IdeaReq(BaseModel): idea:str=Field(min_length=3)
class ProjectReq(BaseModel): project:Dict[str,Any]
class ModifyReq(BaseModel): project:Dict[str,Any]; change:str=Field(min_length=2)
COMPONENT_TYPES={'stat','button','announcement','list','form','card','text','image','toggle'}
def clean_json_text(raw:str)->Any:
    raw=raw.strip()
    raw=re.sub(r'^```(?:json)?\s*','',raw,flags=re.I)
    raw=re.sub(r'\s*```$','',raw)
    try:return json.loads(raw)
    except Exception: pass
    start=min([i for i in [raw.find('{'),raw.find('[')] if i>=0], default=-1)
    if start>=0:
        end=max(raw.rfind('}'),raw.rfind(']'))
        if end>start:
            return json.loads(raw[start:end+1])
    raise ValueError('Model did not return valid JSON')
async def ollama(prompt:str, system:str=''):
    payload={'model':OLLAMA_MODEL,'stream':False,'format':'json','options':{'temperature':0.2},'messages':[]}
    if system: payload['messages'].append({'role':'system','content':system})
    payload['messages'].append({'role':'user','content':prompt})
    try:
        headers={}
        if OLLAMA_API_KEY:
            headers['Authorization']=f'Bearer {OLLAMA_API_KEY}'

        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            r=await client.post(
                f'{OLLAMA_BASE_URL}/api/chat',
                json=payload,
                headers=headers
            )
            r.raise_for_status()
            data=r.json()
            return clean_json_text(data['message']['content'])
    except httpx.ConnectError:
        raise HTTPException(503, f'Ollama is unreachable at {OLLAMA_BASE_URL}. Start Ollama or set OLLAMA_BASE_URL to your GPU server.')
    except httpx.TimeoutException:
        raise HTTPException(504, 'Ollama timed out. Try a shorter prompt or a GPU-backed Ollama server.')
    except HTTPException: raise
    except Exception as e:
        raise HTTPException(502, f'Ollama request failed: {str(e)}')
async def ai_json(instruction:str, system:str):
    result=await ollama(instruction,system)
    if not isinstance(result,dict): raise HTTPException(502,'Ollama returned an unexpected structure.')
    return result
UNDERSTAND_SYSTEM='''You are Lunor App Studio's product discovery agent. Return ONLY JSON. Be concrete and tailored to the user's app idea. Do not invent unrelated features.'''
PLAN_SYSTEM='''You are Lunor App Studio's senior mobile architect. Return ONLY JSON. Prefer Flutter + Firebase for student prototypes unless the idea strongly requires another stack. Explain decisions simply.'''
BUILD_SYSTEM='''You are Lunor App Studio's app builder. Return ONLY JSON matching the supplied schema. Build a coherent mobile app from the user's requirements. Every screen and component must be derived from the idea. Use only supported component types: stat, button, announcement, list, form, card, text, image, toggle. Buttons should have meaningful actions using action values such as navigate:<Screen>, toast:<message>, submit:<form>, toggle:<name>. Keep content realistic and specific.'''
EXPLAIN_SYSTEM='''You are Lunor App Studio's code mentor. Return ONLY JSON. Explain the actual current project and generated app, not a generic tutorial.'''
LEARN_SYSTEM='''You are Lunor App Studio's learning coach. Return ONLY JSON. Create short, practical lessons based on the actual stack, architecture, and features in the project.'''
MODIFY_SYSTEM='''You are Lunor App Studio's modification agent. Return ONLY JSON. You receive an existing app definition. Make the smallest possible changes needed to satisfy the requested change. Preserve all existing screens, content, and functionality unless the request explicitly asks to remove/change them. Never replace the app with a generic demo.'''
SCHEMA='''App JSON schema: {"app_name":string,"tagline":string,"theme":{"primary":string,"dark":boolean},"screens":[{"name":string,"title":string,"components":[{"type":one of stat/button/announcement/list/form/card/text/image/toggle,"label":string,"value":string,"items":[string],"action":string,"fields":[{"name":string,"label":string,"type":string}]}]}]}'''
def as_list(v):
    return v if isinstance(v,list) else ([] if v is None else [v])
def normalize_plan(d):
    if not isinstance(d,dict): raise ValueError('Plan output must be an object')
    out=dict(d)
    for k in ('stack','screens','data_model','architecture','security','build_order','why_this_plan'):
        out[k]=as_list(out.get(k))
    out['stack']=[x for x in out['stack'] if isinstance(x,dict)]
    out['screens']=[x for x in out['screens'] if isinstance(x,dict)]
    out['data_model']=[x for x in out['data_model'] if isinstance(x,dict)]
    out['architecture']=[x for x in out['architecture'] if isinstance(x,dict)]
    out['security']=[str(x) for x in out['security']]
    out['build_order']=[str(x) for x in out['build_order']]
    out['why_this_plan']=[str(x) for x in out['why_this_plan']]
    return out
def normalize_learning(d):
    if not isinstance(d,dict): raise ValueError('Learning output must be an object')
    out=dict(d)
    out['lessons']=[x for x in as_list(out.get('lessons')) if isinstance(x,dict)]
    out['resources']=[x for x in as_list(out.get('resources')) if isinstance(x,dict)]
    for i,x in enumerate(out['lessons']):
        x.setdefault('id',f'lesson-{i+1}')
        x['topics']=as_list(x.get('topics'))
    return out
def validate_app(d:Dict[str,Any])->Dict[str,Any]:
    if not isinstance(d,dict) or not isinstance(d.get('screens'),list) or not d['screens']:
        raise ValueError('Missing screens')
    out={'app_name':str(d.get('app_name') or 'My App'),'tagline':str(d.get('tagline') or 'Built with Lunor App Studio'),'theme':d.get('theme') if isinstance(d.get('theme'),dict) else {'primary':'#ff5b45','dark':True},'screens':[]}
    for s in d['screens'][:10]:
        if not isinstance(s,dict): continue
        comps=[]
        for c in (s.get('components') or [])[:12]:
            if not isinstance(c,dict) or c.get('type') not in COMPONENT_TYPES: continue
            x={k:c[k] for k in ['type','label','value','items','action','fields'] if k in c}
            x['type']=c['type']; x['label']=str(c.get('label') or c.get('title') or '')
            if 'items' in x and not isinstance(x['items'],list): x['items']=[]
            if 'fields' in x and not isinstance(x['fields'],list): x['fields']=[]
            comps.append(x)
        out['screens'].append({'name':str(s.get('name') or f'Screen {len(out["screens"])+1}'),'title':str(s.get('title') or s.get('name') or 'Screen'),'components':comps})
    if not out['screens']: raise ValueError('No valid screens')
    return out
@app.get('/api/health')
async def health():
    ollama_ok=False
    try:
        headers={}
        if OLLAMA_API_KEY:
            headers['Authorization']=f'Bearer {OLLAMA_API_KEY}'

        async with httpx.AsyncClient(timeout=3) as client:
            r=await client.get(
                f'{OLLAMA_BASE_URL}/api/tags',
                headers=headers
            )
            ollama_ok=r.status_code==200
    except Exception: pass
    return {'ok':True,'ai_provider':'ollama','ai_enabled':ollama_ok,'ollama_url':OLLAMA_BASE_URL,'ollama_model':OLLAMA_MODEL,'mode':'AI_LOCAL_OLLAMA' if ollama_ok else 'AI_OLLAMA_UNREACHABLE'}
@app.post('/api/understand')
async def understand(req:IdeaReq):
    prompt=f'''Analyze this app idea:\n{req.idea}\n\nReturn JSON with keys: summary, users (array of objects with role, goals), features (array of objects with name, purpose, priority), constraints (array), assumptions (array), questions (array of objects with question, why), success_metrics (array).'''
    return await ai_json(prompt,UNDERSTAND_SYSTEM)
@app.post('/api/plan')
async def plan(req:ProjectReq):
    p=req.project
    prompt=f'''Create a technical product plan from this project state:\n{json.dumps(p,ensure_ascii=False)[:12000]}\n\nReturn JSON with keys: stack (array objects technology, reason), screens (array objects name,purpose), data_model (array objects entity,fields array), architecture (array objects layer,details), security (array), build_order (array), why_this_plan (array).'''
    try: return normalize_plan(await ai_json(prompt,PLAN_SYSTEM))
    except ValueError as e: raise HTTPException(502,f'Plan output was invalid: {e}')
@app.post('/api/build')
async def build(req:ProjectReq):
    p=req.project
    prompt=f'''Build the app described below.\nPROJECT:\n{json.dumps(p,ensure_ascii=False)[:14000]}\n\n{SCHEMA}\nReturn exactly one JSON object matching the schema. Create 3-6 useful screens and enough components to make the preview feel like a real app. The first screen should be the most useful home/dashboard screen.'''
    try: return validate_app(await ai_json(prompt,BUILD_SYSTEM))
    except ValueError as e: raise HTTPException(502,f'Build output was invalid: {e}')
@app.post('/api/modify')
async def modify(req:ModifyReq):
    current=req.project.get('app_definition') or req.project.get('app')
    if not current: raise HTTPException(400,'No existing app definition to modify.')
    prompt=f'''CURRENT APP:\n{json.dumps(current,ensure_ascii=False)[:18000]}\n\nUSER CHANGE:\n{req.change}\n\n{SCHEMA}\nReturn the FULL updated app JSON. Preserve everything unrelated to the request. If the request is ambiguous, make the safest minimal change and preserve the rest.'''
    try:
        updated=validate_app(await ai_json(prompt,MODIFY_SYSTEM))
        return updated
    except ValueError as e:
        raise HTTPException(502,f'Could not apply modification safely; current app was preserved. {e}')
@app.post('/api/explain')
async def explain(req:ProjectReq):
    prompt=f'''Explain this exact project to a student:\n{json.dumps(req.project,ensure_ascii=False)[:18000]}\n\nReturn JSON with keys: overview, architecture (array objects part, explanation), screen_walkthrough (array objects screen, explanation), key_concepts (array objects concept, explanation), next_steps (array).'''
    return await ai_json(prompt,EXPLAIN_SYSTEM)
@app.post('/api/learn')
async def learn(req:ProjectReq):
    prompt=f'''Create a learning path for this exact app project:\n{json.dumps(req.project,ensure_ascii=False)[:16000]}\n\nReturn JSON with keys: lessons (array objects id,title,level,why,topics array,practice), resources (array objects title,type,why), project_challenge, estimated_hours.'''
    try: return normalize_learning(await ai_json(prompt,LEARN_SYSTEM))
    except ValueError as e: raise HTTPException(502,f'Learning output was invalid: {e}')
@app.get('/')
async def root(): return {'name':'Lunor App Studio API','docs':'/docs'}
