import asyncio
from playwright.async_api import async_playwright
import nest_asyncio
import json

nest_asyncio.apply()

TEALIUM_HOOK_SCRIPT = """
(() => {
    window.tealiumSpecificEvents = [];
    const logTealiumEvent = (type, data) => {
        try {
            const copy = JSON.parse(JSON.stringify(data || {}));
            window.tealiumSpecificEvents.push({ type, timestamp: new Date().toISOString(), data: copy });
        } catch (e) {
            window.tealiumSpecificEvents.push({ type, timestamp: new Date().toISOString(), error: e.message });
        }
    };

    const hook = (utag) => {
        if (!utag || utag.view?.__hooked || utag.link?.__hooked) return;
        const originalLink = utag.link;
        const originalView = utag.view;

        if (typeof originalLink === 'function') {
            utag.link = function(data) {
                logTealiumEvent('utag.link', data);
                return originalLink.apply(this, arguments);
            };
            utag.link.__hooked = true;
        }

        if (typeof originalView === 'function') {
            utag.view = function(data) {
                logTealiumEvent('utag.view', data);
                return originalView.apply(this, arguments);
            };
            utag.view.__hooked = true;
        }
    };

    if (window.utag) {
        hook(window.utag);
    } else {
        const interval = setInterval(() => {
            if (window.utag) {
                hook(window.utag);
                clearInterval(interval);
            }
        }, 500);
        setTimeout(() => clearInterval(interval), 15000);
    }
})();
"""

async def record_tealium_click(url: str, selector: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        await page.add_init_script(TEALIUM_HOOK_SCRIPT)

        print(f"Navigating to {url} ...")
        await page.goto(url, wait_until="load")

        await page.wait_for_timeout(4000)  # Let scripts settle

        print(f"Clicking button: {selector}")
        element = page.locator(selector)
        await element.wait_for(state="visible", timeout=15000)
        await element.click()

        await page.wait_for_timeout(3000)

        print("\n📦 Tealium Events Captured:")
        tealium_events = await page.evaluate("() => window.tealiumSpecificEvents")
        print(json.dumps(tealium_events, indent=2))

        await browser.close()

# Set the URL and selector
URL = "https://www.penguinrandomhouse.com/books/734292/the-very-hungry-caterpillars-peekaboo-easter-by-eric-carle-illustrated-by-eric-carle/9780593750179/"
SELECTOR = "div#collapse2 > div.panel-body > ul.ttl-data > li.active > div.format-info > form > button.btn.buy2"

asyncio.run(record_tealium_click(URL, SELECTOR))
