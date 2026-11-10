#!/usr/bin/env python3
"""Capture only real saved live-session UI. Never start/answer a session."""
from pathlib import Path
import json
import os
import sys
import hashlib
from playwright.sync_api import sync_playwright,expect
from dotenv import load_dotenv
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'video/public/captures'
load_dotenv(ROOT/'.env')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    records=[]
    for path in (ROOT/'data/ui_sessions').glob('*.json'):
        record=json.loads(path.read_text());records.append(record)
    normal=next(s for s in records if s.get('fields',{}).get('token',{}).get('value')==14 and s['status']=='ready' and not s['mock'])
    urgent=next(s for s in records if s.get('fields',{}).get('token',{}).get('value')==31 and s['status']=='red_flag' and not s['mock'])
    active=next(s for s in records if not s['mock'] and s['status']=='in_progress' and s.get('fields',{}).get('token',{}).get('value')==14)
    protected={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'data/ui_sessions').glob('*.json')}
    provenance=[];errors=[];blocked=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True)
        context=browser.new_context(viewport={'width':390,'height':844},device_scale_factor=1,color_scheme='dark',reduced_motion='reduce')
        context.add_init_script("localStorage.setItem('queuesaathi.uiLanguage','hinglish');localStorage.setItem('queuesaathi.questionLanguage','hinglish');")
        def guard(route):
            if route.request.method not in {'GET','HEAD'}:blocked.append(route.request.url);route.abort()
            else:route.continue_()
        context.route('**/api/session/**',guard)
        patient=context.new_page();patient.on('pageerror',lambda e:errors.append(str(e)))
        patient.goto('http://localhost:8020/intake?kiosk=1',wait_until='networkidle')
        expect(patient.locator('input[value="hinglish"]')).to_be_checked()
        patient.evaluate('async()=>{await document.fonts.ready}')
        patient.screenshot(path=str(OUT/'intake-language.png'),animations='disabled')
        provenance.append(dict(file='intake-language.png',source=patient.url,viewport=[390,844],synthetic=False))
        for name,record,selector in [('question',active,'.question-card'),('red-alert',urgent,'.alert-card')]:
            patient.evaluate("value=>sessionStorage.setItem('queuesaathi.live.session.v1',JSON.stringify(value))",{'id':record['id'],'scenario':'normal'})
            patient.goto('http://localhost:8020/intake',wait_until='networkidle')
            patient.get_by_role('button',name='Shuru karein',exact=True).click()
            expect(patient.locator(selector)).to_be_visible()
            patient.evaluate('async()=>{await document.fonts.ready}')
            patient.screenshot(path=str(OUT/(name+'.png')),animations='disabled')
            provenance.append(dict(file=name+'.png',source=patient.url,viewport=[390,844],session_id=record['id'],synthetic=False))
        doctor=context.new_page();doctor.set_viewport_size({'width':1440,'height':900})
        doctor.goto('http://localhost:8020/doctor?session='+urgent['id'],wait_until='networkidle')
        doctor.get_by_label('Clinic PIN',exact=True).fill(os.getenv('CLINIC_PIN','1234'))
        doctor.get_by_role('button',name='Unlock Doctor view').click()
        expect(doctor.get_by_role('button',name='Lock',exact=True)).to_be_visible()
        for token,record in [(31,urgent),(14,normal)]:
            doctor.goto('http://localhost:8020/doctor?session='+record['id'],wait_until='networkidle')
            expect(doctor.locator('.at-a-glance')).to_be_visible()
            expect(doctor.locator('.queue-item.selected')).to_contain_text('Token '+str(token))
            doctor.evaluate('async()=>{await document.fonts.ready}')
            doctor.screenshot(path=str(OUT/f'doctor-token-{token}.png'),animations='disabled')
            provenance.append(dict(file=f'doctor-token-{token}.png',source=doctor.url,viewport=[1440,900],session_id=record['id'],token=token,synthetic=False,banner_bounds=doctor.locator('.doctor-alert').bounding_box() if token==31 else None))
        browser.close()
    assert not blocked,blocked
    assert not errors,errors
    assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==value for path,value in protected.items()),'Capture changed a saved session'
    provenance.append(dict(file='medicine-readback.png',source='/Users/sagarp/Desktop/demo_video/patient1_clean.mp4',timestamp_seconds=106,source_crop=[736,54,448,972],synthetic=False))
    (OUT/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print('Captured six real app screens; saved records unchanged; no new intakes, sample screens or paid calls.')

if __name__=='__main__':main()
