import path from 'node:path';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {bundle} from '@remotion/bundler';
import {selectComposition,renderMedia,renderStill} from '@remotion/renderer';
const root=path.resolve(import.meta.dirname,'..');
const final=process.argv.includes('--final');
const withClips=final||process.argv.includes('--clips');
const id=final?'QueueSaathiFinal':withClips?'QueueSaathiClipPreview':'QueueSaathiPreview';
const outputFile=final?'final_raw.mp4':withClips?'preview_with_clips.mp4':'preview.mp4';
const browserExecutable=process.env.REMOTION_BROWSER_EXECUTABLE||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
for(const file of ['intake-language.png','question.png','medicine-readback.png','red-alert.png','doctor-token-14.png','doctor-token-31.png'])if(!fs.existsSync(path.join(root,'public/captures',file)))throw new Error('Missing real capture: '+file);
const clips=JSON.parse(fs.readFileSync(path.join(root,'src/clip-metadata.json'),'utf8'));
if(withClips)for(const clip of Object.values(clips)){
 const media=path.join(root,'public/media',clip.file);
 if(!fs.existsSync(media))throw new Error('Missing real video: '+clip.file);
 if(crypto.createHash('sha256').update(fs.readFileSync(media)).digest('hex')!==clip.sha256)throw new Error('Clip changed: regenerate its metadata before rendering '+clip.file);
}
const framesDir=path.join(root,'out',final?'final-frames':withClips?'clips-frames':'');fs.mkdirSync(framesDir,{recursive:true});
console.log(final?'Bundling final: real clips, Avinash VO and captions…':withClips?'Bundling real clips + their own audio; no VO/music…':'Bundling standalone Stage 1 (no audio, grey real-clip placeholders)…');
const serveUrl=await bundle({entryPoint:path.join(root,'src/index.tsx'),publicDir:path.join(root,'public')});
const composition=await selectComposition({serveUrl,id,browserExecutable});
const extra=withClips?Math.max(0,clips.C.frames-180):0;
const checks=final?[45,145,260,500,700,900,1150,1290,1450,1590,1770]:withClips?[75,340,425,560,708,860,960,1070,1085,1210,1309,1410+extra,1510+extra,1650+extra,1760+extra]:[75,235,340,550,780,960,1160,1295,1410,1510,1650,1760];
for(const originalFrame of checks){const frame=withClips&&!final&&originalFrame>=180?originalFrame-75:originalFrame;await renderStill({serveUrl,composition,browserExecutable,frame,output:path.join(framesDir,`frame-${frame}.png`),imageFormat:'png'});}
let previous=-1;
await renderMedia({serveUrl,composition,browserExecutable,codec:'h264',outputLocation:path.join(root,'out',outputFile),muted:!withClips,enforceAudioTrack:withClips,audioCodec:'aac',audioBitrate:'320k',sampleRate:48000,concurrency:3,crf:18,imageFormat:'jpeg',jpegQuality:92,pixelFormat:'yuv420p',onProgress:({progress})=>{const pc=Math.floor(progress*100);if(pc>=previous+5){console.log('Render '+pc+'%');previous=pc}}});
console.log(`Finished: video/out/${outputFile} · ${(composition.durationInFrames/30).toFixed(3)} seconds · 1920×1080 · 30 fps · ${final?'Avinash VO + real clip audio + captions':withClips?'original clip audio only':'no audio'}`);
