"""Browser checks and desktop/mobile screenshots for the Phase 2 landing page."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/screenshots'
OUT.mkdir(parents=True,exist_ok=True)
BASE=os.getenv('WEB_URL','http://127.0.0.1:5173')
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome')
    page=browser.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
    errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.goto(BASE,wait_until='networkidle')
    page.get_by_text('95%',exact=True).wait_for()
    page.evaluate('document.fonts.ready')
    page.wait_for_timeout(800)
    assert page.get_by_role('heading',level=1).count()==1
    assert page.locator('.stat-number').nth(1).inner_text().startswith('4/4')
    assert page.locator('.stat-number').nth(2).inner_text().startswith('1/16')
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.screenshot(path=str(OUT/'phase2-landing-desktop.png'),full_page=True)
    page.screenshot(path=str(OUT/'phase2-landing-desktop-hero.png'))
    page.get_by_role('link',name='How it works',exact=True).click()
    assert page.evaluate('location.hash')=='#how-it-works'
    page.get_by_role('link',name='Open doctor view',exact=True).click()
    page.get_by_role('heading',name='A clearer picture, before the consultation.').wait_for()
    page.get_by_role('link',name='Back to QueueSaathi',exact=True).click()
    page.get_by_role('link',name='Start patient intake',exact=True).first.click()
    page.get_by_role('heading',name='Your story starts with your voice.').wait_for()
    page.get_by_role('link',name='Back to QueueSaathi',exact=True).click()
    page.get_by_text('95%',exact=True).wait_for()
    for width in [320,390,768]:
        page.set_viewport_size({'width':width,'height':844})
        page.evaluate('scrollTo(0,0)')
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),f'Horizontal overflow at {width}'
    page.set_viewport_size({'width':390,'height':844})
    page.evaluate('scrollTo(0,0)')
    page.get_by_role('button',name='Open navigation').click()
    page.get_by_role('navigation',name='Mobile navigation').get_by_role('link',name='Results',exact=True).click()
    assert not page.locator('#mobile-nav').count()
    page.evaluate('scrollTo(0,0)')
    page.wait_for_timeout(700)
    page.screenshot(path=str(OUT/'phase2-landing-mobile.png'),full_page=True)
    page.screenshot(path=str(OUT/'phase2-landing-mobile-hero.png'))
    # API failure must not leave stale/fabricated performance claims on screen.
    page.route('**/api/results',lambda route:route.fulfill(status=503,body='Unavailable'))
    page.reload(wait_until='networkidle')
    page.get_by_text('Recorded results are temporarily unavailable.',exact=False).wait_for()
    page.unroute('**/api/results')
    page.get_by_role('button',name='Try again').click()
    page.get_by_text('95%',exact=True).wait_for()
    # Prove all highlighted numbers come from the response, not baked-in copy.
    modified={'datasets':{'setA_summary':[
      {'speaker':'overall','condition':'keyterms_off','name_accuracy':'.13'},
      {'speaker':'overall','condition':'keyterms_on','name_accuracy':'.37'}],
      'setB_summary_partB_v2':[
      {'speaker':'overall','field':'red_flags_caught','correct':'9','total':'10'},
      {'speaker':'overall','field':'false_alarms','correct':'2','total':'7'}]}}
    page.route('**/api/results',lambda route:route.fulfill(json=modified))
    page.reload(wait_until='networkidle')
    page.get_by_text('37%',exact=True).wait_for()
    assert '9/10' in page.locator('.stat-number').nth(1).inner_text()
    assert '2/7' in page.locator('.stat-number').nth(2).inner_text()
    assert not errors,errors
    browser.close()
print(json.dumps({'status':'passed','screenshots':['phase2-landing-desktop.png','phase2-landing-mobile.png'],'checks':['CSV-backed metrics','320/390/768/1440 layouts without overflow','patient/doctor preview links','mobile menu','API failure and retry','dynamic response numbers','no browser runtime errors']},indent=2))
