"""Offline submission preparation; copies approved assets and builds a fixed timeline."""
from pathlib import Path
import subprocess,json,hashlib,math,shutil,re
ROOT=Path(__file__).resolve().parents[1];SOURCE=Path('/Users/sagarp/Desktop/demo_video');MEDIA=ROOT/'public/media/submission';MEDIA.mkdir(parents=True,exist_ok=True)
plan=json.loads((ROOT/'submission-voiceover-plan.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
protected={str(p):sha(p) for p in [ROOT/'out/queuesaathi_demo.mp4',ROOT/'src/final-timeline.json',ROOT/'src/clip-metadata.json']}
(ROOT/'out/submission-protected.json').write_text(json.dumps(protected,indent=2)+'\n')
# Ordered visual segments. All VO ends before the following real recording begins.
entries=[('Clinic queue',4,1,'queue'),('Patient quote',3.5,2,'quote'),('Logo and intake',8,3,'intro'),('Pipeline',12,4,'pipeline'),('Language choice',6,5,'language'),('Complaint exchange',9.5,0,'clipA'),('Duration introduction',5.5,6,'durationIntro'),('Duration exchange',2.5,0,'clipF'),('Medicine keyterms',8.5,7,'keyterms'),('Medicine read-back',7.5,0,'clipB'),('Patient red alert',8,0,'clipC'),('Reception escalation',6.5,8,'reception'),('Doctor queue introduction',7,9,'queueIntro'),('Doctor queue',4,0,'doctorQueue'),('Doctor evidence introduction',7.5,10,'doctorIntro'),('Token 31 evidence',7,0,'doctorRed'),('Token 14 evidence',9.5,0,'doctorFever'),('Evaluation results',17,11,'results'),('Real results row',4,0,'resultsStats'),('Principles',6.5,12,'principles'),('End card',6,13,'end')]
sections=[];voiceovers=[];captions=[];clips={};cursor=0
for i,line in enumerate(plan['lines'],1):
 src=SOURCE/'vo'/line['file'];target=MEDIA/line['file'];duration=float(json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(src)]))['format']['duration'])
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(src),'-af','loudnorm=I=-16:TP=-1.5:LRA=11','-ar','48000','-c:a','pcm_s16le',str(target)],check=True)
 line.update(duration=duration,number=i,source_hash=sha(src))
for name,seconds,vo,kind in entries:
 frames=round(seconds*30)
 if vo:frames=max(frames,math.ceil(plan['lines'][vo-1]['duration']*30)+3)
 s=dict(name=name,fromFrame=cursor,frames=frames,kind=kind,vo=vo);sections.append(s)
 if vo:
  line=plan['lines'][vo-1];start=cursor+3;assert math.ceil(line['duration']*30)+3<=frames,(vo,frames,line['duration'])
  voiceovers.append(dict(**line,fromFrame=start,frames=math.ceil(line['duration']*30)))
  # Readable phrase captions, derived only from the approved transcript.
  words=line['caption'].split();groups=[];chunk=[]
  for word in words:
   chunk.append(word)
   if len(' '.join(chunk))>65 or word.endswith(('.', '?', '!')):groups.append(' '.join(chunk));chunk=[]
  if chunk:groups.append(' '.join(chunk))
  weights=[len(g.split()) for g in groups];total=sum(weights);elapsed=0
  for g,w in zip(groups,weights):
   a=start+round(line['duration']*30*elapsed/total);elapsed+=w;b=start+round(line['duration']*30*elapsed/total)
   captions.append(dict(fromFrame=a,toFrame=b,text=g))
 else:
  src=SOURCE/(kind+'.mp4');shutil.copy2(src,MEDIA/src.name)
  probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_type,width,height,nb_frames:format=duration','-of','json',str(src)]));v=next(s for s in probe['streams'] if s['codec_type']=='video')
  clips[kind]=dict(file=src.name,frames=int(v['nb_frames']),width=v['width'],height=v['height'],source_hash=sha(src),fromFrame=cursor,silent=kind in ['doctorQueue','resultsStats'])
  assert clips[kind]['frames']<=frames
 cursor+=frames
# Actual real-clip speech; timings follow the approved cuts and retained transcripts.
cues={
'clipA':[(0,3.2,'Aaj aap kis takleef ke liye aaye hain? Apne shabdon mein bataiye.'),(3.2,5.5,'Mujhe actually 3 din se bukhaar hai'),(5.5,7.767,'aur gale mein bhi thoda dard hai.')],
'clipF':[(0,1.3667,'Yeh takleef kab se hai?'),(1.3667,2.0333,'Three days.')],
'clipB':[(0,2.567,'Main abhi ke liye toh Dolo 650 le raha hoon.'),(2.567,6.767,'Aapne bataya: Dolo 650. Kya yeh sahi hai?')],
'clipC':[(0,2,'Haan, mujhe subah se seene mein dard hai'),(2,4,'aur bahut bhaari lag raha hai.'),(4.267,7.833,'Yeh zaroori lag raha hai. Kripya abhi reception par bataiye.')],
'doctorRed':[(1,3,'Haan, mujhe subah se seene mein dard hai'),(3,4.69,'aur bahut bhaari lag raha hai.')],
'doctorFever':[(5.1,7.82,'Main abhi ke liye toh Dolo 650 le raha hoon.')]}
for kind,rows in cues.items():
 for a,b,text in rows:captions.append(dict(fromFrame=clips[kind]['fromFrame']+round(a*30),toFrame=clips[kind]['fromFrame']+round(b*30),text=text))
assert 3600<=cursor<=5400
# No live speech overlap with a real clip, including the complete evidence tracks.
for line in voiceovers:
 for clip in clips.values():assert line['fromFrame']+line['frames']<=clip['fromFrame'] or clip['fromFrame']+clip['frames']<=line['fromFrame']
result=dict(frames=cursor,duration=cursor/30,sections=sections,voiceovers=voiceovers,captions=captions,clips=clips,music=False)
(ROOT/'src/submission-timeline.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
(ROOT/'out/submission-timing.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(f'Prepared Submission: {cursor/30:.3f} seconds, {cursor} frames; 13 approved voice-overs; no overlap.')
