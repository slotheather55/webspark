import csv
import json
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError

# Paths
ROOT_DIR = Path(__file__).parents[1]
CSV_FILE = ROOT_DIR / 'links_product_page.csv'
DOM_STATE_DIR = ROOT_DIR / 'browser-use' / 'dom_state_data'

# Ensure output directory exists
DOM_STATE_DIR.mkdir(parents=True, exist_ok=True)


def load_selectors(csv_path: Path):
    selectors = []
    with csv_path.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            css = row.get('CSS Selector', '').strip()
            if not css:
                continue
            selectors.append({
                'index': row.get('Index', '').strip(),
                'description': row.get('Description', '').strip(),
                'css': css,
            })
    return selectors


def select_and_click(page, selectors):
    # Filter selectors present on page
    present = []
    for sel in selectors:
        try:
            if page.locator(sel['css']).count() > 0:
                present.append(sel)
        except Exception:
            continue
    # Choose a selector (example: first 'Add to cart' or first available)
    if not present:
        return None
    candidate = next((s for s in present if 'add to cart' in s['description'].lower()), present[0])
    # Click candidate
    page.click(candidate['css'])
    return candidate


def test_ai_agent_click_and_record():
    selectors = load_selectors(CSV_FILE)
    events = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_context().new_page()

        urls = [
            'https://www.penguinrandomhouse.com/books/',
            'https://www.penguinrandomhouse.com/books/536247/devotions-a-read-with-jenna-pick-by-mary-oliver/'
        ]

        for url in urls:
            # Page view event
            ts = datetime.utcnow().isoformat()
            events.append({
                'timestamp': ts,
                'event': 'page_view',
                'url': url
            })
            page.goto(url, wait_until='networkidle')

            # Take screenshot after load
            shot1 = DOM_STATE_DIR / f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_view.png"
            page.screenshot(path=str(shot1), full_page=True)
            events.append({
                'timestamp': datetime.utcnow().isoformat(),
                'event': 'screenshot',
                'file': str(shot1.name)
            })

            # Select and click
            candidate = select_and_click(page, selectors)
            if candidate:
                # Record click event
                ts2 = datetime.utcnow().isoformat()
                events.append({
                    'timestamp': ts2,
                    'event': 'click',
                    'selector': candidate['css'],
                    'description': candidate['description']
                })
                # Screenshot after click
                shot2 = DOM_STATE_DIR / f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_click.png"
                page.screenshot(path=str(shot2), full_page=True)
                events.append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'event': 'screenshot',
                    'file': str(shot2.name)
                })

        browser.close()

    # Persist events
    out_file = DOM_STATE_DIR / f"session_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"
    with out_file.open('w', encoding='utf-8') as f:
        json.dump({'events': events}, f, indent=2)

    # Basic assertions
    assert events, 'No events recorded.'
    assert any(e['event'] == 'click' for e in events), 'No click event recorded.'
