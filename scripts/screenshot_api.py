"""Playwright screenshot of the Phase 1 API documentation (no patient data)."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(channel="chrome")
    page=browser.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
    page.goto(os.getenv('API_URL','http://127.0.0.1:8000')+'/docs',wait_until='networkidle')
    page.get_by_role('heading',name='QueueSaathi API',exact=False).wait_for()
    page.screenshot(path=str(ROOT/'docs/screenshots/phase1-api-desktop.png'),full_page=True)
    page.set_viewport_size({'width':390,'height':844})
    page.screenshot(path=str(ROOT/'docs/screenshots/phase1-api-mobile.png'),full_page=True)
    browser.close()
