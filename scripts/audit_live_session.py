"""Read-only audit of the approved session: no network or provider calls."""
import json
from pathlib import Path
import sys
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.api import live,main,prompt_cache
sid=live.current_id() or (main.ROOT/'cache/ui_live_session_id.txt').read_text().strip()
audit=live.counts(sid)
fixed=[r for r in audit['calls'] if r['provider']=='Timbre' and r.get('purpose')=='fixed_prompt']
readbacks=[r for r in audit['calls'] if r['provider']=='Timbre' and r.get('purpose')=='medicine_readback']
unexpected=[r for r in audit['calls'] if r['provider']=='Timbre' and r.get('purpose') not in {'fixed_prompt','medicine_readback'}]
cutoff=max((r['time'] for r in fixed),default='')
after=[r for r in audit['calls'] if r['provider']=='Timbre' and r['time']>cutoff]
path=main.STORE/(sid+'.json')
record=json.loads(path.read_text()) if path.exists() else None
result={'session_id':sid,'status':record['status'] if record else 'not_started',
 'answered_clips':len(record['answers']) if record else 0,
 'http_attempts':audit['real_http_attempts'],'groq_tokens':audit['groq_tokens'],
 'fixed_timbre_calls':len(fixed),'fixed_calls_per_prompt':dict(Counter(r.get('prompt_id') for r in fixed)),
 'fixed_cache_valid':all(prompt_cache.valid(q,t) for q,t in prompt_cache.texts(main.PROMPTS).items()),
 'dynamic_readback_timbre_calls':len(readbacks),'unexpected_timbre_calls':len(unexpected),
 'only_readback_timbre_after_fixed_generation':all(r.get('purpose')=='medicine_readback' for r in after),
 'final_doctor_record':({'fields':record['fields'],'medicines':record['medicines'],'red_flag':record['red_flag']} if record and record['status']!='in_progress' else None)}
output=main.ROOT/'logs'/('live_session_audit_'+sid+'.json');output.parent.mkdir(parents=True,exist_ok=True)
output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
