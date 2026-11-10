from pathlib import Path
import subprocess,json,math,shutil
ROOT=Path(__file__).resolve().parents[1]
plan=json.loads((ROOT/'voiceover-plan.json').read_text());plan['voice']='Avinash';(ROOT/'voiceover-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
media=ROOT/'public/media';vo=Path('/Users/sagarp/Desktop/demo_video/vo')
base=[105,90,150,300,120,240,235,90,210,150,90]
names=['Clinic queue','Patient quote','Logo and intake','Clip A','Prisma and validation','Clip B','Clip C','Reception','Doctor summaries','Recorded results','End card']
indices=[0,1,2,4,7,8,9,10];lines=[];over=[]
for i,line in enumerate(plan['lines']):
 src=vo/line.get('source_file',line['file']);duration=float(json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(src)]))['format']['duration'])
 target=media/line['file']
 # Fix streaming WAV headers and normalise each VO to match the real clips.
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(src),'-af','loudnorm=I=-16:TP=-1:LRA=11','-ar','48000','-c:a','pcm_s16le',str(target)],check=True)
 scene=indices[i];needed=math.ceil(duration*30)
 if needed>base[scene]:over.append(dict(line=i+1,duration=duration,original_scene_seconds=base[scene]/30,extension_frames=needed-base[scene]));base[scene]=needed
 lines.append(dict(**line,duration=duration,scene=scene))
# Recover 41 frames of visual hold time, preserving complete speech and clips.
base[2]-=30  # Logo/intake: 5s -> 4s, exactly fits its 4s voice-over.
base[8]-=11  # Doctor screenshots: 7s -> 6.633s, retains full 4.08s VO.
assert sum(base)==1800,base
for line in lines:assert math.ceil(line['duration']*30)<=base[line['scene']]
start=0;sections=[]
for i,(name,frames) in enumerate(zip(names,base)):
 sections.append(dict(name=name,fromFrame=start,frames=frames));start+=frames
captions=[]
for line in lines:
 begin=sections[line['scene']]['fromFrame'];captions.append(dict(fromFrame=begin,toFrame=begin+math.ceil(line['duration']*30),text=line['caption']))
# Clip captions use the saved real-session transcripts and the cached spoken prompts.
clip_cues={3:[(0,3.2,'Aaj aap kis takleef ke liye aaye hain? Apne shabdon mein bataiye.'),(3.2,5.5,'Mujhe actually 3 din se bukhaar hai'),(5.5,7.767,'aur gale mein bhi thoda dard hai.')],5:[(0,2.567,'Main abhi ke liye toh Dolo 650 le raha hoon.'),(2.567,6.767,'Aapne bataya: Dolo 650. Kya yeh sahi hai?')],6:[(0,2,'Haan, mujhe subah se seene mein dard hai'),(2,4,'aur bahut bhaari lag raha hai.'),(4.267,7.833,'Yeh zaroori lag raha hai. Kripya abhi reception par bataiye.')]}
for scene,cues in clip_cues.items():
 begin=sections[scene]['fromFrame']
 for a,b,text in cues:captions.append(dict(fromFrame=begin+round(a*30),toFrame=begin+round(b*30),text=text))
result=dict(frames=start,duration=start/30,sections=sections,voiceovers=lines,overlong=over,captions=captions)
(ROOT/'src/final-timeline.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');(ROOT/'out/final-timing.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['duration','overlong','sections']},indent=2))
