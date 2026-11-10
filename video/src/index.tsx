import React from 'react';
import {Submission} from './submission';
import submissionTimeline from './submission-timeline.json';
import {Composition,registerRoot} from 'remotion';
import {QueueSaathiVideo,CLIP_PREVIEW_FRAMES} from './video';
import finalTimeline from './final-timeline.json';
const Root=()=> <><Composition id="QueueSaathiPreview" component={QueueSaathiVideo} durationInFrames={1800} fps={30} width={1920} height={1080}/><Composition id="QueueSaathiClipPreview" component={QueueSaathiVideo} defaultProps={{withClips:true}} durationInFrames={CLIP_PREVIEW_FRAMES} fps={30} width={1920} height={1080}/><Composition id="QueueSaathiFinal" component={QueueSaathiVideo} defaultProps={{withClips:true,final:true}} durationInFrames={finalTimeline.frames} fps={30} width={1920} height={1080}/><Composition id="Submission" component={Submission} durationInFrames={submissionTimeline.frames} fps={30} width={1920} height={1080}/></>;
registerRoot(Root);
