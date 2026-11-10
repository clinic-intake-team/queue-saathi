"""Final mix and validation for Submission; zero provider calls."""
from pathlib import Path
import subprocess,json,re,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'out/submission';RAW=OUT/'submission_raw.mp4';DEST=Path('/Users/sagarp/Desktop/demo_video/queuesaathi_submission.mp4')
timing=json.loads((ROOT/'src/submission-timeline.json').read_text())
def run(a):return subprocess.run(a,capture_output=True,text=True,check=True)
def measure(p):
 r=run(['ffmpeg','-hide_banner','-nostdin','-i',str(p),'-vn','-af','loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json','-f','null','-'])
 return json.loads(re.findall(r'\{[\s\S]*?\}',r.stderr)[-1])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def decode(p):return np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-map','0:a:0','-ar','48000','-ac','1','-f','f32le','-']),dtype='<f4')
protected=json.loads((ROOT/'out/submission-protected.json').read_text())
for p,h in protected.items():assert sha(Path(p))==h,p
m=measure(RAW)
af=f'loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={m["input_i"]}:measured_TP={m["input_tp"]}:measured_LRA={m["input_lra"]}:measured_thresh={m["input_thresh"]}:offset={m["target_offset"]}:linear=true'
run(['ffmpeg','-hide_banner','-nostdin','-y','-i',str(RAW),'-map','0:v','-map','0:a','-c:v','copy','-af',af,'-c:a','aac','-b:a','320k','-ar','48000','-t',str(timing['duration']),'-movflags','+faststart',str(DEST)])
probe=json.loads(run(['ffprobe','-v','error','-show_entries','stream=codec_type,codec_name,width,height,avg_frame_rate,nb_frames,duration:format=duration,size','-of','json',str(DEST)]).stdout)
v=next(s for s in probe['streams'] if s['codec_type']=='video');assert (v['width'],v['height'],v['avg_frame_rate'],int(v['nb_frames']))==(1920,1080,'30/1',timing['frames'])
assert abs(float(probe['format']['duration'])-timing['duration'])<.05
loudness=measure(DEST);assert abs(float(loudness['input_i'])+16)<.5,loudness;assert float(loudness['input_tp'])<=-1,loudness
rawaudio=decode(RAW);checks=[]
for name,clip in timing['clips'].items():
 source=Path('/Users/sagarp/Desktop/demo_video')/clip['file'];assert sha(source)==clip['source_hash']
 if clip['silent']:continue
 pcm=decode(ROOT/'public/media/submission'/clip['file']);offset=round((1.45 if name=='clipF' else 6 if name=='doctorFever' else 2 if name=='doctorRed' else 1)*48000);length=round((.4 if name=='clipF' else 1)*48000)
 a=pcm[offset:offset+length].astype(float);begin=clip['fromFrame']*1600+offset;b=rawaudio[begin:begin+length].astype(float)
 corr=float(np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)));assert corr>.99,(name,corr);checks.append(dict(clip=name,correlation=corr))
vo_checks=[]
for line in timing['voiceovers']:
 source=Path('/Users/sagarp/Desktop/demo_video/vo')/line['file'];assert sha(source)==line['source_hash']
 for clip in timing['clips'].values():assert line['fromFrame']+line['frames']<=clip['fromFrame'] or clip['fromFrame']+clip['frames']<=line['fromFrame']
 pcm=decode(ROOT/'public/media/submission'/line['file']);a=pcm[19200:67200].astype(float);begin=line['fromFrame']*1600+19200;b=rawaudio[begin:begin+len(a)].astype(float)
 corr=float(np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)));assert corr>.99,(line['file'],corr);vo_checks.append(dict(file=line['file'],correlation=corr))
report=dict(output=str(DEST),duration=timing['duration'],fps=30,resolution=[1920,1080],composition='Submission',provider_calls=0,music=False,loudness=loudness,voiceover_checks=vo_checks,clip_checks=checks,original_60s_unchanged=True,all_inputs_unchanged=True,sections=[dict(name=s['name'],start_seconds=s['fromFrame']/30) for s in timing['sections']],probe=probe,passed=True)
(OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
