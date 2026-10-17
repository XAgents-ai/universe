"""Headless UI smoke test using an in-memory FastAPI test transport.
No publicly accessible server required. Screenshots are optional developer previews.
"""
from pathlib import Path
import server
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright

HERE=Path(__file__).parent
client=TestClient(server.app)

def mock_fetch(source, url, options):
    options = options or {}
    method = options.get('method','GET')
    body = options.get('body')
    r=client.request(method,url,data=body,headers={'Content-Type':'application/json'} if body else {})
    try: data=r.json()
    except Exception: data={}
    return dict(ok=r.is_success,statusText=r.reason_phrase,json=data)

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':960},device_scale_factor=1)
    errors=[]
    page.on('pageerror',lambda err:errors.append(str(err)))
    html=(HERE/'static'/'index.html').read_text().replace('<link rel="stylesheet" href="/static/style.css" />','').replace('<script src="/static/app.js"></script>','')
    page.set_content(html)
    page.add_style_tag(content=(HERE/'static'/'style.css').read_text())
    page.expose_binding('mockFetch',mock_fetch)
    page.evaluate('''() => { window.fetch = async (url,opts={}) => { const r=await window.mockFetch(url,opts);return {ok:r.ok,statusText:r.statusText,json:async()=>r.json};}; }''')
    page.add_script_tag(content=(HERE/'static'/'app.js').read_text())
    page.wait_for_function('document.querySelector("#tickLabel").textContent.includes("TICK")')
    print('audit:',page.locator('#viewTitle').inner_text(),page.locator('#tickLabel').inner_text())
    page.locator('#timeline').fill('11');page.wait_for_timeout(300)
    print('audit:',page.locator('#tickLabel').inner_text())
    page.screenshot(path=str(HERE/'preview.png'),full_page=True)
    page.locator('button[data-role="agent"]').click()
    page.wait_for_timeout(150)
    print('agent:',page.locator('#viewTitle').inner_text())
    page.locator('#x').fill('6');page.locator('#y').fill('7')
    page.locator('#actionButtons button').filter(has_text='OBSERVE').click()
    page.wait_for_timeout(180)
    print('agent observed:',page.locator('#eventLog').inner_text()[:120])
    page.screenshot(path=str(HERE/'preview_human_agent.png'),full_page=True)
    page.locator('button[data-role="experiment"]').click()
    page.wait_for_timeout(150)
    print('experiment:',page.locator('#viewTitle').inner_text())
    page.locator('#x').fill('1');page.locator('#y').fill('1')
    page.locator('#actionButtons button').filter(has_text='DROP').click()
    page.wait_for_timeout(150)
    print('experiment drop event:',page.locator('#eventLog').inner_text()[:130])
    print('JavaScript errors:',errors)
    assert not errors
    browser.close()
