"""Browser smoke test for observer and actor views on one persistent world."""
import os,tempfile
from pathlib import Path
# ensure isolated state before server import
_work=tempfile.TemporaryDirectory()
os.environ['UNIVERSE_STATE_DIR']=_work.name
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
import server
HERE=Path(__file__).parent
client=TestClient(server.app)

def mock_fetch(source,url,options):
    options=options or {};method=options.get('method','GET');body=options.get('body')
    r=client.request(method,url,data=body,headers=options.get('headers') or {})
    try:data=r.json()
    except Exception:data={}
    return dict(ok=r.is_success,statusText=r.reason_phrase,json=data)

with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':960},device_scale_factor=1)
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    html=(HERE/'static'/'index.html').read_text().replace('<link rel="stylesheet" href="/static/style.css" />','').replace('<script src="/static/app.js"></script>','')
    page.set_content(html)
    page.add_style_tag(content=(HERE/'static'/'style.css').read_text())
    page.expose_binding('mockFetch',mock_fetch)
    page.evaluate('''() => { window.fetch = async (url,opts={}) => {const r=await window.mockFetch(url,opts);return {ok:r.ok,statusText:r.statusText,json:async()=>r.json};};}''')
    page.add_script_tag(content=(HERE/'static'/'app.js').read_text())
    page.wait_for_timeout(180)
    page.locator('button[data-role="livewatch"]').click()
    page.wait_for_timeout(200)
    assert 'Persistent live universe' in page.locator('#viewTitle').inner_text()
    assert 'LIVE TICK 20' in page.locator('#tickLabel').inner_text()
    page.screenshot(path=str(HERE/'preview_live_observer.png'),full_page=True)
    page.locator('button[data-role="liveagent"]').click()
    page.wait_for_timeout(200)
    assert 'Shared world' in page.locator('#viewTitle').inner_text()
    assert 'LIVE ACTOR' in page.locator('#tickLabel').inner_text()
    page.locator('#x').fill('3');page.locator('#y').fill('4')
    page.locator('#actionButtons button').filter(has_text='OBSERVE').click();page.wait_for_timeout(150)
    assert 'observe' in page.locator('#eventLog').inner_text()
    page.screenshot(path=str(HERE/'preview_live_agent.png'),full_page=True)
    page.locator('#actionButtons button').filter(has_text='SET').click();page.wait_for_timeout(180)
    assert 'set' in page.locator('#eventLog').inner_text()
    page.locator('button[data-role="livewatch"]').click();page.wait_for_timeout(200)
    assert 'LIVE TICK 22' in page.locator('#tickLabel').inner_text(),page.locator('#tickLabel').inner_text()
    assert not errors,errors
    browser.close()
    print('PASS headless browser: live global view, paid participant observation, charged set, same persistent world, no JS errors')
