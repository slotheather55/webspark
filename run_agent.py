import csv
import json
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError


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
    present = []
    for sel in selectors:
        try:
            if page.locator(sel['css']).count() > 0:
                present.append(sel)
        except Exception:
            continue
    if not present:
        return None
    # prefer "add to cart"
    candidate = next((s for s in present if 'add to cart' in s['description'].lower()), present[0])
    page.click(candidate['css'])
    return candidate


def main():
    ROOT = Path(__file__).parent
    CSV_FILE = ROOT / 'links_product_page.csv'
    OUT_DIR = ROOT / 'browser-use' / 'dom_state_data'
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    selectors = load_selectors(CSV_FILE)
    events = []

    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch(headless=True)
        except Exception as e:
            print('Error launching browser:', e)
            print('→ Run `playwright install` to install browsers')
            return
        page = browser.new_context().new_page()

        urls = [
            'https://www.penguinrandomhouse.com/books/',
            'https://www.penguinrandomhouse.com/books/536247/devotions-a-read-with-jenna-pick-by-mary-oliver/'
        ]

        for url in urls:
            ts = datetime.utcnow().isoformat()
            events.append({'timestamp': ts, 'event': 'page_view', 'url': url})
            page.goto(url, wait_until='networkidle')

            shot = OUT_DIR / f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_view.png"
            page.screenshot(path=str(shot), full_page=True)
            events.append({'timestamp': datetime.utcnow().isoformat(), 'event': 'screenshot', 'file': shot.name})

            candidate = select_and_click(page, selectors)
            if candidate:
                ts2 = datetime.utcnow().isoformat()
                events.append({'timestamp': ts2, 'event': 'click', 'selector': candidate['css'], 'description': candidate['description']})
                shot2 = OUT_DIR / f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_click.png"
                page.screenshot(path=str(shot2), full_page=True)
                events.append({'timestamp': datetime.utcnow().isoformat(), 'event': 'screenshot', 'file': shot2.name})

        browser.close()

    out_file = OUT_DIR / f"session_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"
    with out_file.open('w', encoding='utf-8') as f:
        json.dump({'events': events}, f, indent=2)
    print(f'Done. Events written to {out_file}')


if __name__ == '__main__':
    main()
