import path from 'node:path';
import fs from 'node:fs';
import {bundle} from '@remotion/bundler';
import {selectComposition,renderMedia,renderStill} from '@remotion/renderer';
const root=path.resolve(import.meta.dirname,'..');
const browserExecutable='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const timing=JSON.parse(fs.readFileSync(path.join(root,'src/submission-timeline.json'),'utf8'));
const out=path.join(root,'out/submission');fs.mkdirSync(out,{recursive:true});
console.log('Bundling Submission · '+timing.duration+' seconds · no API calls');
const serveUrl=await bundle({entryPoint:path.join(root,'src/index.tsx'),publicDir:path.join(root,'public')});
const composition=await selectComposition({serveUrl,id:'Submission',browserExecutable});
for(const section of timing.sections){const frame=Math.min(section.fromFrame+Math.round(section.frames*.7),section.fromFrame+section.frames-1);await renderStill({serveUrl,composition,browserExecutable,frame,output:path.join(out,section.kind+'.png'),imageFormat:'png'});}
console.log('Review stills saved.');
let last=-1;
await renderMedia({serveUrl,composition,browserExecutable,codec:'h264',outputLocation:path.join(out,'submission_raw.mp4'),enforceAudioTrack:true,audioCodec:'aac',audioBitrate:'320k',sampleRate:48000,concurrency:3,crf:18,imageFormat:'jpeg',jpegQuality:92,pixelFormat:'yuv420p',onProgress:({progress})=>{const pc=Math.floor(progress*100);if(pc>=last+5){console.log('Submission render '+pc+'%');last=pc;}}});
console.log('Finished Submission raw: '+composition.durationInFrames+' frames / 30fps.');
