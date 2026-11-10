#!/usr/bin/env python3
"""Doctor presentation and real browser audio playback check; no patient data/providers."""
import io
import json
import math
import mimetypes
import os
from pathlib import Path
import struct
import sys
import tempfile
import wave
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright,expect
from app.api import main,clinic_access
ROOT=Path(__file__).resolve().parents[1]


def run():
    with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'GNANI_MOCK':'1','CLINIC_PIN':'1234'}),patch.object(main,'STORE',Path(folder)/'sessions'),patch.object(main,'AUDIO',Path(folder)/'audio'),patch.object(clinic_access,'SECRET',Path(folder)/'secret'),patch('requests.sessions.Session.request',side_effect=AssertionError('No provider calls')),sync_playwright() as p:
        main.AUDIO.mkdir();name='11111111-1111-4111-8111-111111111111.wav';clip='/audio/'+name
        with wave.open(str(main.AUDIO/name),'wb') as audio:
            audio.setparams((1,2,16000,0,'NONE','not compressed'))
            audio.writeframes(b''.join(struct.pack('<h',int(math.sin(i*2*math.pi*440/16000)*1500)) for i in range(24000)))
        transcript='I have chest pain and heaviness since this morning.'
        def field(value,evidence=''):return {'value':value,'status':'ok','evidence':evidence,'clip_url':clip}
        complaint=field({'summary':'chest pain and heaviness since this morning','symptoms':['chest pain','heaviness in chest']},transcript)
        flag={'alert':True,'status':'alert','keyword_flags':['chest pain'],'llm_flags':['Chest pain']}
        checked={'complaint':complaint,'red_flag_symptoms':field(['Chest pain'],transcript),'visit_reason':field(None)}
        session={'id':'22222222-2222-4222-8222-222222222222','created_at':'2026-11-10T01:00:00+00:00','mock':False,'status':'red_flag','intake_complete':False,'stopped_at':'P2','index':2,'question_id':'RF','retry':False,'medicines':[],'fields':{'age':field(60),'sex':field('male'),**checked},'red_flag':flag,'answers':[{'question':'P1','transcript':'I am 60.','extracted':{'age':field(60),'sex':field('male')},'source':'audio','clip_url':clip},{'question':'P2','transcript':transcript,'extracted':checked,'source':'audio','clip_url':clip,'red_flag':flag}]}
        main.save(session);client=TestClient(main.app)
        ranged=client.get(clip,headers={'Range':'bytes=0-43'});assert ranged.status_code==206 and ranged.content[:4]==b'RIFF'
        browser=p.chromium.launch(channel='chrome',headless=True,args=['--autoplay-policy=no-user-gesture-required'])
        page=browser.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        def route(r):
            request=r.request
            if not request.url.startswith('http://clinic.test/'):r.abort();return
            path=request.url.removeprefix('http://clinic.test')
            if path.startswith('/api/'):
                response=client.request(request.method,path.removeprefix('/api'),headers={k:v for k,v in request.headers.items() if k.lower() in {'authorization','content-type','range'}},content=request.post_data_buffer)
                r.fulfill(status=response.status_code,headers=dict(response.headers),body=response.content);return
            asset=ROOT/'web/dist'/path.split('?')[0].lstrip('/')
            if not asset.is_file():asset=ROOT/'web/dist/index.html'
            r.fulfill(content_type=mimetypes.guess_type(asset.name)[0] or 'application/octet-stream',body=asset.read_bytes())
        page.route('**/*',route)
        page.goto('http://clinic.test/doctor');page.get_by_label('Clinic PIN',exact=True).fill('1234');page.get_by_role('button',name='Unlock Doctor view').click()
        banner=page.locator('.doctor-alert');expect(banner).to_be_visible()
        expect(banner.locator('.red-flag-source')).to_have_text('Chest pain — reported at the complaint question')
        assert banner.locator('audio').count()==1
        assert abs(banner.bounding_box()['width']-page.locator('.doctor-layout').bounding_box()['width'])<1
        expect(page.locator('.at-a-glance')).to_have_text('60-year-old man. Chest pain and heaviness since this morning.')
        expect(page.locator('.doctor-fields dd').first).to_contain_text('Chest pain and heaviness since this morning')
        audio=banner.locator('audio');assert audio.get_attribute('preload')=='metadata'
        page.wait_for_function('document.querySelector(".doctor-alert audio").duration>0')
        assert abs(audio.evaluate('el=>el.duration')-1.5)<.05
        audio.evaluate('el=>el.play()');page.wait_for_function('document.querySelector(".doctor-alert audio").currentTime>.2');audio.evaluate('el=>el.pause()')
        # Each evidence player loads metadata and plays; no 00:00 placeholder duration.
        for player in page.locator('.field-evidence audio').all():
            assert player.evaluate('el=>el.duration')>0
            player.evaluate('el=>el.play()');page.wait_for_timeout(250);assert player.evaluate('el=>el.currentTime')>0;player.evaluate('el=>el.pause()')
        page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        assert not errors,errors
        browser.close()
    print(json.dumps({'passed':['full-width single-source red banner','one alert quote/player','deduplicated capitalised complaint','WAV byte-range response','metadata duration 1.5s','audio playback advances','390px no overflow'],'provider_calls':0,'screenshots':0}))

if __name__=='__main__':run()
