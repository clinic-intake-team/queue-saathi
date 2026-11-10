#!/usr/bin/env python3
"""Export the final slide. Requires Python Playwright and Chrome; no app/server or APIs."""
import base64
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
PAGE=ROOT/'docs/diagram/index.html'


def main():
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True)
        page=browser.new_page(viewport={'width':1920,'height':1080},device_scale_factor=2)
        responses={}
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        def collect(response):
            if response.ok and ('fonts.googleapis.com/' in response.url or 'fonts.gstatic.com/' in response.url):
                responses[response.url]=(response.headers.get('content-type',''),response.body())
        page.on('response',collect)
        page.goto(PAGE.as_uri(),wait_until='networkidle')
        page.wait_for_function('window.diagramReady===true')
        assert page.evaluate('document.fonts.check("450 62px Inter") && document.fonts.check(\'italic 74px "Instrument Serif"\')'),'Fonts did not load'
        assert any('fonts.gstatic.com' in url for url in responses),'Google Fonts unavailable; refusing fallback-font export'
        page.wait_for_timeout(4200)
        assert page.locator('[data-node]').count()==6
        assert page.evaluate('Array.from(document.querySelectorAll(".node,.alert-node,.stats")).every(n=>getComputedStyle(n).opacity==="1")')
        assert page.evaluate('document.documentElement.scrollWidth===1920 && document.documentElement.scrollHeight===1080')
        # Static capture omits the moving pulse; animation can be replayed by reload.
        page.evaluate('document.body.classList.add("static")')
        page.screenshot(path=str(ROOT/'docs/pipeline.png'),animations='disabled')
        font_css='\n'.join(body.decode() for mime,body in responses.values() if 'text/css' in mime)
        for url,(mime,body) in responses.items():
            if 'fonts.gstatic.com/' in url:
                font_css=font_css.replace(url,'data:font/woff2;base64,'+base64.b64encode(body).decode())
        # Unused unicode subsets remain external in Google's CSS. Drop those
        # rules; all actually used font files above are embedded in the SVG.
        import re
        font_css='\n'.join(rule for rule in re.findall(r'@font-face\s*\{[^}]+\}',font_css) if 'https://' not in rule)
        svg=page.evaluate('''fonts=>{const svg=document.querySelector('#pipeline').cloneNode(true);svg.querySelectorAll('animateMotion,.pulse').forEach(n=>n.remove());svg.querySelector('style').textContent=fonts+'\\ntext{font-family:Inter,Arial,sans-serif}.node,.alert-node,.stats{opacity:1}.connector,.alert-path{stroke-dasharray:none;stroke-dashoffset:0}.alert-dashes{stroke-dasharray:5 7}';return new XMLSerializer().serializeToString(svg)}''',font_css)
        (ROOT/'docs/pipeline.svg').write_text('<?xml version="1.0" encoding="UTF-8"?>\n'+svg)
        # Reduced-motion is fully static, including the attention branch.
        reduced=browser.new_page(viewport={'width':1920,'height':1080},reduced_motion='reduce')
        reduced.goto(PAGE.as_uri(),wait_until='networkidle');reduced.wait_for_function('window.diagramReady===true')
        assert reduced.locator('animateMotion').count()==0
        assert reduced.evaluate('getComputedStyle(document.querySelector(".node")).opacity==="1"')
        assert not errors,errors
        browser.close()
    print(json.dumps({'png':'docs/pipeline.png','resolution':'3840×2160','svg':'docs/pipeline.svg','nodes':6,'reduced_motion':'passed','page_errors':errors}))

if __name__=='__main__':main()
