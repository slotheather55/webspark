import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup


SEARCH_TERMS = ["Amazon", "Add to Cart", "Barnes & Noble"]
URL = "https://www.penguinrandomhouse.com/books/734292/the-very-hungry-caterpillars-peekaboo-easter-by-eric-carle-illustrated-by-eric-carle/9780593750179/"

async def run_scraper():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await page.goto(URL, wait_until="domcontentloaded")

        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        for term in SEARCH_TERMS:
            print(f"\n🔍 Searching for: {term}")

            matches = []

            # 1. Visible text matches
            elements = await page.locator(f"text={term}").element_handles()

            # 2. Attribute matches
            attributes = ["alt", "title", "aria-label"]
            for attr in attributes:
                attr_matches = await page.locator(f"[{attr}*='{term}']").element_handles()
                elements.extend(attr_matches)

            seen = set()
            for el in elements:
                try:
                    # Avoid duplicates
                    ref = await el.evaluate("el => el.outerHTML")
                    if ref in seen:
                        continue
                    seen.add(ref)

                    tag = await el.evaluate("el => el.tagName.toLowerCase()")
                    visible = await el.is_visible()
                    href = await el.get_attribute("href")

                    # Get text content
                    text = await el.evaluate("el => el.textContent.trim()")

                    # Get closest heading for context
                    context_text = await el.evaluate("""
                        el => {
                            let heading = el.closest('section, div');
                            while (heading) {
                                let found = heading.querySelector('h1,h2,h3,h4,h5');
                                if (found) return found.innerText.trim();
                                heading = heading.parentElement;
                            }
                            return '';
                        }
                    """)

                    # Build CSS selector
                    selector = await el.evaluate("""
                        el => {
                            function buildSelector(el) {
                                if (!el || el.nodeType !== 1) return '';
                                if (el.id) return `#${el.id}`;
                                let path = [];
                                while (el.parentElement) {
                                    let index = Array.from(el.parentElement.children).indexOf(el) + 1;
                                    path.unshift(`${el.tagName.toLowerCase()}:nth-of-type(${index})`);
                                    el = el.parentElement;
                                }
                                return path.join(" > ");
                            }
                            return buildSelector(el);
                        }
                    """)

                    matches.append({
                        "Text": text,
                        "Tag": tag,
                        "Selector": selector,
                        "Context": context_text or "(no context found)",
                        "URL": href or "None",
                        "Visible": "Yes" if visible else "No"
                    })

                except Exception as e:
                    print(f"Error extracting element info: {e}")

            if not matches:
                print("No matches found.")
            else:
                for match in matches:
                    print("\n" + "=" * 40)
                    for k, v in match.items():
                        print(f"{k}: {v}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(run_scraper())
