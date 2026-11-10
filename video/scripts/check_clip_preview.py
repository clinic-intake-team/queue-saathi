#!/usr/bin/env python3
"""Verify picture length and that the supplied clips are the sole, unity-gain audio."""
from pathlib import Path
import hashlib
import json
import math
import subprocess
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
META=json.loads((ROOT/'src/clip-metadata.json').read_text())
OUTPUT=ROOT/'out/preview_with_clips.mp4'


def decode(path):
    return np.frombuffer(subprocess.check_output(['ffmpeg','-hide_banner','-loglevel','error','-i',str(path),'-map','0:a:0','-ac','1','-ar','48000','-f','f32le','-']),dtype='<f4')


def main():
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_type,codec_name,width,height,avg_frame_rate,nb_frames,duration,sample_rate,channels:format=duration,size','-of','json',str(OUTPUT)],text=True))
    video=next(row for row in probe['streams'] if row['codec_type']=='video')
    audio=next(row for row in probe['streams'] if row['codec_type']=='audio')
    extension=max(0,META['C']['frames']-180);frames=1800+extension-75
    assert video['nb_frames']==str(frames)
    assert video['avg_frame_rate']=='30/1' and (video['width'],video['height'])==(1920,1080)
    assert abs(float(probe['format']['duration'])-frames/30)<.05
    assert audio['codec_name']=='aac' and audio['sample_rate']=='48000'
    mix=decode(OUTPUT);active=np.zeros(len(mix),dtype=bool);details=[]
    for letter,start in [('A',11.5),('B',25.5),('C',33.5)]:
        meta=META[letter];source=ROOT/'public/media'/meta['file'];original=Path('/Users/sagarp/Desktop/demo_video')/meta['file']
        assert hashlib.sha256(source.read_bytes()).hexdigest()==meta['sha256']
        assert hashlib.sha256(original.read_bytes()).hexdigest()==meta['sha256']
        pcm=decode(source);offset=48000 if letter!='B' else 24000
        expected=pcm[offset:offset+48000].astype(np.float64)
        nominal=int(start*48000)+offset;margin=2048
        actual=mix[nominal-margin:nominal+len(expected)+margin].astype(np.float64)
        fft_size=1<<math.ceil(math.log2(len(actual)+len(expected)-1))
        correlation=np.fft.irfft(np.fft.rfft(actual,fft_size)*np.conj(np.fft.rfft(expected,fft_size)),fft_size)
        shift=int(np.argmax(correlation[:margin*2+1]));aligned=actual[shift:shift+len(expected)]
        similarity=float(np.dot(expected,aligned)/(np.linalg.norm(expected)*np.linalg.norm(aligned)))
        gain=float(20*np.log10(np.sqrt(np.mean(aligned**2))/np.sqrt(np.mean(expected**2))))
        assert similarity>.95,(letter,similarity)
        assert abs(gain)<.35,(letter,gain)
        begin=max(0,int(start*48000)-6000);end=min(len(mix),int((start+meta['frames']/30)*48000)+6000);active[begin:end]=True
        details.append(dict(clip=letter,start_seconds=start,played_seconds=meta['frames']/30,audio_correlation=similarity,level_change_db=gain,offset_samples=shift-margin,source_unchanged=True))
    outside=mix[~active]
    outside_rms_db=float(20*np.log10(max(float(np.sqrt(np.mean(outside**2))),1e-12)))
    assert outside_rms_db<-80,outside_rms_db
    sections=[('Clinic queue',0),('Patient quote',6),('Logo and intake',9),('Clip A',14),('Prisma and validation',24),('Clip B',28),('Clip C',36),('Reception',(1260+extension)/30),('Doctor summaries',(1350+extension)/30),('Recorded results',(1560+extension)/30),('End card',(1710+extension)/30)]
    sections=[(label,start-2.5 if start else 0) for label,start in sections]
    result=dict(output=str(OUTPUT),duration_seconds=frames/30,frames=frames,resolution=[1920,1080],fps=30,voiceover=False,music=False,clips=details,non_clip_audio_rms_db=outside_rms_db,sections=[dict(section=label,start_seconds=start) for label,start in sections],probe=probe)
    (ROOT/'out/clip-preview-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'duration_seconds':frames/30,'clip_audio':details,'non_clip_audio_rms_db':outside_rms_db,'passed':True},indent=2))

if __name__=='__main__':main()
