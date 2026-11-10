"""Cut only approved submission excerpts; never overwrite input recordings."""
from pathlib import Path
import hashlib,json,re,subprocess
ROOT=Path(__file__).resolve().parents[2]
FOLDER=Path('/Users/sagarp/Desktop/demo_video')
CACHE=ROOT/'cache/submission_review';CACHE.mkdir(parents=True,exist_ok=True)
FPS=30
PLANS=[
 dict(name='clipF',source='patient1_clean.mp4',segments=[(1702,1743,'app'),(1835,1855,'patient')]),
 dict(name='doctorQueue',source='doctor.mov',segments=[(360,480,'silent')]),
 dict(name='doctorRed',source='doctor.mov',segments=[(1335,1545,'evidence')]),
 dict(name='doctorFever',source='doctor.mov',segments=[(525,690,'evidence'),(705,825,'evidence')]),
 dict(name='resultsStats',source='home.mov',segments=[(450,540,'silent')],hold=30,crop='crop=1680:330:120:0,scale=1920:-2,pad=1920:1080:0:(oh-ih)/2:color=0x05070D')]
def run(args):return subprocess.run(args,capture_output=True,text=True,check=True)
def measure(path,start=None,end=None):
 cmd=['ffmpeg','-hide_banner','-nostdin']
 if start is not None:cmd+=['-ss',str(start),'-t',str(end-start)]
 cmd+=['-i',str(path),'-vn','-af','loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json','-f','null','-']
 return json.loads(re.findall(r'\{[\s\S]*?\}',run(cmd).stderr)[-1])
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
hashes={p['source']:digest(FOLDER/p['source']) for p in PLANS}
results=[]
for p in PLANS:
 target=FOLDER/(p['name']+'.mp4');temp=CACHE/(p['name']+'_balanced.mp4')
 if target.exists():raise RuntimeError('Refusing to overwrite '+str(target))
 source=FOLDER/p['source'];gain=0;levels={}
 if p['name']=='clipF':
  for a,b,role in p['segments']:levels[role]=measure(source,a/FPS,b/FPS)
  gain=float(levels['app']['input_i'])-float(levels['patient']['input_i'])
  if not -40<gain<40:raise RuntimeError(('Unusable voice measurement',levels))
 filters=[]
 for i,(a,b,role) in enumerate(p['segments']):
  vf=f'[0:v]trim=start_frame={a}:end_frame={b},setpts=PTS-STARTPTS'
  if p.get('crop'):vf+=','+p['crop']
  if p.get('hold'):vf+=f',tpad=stop_mode=clone:stop_duration={p["hold"]/FPS}'
  filters.append(vf+f'[v{i}]')
  vol='0' if role=='silent' else f'{gain}dB' if role=='patient' else '0dB'
  af=f'[0:a]atrim=start={a/FPS}:end={b/FPS},asetpts=PTS-STARTPTS,volume={vol}'
  if p.get('hold'):af+=f',apad=pad_dur={p["hold"]/FPS}'
  filters.append(af+f'[a{i}]')
 filters.append(''.join(f'[v{i}][a{i}]' for i in range(len(p['segments'])))+f'concat=n={len(p["segments"])}:v=1:a=1[v][a]')
 run(['ffmpeg','-hide_banner','-nostdin','-y','-i',str(source),'-filter_complex',';'.join(filters),'-map','[v]','-map','[a]','-r','30','-c:v','libx264','-preset','medium','-crf','18','-threads','4','-pix_fmt','yuv420p','-c:a','aac','-b:a','320k','-ar','48000',str(temp)])
 frames=sum(b-a for a,b,_ in p['segments'])+p.get('hold',0);duration=frames/FPS
 silent=all(role=='silent' for _,_,role in p['segments'])
 af=[]
 if not silent:
  m=measure(temp);af=['-af',f'loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={m["input_i"]}:measured_TP={m["input_tp"]}:measured_LRA={m["input_lra"]}:measured_thresh={m["input_thresh"]}:offset={m["target_offset"]}:linear=true']
 run(['ffmpeg','-hide_banner','-nostdin','-n','-i',str(temp),'-map','0:v','-map','0:a','-c:v','copy',*af,'-ar','48000','-c:a','aac','-b:a','320k','-t',str(duration),'-movflags','+faststart',str(target)])
 probe=json.loads(run(['ffprobe','-v','error','-show_entries','stream=codec_type,nb_frames,width,height:format=duration','-of','json',str(target)]).stdout)
 v=next(s for s in probe['streams'] if s['codec_type']=='video');assert int(v['nb_frames'])==frames
 assert abs(float(probe['format']['duration'])-duration)<.05
 m=None if silent else measure(target)
 if m and abs(float(m['input_i'])+16)>=.6:
  # Sparse evidence playback can under-shoot loudnorm's gated target.
  adjusted=CACHE/(p['name']+'_relevel.mp4');gain_fix=-16-float(m['input_i'])
  run(['ffmpeg','-v','error','-y','-i',str(target),'-c:v','copy','-af',f'volume={gain_fix}dB,alimiter=limit=0.841395:level=false:latency=true','-c:a','aac','-b:a','320k','-ar','48000','-t',str(duration),'-movflags','+faststart',str(adjusted)])
  target.write_bytes(adjusted.read_bytes());m=measure(target)
 if m:
  assert abs(float(m['input_i'])+16)<.6,(p['name'],m)
  assert float(m['input_tp'])<=-1,(p['name'],m)
 row=dict(name=p['name'],source=p['source'],source_segments=p['segments'],duration=duration,frames=frames,patient_gain_db=gain,voice_levels=levels,loudness=m,silent=silent,output=str(target))
 results.append(row);(CACHE/'submission_cut_results.json').write_text(json.dumps(dict(original_hashes=hashes,clips=results),indent=2)+'\n')
 print(json.dumps({k:row[k] for k in ['name','duration','patient_gain_db','loudness','silent']}),flush=True)
assert all(digest(FOLDER/n)==h for n,h in hashes.items())
print('All source files unchanged; all five clips complete.',flush=True)
