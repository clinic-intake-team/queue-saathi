"""Screenshot-free language UI test with all API requests mocked (zero credits)."""
import csv
import json
from pathlib import Path
import os
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
from sys import path
path.insert(0,str(ROOT))
from app.api import languages
import yaml
original=yaml.safe_load((ROOT/'prompts.yaml').read_text())
allprompts={locale:languages.prompts(locale,original) for locale in languages.LANGUAGES}
datasets={name:list(csv.DictReader((ROOT/'eval/results'/f'{name}.csv').open())) for name in ['setA_summary','setB_summary_partB_v2']}
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome')
    context=browser.new_context(viewport={'width':390,'height':844},reduced_motion='reduce')
    page=context.new_page();errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
    def mocked(route):
        request=route.request
        if '/api/languages' in request.url:route.fulfill(json={'prompts':allprompts,'audio_cached':{'hinglish':20,'hi':0,'en':0}})
        elif '/api/health' in request.url:route.fulfill(json={'mock':True,'real_calls_enabled':False})
        elif '/api/results' in request.url:route.fulfill(json={'datasets':datasets})
        else:route.fulfill(status=503,json={'detail':'Provider calls forbidden in language UI test'})
    page.route('**/api/**',mocked)
    page.goto(os.getenv('WEB_URL','http://127.0.0.1:5173'),wait_until='networkidle')
    page.get_by_label('Interface language',exact=True).select_option('hi')
    page.get_by_label('Question language',exact=True).select_option('en')
    assert page.locator('html').get_attribute('lang')=='hi'
    page.get_by_role('link',name='मरीज़ की जानकारी देना शुरू करें',exact=True).first.wait_for()
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.reload(wait_until='networkidle')
    assert page.get_by_label('Interface language',exact=True).input_value()=='hi'
    assert page.get_by_label('Question language',exact=True).input_value()=='en'
    page.goto('http://127.0.0.1:5173/intake?screen=question',wait_until='networkidle')
    page.get_by_role('heading',name=allprompts['en']['P2'],exact=True).wait_for()
    page.get_by_label('Question language',exact=True).select_option('hi')
    page.get_by_role('heading',name=allprompts['hi']['P2'],exact=True).wait_for()
    page.get_by_label('Interface language',exact=True).select_option('en')
    page.get_by_role('button',name='Use a sample answer',exact=True).wait_for()
    page.get_by_role('heading',name=allprompts['hi']['P2'],exact=True).wait_for()
    page.get_by_label('Question language',exact=True).select_option('hinglish')
    page.get_by_role('heading',name=allprompts['hinglish']['P2'],exact=True).wait_for()
    page.get_by_role('button',name='Use a sample answer',exact=True).click()
    page.get_by_role('heading',name='I heard:',exact=True).wait_for()
    page.get_by_role('button',name='Record again',exact=True).wait_for()
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    assert not errors,errors
    browser.close()
print('PASS: independent selectors, Hindi/English/Hinglish questions, persistent preferences, translated patient UI, 390px layout, no runtime errors; no screenshots or real API requests.')
