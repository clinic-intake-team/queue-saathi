"""Phase 3 browser verification. Intentionally never captures screenshots."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
BASE=os.getenv('WEB_URL','http://127.0.0.1:5173')
AXE=ROOT/'web/node_modules/axe-core/axe.min.js'
report={'screens':{},'checks':[],'contrast_violations':[]}
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',args=['--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream'])
    context=browser.new_context(viewport={'width':390,'height':844},permissions=['microphone'],reduced_motion='reduce')
    errors=[];cloud=[]
    context.on('page',lambda page:page.on('pageerror',lambda error:errors.append(str(error))))
    def guard(route):
        if any(host in route.request.url for host in ['api.groq.com','api.vachana.ai','generativelanguage.googleapis.com']):
            cloud.append(route.request.url);route.abort()
        else:route.continue_()
    context.route('**/*',guard)
    page=context.new_page()
    for screen in ['landing','question','recording','transcript','readback','red-flag','needs-check','done','unclear']:
        page.goto(BASE+('/' if screen=='landing' else '/intake?screen='+screen),wait_until='networkidle')
        if screen=='landing':page.get_by_text('95%',exact=True).wait_for()
        else:page.locator('#intake-heading').wait_for()
        page.wait_for_timeout(250)
        for width in [390,320,1440]:
            page.set_viewport_size({'width':width,'height':844})
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(screen,width,'horizontal overflow')
        page.set_viewport_size({'width':390,'height':844})
        page.add_script_tag(path=str(AXE))
        results=page.evaluate("""async()=>await axe.run(document,{runOnly:{type:'rule',values:['color-contrast','button-name','link-name','aria-valid-attr-value']}})""")
        violations=[{'screen':screen,'rule':v['id'],'nodes':[{'target':n['target'],'reason':n.get('failureSummary')} for n in v['nodes']]} for v in results['violations']]
        report['contrast_violations'].extend(violations)
        report['screens'][screen]='responsive'
    print(json.dumps({'accessibility':report['contrast_violations']},indent=2),flush=True)
    # Screen-preview URLs simulate recording; they must never request the mic.
    page.goto(BASE+'/intake?screen=recording',wait_until='networkidle')
    page.evaluate("()=>{window.micRequests=0; navigator.mediaDevices.getUserMedia=()=>{window.micRequests++;return Promise.reject(new Error('No mic in preview'))}}")
    page.get_by_role('button',name='Stop recording',exact=True).click()
    page.get_by_role('heading',name='Maine suna:',exact=True).wait_for()
    assert page.evaluate('window.micRequests')==0
    report['checks'].append('Recording preview never requests microphone access')
    # Full real-HTTP mock flow, including correcting a medicine before confirming.
    page.goto(BASE+'/intake?new=1',wait_until='networkidle')
    page.get_by_role('button',name='Use a sample answer',exact=True).click()
    page.get_by_role('button',name='Record again / Dobara record karein',exact=True).click()
    page.get_by_role('heading',name='Namaste! Main clinic ki taraf se',exact=False).wait_for()
    for _ in range(6):
        page.get_by_role('button',name='Use a sample answer',exact=True).click()
        page.get_by_role('heading',name='Maine suna:',exact=True).wait_for()
        page.get_by_role('button',name='Agla sawaal',exact=True).click()
    page.get_by_role('button',name='Nahi, badalna hai',exact=True).wait_for()
    page.get_by_role('button',name='Nahi, badalna hai',exact=True).click()
    page.get_by_role('button',name='Use a sample answer',exact=True).click()
    page.get_by_role('heading',name='Maine suna:',exact=True).wait_for()
    page.get_by_role('button',name='Agla sawaal',exact=True).click()
    page.get_by_text('Paracetamol 500',exact=True).wait_for()
    page.get_by_role('button',name='Haan, sahi hai',exact=True).click()
    page.get_by_role('button',name='Use a sample answer',exact=True).click()
    page.get_by_role('heading',name='Maine suna:',exact=True).wait_for()
    page.get_by_role('button',name='Agla sawaal',exact=True).click()
    page.get_by_role('button',name='Use a sample answer',exact=True).click()
    page.get_by_role('button',name='Pura karein',exact=True).click()
    page.get_by_role('heading',name='Shukriya!',exact=True).wait_for()
    assert page.locator('.token-card strong').inner_text()=='24'
    page.goto(BASE+'/intake',wait_until='networkidle')
    page.get_by_role('heading',name='Shukriya!',exact=True).wait_for()
    report['checks'].append('Full mock flow, medicine correction/confirmation, done token, and saved-session restore')
    # Browser MediaRecorder emits real WebM; backend converts it, with zero cloud calls.
    page.goto(BASE+'/intake?new=1',wait_until='networkidle')
    page.get_by_role('button',name='Start recording',exact=True).click()
    page.get_by_role('button',name='Stop recording',exact=True).wait_for()
    page.wait_for_timeout(650)
    page.get_by_role('button',name='Stop recording',exact=True).click()
    page.get_by_role('heading',name='Maine suna:',exact=True).wait_for()
    page.get_by_text('Mera token 24 hai.',exact=True).wait_for()
    report['checks'].append('Actual MediaRecorder WebM upload + ffmpeg conversion using fake browser microphone')
    # Denial must be recoverable without recording permission.
    page.goto(BASE+'/intake?new=1',wait_until='networkidle')
    page.evaluate("()=>{navigator.mediaDevices.getUserMedia=()=>Promise.reject(new DOMException('Denied','NotAllowedError'))}")
    page.get_by_role('button',name='Start recording',exact=True).click()
    page.get_by_text('Microphone access was not allowed.',exact=False).wait_for()
    page.get_by_role('button',name='Use a sample answer',exact=True).click()
    page.get_by_role('heading',name='Maine suna:',exact=True).wait_for()
    report['checks'].append('Microphone-denied fallback remains usable')
    # Both safety layers and re-ask are exercised through actual mock API sessions.
    for scenario,count in [('red_flag',3),('needs_check',5),('unclear',2)]:
        page.goto(BASE+'/intake?new=1&scenario='+scenario,wait_until='networkidle')
        for i in range(count):
            page.get_by_role('button',name='Use a sample answer',exact=True).click()
            if i<count-1:
                page.get_by_role('heading',name='Maine suna:',exact=True).wait_for()
                page.get_by_role('button',name='Agla sawaal',exact=True).click()
        if scenario=='unclear':
            page.get_by_role('button',name='Phir se bataiye',exact=True).wait_for()
            page.get_by_role('button',name='Phir se bataiye',exact=True).click()
            page.get_by_role('heading',name='Maaf kijiye, theek se samajh nahi aaya.',exact=False).wait_for()
        else:page.locator('.alert-card').wait_for()
    report['checks'].append('API-driven red flag, needs_check, and gentle re-ask')
    assert not errors,errors
    assert not cloud,cloud
    report['checks'].append('No browser runtime errors or paid API requests')
    browser.close()
print(json.dumps(report,indent=2))
assert not report['contrast_violations'],'Accessibility checks failed; see violations above.'
