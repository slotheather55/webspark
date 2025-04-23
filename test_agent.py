#!/usr/bin/env python3
"""
test_agent.py

Run a browser-use AI agent for a given task prompt, record all actions, and save history to a JSON file.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv
import base64
import time
from pathlib import Path
import json
from playwright.async_api import async_playwright
from gemini_analyzer import TEALIUM_PAYLOAD_MONITOR_SCRIPT, POST_LOAD_WAIT_MS
from typing import List, Dict, Any

# Ensure browser-use library is on the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'browser-use'))

from langchain_openai import ChatOpenAI
from browser_use import Agent

async def main(task_prompt: str = None):
    load_dotenv()
    if task_prompt is None:
        # Hardcoded default task: navigate and add to cart
        task_prompt = "Click on https://www.penguinrandomhouse.com/books/536247/devotions-a-read-with-jenna-pick-by-mary-oliver/ and then add to cart."
    
    # Check for OpenAI API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("ERROR: OPENAI_API_KEY environment variable not set. Please set it in your .env file.")
        # Use a mock LLM for testing without API key
        from langchain.llms.fake import FakeListLLM
        responses = [
            '{"action": [{"navigate_browser": {"url": "' + task_prompt.split("Click on ")[1].split(" and")[0] + '"}}]}',
            '{"action": [{"click_element_by_index": {"element_index": 0, "element_type": "button", "element_text": "Add to cart"}}]}',
            '{"action": [{"finish": {"reason": "Task completed successfully"}}]}'
        ]
        llm = FakeListLLM(responses=responses)
    else:
        # Use the real OpenAI LLM
        llm = ChatOpenAI(model="gpt-4o", openai_api_key=openai_api_key)
    
    # Run the agent
    try:
        print(f"Starting agent with task: {task_prompt}")
        agent = Agent(task=task_prompt, llm=llm)
        history = await agent.run(max_steps=50)
        print("Agent run completed successfully")
    except Exception as e:
        print(f"ERROR: Agent run failed: {str(e)}")
        # Create a minimal JSON output with the error
        error_data = {
            "error": str(e),
            "history": []
        }
        with open("out.json", "w", encoding="utf-8") as f:
            json.dump(error_data, f, indent=2)
        print("Error saved to out.json")
        return []  # Return empty list to indicate error

    # Save screenshots externally
    screenshot_dir = Path(__file__).parent / 'browser-use' / 'dom_state_data'
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    
    # Process screenshots before saving to JSON
    screenshot_paths = {}
    for idx, h in enumerate(history.history):
        b64 = h.state.screenshot
        if b64:
            file_name = f"dom_state_{int(time.time())}_{idx}.png"
            file_path = screenshot_dir / file_name
            with open(file_path, 'wb') as f:
                f.write(base64.b64decode(b64))
            # Store path for later use in JSON
            screenshot_paths[idx] = str(file_path)
            # Update reference in history object
            h.state.screenshot = str(file_path)

    # Save history to JSON file
    history.save_to_file("out.json")
    print("Done. History saved to out.json; screenshots in dom_state_data")

    # Load the history data
    data = json.load(open("out.json", "r", encoding="utf-8"))
    
    # Create a new data structure for our enhanced history with Tealium events
    enhanced_history = []
    successful_selectors = [] # List to store selectors from successful interactions
    print("Processing agent history and capturing Tealium events...")
    
    # Process each history entry
    for idx, h_entry in enumerate(data.get("history", [])):
        # Create a copy of the entry to avoid modifying the original
        enhanced_entry = dict(h_entry)
        url = h_entry.get("state", {}).get("url")
        interacted_element = h_entry.get("state", {}).get("interacted_element", [None])[0]
        
        # Store selectors for future simulation if an element was interacted with
        if interacted_element:
            try:
                selector_info = {
                    "description": f"Agent: {interacted_element.get('tag_name', 'element')} ({interacted_element.get('highlight_index', '?')})", # Add a basic description
                    "tag_name": interacted_element.get("tag_name"),
                    "xpath": interacted_element.get("xpath"),
                    "selector": interacted_element.get("css_selector"), # Use 'selector' key for consistency
                    "highlight_index": interacted_element.get("highlight_index")
                }
                enhanced_entry["selector_info"] = selector_info
                # Add to list if it seems like a successful action (e.g., has a selector and was part of a known action type)
                action = h_entry.get("model_output", {}).get("action", [{}])[0]
                action_type = list(action.keys())[0] if action and isinstance(action, dict) else "unknown"
                if selector_info.get("selector") and action_type not in ["finish", "fail", "unknown"]:
                    successful_selectors.append(selector_info)

            except Exception as e:
                print(f"Error extracting selector info: {e}")
        
        # Capture Tealium events for the URL
        if url and url != "about:blank":
            try:
                print(f"Capturing Tealium events for URL in step {idx+1}: {url}")
                events = await capture_tealium_for_url(url)
                enhanced_entry["tealium_events"] = events
                
                # If this was a click action, capture Tealium events specifically for this action
                if interacted_element:
                    try:
                        action = h_entry.get("model_output", {}).get("action", [{}])[0]
                        action_type = "unknown"
                        if action and isinstance(action, dict):
                            action_type = list(action.keys())[0] if action else "unknown"
                        
                        # For click actions, we want to capture the Tealium events that happened during the click
                        if action_type == "click_element_by_index" or (isinstance(action_type, str) and "click" in action_type.lower()):
                            print(f"Capturing click-specific Tealium events for step {idx+1}")
                            click_events = await capture_tealium_for_url(url, capture_click_events=True)
                            enhanced_entry["click_tealium_events"] = click_events
                        
                        # Also capture post-click events if we navigate to a new URL
                        if idx < len(data.get("history", [])) - 1:
                            next_url = data["history"][idx+1].get("state", {}).get("url")
                            if next_url and next_url != url:
                                print(f"Capturing post-click Tealium events for step {idx+1} on URL: {next_url}")
                                post_click_events = await capture_tealium_for_url(next_url)
                                enhanced_entry["post_click_tealium_events"] = post_click_events
                    except Exception as e:
                        print(f"Error capturing click events: {e}")
            except Exception as e:
                print(f"Error capturing Tealium events: {e}")
        
        # Add the enhanced entry to our new history
        enhanced_history.append(enhanced_entry)
    
    # Replace the history in the data with our enhanced history
    data["history"] = enhanced_history
    
    # Save the enhanced data
    with open("out.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    print("Data processing complete and saved to out.json")

    # --- Extract and Save Selectors --- #
    if successful_selectors: # Only run if we found selectors
        extract_and_save_selectors(successful_selectors)

async def capture_tealium_for_url(url: str, capture_click_events=False):
    events = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Add the Tealium monitoring script
        await page.add_init_script(TEALIUM_PAYLOAD_MONITOR_SCRIPT)
        
        # Navigate to the URL
        await page.goto(url, wait_until='networkidle')
        await page.wait_for_timeout(POST_LOAD_WAIT_MS)
        
        # If we're specifically looking for click events, try to find and click the Add to Cart button
        if capture_click_events:
            try:
                # Try to find and click the Add to Cart button
                print(f"Looking for Add to Cart button on {url}")
                add_to_cart_selectors = [
                    'div[id^="collapse"].in form[action*="prhcart.php"] button:has-text("Add to cart")',
                    'button:has-text("Add to Cart")',
                    'button:has-text("ADD TO CART")',
                    'button.btn.buy2',
                    'form[action*="prhcart.php"] button'
                ]
                
                # Try each selector
                for selector in add_to_cart_selectors:
                    try:
                        if await page.locator(selector).count() > 0:
                            print(f"Found Add to Cart button with selector: {selector}")
                            # Click the button
                            await page.click(selector)
                            print("Clicked Add to Cart button")
                            # Wait for events to fire
                            await page.wait_for_timeout(2000)
                            break
                    except Exception as click_e:
                        print(f"Could not click selector {selector}: {click_e}")
                        continue
            except Exception as e:
                print(f"Error during click simulation: {e}")
        
        # Capture the Tealium events
        try:
            events = await page.evaluate("() => window.tealiumSpecificEvents || []")
            print(f"Captured {len(events)} Tealium events from {url}")
        except Exception as e:
            events = {"error": str(e)}
            print(f"Error capturing Tealium events: {e}")
        
        await browser.close()
    return events

def extract_and_save_selectors(selectors_to_save: List[Dict[str, Any]]):
    """Extract selectors from successful agent interactions and save them for future use."""
    if not selectors_to_save:
        print("No successful selectors found to save.")
        return

    output_file = Path(__file__).parent / "agent_discovered_selectors.json"
    existing_selectors = []
    if output_file.exists():
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                existing_selectors = json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Could not decode existing selectors file {output_file}. Overwriting.")
        except Exception as e:
            print(f"Error reading existing selectors file {output_file}: {e}. Overwriting.")

    print(f"Found {len(selectors_to_save)} new potential selectors from agent run.")

    # Create a set of existing selectors for quick lookup
    existing_selector_set = {s.get('selector') for s in existing_selectors if s.get('selector')}

    new_count = 0
    # Prepare selectors in the desired format, adding only new ones
    formatted_selectors = existing_selectors # Start with existing ones
    for item in selectors_to_save:
        css_selector = item.get('selector')
        if css_selector and css_selector not in existing_selector_set:
            formatted_selector = {
                "description": item.get("description", f"Agent Discovered: {item.get('tag_name', 'element')}"),
                "selector": css_selector
                # Add other relevant info if needed, like xpath, tag_name etc.
                # "xpath": item.get("xpath"),
                # "tag_name": item.get("tag_name")
            }
            formatted_selectors.append(formatted_selector)
            existing_selector_set.add(css_selector) # Add to set to prevent duplicates within this run
            new_count += 1

    if new_count > 0:
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(formatted_selectors, f, indent=4)
            print(f"Successfully saved {new_count} new agent-discovered selectors to {output_file}")
        except Exception as e:
            print(f"Error saving agent-discovered selectors to {output_file}: {e}")
    else:
        print("No new unique selectors found to add.")


if __name__ == '__main__':
    import sys
    # Allow passing task prompt via CLI argument
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else None))
