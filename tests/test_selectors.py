# test_css_selectors_summary.py
#
# Prerequisites:
#   pip install playwright
#   playwright install
#
import csv
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError

# Dynamically resolve project paths
ROOT_DIR = Path(__file__).parents[1]
BASE_URL = (
    "https://www.penguinrandomhouse.com/books/"
    "536247/devotions-a-read-with-jenna-pick-by-mary-oliver/"
)
CSV_FILE = ROOT_DIR / "links_product_page.csv"

def load_selectors():
    selectors = []
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            css = row.get("CSS Selector", "").strip()
            if not css:
                continue
            selectors.append({
                "index":       row.get("Index", "").strip(),
                "description": row.get("Description", "").strip(),
                "css":         css,
            })
    return selectors

def test_css_selectors(page, selectors):
    broken = []
    page.goto(BASE_URL, wait_until="networkidle")
    for sel in selectors:
        idx  = sel["index"]
        desc = sel["description"]
        css  = sel["css"]
        print(f"[test_css] {idx}: {desc}")
        print(f"[test_css] Selector → {css}")
        try:
            page.wait_for_selector(css, timeout=5000)
            count = page.locator(css).count()
            print(f"[test_css] Found {count} element(s)\n")
        except TimeoutError:
            print(f"[test_css] NOT found: {desc}\n")
            broken.append((idx, desc, css))
    return broken

def main():
    selectors = load_selectors()
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_context().new_page()
        broken = test_css_selectors(page, selectors)
        browser.close()

    print("=== Summary ===")
    if not broken:
        print(" All CSS selectors passed!")
    else:
        print(f" {len(broken)} selector(s) failed:")
        for idx, desc, css in broken:
            print(f"  • Index {idx}: {desc}")
            print(f"      Selector: {css}")
    print("================")

if __name__ == "__main__":
    main()
