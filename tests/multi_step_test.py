import time
from playwright.sync_api import sync_playwright, expect

# --- Configuration ---
START_URL = "https://www.penguinrandomhouse.com/books/318638/upstream-by-mary-oliver/9780143130086/"
TARGET_BOOK_WORKID = "607057" # Orwell's Roses

# --- Selectors ---
carousel_container_selector = '#recommendationCarousel'
# *** CHANGE: Target the whole carousel element container ***
carousel_item_selector = f'{carousel_container_selector} div.carousel-element[data-workid="{TARGET_BOOK_WORKID}"]'
# We still need the modal selector for verification
modal_selector = '#single-title-view'

def run_carousel_test():
    with sync_playwright() as p:
        # --- Setup ---
        browser = p.chromium.launch(headless=False, slow_mo=500)
        page = browser.new_page()
        page.set_viewport_size({"width": 1280, "height": 800})

        print(f"Navigating to: {START_URL}")
        try:
            page.goto(START_URL, wait_until='load', timeout=60000)
            print("Page loaded.")
        except Exception as e:
            print(f"ERROR: Failed to navigate to page. Error: {e}")
            page.screenshot(path="goto_failed.png")
            browser.close()
            return

        # --- Wait for Carousel and Click Carousel Item ---
        try:
            print(f"Waiting for carousel container: {carousel_container_selector}")
            carousel_container = page.locator(carousel_container_selector)
            expect(carousel_container).to_be_visible(timeout=20000)
            print("Carousel container is visible.")

            # *** CHANGE: Use the carousel item selector ***
            print(f"Looking for carousel item: {carousel_item_selector}")
            carousel_item = page.locator(carousel_item_selector)

            print("Scrolling carousel item into view...")
            carousel_item.scroll_into_view_if_needed()
            time.sleep(1) # Pause after scroll

            print("Waiting for carousel item to be visible...")
            expect(carousel_item).to_be_visible(timeout=15000)
            print("Carousel item is visible.")

            # --- Handle potential cookie banner just before clicking ---
            cookie_banner = page.locator('#prh_privacy_prompt')
            if cookie_banner.is_visible(timeout=1000):
                 print("Cookie banner detected, attempting to dismiss...")
                 accept_button = cookie_banner.get_by_role("button", name="I Agree")
                 if accept_button.is_visible(timeout=1000):
                     accept_button.click(timeout=5000)
                     expect(cookie_banner).not_to_be_visible(timeout=5000)
                     print("Cookie banner dismissed.")
                 else:
                     print("Could not find 'I Agree' button on visible banner.")
            # --- End Cookie Handling ---

            # *** CHANGE: Click the carousel item itself ***
            print("Attempting to click carousel item...")
            carousel_item.click(timeout=10000) # Click the container
            print("Carousel item clicked successfully.")

            # --- Basic Verification: Check if modal appeared ---
            print(f"Waiting for modal '{modal_selector}' to appear...")
            modal = page.locator(modal_selector)
            expect(modal).to_be_visible(timeout=15000)
            print("VERIFICATION SUCCESS: Modal appeared.")

            print("Test sequence complete. Pausing before closing...")
            time.sleep(5)

        except Exception as e:
            print(f"ERROR during interaction: {e}")
            page.screenshot(path="interaction_error.png")

        # --- Teardown ---
        print("Closing browser.")
        browser.close()

if __name__ == "__main__":
    run_carousel_test()