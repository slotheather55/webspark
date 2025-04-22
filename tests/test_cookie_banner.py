# test_affiliates_and_cart.py
#
# Prerequisites:
#   pip install playwright
#   playwright install
#
from playwright.sync_api import sync_playwright, TimeoutError

BASE_URL = (
    "https://www.penguinrandomhouse.com/books/"
    "536247/devotions-a-read-with-jenna-pick-by-mary-oliver/"
)

# XPaths pulled directly from your reference table (indices 29–36)
AFFILIATES = {
    "amazon": {
        "selector": "xpath=/html/body/div[5]/main/div[3]/div/div/div[2]/div/div[3]/div[5]"
                    "/div/div[2]/div/ul/li/div[2]/div/a",
        "domain": "amazon.com"
    },
    "barnes": {
        "selector": "xpath=/html/body/div[5]/main/div[3]/div/div/div[2]/div/div[3]/div[5]"
                    "/div/div[2]/div/ul/li/div[2]/div/a[2]",
        "domain": "barnesandnoble.com"
    },
    "booksamillion": {
        "selector": "xpath=/html/body/div[5]/main/div[3]/div/div/div[2]/div/div[3]/div[5]"
                    "/div/div[2]/div/ul/li/div[2]/div/a[3]",
        "domain": "booksamillion.com"
    },
    "bookshop": {
        "selector": "xpath=/html/body/div[5]/main/div[3]/div/div/div[2]/div/div[3]/div[5]"
                    "/div/div[2]/div/ul/li/div[2]/div/a[4]",
        "domain": "bookshop.org"
    },
    "hudson": {
        "selector": "xpath=/html/body/div[5]/main/div[3]/div/div/div[2]/div/div[3]/div[5]"
                    "/div/div[2]/div/ul/li/div[2]/div/a[5]",
        "domain": "hudsonbooksellers.com"
    },
    "powells": {
        "selector": "xpath=/html/body/div[5]/main/div[3]/div/div/div[2]/div/div[3]/div[5]"
                    "/div/div[2]/div/ul/li/div[2]/div/a[6]",
        "domain": "powells.com"
    },
    "target": {
        "selector": "xpath=/html/body/div[5]/main/div[3]/div/div/div[2]/div/div[3]/div[5]"
                    "/div/div[2]/div/ul/li/div[2]/div/a[7]",
        "domain": "target.com"
    },
    "walmart": {
        "selector": "xpath=/html/body/div[5]/main/div[3]/div/div/div[2]/div/div[3]/div[5]"
                    "/div/div[2]/div/ul/li/div[2]/div/a[8]",
        "domain": "walmart.com"
    }
}

# XPath for index 27 – the Add to Cart button
ADD_TO_CART_SELECTOR = (
    "xpath=/html/body/div[5]/main/div[3]/div/div/div[2]/div/div[3]/div[5]"
    "/div/div[2]/div/ul/li/div/form/button"
)

def test_affiliate_links(page):
    print("[affiliates] Navigating to Devotions page")
    page.goto(BASE_URL, wait_until="networkidle")

    for name, info in AFFILIATES.items():
        sel = info["selector"]
        domain = info["domain"]

        print(f"[affiliates] Testing {name}")
        print(f"[affiliates] XPath: {sel}")

        # wait for the element to appear
        page.wait_for_selector(sel, timeout=10000)
        count = page.locator(sel).count()
        print(f"[affiliates] Locator count for {name}: {count}")

        # click and capture popup
        with page.expect_popup() as popup_info:
            page.click(sel)
        popup = popup_info.value
        popup.wait_for_load_state("domcontentloaded", timeout=10000)

        url = popup.url
        print(f"[affiliates] {name} opened URL: {url}")
        assert domain in url, (
            f"[affiliates] ❌ Expected '{domain}' in URL, got {url!r}"
        )
        popup.close()
        print(f"[affiliates] ✅ {name} link OK\n")

def test_add_to_cart(page):
    print("[add_to_cart] Navigating to Devotions page")
    page.goto(BASE_URL, wait_until="networkidle")

    print("[add_to_cart] Waiting for Add to Cart button")
    print(f"[add_to_cart] XPath: {ADD_TO_CART_SELECTOR}")
    page.wait_for_selector(ADD_TO_CART_SELECTOR, timeout=10000)
    count = page.locator(ADD_TO_CART_SELECTOR).count()
    print(f"[add_to_cart] Locator count for Add to Cart: {count}")

    btn = page.locator(ADD_TO_CART_SELECTOR).first
    btn.scroll_into_view_if_needed()
    print("[add_to_cart] Clicking Add to Cart…")
    try:
        with page.expect_response(
                lambda resp: "prhcart" in resp.url and resp.status == 200,
                timeout=15000):
            btn.click()
        print("[add_to_cart] ✅ Cart request succeeded")
    except TimeoutError:
        raise AssertionError(
            "[add_to_cart] ❌ Add to Cart did not trigger a successful cart request"
        )

def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)

        # run affiliates test
        ctx_aff = browser.new_context()
        page_aff = ctx_aff.new_page()
        try:
            test_affiliate_links(page_aff)
        finally:
            ctx_aff.close()

        # run add‑to‑cart test
        ctx_cart = browser.new_context()
        page_cart = ctx_cart.new_page()
        try:
            test_add_to_cart(page_cart)
        finally:
            ctx_cart.close()

        browser.close()
    print("🎉 All tests completed successfully.")

if __name__ == "__main__":
    main()
