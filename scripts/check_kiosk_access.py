#!/usr/bin/env python3
"""Browser regression: route all app traffic to local TestClient, never providers."""
import json
import mimetypes
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright,expect
from app.api import main,clinic_access
ROOT=Path(__file__).resolve().parents[1]


def run():
    with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'GNANI_MOCK':'1','CLINIC_PIN':'1234'}),patch.object(main,'STORE',Path(folder)/'sessions'),patch.object(clinic_access,'SECRET',Path(folder)/'secret'),patch('requests.sessions.Session.request',side_effect=AssertionError('No provider calls')),sync_playwright() as p:
        client=TestClient(main.app);browser=p.chromium.launch(channel='chrome',headless=True)
        page=browser.new_page(viewport={'width':390,'height':844});errors=[];seen=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        def route(request_route):
            request=request_route.request;url=request.url
            if not url.startswith('http://clinic.test/'):
                request_route.abort();return
            path=url.removeprefix('http://clinic.test')
            if path.startswith('/api/'):
                seen.append(path)
                response=client.request(request.method,path.removeprefix('/api'),headers={k:v for k,v in request.headers.items() if k.lower() in {'authorization','content-type'}},content=request.post_data_buffer)
                request_route.fulfill(status=response.status_code,headers=dict(response.headers),body=response.content);return
            file=ROOT/'web/dist'/path.split('?')[0].lstrip('/')
            if not file.is_file():file=ROOT/'web/dist/index.html'
            request_route.fulfill(status=200,content_type=mimetypes.guess_type(file.name)[0] or 'application/octet-stream',body=file.read_bytes())
        page.route('**/*',route)
        page.goto('http://clinic.test/doctor');expect(page.get_by_label('Clinic PIN',exact=True)).to_be_visible()
        assert not any(path.startswith('/sessions') for path in seen)
        page.get_by_label('Clinic PIN',exact=True).fill('0000');page.get_by_role('button',name='Unlock Doctor view').click();expect(page.get_by_role('alert')).to_have_text('Incorrect clinic PIN.')
        page.get_by_label('Clinic PIN',exact=True).fill('1234');page.get_by_role('button',name='Unlock Doctor view').click();expect(page.get_by_role('button',name='Lock',exact=True)).to_be_visible()
        assert page.evaluate("localStorage.getItem('queuesaathi.clinic.device')")!='1234'
        page.reload();expect(page.get_by_role('button',name='Lock',exact=True)).to_be_visible()
        page.get_by_role('button',name='Lock',exact=True).click();expect(page.get_by_label('Clinic PIN',exact=True)).to_be_visible()
        assert page.evaluate("localStorage.getItem('queuesaathi.clinic.device')") is None
        page.goto('http://clinic.test/intake?kiosk=1');expect(page.get_by_role('heading',name='Kis bhasha mein baat karein?')).to_be_visible()
        assert page.locator('a[href="/"],a[href^="/doctor"],a[href^="/results"]').count()==0
        assert page.get_by_role('button',name='Exit',exact=True).count()==1
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        page.get_by_role('button',name='Exit',exact=True).click();expect(page.get_by_role('heading',name='Kis bhasha mein baat karein?')).to_be_visible()
        page.clock.install()
        page.goto('http://clinic.test/intake?kiosk=1&screen=done');expect(page.locator('.done-card')).to_be_visible()
        assert page.locator('a[href="/"],a[href^="/doctor"],a[href^="/results"]').count()==0
        page.clock.fast_forward(14900);expect(page.locator('.done-card')).to_be_visible()
        page.clock.fast_forward(200);expect(page.get_by_role('heading',name='Kis bhasha mein baat karein?')).to_be_visible()
        page.goto('http://clinic.test/intake?kiosk=1&screen=red-flag');expect(page.locator('.alert-card')).to_be_visible()
        page.get_by_role('button',name='Theek hai',exact=True).click();expect(page.get_by_role('heading',name='Kis bhasha mein baat karein?')).to_be_visible()
        page.goto('http://clinic.test/intake?kiosk=1&screen=red-flag');expect(page.locator('.alert-card')).to_be_visible()
        page.clock.fast_forward(29900);expect(page.locator('.alert-card')).to_be_visible()
        page.clock.fast_forward(200);expect(page.get_by_role('heading',name='Kis bhasha mein baat karein?')).to_be_visible()
        page.goto('http://clinic.test/intake?screen=red-flag');expect(page.locator('.alert-card')).to_be_visible()
        page.get_by_role('button',name='Theek hai',exact=True).click();expect(page.get_by_role('heading',name='Kis bhasha mein baat karein?')).to_be_visible()
        assert 'kiosk=1' not in page.url
        assert not any('/session/start' in path for path in seen)
        assert not errors,errors
        browser.close()
    print(json.dumps({'passed':['PIN rejection/unlock','remembered device','Lock clears token','queue inaccessible before unlock','kiosk header and Exit','390px kiosk no overflow','15-second completion reset','30-second alert reset','Theek hai returns to language in both modes','no automatic session start'],'provider_calls':0,'screenshots':0}))

if __name__=='__main__':run()
