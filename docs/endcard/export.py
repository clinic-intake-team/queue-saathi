#!/usr/bin/env python3
"""Capture the REAL intake language screen, verify the sequence and export its hold frame."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright,expect

DIRECTORY=Path(__file__).resolve().parent


def main():
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True)
        patient=browser.new_page(viewport={'width':390,'height':844},device_scale_factor=1,color_scheme='dark',reduced_motion='reduce')
        errors=[];requests=[]
        patient.on('pageerror',lambda e:errors.append(str(e)))
        patient.on('request',lambda request:requests.append((request.method,request.url)))
        patient.add_init_script("localStorage.setItem('queuesaathi.uiLanguage','hinglish');localStorage.setItem('queuesaathi.questionLanguage','hinglish');sessionStorage.removeItem('queuesaathi.intake.light');")
        patient.goto('http://localhost:8020/intake?kiosk=1',wait_until='networkidle')
        expect(patient.get_by_role('heading',name='Kis bhasha mein baat karein?',exact=True)).to_be_visible()
        expect(patient.locator('input[name="intake-language"][value="hinglish"]')).to_be_checked()
        await_fonts=patient.evaluate("async()=>{await document.fonts.load('450 22px Inter');await document.fonts.ready;return document.fonts.check('450 22px Inter')}")
        assert await_fonts,'App font unavailable'
        assert patient.evaluate('document.documentElement.scrollWidth<=390')
        patient.screenshot(path=str(DIRECTORY/'screen.png'),full_page=False,animations='disabled')
        assert not any(method!='GET' for method,url in requests),'Screen capture must not start a session or make paid calls'
        # Exercise the on-load timeline without screenshots of intermediate phases.
        card=browser.new_page(viewport={'width':1920,'height':1080},device_scale_factor=1)
        card.on('pageerror',lambda e:errors.append(str(e)))
        card.goto((DIRECTORY/'index.html').as_uri(),wait_until='domcontentloaded')
        card.wait_for_function('window.endcardReady===true')
        card.wait_for_timeout(1500)
        assert card.locator('.phone-stage').evaluate('el=>getComputedStyle(el).opacity')=='1'
        assert card.locator('.wordmark-stage').evaluate('el=>Number(getComputedStyle(el).opacity)')<.01
        card.wait_for_timeout(3000)
        assert card.locator('.phone-stage').evaluate('el=>Number(getComputedStyle(el).opacity)')<.01
        assert card.locator('.wordmark-stage').evaluate('el=>getComputedStyle(el).opacity')=='1'
        assert card.evaluate('document.fonts.check(\'italic 39px "Instrument Serif"\')')
        assert card.evaluate('document.documentElement.scrollWidth===1920 && document.documentElement.scrollHeight===1080')
        card.screenshot(path=str(DIRECTORY/'final.png'),animations='disabled')
        reduced=browser.new_page(viewport={'width':1920,'height':1080},reduced_motion='reduce')
        reduced.goto((DIRECTORY/'index.html').as_uri(),wait_until='networkidle');reduced.wait_for_function('window.endcardReady===true')
        assert reduced.locator('.phone-stage').evaluate('el=>getComputedStyle(el).display')=='none'
        assert reduced.locator('.wordmark-stage').evaluate('el=>getComputedStyle(el).opacity')=='1'
        assert not errors,errors
        browser.close()
    print(json.dumps({'screen':'docs/endcard/screen.png','screen_size':[390,844],'source':'http://localhost:8020/intake?kiosk=1','final':'docs/endcard/final.png','final_size':[1920,1080],'timeline':'verified','reduced_motion':'verified','app_changed':False,'paid_calls':0}))

if __name__=='__main__':main()
