#!/usr/bin/env python3
"""Start QueueSaathi with Vite development or a single-server production build."""
import os
import argparse
import json
import uuid
from pathlib import Path
import signal
import subprocess
import sys
import time
from web_tool import npm_command

ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--prod',action='store_true',help='Build the frontend and serve it with the API on one port (no Vite server).')
parser.add_argument('--live',action='store_true',help='Explicit opt-in: enable real API calls for user-started intake sessions.')
parser.add_argument('--preflight',action='store_true',help='Print call counts/configuration without network access.')
parser.add_argument('--prepare-fixed-prompts',action='store_true',help='With --live: explicitly generate fixed audio once, then exit.')
parser.add_argument('--prompt',help='With --prepare-fixed-prompts: regenerate only this fixed prompt if changed.')
parser.add_argument('--prompt-language',choices=['hi','en','hinglish'],default='hinglish',help='Language of fixed prompts to precache.')
args=parser.parse_args()
if args.prompt and not args.prepare_fixed_prompts:parser.error('--prompt requires --prepare-fixed-prompts')
if args.prepare_fixed_prompts and not args.live:parser.error('--prepare-fixed-prompts requires explicit --live')
if args.preflight:
    sys.path.insert(0,str(ROOT))
    from app.api.main import live_plan
    print(json.dumps(live_plan(args.prompt_language),indent=2))
    raise SystemExit(0)
os.environ['GNANI_MOCK']='0' if args.live else '1'
if args.live:
    gate=ROOT/'cache/ui_live_session_id.txt'
    gate.parent.mkdir(parents=True,exist_ok=True)
    if gate.exists():sid=str(uuid.UUID(gate.read_text().strip()))
    else:
        sid=str(uuid.uuid4());gate.write_text(sid+'\n')
    os.environ['GNANI_UI_LIVE_APPROVED']='1'
    os.environ['GNANI_UI_LIVE_SESSION_ID']=sid
else:
    os.environ.pop('GNANI_UI_LIVE_APPROVED',None)
    os.environ.pop('GNANI_UI_LIVE_SESSION_ID',None)
if args.prepare_fixed_prompts:
    sys.path.insert(0,str(ROOT))
    from app.api import main, prompt_cache, languages
    prompt_cache.generate({'id':sid,'mock':False},languages.prompts(args.prompt_language,main.PROMPTS),only=args.prompt,language=args.prompt_language)
    raise SystemExit(0)
port=os.getenv('PORT','8000')
children=[]
process_options = {'start_new_session': True} if os.name == 'posix' else {'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP}

def stop_child(child):
    if child.poll() is not None:
        return
    try:
        if os.name == 'posix':
            os.killpg(child.pid, signal.SIGTERM)
        else:
            subprocess.run(['taskkill', '/PID', str(child.pid), '/T', '/F'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    except ProcessLookupError:
        pass
try:
    web_command=npm_command() if (ROOT/'web/package.json').exists() else None
    if args.prod:
        subprocess.run([*web_command,'run','build'],cwd=ROOT/'web',check=True)
    target='app.api.production:production_app' if args.prod else 'app.api.main:app'
    command=[sys.executable,'-m','uvicorn',target,'--host','127.0.0.1','--port',port]
    if args.prod:command.append('--factory')
    children.append(subprocess.Popen(command,**process_options))
    if web_command and not args.prod:
        children.append(subprocess.Popen([*web_command,'run','dev','--','--host','127.0.0.1'],cwd=ROOT/'web',**process_options))
    if args.prod:print(f'QueueSaathi app: http://127.0.0.1:{port} · API docs: http://127.0.0.1:{port}/api/docs',flush=True)
    print(f'QueueSaathi API: http://127.0.0.1:{port}/{"api/" if args.prod else ""}docs · {'LIVE: real API calls for patient intake' if args.live else 'MOCK: no paid calls'}.',flush=True)
    while all(child.poll() is None for child in children):
        time.sleep(.2)
    failed=next(child for child in children if child.poll() is not None)
    if failed.returncode:
        raise SystemExit(failed.returncode)
except KeyboardInterrupt:
    pass
finally:
    for child in children:
        stop_child(child)
    for child in children:
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()
