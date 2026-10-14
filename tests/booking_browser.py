#!/usr/bin/env python3
"""Optional Playwright browser tests; Cal.com is mocked (no real bookings)."""
import subprocess
import time
import urllib.request
from playwright.sync_api import sync_playwright

PORT=18765
URL=f'http://127.0.0.1:{PORT}'
CONFIG_URL=f'{URL}/assets/js/booking-config.js'


def wait_server():
    for _ in range(80):
        try:
            urllib.request.urlopen(URL, timeout=1)
            return
        except Exception:
            time.sleep(0.1)
    raise RuntimeError('Local test server did not start')


def config_event(url):
    return f'window.KTAWF_BOOKING = {{ eventUrl: {url!r}, theme: "light", brandColor: "#25382e" }};'


MOCK_CAL = '''
window.__calQueue = (window.Cal.q || []).map(x => Array.from(x));
const iframe = document.createElement('iframe');
iframe.title = 'Cal.com mock';
iframe.srcdoc = '<p>MOCK EMBED — NO REAL BOOKINGS</p>';
iframe.style.height = '680px';
document.getElementById('cal-inline').append(iframe);
'''


def browser_test(page, label, expected_origin):
    page.wait_for_selector('#cal-inline iframe')
    calls = page.evaluate("window.__calQueue.map(x => [x[0], x[1]])")
    assert [x[0] for x in calls] == ['init', 'inline', 'ui'], calls
    assert calls[0][1]['origin'] == expected_origin, calls
    assert calls[1][1]['calLink'] == 'test-user/45min', calls
    assert page.locator('#booking-open-link').is_visible(), label
    assert page.locator('#booking-status').is_hidden(), label
    assert page.evaluate('document.documentElement.scrollWidth <= document.documentElement.clientWidth'), label
    print(f'PASS {label}: Cal.com bootstrap, fallback link, responsive embed')


def main():
    server=subprocess.Popen(['python3','-m','http.server',str(PORT),'--directory',
                             str(__import__('pathlib').Path(__file__).parents[1]/'public')],
                             stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        wait_server()
        with sync_playwright() as play:
            browser=play.chromium.launch(executable_path='/usr/bin/chromium', headless=True,
                                         args=['--no-sandbox','--disable-dev-shm-usage'])
            for width in [390,768,1440]:
                page=browser.new_page(viewport={'width':width,'height':844})
                errors=[]
                page.on('pageerror',lambda e: errors.append(str(e)))
                page.route(CONFIG_URL, lambda route: route.fulfill(content_type='application/javascript',body=config_event('')))
                page.goto(URL,wait_until='load')
                assert page.locator('#booking-open-link').is_hidden()
                assert 'не активовано' in page.locator('#booking-status').inner_text()
                assert not errors, errors
                assert page.evaluate('document.documentElement.scrollWidth <= document.documentElement.clientWidth')
                print(f'PASS {width}px: intentionally empty test configuration, no fake calendar')
                page.close()

            # Confirm the production configuration is wired to the given event; no real booking is made.
            page=browser.new_page(viewport={'width':390,'height':844})
            page.route('**/embed/embed.js',lambda route:route.fulfill(content_type='application/javascript',body=MOCK_CAL))
            page.goto(URL,wait_until='domcontentloaded')
            page.wait_for_selector('#cal-inline iframe')
            assert page.locator('#booking-open-link').get_attribute('href') == 'https://cal.com/bogdan-n-usjpw6/consultation'
            calls=page.evaluate('window.__calQueue.map(x => [x[0], x[1]])')
            assert calls[1][1]['calLink'] == 'bogdan-n-usjpw6/consultation'
            print('PASS production URL: correct event slug and public fallback link')
            page.close()

            for host,origin in [('cal.com','https://app.cal.com'),('cal.eu','https://app.cal.eu')]:
                page=browser.new_page(viewport={'width':390,'height':844})
                errors=[]
                page.on('pageerror',lambda e: errors.append(str(e)))
                page.route(CONFIG_URL,lambda route,host=host:route.fulfill(content_type='application/javascript',body=config_event('https://'+host+'/test-user/45min')))
                page.route('**/embed/embed.js',lambda route: route.fulfill(content_type='application/javascript',body=MOCK_CAL))
                page.goto(URL,wait_until='domcontentloaded')
                browser_test(page,host,origin)
                assert not errors, errors
                page.close()

            page=browser.new_page()
            outgoing=[]
            page.on('request',lambda request: outgoing.append(request.url))
            page.route(CONFIG_URL,lambda route:route.fulfill(content_type='application/javascript',body=config_event('https://evil.example/test-user/45min')))
            page.goto(URL,wait_until='load')
            assert 'тимчасово недоступний' in page.locator('#booking-status').inner_text()
            assert not any('cal.com/' in x or 'cal.eu/' in x for x in outgoing)
            assert page.locator('#booking-open-link').is_hidden()
            print('PASS disallowed URL: fail closed without requests')
            page.close()
            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=5)

if __name__=='__main__': main()
