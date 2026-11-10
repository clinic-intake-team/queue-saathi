"""Loudness-normalise the rendered final and verify timing, streams and audio."""
from pathlib import Path
import subprocess,json,re,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
raw=ROOT/'out/final_raw.mp4';out=ROOT/'out/queuesaathi_demo.mp4'
timing=json.loads((ROOT/'src/final-timeline.json').read_text())
def run(args):return subprocess.run(args,capture_output=True,text=True,check=True)
def measure(path):
 result=run(['ffmpeg','-hide_banner','-nostdin','-i',str(path),'-vn','-af','loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json','-f','null','-'])
 return json.loads(re.findall(r'\{[\s\S]*?\}',result.stderr)[-1])
m=measure(raw)
af=f"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true"
run(['ffmpeg','-hide_banner','-nostdin','-y','-i',str(raw),'-map','0:v:0','-map','0:a:0','-c:v','copy','-af',af,'-ar','48000','-c:a','aac','-b:a','320k','-movflags','+faststart','-t',str(timing['duration']),str(out)])
probe=json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(out)]).stdout)
v=next(s for s in probe['streams'] if s['codec_type']=='video')
assert timing['frames']==1800 and timing['duration']==60
assert int(v['nb_frames'])==timing['frames'];assert (v['width'],v['height'],v['avg_frame_rate'])==(1920,1080,'30/1')
assert abs(float(probe['format']['duration'])-timing['duration'])<.05
loudness=measure(out)
assert abs(float(loudness['input_i'])+16)<.5,loudness
assert float(loudness['input_tp'])<=-1,loudness
for line in timing['voiceovers']:
 s=timing['sections'][line['scene']];assert line['duration']<=s['frames']/30
 assert line['scene'] not in [3,5,6]
meta=json.loads((ROOT/'src/clip-metadata.json').read_text())
for clip in meta.values():
 for path in [ROOT/'public/media'/clip['file'],Path('/Users/sagarp/Desktop/demo_video')/clip['file']]:assert hashlib.sha256(path.read_bytes()).hexdigest()==clip['sha256']
# Validate the raw render's clip waveforms against their sources at their shifted starts.
def decode(path):return np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-map','0:a:0','-ac','1','-ar','48000','-f','f32le','-']),dtype='<f4')
rawaudio=decode(raw);checks=[]
for letter,scene in [('A',3),('B',5),('C',6)]:
 src=decode(ROOT/'public/media'/meta[letter]['file']);offset=48000 if letter!='B' else 24000
 start=timing['sections'][scene]['fromFrame']/30
 a=src[offset:offset+48000].astype(float);b=rawaudio[round(start*48000)+offset:round(start*48000)+offset+48000].astype(float)
 corr=float(np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)));assert corr>.99,(letter,corr)
 checks.append(dict(clip=letter,start=start,correlation=corr))
report=dict(output=str(out),duration=timing['duration'],resolution=[1920,1080],fps=30,voice='Avinash',model='timbre-v3.0',voiceover_lines=8,clip_audio=checks,originals_unchanged=True,music=False,loudness=loudness,overlong=timing['overlong'],sections=[dict(name=s['name'],start=s['fromFrame']/30) for s in timing['sections']],checks_passed=True)
(ROOT/'out/final-validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
