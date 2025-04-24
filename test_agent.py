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
from typing import List, Dict, Any

# Ensure browser-use library is on the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'browser-use'))

# Import required packages
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage

# Create a simple mock chat model for testing
from typing import List, Any, Optional, Dict
from pydantic import Field

class MockChatModel(BaseChatModel):
    responses: List[str] = Field(default_factory=list)
    response_index: int = Field(default=0)
    
    def _generate(self, messages=None, stop=None, run_manager=None, **kwargs):
        from langchain_core.outputs import ChatGeneration, ChatResult
        
        if self.response_index < len(self.responses):
            response = self.responses[self.response_index]
            self.response_index += 1
        else:
            response = '{"action": [{"finish": {"reason": "No more responses"}}]}'
        
        message = AIMessage(content=response)
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])
    
    def _llm_type(self) -> str:
        return "mock_chat_model"

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
        responses = [
            '{"action": [{"navigate_browser": {"url": "' + task_prompt.split("Click on ")[1].split(" and")[0] + '"}}]}',
            '{"action": [{"click_element_by_index": {"element_index": 0, "element_type": "button", "element_text": "Add to cart"}}]}',
            '{"action": [{"finish": {"reason": "Task completed successfully"}}]}'
        ]
        llm = MockChatModel(responses=responses)
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
    
    # Create a new data structure for our enhanced history
    enhanced_history = []
    successful_selectors = [] # List to store selectors from successful interactions
    print("Processing agent history...") # Updated print message
    
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
                    "highlight_index": interacted_element.get("highlight_index"),
                    "url": url # Store the URL where the interaction happened
                }
                enhanced_entry["selector_info"] = selector_info
                # Add to list if it seems like a successful action (e.g., has a selector and was part of a known action type)
                action = h_entry.get("model_output", {}).get("action", [{}])[0]
                action_type = list(action.keys())[0] if action and isinstance(action, dict) else "unknown"
                if selector_info.get("selector") and action_type not in ["finish", "fail", "unknown"]:
                    successful_selectors.append(selector_info)

            except Exception as e:
                print(f"Error extracting selector info: {e}")
        
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

def extract_and_save_selectors(selectors_to_save: List[Dict[str, Any]]):
    """
    Extracts unique selectors used in successful interactions and saves them
    to agent_discovered_selectors.json. Associates selectors with the URL
    where they were used.
    """
    output_file = Path(__file__).parent / "agent_discovered_selectors.json"
    print(f"Extracting and saving successful selectors to {output_file}...")

    unique_selectors_by_url = {}

    for item in selectors_to_save:
        selector = item.get("selector")
        url = item.get("url") # Get the URL associated with this selector
        description = item.get("description", "Agent interaction")

        if selector and url:
            # Create a unique key for the selector within its URL context
            selector_key = f"{url}::{selector}"

            if url not in unique_selectors_by_url:
                unique_selectors_by_url[url] = {}

            if selector not in unique_selectors_by_url[url]:
                 unique_selectors_by_url[url][selector] = {
                    "selector": selector,
                    "url": url, # Store the URL
                    "description": description,
                    "count": 1,
                    # Include other relevant details if needed
                    "tag_name": item.get("tag_name"),
                    "xpath": item.get("xpath"),
                    "highlight_index": item.get("highlight_index")
                 }
            else:
                 unique_selectors_by_url[url][selector]["count"] += 1
                 # Update description if a more specific one is found later? (Optional)
                 # unique_selectors_by_url[url][selector]["description"] = description


    # Flatten the structure for saving
    final_selectors_list = []
    for url_selectors in unique_selectors_by_url.values():
        final_selectors_list.extend(url_selectors.values())


    try:
        # Load existing selectors if file exists
        existing_selectors = []
        if output_file.exists():
            try:
                with open(output_file, "r", encoding="utf-8") as f:
                    existing_selectors = json.load(f)
                    if not isinstance(existing_selectors, list):
                        print(f"Warning: Existing selectors file format is not a list. Overwriting.")
                        existing_selectors = []
            except json.JSONDecodeError:
                print(f"Warning: Could not decode existing selectors file. Overwriting.")
                existing_selectors = []

        # Combine and deduplicate (based on url + selector)
        combined_selectors_dict = {f"{s.get('url')}::{s.get('selector')}": s for s in existing_selectors}
        for new_selector in final_selectors_list:
             key = f"{new_selector.get('url')}::{new_selector.get('selector')}"
             if key not in combined_selectors_dict: # Only add truly new ones
                 combined_selectors_dict[key] = new_selector
             # Optional: Update existing descriptions or counts if needed


        final_list_to_save = list(combined_selectors_dict.values())


        # Save the combined and deduplicated list
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(final_list_to_save, f, indent=4)
        print(f"Successfully saved {len(final_list_to_save)} unique selectors to {output_file}")
    except Exception as e:
        print(f"Error saving selectors to {output_file}: {e}")


if __name__ == '__main__':
    import sys
    # Allow passing task prompt via CLI argument
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else None))
