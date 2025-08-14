#!/usr/bin/env python3
"""
browser_automation_agent.py

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
import logging
import traceback
from playwright.async_api import async_playwright
from typing import List, Dict, Any

# Add browser-use directory to Python path (go up one level from analyzers folder)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'browser-use'))

# Import required packages
from langchain_openai import ChatOpenAI, AzureChatOpenAI
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

from browser_use import Agent, Browser, BrowserConfig, BrowserProfile
from playwright._impl._api_structures import ViewportSize

async def main(task_prompt: str = None):
    load_dotenv()
    if task_prompt is None:
        # Hardcoded default task: navigate and find the buy button
        task_prompt = "Go to https://www.penguinrandomhouse.com/books/704944/happy-place-by-emily-henry/ and click on the 'Buy' button, then find and click on any other interactive element on the page."
    
    # Prepend GDPR/cookie banner dismissal to the task
    # Check if the task already includes cookie dismissal instructions
    if "cookie" not in task_prompt.lower() and "gdpr" not in task_prompt.lower() and "consent" not in task_prompt.lower():
        # Add cookie dismissal as a mandatory first step
        original_task = task_prompt
        task_prompt = f"IMPORTANT: After navigating to any page, your FIRST action must be to look for and dismiss any cookie consent banner, GDPR notice, or privacy popup. Click Accept, Agree, Submit, or any consent button. Only AFTER dismissing the banner, proceed with this task: {original_task}"
    
    # Check model provider configuration
    model_provider = os.getenv("MODEL_PROVIDER", "openai").lower()
    
    if model_provider == "azure":
        # Azure OpenAI Configuration
        azure_tenant_id = os.getenv("AZURE_TENANT_ID")
        azure_client_id = os.getenv("AZURE_CLIENT_ID")
        azure_client_secret = os.getenv("AZURE_CLIENT_SECRET")
        azure_deployment_model = os.getenv("AZURE_DEPLOYMENT_MODEL")
        azure_api_base = os.getenv("AZURE_API_BASE")
        
        if not all([azure_tenant_id, azure_client_id, azure_client_secret, azure_deployment_model, azure_api_base]):
            print("ERROR: Azure OpenAI configuration incomplete. Please set all Azure environment variables in your .env file.")
            print("Required: AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_DEPLOYMENT_MODEL, AZURE_API_BASE")
            # Use a mock LLM for testing without proper Azure config
            responses = [
                '{"action": [{"navigate_browser": {"url": "' + task_prompt.split("Click on ")[1].split(" and")[0] + '"}}]}',
                '{"action": [{"click_element_by_index": {"element_index": 0, "element_type": "button", "element_text": "Add to cart"}}]}',
                '{"action": [{"finish": {"reason": "Task completed successfully"}}]}'
            ]
            llm = MockChatModel(responses=responses)
        else:
            # Use Azure OpenAI
            print(f"Using Azure OpenAI with deployment: {azure_deployment_model}")
            llm = AzureChatOpenAI(
                azure_deployment=azure_deployment_model,
                azure_endpoint=azure_api_base,
                api_version="2023-12-01-preview",
                azure_ad_token_provider=None,  # Will use client credentials
                openai_api_key=azure_client_secret  # Using client secret as API key
            )
    else:
        # OpenAI Configuration (default)
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
            print(f"Using OpenAI with model: gpt-4o")
            llm = ChatOpenAI(model="gpt-4o", openai_api_key=openai_api_key)
    
    # Configure browser with larger viewport
    browser_profile = BrowserProfile(
        headless=True,  # Run in headless mode with larger viewport
        window_size=ViewportSize(width=1920, height=1080)
    )
    
    # Run the agent
    try:
        print(f"Starting agent with task: {task_prompt}")
        # Pass browser_profile instead of browser instance
        agent = Agent(task=task_prompt, llm=llm, browser_profile=browser_profile)
        history = await agent.run(max_steps=50)
        print("Agent run completed successfully")
    except Exception as e:
        print(f"ERROR: Agent run failed: {str(e)}")
        # Create a minimal JSON output with the error
        error_data = {
            "error": str(e),
            "history": []
        }
        with open("data/browser_automation_history.json", "w", encoding="utf-8") as f:
            json.dump(error_data, f, indent=2)
        print("Error saved to data/browser_automation_history.json")
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
    history.save_to_file("data/browser_automation_history.json")
    print("Done. History saved to data/browser_automation_history.json; screenshots in dom_state_data")

    # Load the history data
    data = json.load(open("data/browser_automation_history.json", "r", encoding="utf-8"))
    
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
        
        # Get action type for context
        action = h_entry.get("model_output", {}).get("action", [{}])[0]
        action_type = list(action.keys())[0] if action and isinstance(action, dict) else "unknown"
        
        # Store selectors for directly interacted elements
        if interacted_element:
            try:
                selector_info = {
                    "description": f"Agent: {interacted_element.get('tag_name', 'element')} ({interacted_element.get('highlight_index', '?')})",
                    "tag_name": interacted_element.get("tag_name"),
                    "xpath": interacted_element.get("xpath"),
                    "selector": interacted_element.get("css_selector"),
                    "highlight_index": interacted_element.get("highlight_index"),
                    "url": url,
                    "action_type": action_type
                }
                enhanced_entry["selector_info"] = selector_info
                print(f"DEBUG: Processing action type: {action_type}, has selector: {bool(selector_info.get('selector'))}")
                if selector_info.get("selector") and action_type not in ["finish", "fail", "unknown", "done"]:
                    successful_selectors.append(selector_info)
                    print(f"DEBUG: Added interacted selector: {selector_info['selector']}")

            except Exception as e:
                print(f"Error extracting interacted element selector: {e}")
        
        # ALSO capture all visible elements from the page state for comprehensive analysis
        try:
            # Check multiple possible locations for elements data
            state = h_entry.get("state", {})
            elements = state.get("element_tree", [])
            
            if not elements:
                # Try alternative locations for elements
                elements = state.get("elements", [])
            if not elements:
                elements = state.get("clickable_elements", [])
            if not elements:
                elements = state.get("dom_elements", [])
                
            print(f"DEBUG: Action {action_type} - checking elements. State keys: {list(state.keys())}")
            print(f"DEBUG: Found {len(elements)} elements for action {action_type}")
            
            if elements and url and action_type not in ["finish", "fail", "unknown", "done"]:
                print(f"DEBUG: Processing {len(elements)} elements on page for action {action_type}")
                
                # Extract selectors from key interactive elements
                for i, element in enumerate(elements[:20]):  # Limit to first 20 elements to avoid too much data
                    print(f"DEBUG: Element {i}: {element.get('tag_name')} - {bool(element.get('css_selector'))}")
                    if element.get("css_selector") and element.get("tag_name") in ["button", "a", "input", "select", "form"]:
                        element_selector_info = {
                            "description": f"Page: {element.get('tag_name', 'element')} ({element.get('highlight_index', '?')})",
                            "tag_name": element.get("tag_name"),
                            "xpath": element.get("xpath"),
                            "selector": element.get("css_selector"),
                            "highlight_index": element.get("highlight_index"),
                            "url": url,
                            "action_type": f"page_scan_{action_type}"
                        }
                        # Only add if we don't already have this selector
                        if not any(s.get("selector") == element_selector_info["selector"] for s in successful_selectors):
                            successful_selectors.append(element_selector_info)
                            print(f"DEBUG: Added page element selector: {element_selector_info['selector']}")
        except Exception as e:
            print(f"Error extracting page elements: {e}")
            import traceback
            traceback.print_exc()
        
        # Add the enhanced entry to our new history
        enhanced_history.append(enhanced_entry)
    
    # Replace the history in the data with our enhanced history
    data["history"] = enhanced_history
    
    # Save the enhanced data
    with open("data/browser_automation_history.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    print("Data processing complete and saved to data/browser_automation_history.json")

    # --- Extract and Save Selectors --- #
    print(f"DEBUG: Found {len(successful_selectors)} successful selectors")
    # Always try to save selectors, even if the list is empty
    # This ensures the file is created even if no selectors were found
    extract_and_save_selectors(successful_selectors)

def extract_and_save_selectors(selectors_to_save: List[Dict[str, Any]]):
    """
    Extracts unique selectors used in successful interactions and saves them
    to agent_discovered_selectors.json. Associates selectors with the URL
    where they were used.
    """
    output_file = Path(__file__).parent.parent / "data" / "ai_discovered_selectors.json"
    print(f"Extracting and saving successful selectors to {output_file}...")
    print(f"DEBUG: selectors_to_save: {selectors_to_save}")

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
                    content = f.read().strip()
                    if content:  # Only try to parse if there's content
                        # Re-read the file for parsing since we already read content
                        f.seek(0)
                        existing_selectors = json.load(f)
                        if not isinstance(existing_selectors, list):
                            print(f"Warning: Existing selectors file format is not a list. Overwriting.")
                            existing_selectors = []
                    else:
                        print(f"Warning: Existing selectors file is empty. Starting with empty list.")
                        existing_selectors = []
            except json.JSONDecodeError as e:
                print(f"Warning: Could not decode existing selectors file. Overwriting. Error: {e}")
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
        
        # Verify the file was created and has content
        if output_file.exists():
            file_size = output_file.stat().st_size
            print(f"DEBUG: Verified file exists with size: {file_size} bytes")
            if file_size == 0:
                print("WARNING: File exists but is empty!")
        else:
            print("ERROR: File was not created!")
    except Exception as e:
        print(f"Error saving selectors to {output_file}: {e}")
        print(f"Exception traceback: {traceback.format_exc()}")

# --- Custom Async Logging Handler ---
class AsyncQueueHandler(logging.Handler):
    """Sends LogRecord objects to an asyncio Queue."""
    def __init__(self, queue: asyncio.Queue):
        super().__init__()
        self.queue = queue

    def emit(self, record: logging.LogRecord):
        # Don't format here, put the raw record
        try:
            self.queue.put_nowait(record)
        except asyncio.QueueFull:
            # Handle queue full case if necessary, e.g., log a warning
            print(f"Log queue full, dropping record: {record.getMessage()}", file=sys.stderr)

# --- Main Async Generator ---
async def main_generator(task: str):
    """Runs the browser agent task, yielding logs and final results."""
    log_queue = asyncio.Queue()
    logger = logging.getLogger() # Get root logger
    # Ensure log level is appropriate (e.g., INFO)
    # Avoid setting level here if Flask/Uvicorn manages it, but ensure it's not higher than needed.
    logger.setLevel(logging.INFO)

    # Setup handler
    queue_handler = AsyncQueueHandler(log_queue)
    # Formatter will be used when retrieving from queue
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    queue_handler.setFormatter(formatter)

    # Add handler - check prevents duplicates if called multiple times rapidly
    # Consider a more robust check if concurrency is expected
    handler_added = False
    if queue_handler not in logger.handlers:
        logger.addHandler(queue_handler)
        handler_added = True

    agent_task = None
    queue_reader_task = None
    history_data = []
    selectors_data = []
    error_message = None
    agent_finished = False

    try:
        # Create task to run the agent logic (main function is already async)
        agent_task = asyncio.create_task(main(task), name="agent_run_task")
        # Create task to read the first item from the queue
        queue_reader_task = asyncio.create_task(log_queue.get(), name="queue_reader_task")

        pending = {agent_task, queue_reader_task}

        while not agent_finished:
            # Wait for either task to complete
            done, pending = await asyncio.wait(
                pending, return_when=asyncio.FIRST_COMPLETED
            )

            if queue_reader_task in done:
                try:
                    log_record: logging.LogRecord = queue_reader_task.result()
                    # Format the record using the handler's formatter
                    log_message_str = queue_handler.format(log_record)
                    yield json.dumps({"status": "log", "message": log_message_str})
                    log_queue.task_done()
                except asyncio.CancelledError:
                     pass # Task was cancelled, likely because agent finished
                except Exception as log_e:
                    print(f"Error processing log record: {log_e}", file=sys.stderr) # Log processing error

                # If the agent is still running, schedule the next queue read
                if not agent_task.done():
                    queue_reader_task = asyncio.create_task(log_queue.get(), name="queue_reader_task")
                    pending.add(queue_reader_task)
                else:
                     # Agent finished while we were processing log, ensure flag is set
                     agent_finished = True
                     queue_reader_task = None # No more reading needed

            if agent_task in done:
                agent_finished = True
                # Cancel the pending queue reader if it exists and is pending
                if queue_reader_task in pending:
                    queue_reader_task.cancel()
                    pending.remove(queue_reader_task) # Remove from pending set
                # Set task to None to avoid issues if loop iterates again
                queue_reader_task = None

                try:
                    # Get the agent output - could be history data or [] if error
                    history_data = agent_task.result() # Get result or raise exception
                    
                    # Data has already been processed and saved by main()
                    # Load it from the browser_automation_history.json file for consistency
                    try:
                        with open('data/browser_automation_history.json', 'r') as f:
                            data = json.load(f)
                            history_data = data.get('history', [])
                    except (FileNotFoundError, json.JSONDecodeError) as e:
                        logging.warning(f"Could not load processed data from data/browser_automation_history.json: {e}")
                    
                    # We don't have the selectors_data separately, but the frontend doesn't seem to use it
                    # directly, so we'll pass an empty list
                    selectors_data = []
                    # This log might arrive *after* completion signal if queue is processed slowly
                    # logging.info("Agent run and processing finished successfully.")
                except asyncio.CancelledError:
                     error_message = "Agent task was cancelled."
                     logging.warning(error_message)
                except Exception as e:
                    error_message = f"An error occurred during agent execution/processing: {e}"
                    # Log the full traceback via the logger itself
                    logging.exception(error_message)
                # Agent task is done, remove from loop consideration
                agent_task = None


        # Agent finished, drain any remaining logs from the queue
        while not log_queue.empty():
            try:
                log_record = log_queue.get_nowait()
                log_message_str = queue_handler.format(log_record)
                yield json.dumps({"status": "log", "message": log_message_str})
                log_queue.task_done()
            except asyncio.QueueEmpty:
                break # Should not happen with check, but safe practice
            except Exception as drain_e:
                 print(f"Error draining log queue: {drain_e}", file=sys.stderr)


    except asyncio.CancelledError:
         error_message = "Agent streaming task cancelled."
         logging.warning(error_message)
         # Ensure background tasks are cancelled
         if agent_task and not agent_task.done(): agent_task.cancel()
         if queue_reader_task and not queue_reader_task.done(): queue_reader_task.cancel()

    except Exception as main_loop_e:
        error_message = f"Error in agent streaming loop: {main_loop_e}"
        logging.exception(error_message)
        # Ensure background tasks are cancelled
        if agent_task and not agent_task.done(): agent_task.cancel()
        if queue_reader_task and not queue_reader_task.done(): queue_reader_task.cancel()


    finally:
        # Remove handler only if it was added by this instance
        if handler_added and queue_handler in logger.handlers:
             logger.removeHandler(queue_handler)

        # Yield final status (error or complete)
        if error_message:
            yield json.dumps({"status": "error", "message": error_message})
        else:
            # Yield success log *before* final completion message
            success_log = logging.LogRecord(
                name='agent_runner', level=logging.INFO, pathname='', lineno=0,
                msg='Agent run and processing finished successfully.', args=[], exc_info=None, func=''
            )
            yield json.dumps({"status": "log", "message": queue_handler.format(success_log)})

            final_result = {
                "history": history_data,
                "extracted_selectors": selectors_data
            }
            yield json.dumps({"status": "complete", "result": final_result})


# Removed argparse and __main__ block
