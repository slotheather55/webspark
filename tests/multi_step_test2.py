import time
from playwright.sync_api import sync_playwright, expect # Keep expect for cookie banner check

# --- Configuration ---
START_URL = "https://www.penguinrandomhouse.com/books/318638/upstream-by-mary-oliver/9780143130086/"

# --- Viewport Data ---
# *** CRITICAL: Ensure these match your recording environment ***
MY_VIEWPORT_WIDTH = 1920
MY_VIEWPORT_HEIGHT = 950 # Adjust if needed

# --- Coordinate Data ---
# Step 2: Quick View Click
QUICK_VIEW_VIEWPORT_X = 276
QUICK_VIEW_VIEWPORT_Y = 313
QUICK_VIEW_SCROLL_X = 0
QUICK_VIEW_SCROLL_Y = 2045.3333740234375

# Step 3: Modal Add to Cart Click
MODAL_ATC_VIEWPORT_X = 1092
MODAL_ATC_VIEWPORT_Y = 352
MODAL_ATC_SCROLL_X = 0
MODAL_ATC_SCROLL_Y = 1896.6666259765625

# Step 4: Modal Play Button Click
MODAL_PLAY_VIEWPORT_X = 502
MODAL_PLAY_VIEWPORT_Y = 347
MODAL_PLAY_SCROLL_X = 0
MODAL_PLAY_SCROLL_Y = 1896.6666259765625

# --- Selectors (Only for Cookie Banner) ---
cookie_banner_selector = '#prh_privacy_prompt'
# Using text locator for accept button as it worked previously
cookie_accept_button_locator_text = ':text-is("I Agree")'

def run_hybrid_coord_only_after_cookie():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=600)
        context = browser.new_context(
            viewport={'width': MY_VIEWPORT_WIDTH, 'height': MY_VIEWPORT_HEIGHT}
        )
        page = context.new_page()
        print(f"Set viewport to {MY_VIEWPORT_WIDTH}x{MY_VIEWPORT_HEIGHT}")

        print(f"Navigating to: {START_URL}")
        try:
            page.goto(START_URL, wait_until='load', timeout=60000)
            print("Page loaded.")
            print("Pausing 2 seconds for page to settle...")
            time.sleep(2)
            print("Pause complete.")
        except Exception as e:
            print(f"ERROR: Failed to navigate to page. Error: {e}")
            page.screenshot(path="goto_failed_coord_strict.png")
            browser.close()
            return

        # --- Step 1: Dismiss Cookie Banner using LOCATOR ---
        banner_dismissed = False
        try:
            cookie_banner = page.locator(cookie_banner_selector)
            if cookie_banner.is_visible(timeout=7000):
                print("STEP 1: Cookie Banner found. Locating 'I Agree' button...")
                accept_button = cookie_banner.locator(cookie_accept_button_locator_text)

                print("Waiting for 'I Agree' button to be enabled...")
                expect(accept_button).to_be_enabled(timeout=10000)

                print("Clicking 'I Agree' button using locator...")
                accept_button.click()

                print("Verifying cookie banner disappeared...")
                # This is the ONLY locator-based verification after step 1
                expect(cookie_banner).not_to_be_visible(timeout=10000)
                print("-> VERIFICATION SUCCESS: Cookie banner dismissed using locator.")
                banner_dismissed = True
                time.sleep(1)
            else:
                print("STEP 1: Cookie banner not initially visible or already dismissed.")
                banner_dismissed = True

        except Exception as e:
            print(f"ERROR during Step 1 (Cookie Banner dismissal): {e}")
            page.screenshot(path="step1_cookie_locator_error_strict.png")
            browser.close() # Stop if banner cannot be reliably dismissed
            return

        # --- Subsequent steps ONLY use coordinates ---
        if banner_dismissed:
            # --- Step 2: Scroll and Click Coordinate for Quick View ---
            try:
                scroll_y_target_step2 = float(QUICK_VIEW_SCROLL_Y)
                print(f"STEP 2: Scrolling page to Y={scroll_y_target_step2})...")
                page.evaluate(f"() => window.scrollTo({QUICK_VIEW_SCROLL_X}, {scroll_y_target_step2})")
                time.sleep(0.75)
                print("-> Scroll complete.")

                print(f"STEP 2: Clicking Quick View at VIEWPORT ({QUICK_VIEW_VIEWPORT_X}, {QUICK_VIEW_VIEWPORT_Y})...")
                page.mouse.click(QUICK_VIEW_VIEWPORT_X, QUICK_VIEW_VIEWPORT_Y)
                print(f"-> Performed click action for Quick View (No outcome verified).")
                # Add pause to allow modal to visually open, but don't check with locator
                time.sleep(2)

            except Exception as e:
                print(f"ERROR during Step 2 (Quick View coord click): {e}")
                page.screenshot(path="step2_quickview_coord_error_strict.png")
                browser.close()
                return

            # --- Step 3: Scroll (if needed) and Click Coordinate for Modal Add to Cart ---
            try:
                scroll_y_target_step3 = float(MODAL_ATC_SCROLL_Y)
                current_scroll_y = page.evaluate("() => window.scrollY")
                if abs(current_scroll_y - scroll_y_target_step3) > 5:
                     print(f"STEP 3: Scrolling page to Y={scroll_y_target_step3} (Scroll changed)...")
                     page.evaluate(f"() => window.scrollTo({MODAL_ATC_SCROLL_X}, {scroll_y_target_step3})")
                     time.sleep(0.75)
                     print("-> Scroll complete.")
                else:
                     print(f"STEP 3: Scroll position Y={current_scroll_y} close enough to target Y={scroll_y_target_step3}, not scrolling.")

                print(f"STEP 3: Clicking Modal Add To Cart at VIEWPORT ({MODAL_ATC_VIEWPORT_X}, {MODAL_ATC_VIEWPORT_Y})...")
                page.mouse.click(MODAL_ATC_VIEWPORT_X, MODAL_ATC_VIEWPORT_Y)
                print(f"-> Performed click action for Modal Add To Cart (No outcome verified).")
                time.sleep(1.5) # Pause, maybe cart updates

            except Exception as e:
                print(f"ERROR during Step 3 (Modal Add to Cart coord click): {e}")
                page.screenshot(path="step3_modal_atc_coord_error_strict.png")
                browser.close()
                return

            # --- Step 4: Scroll (if needed) and Click Coordinate for Modal Play Button ---
            try:
                scroll_y_target_step4 = float(MODAL_PLAY_SCROLL_Y)
                current_scroll_y = page.evaluate("() => window.scrollY")
                if abs(current_scroll_y - scroll_y_target_step4) > 5:
                     print(f"STEP 4: Scrolling page to Y={scroll_y_target_step4} (Scroll changed)...")
                     page.evaluate(f"() => window.scrollTo({MODAL_PLAY_SCROLL_X}, {scroll_y_target_step4})")
                     time.sleep(0.75)
                     print("-> Scroll complete.")
                else:
                     print(f"STEP 4: Scroll position Y={current_scroll_y} same as Step 3 target Y={scroll_y_target_step4}, not scrolling.")


                print(f"STEP 4: Clicking Modal Play Button at VIEWPORT ({MODAL_PLAY_VIEWPORT_X}, {MODAL_PLAY_VIEWPORT_Y})...")
                page.mouse.click(MODAL_PLAY_VIEWPORT_X, MODAL_PLAY_VIEWPORT_Y)
                print(f"-> Performed click action for Modal Play Button (No outcome verified).")
                time.sleep(1)

            except Exception as e:
                print(f"ERROR during Step 4 (Modal Play Button coord click): {e}")
                page.screenshot(path="step4_modal_play_coord_error_strict.png")
                browser.close()
                return

        else:
             print("ABORTING: Could not reliably dismiss cookie banner.")
             browser.close()
             return

        # --- Final ---
        print("Full coordinate-based test sequence attempted (Cookie Banner via Locator).")
        print("Pausing 5 seconds before closing...")
        time.sleep(5)
        print("Closing browser.")
        browser.close()

if __name__ == "__main__":
    run_hybrid_coord_only_after_cookie()