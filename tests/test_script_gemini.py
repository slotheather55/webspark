import asyncio
from playwright.async_api import async_playwright, expect 
import os
import requests
import json
import base64
from dotenv import load_dotenv
import time

# --- Configuration ---
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("No OpenAI API key found. Add it to your .env file")

URL = "https://www.penguinrandomhouse.com/books/734292/the-very-hungry-caterpillars-peekaboo-easter-by-eric-carle-illustrated-by-eric-carle/9780593750179/"

# Define the elements we want selectors for, including their context and a basic locator
ELEMENTS_TO_PROCESS = [
    {
        "name": "Add to Cart Button (Board Book)",
        "context_description": "Board Book", # Used to find the right section
        "basic_locator": 'button:has-text("ADD TO CART")', # Playwright locator relative to context
        "ai_description": "The main 'Add to Cart' button" # Description for AI prompt
    },
    {
        "name": "Amazon Retailer Link (Board Book)",
        "context_description": "Board Book",
        "basic_locator": 'a:has-text("Amazon")', # Simple locator for the link
        "ai_description": "The link specifically for the 'Amazon' retailer"
    },
    {
        "name": "Barnes & Noble Retailer Link (Board Book)",
        "context_description": "Board Book",
        "basic_locator": 'a:has-text("Barnes & Noble")',
        "ai_description": "The link specifically for the 'Barnes & Noble' retailer"
    },
    # Add more elements here if needed
]

# --- Helper Functions ---
def encode_image_to_base64(image_path):
    # Less critical now, but potentially useful for future enhancements or debugging AI
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError: print(f"Info: Snapshot file not found at {image_path}"); return None
    except Exception as e: print(f"Error encoding image: {e}"); return None

# --- Playwright: Pinpoint Target and Extract Local Context ---
# *** Incorporates the fix for the 'is_attached' error and robust expansion wait ***
# --- Playwright: Pinpoint Target and Extract Local Context ---
# *** Incorporates BOTH ElementHandle fix AND expect().to_have_class() fix ***
async def pinpoint_and_extract(page, context_description, basic_target_locator):
    """
    Finds the specific instance of the target element within its context,
    ENSURING THE CONTEXT CONTAINER IS EXPANDED using robust methods,
    and extracts the outerHTML of the target and its parent using ElementHandles.
    """
    print(f"\n playwright: Pinpointing target using locator '{basic_target_locator}' within context '{context_description}'...")
    section_container_locator = None
    target_element_handle = None # This will store the final ElementHandle of the target
    parent_html = None
    target_html = None
    section_selector_used = None
    trigger_handle = None # Stores the ElementHandle of the trigger

    # 1. Find Context Anchor (Accordion Trigger) Locator and Get Handle
    try:
        # Prioritize visible triggers first
        trigger_locator_visible = page.locator(
             f'[data-bs-toggle*="collapse"]:has-text("{context_description}"):visible, '
             f'[data-toggle*="collapse"]:has-text("{context_description}"):visible'
        )
        # Fallback if no visible trigger found initially
        trigger_locator_any = page.locator(
             f'[data-bs-toggle*="collapse"]:has-text("{context_description}"), '
             f'[data-toggle*="collapse"]:has-text("{context_description}")'
        )

        trigger_locator_to_use = None
        if await trigger_locator_visible.count() > 0:
             print(f"   Found {await trigger_locator_visible.count()} potential visible trigger(s)... Using first.")
             trigger_locator_to_use = trigger_locator_visible.first
        elif await trigger_locator_any.count() > 0:
             print(f"   No visible trigger found initially. Found {await trigger_locator_any.count()} matching trigger(s) anywhere... Using first.")
             trigger_locator_to_use = trigger_locator_any.first
        else:
             print(f"   Could not find any trigger locator for '{context_description}'. Aborting.")
             return None, None, None # Abort early if no trigger locator

        # --- Get ElementHandle for the trigger ---
        if trigger_locator_to_use:
            try:
                print("   Attempting to get handle for trigger locator...")
                # Use element_handle() to get the specific handle
                trigger_handle = await trigger_locator_to_use.element_handle(timeout=5000)
                if not trigger_handle:
                    print("   Could not get handle for the trigger element.")
                    # No handle, can't proceed with this trigger
                else:
                    print("   Successfully got trigger handle.")
                    # --- Get target ID from the handle ---
                    target_id = await trigger_handle.get_attribute("data-bs-target") or \
                                await trigger_handle.get_attribute("data-target") or \
                                await trigger_handle.get_attribute("href")

                    if target_id and target_id.startswith("#"):
                        section_selector_used = target_id
                        # Locate the container using the ID
                        container_check_locator = page.locator(section_selector_used)
                        if await container_check_locator.count() == 1:
                            section_container_locator = container_check_locator # Store the locator
                            print(f"   Located context container element: {section_selector_used}")
                        else:
                            print(f"   Trigger target {target_id} not found or not unique on page.")
                            section_selector_used = None # Invalidate if container not found
                    else:
                        print(f"   Trigger handle found but has no valid target attribute (data-bs-target, data-target, href starting with #).")
            except Exception as e_handle:
                 print(f"   Error getting handle or attributes for trigger: {e_handle}")
                 trigger_handle = None # Ensure handle is None if error occurs
                 # If we failed to get the handle, we might not have the section_selector_used either

        # If we couldn't identify the container locator via the trigger, abort.
        if not section_container_locator:
            print(f"   Failed to identify a unique container locator for '{context_description}' using trigger mechanism. Aborting pinpoint.")
            # Clean up trigger handle if it exists
            if trigger_handle: await trigger_handle.dispose()
            return None, None, None

    except Exception as e:
        print(f"   Critical error during initial trigger/container finding for '{context_description}': {e}")
        if trigger_handle: await trigger_handle.dispose()
        return None, None, None

    # *** STEP 1.5: Ensure Container is Expanded using Handle and Expect ***
    try:
        print(f"   Checking if container {section_selector_used} is expanded...")
        is_expanded = await section_container_locator.evaluate('el => el.classList.contains("show")')

        if not is_expanded:
            print(f"   Container {section_selector_used} is collapsed. Attempting to click trigger...")
            # Use the trigger_handle we obtained earlier
            if trigger_handle and await trigger_handle.is_attached(): # Check handle validity
                print(f"   Trigger handle is valid. Scrolling and clicking.")
                await trigger_handle.scroll_into_view_if_needed(timeout=5000)
                await trigger_handle.click(timeout=5000)
                print(f"   Clicked trigger. Waiting for container '{section_selector_used}' to expand (gain 'show' class)...")

                # *** Use expect().to_have_class() to wait for expansion ***
                await expect(section_container_locator).to_have_class(
                    "show",
                    timeout=10000 # Keep generous timeout
                )
                print(f"   Container {section_selector_used} now has 'show' class (is expanded).")
            else:
                # If trigger_handle is None or detached here, expansion cannot proceed
                print("   Cannot expand container: Trigger handle was not obtained, is invalid, or became detached.")
                if trigger_handle: await trigger_handle.dispose()
                return None, None, None # Fail pinpointing
        else:
            print(f"   Container {section_selector_used} is already expanded (has 'show' class).")

    except Exception as e:
        print(f"   Error ensuring container {section_selector_used} is expanded: {e}")
        print(f"   Error Type: {type(e)}")
        if trigger_handle: await trigger_handle.dispose()
        return None, None, None # Abort if expansion check/wait fails


    # 2. Find Target Element *Handle* within Expanded Container
    final_target_locator = None # To store the specific locator used (e.g., .first)
    try:
        print(f"   Scrolling container {section_selector_used} into view...")
        await section_container_locator.scroll_into_view_if_needed(timeout=5000)
        await page.wait_for_timeout(300) # Brief wait

        # Locate the target *within* the container
        element_locator = section_container_locator.locator(basic_target_locator)
        count = await element_locator.count()
        print(f"   Found {count} instance(s) of '{basic_target_locator}' within {section_selector_used}.")

        if count == 1:
            final_target_locator = element_locator # Use the unique locator
            print(f"   Waiting for the unique element to be visible...")
            await final_target_locator.wait_for(state="visible", timeout=5000)
            print(f"   Uniquely located *visible* target.")
        elif count > 1:
             print(f"   Found {count} elements. Trying first visible instance within container.")
             # Combine :visible within the container locator
             final_target_locator = section_container_locator.locator(f'{basic_target_locator}:visible').first
             # Check if the 'first visible' locator actually finds something
             await final_target_locator.wait_for(state="attached", timeout=5000) # Wait for it to exist
             await final_target_locator.wait_for(state="visible", timeout=5000) # Then wait for visible
             print(f"   Located first visible instance.")
        else: # count == 0
             print(f"   Target element not found using '{basic_target_locator}' within expanded {section_selector_used}.")
             if trigger_handle: await trigger_handle.dispose()
             return None, None, None

        # --- Get the ElementHandle for the final target ---
        print("   Attempting to get handle for the final target element...")
        target_element_handle = await final_target_locator.element_handle(timeout=5000)
        if not target_element_handle:
             print("   Failed to get handle for the final target element.")
             # Fall through to return None, None, None
        else:
             print("   Successfully got final target element handle.")

    except Exception as e:
        print(f"   Error finding/getting handle for target element within container: {e}")
        if trigger_handle: await trigger_handle.dispose()
        if target_element_handle: await target_element_handle.dispose() # Clean up if partially successful
        return None, None, None

    # 3. Extract HTML Snippets using ElementHandles
    if target_element_handle:
        try:
            if await target_element_handle.is_attached():
                target_html = await target_element_handle.evaluate("el => el.outerHTML")
                # Get parent handle directly using JS evaluation for reliability
                parent_js_handle = await target_element_handle.evaluate_handle("el => el.parentElement")
                # Convert JSHandle to ElementHandle for further operations if needed, check it's valid
                parent_element_handle = parent_js_handle.as_element()

                if parent_element_handle and await parent_element_handle.is_attached():
                    parent_html = await parent_element_handle.evaluate("el => el.outerHTML")
                    print("   Extracted target and parent HTML snippets using handles.")
                    # Dispose the parent handle once done
                    await parent_element_handle.dispose()
                else:
                    print("   Could not locate a valid attached parent element via JS.")
                    parent_html = None
                    # Dispose the JSHandle if element handle wasn't valid
                    await parent_js_handle.dispose()

            else:
                print("   Target element handle became detached before HTML extraction.")
                target_html, parent_html = None, None
                # Dispose the handle if it became detached
                await target_element_handle.dispose()
                target_element_handle = None

        except Exception as e:
            print(f"   Error extracting HTML snippets using handles: {e}")
            target_html, parent_html = None, None
            # Attempt to dispose handles if an error occurred during extraction
            if target_element_handle: await target_element_handle.dispose()
            target_element_handle = None # Mark as invalid

    # Clean up trigger handle before returning
    if trigger_handle: await trigger_handle.dispose()

    # Return results. Handle should only be returned if it's still valid.
    if target_element_handle and await target_element_handle.is_attached():
         return target_html, parent_html, target_element_handle # Return the valid handle
    else:
         print("   Returning None for handles as target handle is invalid or was not found/extracted.")
         # Ensure cleanup if handle exists but is detached
         if target_element_handle: await target_element_handle.dispose()
         return None, None, None


# --- Playwright Validation ---
# *** Updated to use ElementHandle consistently ***
async def validate_ai_selector(page, original_target_handle, ai_selector):
    """
    Validates if the AI selector uniquely identifies the original target element.
    Expects original_target_handle to be an ElementHandle.
    """
    print(f"\n🧪 Validating AI selector: `{ai_selector}`")
    if not ai_selector:
        print("   ❌ FAILED: No selector provided for validation.")
        return False

    # Check if the original handle (should be an ElementHandle) is still valid
    if not original_target_handle or not isinstance(original_target_handle, playwright.async_api.ElementHandle) or not await original_target_handle.is_attached():
        print("   ❌ FAILED: Original element handle is invalid, lost, or detached. Cannot validate.")
        # Dispose if it exists but is detached/invalid type
        if original_target_handle and isinstance(original_target_handle, playwright.async_api.ElementHandle): await original_target_handle.dispose()
        return False

    try:
        ai_locator = page.locator(ai_selector)
        count = await ai_locator.count()

        if count == 0: print(f"   ❌ FAILED: AI selector matched 0 elements."); return False
        if count > 1: print(f"   ❌ FAILED: AI selector matched {count} elements (expected 1)."); return False

        # count == 1, check if it's the correct one using the handle
        print("   AI selector found 1 element. Checking if it matches the original handle...")
        ai_found_handle = await ai_locator.element_handle()

        if not ai_found_handle:
             print("   ❌ FAILED: Could not get handle for element found by AI selector.")
             return False # Cannot compare if handle isn't available

        # Compare the handles directly
        is_same_element = await page.evaluate("([h1, h2]) => h1 === h2", [ai_found_handle, original_target_handle])

        # Dispose the handle found by AI selector after comparison
        await ai_found_handle.dispose()

        if is_same_element:
             # Final visibility check on the *original* handle (which we validated is the same)
             # or alternatively on the ai_locator which we know points to the same element
             print("   Element handles match. Checking visibility...")
             await expect(ai_locator).to_be_visible(timeout=3000) # Use expect for visibility check too
             print(f"   ✅ PASSED: AI selector uniquely found the correct visible element.")
             return True
        else:
             print(f"   ❌ FAILED: AI selector found a different element than the original target.")
             return False

    except Exception as e:
        print(f"   ❌ FAILED: Error during validation (selector:'{ai_selector}'). Error: {e}")
        return False
    finally:
        # Ensure the original handle is disposed *after* validation is fully complete
        # (It should be disposed automatically when pinpoint_and_extract returns,
        # but explicit disposal here might be safer if passed around more)
        # However, the calling function `main` might still need it if validation fails
        # It's better practice to let the caller manage the lifecycle or dispose at the very end.
        # For now, we won't dispose original_target_handle here.
        pass

# --- Main Orchestration ---
# *** Updated to manage ElementHandle lifecycle ***
async def main():
    """
    Main function to orchestrate the process for all defined elements.
    """
    results = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False) # Start visible for debugging
        page = await browser.new_page()
        await page.set_viewport_size({"width": 1366, "height": 768})
        original_handle = None # Define handle outside loop for cleanup

        try:
            print(f"Navigating to {URL}...")
            await page.goto(URL, wait_until="networkidle", timeout=90000)
            print("Page loaded.")
            await page.wait_for_timeout(3000) # Allow slightly longer

            # --- Cookie Handling ---
            # (Keep your existing cookie handling logic)
            print(" playwright: Attempting to dismiss cookie banner (if present)...")
            # ... (cookie logic) ...


            # Process each element defined in ELEMENTS_TO_PROCESS
            for element_info in ELEMENTS_TO_PROCESS:
                element_name = element_info["name"]
                print(f"\n--- Processing: {element_name} ---")
                results[element_name] = {"status": "Failed", "selector": None} # Default result
                original_handle = None # Reset handle for each element

                try:
                    # 1. Pinpoint and Extract - returns an ElementHandle now
                    target_html, parent_html, original_handle = await pinpoint_and_extract(
                        page,
                        element_info["context_description"],
                        element_info["basic_locator"]
                    )

                    if not original_handle: # Check if handle was successfully returned
                        print(f"Failed to pinpoint {element_name}. Skipping AI generation and validation.")
                        results[element_name]["status"] = "Failed (Pinpoint)"
                        continue # Move to next element

                    # Ensure handle is valid before proceeding (belt and suspenders)
                    if not await original_handle.is_attached():
                         print(f"Pinpointed handle for {element_name} became detached before AI call. Skipping.")
                         results[element_name]["status"] = "Failed (Pinpoint Handle Lost)"
                         await original_handle.dispose() # Clean up detached handle
                         original_handle = None
                         continue


                    # 2. Get Selector from AI
                    ai_selector = get_selector_from_ai_snippet(
                        target_html,
                        parent_html,
                        element_info["ai_description"]
                    )

                    if not ai_selector:
                        print(f"Failed to get selector from AI for {element_name}. Skipping validation.")
                        results[element_name]["status"] = "Failed (AI Generation)"
                        # Dispose handle if AI fails
                        if original_handle: await original_handle.dispose()
                        original_handle = None
                        continue

                    # 3. Validate Selector - Pass the ElementHandle
                    is_valid = await validate_ai_selector(
                        page,
                        original_handle, # Pass the handle
                        ai_selector
                    )

                    results[element_name]["selector"] = ai_selector
                    results[element_name]["status"] = "Success" if is_valid else "Failed (Validation)"

                finally:
                     # Ensure handle is disposed after processing each element
                     if original_handle:
                         print(f"   Disposing handle for {element_name}.")
                         await original_handle.dispose()
                         original_handle = None


        except Exception as e:
            print(f"\n--- Critical Error during page processing: {e} ---")
            try:
                await page.screenshot(path="critical_error_screenshot.png")
                print("Saved error screenshot.")
            except: pass
        finally:
            print("\nClosing browser...")
            # Ensure any lingering handle is disposed if main loop exited unexpectedly
            if original_handle and isinstance(original_handle, playwright.async_api.ElementHandle):
                try: await original_handle.dispose()
                except: pass # Ignore errors during final cleanup
            await browser.close()

    # --- Final Summary ---
    # (Keep your existing summary logic)
    print("\n=== FINAL RESULTS ===")
    # ... (summary logic) ...

if __name__ == "__main__":
     # (Keep your existing __main__ block)
     if not OPENAI_API_KEY: print("Error: OPENAI_API_KEY environment variable not set.")
     else: asyncio.run(main())