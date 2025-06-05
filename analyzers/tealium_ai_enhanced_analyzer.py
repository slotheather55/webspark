import asyncio
import json
import sys
import re
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, AsyncGenerator
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError, Page, Browser, BrowserContext
import traceback
import nest_asyncio
import os
from pathlib import Path

# Import the original scripts for reuse of common components
# Assuming gemini_analyzer.py is in the same directory or Python path
try:
    from analyzers.tealium_manual_analyzer import (
        TAG_VENDORS, GLOBAL_VENDOR_OBJECTS, POST_LOAD_WAIT_MS, POST_CLICK_WAIT_MS,
        PRIVACY_PROMPT_ACCEPT_SELECTOR, MINICART_OVERLAY_SELECTOR,
        TEALIUM_PAYLOAD_MONITOR_SCRIPT, GENERAL_EVENT_TRACKER_SCRIPT,
        POST_LOAD_TAG_DETECTION_SCRIPT, get_data_from_page, clear_tracking_data,
        dismiss_overlays, analyze_vendors_on_page, find_vendors_in_requests,
        format_results_for_console
    )
except ImportError:
    print("ERROR: Could not import components from 'analyzers.tealium_manual_analyzer'.")
    print("Ensure 'analyzers/tealium_manual_analyzer.py' is accessible in the Python path.")
    sys.exit(1)


nest_asyncio.apply()

# Load agent-discovered selectors from JSON file
AGENT_SELECTORS_FILE = Path(__file__).parent.parent / "data" / "ai_discovered_selectors.json"

def load_agent_selectors() -> List[Dict[str, Any]]:
    """
    Load agent-discovered selectors from the JSON file.
    Returns a list of selector dictionaries.
    """
    try:
        if AGENT_SELECTORS_FILE.exists():
            with open(AGENT_SELECTORS_FILE, "r", encoding="utf-8") as f:
                content = f.read()
                if not content.strip(): # Handle empty file case
                    print(f"Warning: Agent selectors file is empty ({AGENT_SELECTORS_FILE})")
                    return []
                selectors = json.loads(content)
            # Basic validation: Check if it's a list of dicts
            if isinstance(selectors, list) and all(isinstance(item, dict) for item in selectors):
                 print(f"Loaded {len(selectors)} agent-discovered selectors from {AGENT_SELECTORS_FILE.name}")
                 return selectors
            else:
                 print(f"Error: Invalid format in {AGENT_SELECTORS_FILE.name}. Expected a list of dictionaries.")
                 return []
        else:
            print(f"Warning: Agent selectors file not found at {AGENT_SELECTORS_FILE}")
            return []
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {AGENT_SELECTORS_FILE.name}: {e}")
        return []
    except Exception as e:
        print(f"Error loading agent-discovered selectors: {e}")
        return []

# Main analysis function as async generator (Keep the existing function as is)
async def analyze_page_tags_and_events(url: str) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Main async generator function to perform page analysis and yield status updates.
    Uses agent-discovered selectors for interactions.

    Args:
        url: The URL to analyze

    Yields:
        Status dictionaries or the final results dictionary
    """
    # Load agent-discovered selectors
    agent_selectors = load_agent_selectors()

    # Filter selectors for the specific URL being analyzed
    # This assumes the selectors list might contain entries for multiple URLs
    selectors_for_this_url = [s for s in agent_selectors if s.get('url') == url and s.get('selector')]
    if not selectors_for_this_url:
         # Fallback: Check if *any* selectors exist, even if URL doesn't match strictly (less ideal)
         any_valid_selectors = [s for s in agent_selectors if s.get('selector')]
         if any_valid_selectors:
              yield {
                  "status": "warning",
                  "message": f"Warning: No agent selectors found specifically for URL '{url}'. Using {len(any_valid_selectors)} selectors found in the file, which might be for other URLs."
              }
              selectors_to_use = any_valid_selectors
         else:
              yield {
                  "status": "error",
                  "message": f"Error: No valid agent-discovered selectors found for URL '{url}' or in the file generally."
              }
              # Optionally return results with error, or just return
              results_error = {"url": url, "error": f"No valid selectors found for {url}."}
              yield {"status": "complete", "results": results_error}
              return
    else:
        selectors_to_use = selectors_for_this_url
        yield {
            "status": "progress",
            "message": f"Found {len(selectors_to_use)} agent selectors specific to URL: {url}"
        }


    # Initialize results dictionary
    results = { # Simplified structure for agent analysis initially
        "url": url,
        "analysisTimestamp": datetime.now().isoformat(),
        "steps": [], # Using steps similar to original analyzer
        "error": None
    }

    # Yield initial status update
    yield { #
        "status": "starting", #
        "message": f"🚀 Starting Agent Analysis for: {url}", #
        "url": url #
    }
    analysis_start_time = time.time()
    browser: Optional[Browser] = None
    context: Optional[BrowserContext] = None
    page: Optional[Page] = None
    nav_success = False # Track navigation status

    async with async_playwright() as p: #
        try:
            # --- Browser Setup (similar to original gemini_analyzer) ---
            yield {"status": "progress", "message": "    Launching browser..."} #
            browser = await p.chromium.launch(headless=True) #
            yield {"status": "progress", "message": "    >>> Browser launched successfully."} #
            context = await browser.new_context( #
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36", #
                viewport={"width": 1920, "height": 1080}, #
                java_script_enabled=True, #
                ignore_https_errors=True #
            )
            page = await context.new_page() #
            page.set_default_timeout(45000) # Set default timeout #

            # Add event listeners and monitoring scripts
            yield {"status": "progress", "message": "    Setting up monitoring scripts..."} #
            await page.add_init_script(TEALIUM_PAYLOAD_MONITOR_SCRIPT) #
            await page.add_init_script(GENERAL_EVENT_TRACKER_SCRIPT) #

             # --- Navigation (similar to original gemini_analyzer) ---
            yield {"status": "progress", "message": f"    Navigating to {url}..."} #
            load_start_time = time.time()
            network_requests_load = []
            def log_request(request):
                if request.url and not request.url.startswith('data:'):
                     network_requests_load.append({"url": request.url, "method": request.method})
            page.on("request", log_request)

            try:
                await page.goto(url, wait_until='networkidle', timeout=60000) #
                nav_success = True #
            except PlaywrightTimeoutError as nav_error: #
                yield {"status": "warning", "message": f"      Warning: Navigation with 'networkidle' timed out after 60s. Page might still be usable. ({nav_error})"} #
                nav_success = True # Treat as potentially usable #
            except PlaywrightError as nav_error: #
                 yield {"status": "warning", "message": f"      Error during navigation: {nav_error}. Trying 'load' state."} #
                 try: #
                      await page.goto(url, wait_until='load', timeout=40000) #
                      nav_success = True #
                 except Exception as fallback_nav_error: #
                       error_msg = f"      ❌ Fallback navigation ('load' state) also failed: {fallback_nav_error}" #
                       yield {"status": "error", "message": error_msg} #
                       results["steps"].append({"step": "Page Navigation", "status": "Failed", "error": str(fallback_nav_error)}) #
                       nav_success = False # Explicitly set to false #

            # Detach listener safely
            try:
                 page.remove_listener("request", log_request)
            except Exception as detach_err:
                 yield {"status": "warning", "message": f"      Warning: Could not detach request listener: {detach_err}"}


            load_duration = time.time() - load_start_time #
            if nav_success: #
                yield {"status": "progress", "message": f"    Page load attempt finished in {load_duration:.2f} seconds."} #
                results["steps"].append({"step": "Page Load", "duration_sec": load_duration, "status": "Completed (or Timeout)"}) #

                # Get page title
                results["page_title"] = await page.title() #
                yield {"status": "progress", "message": f"    Page title: {results['page_title']}"} #

                yield {"status": "progress", "message": "    Attempting to dismiss overlays..."} #
                await dismiss_overlays(page) #

                yield {"status": "progress", "message": f"    Waiting {POST_LOAD_WAIT_MS / 1000}s for async scripts..."} #
                await page.wait_for_timeout(POST_LOAD_WAIT_MS) #

                # --- Initial Data Collection (similar to original) ---
                yield {"status": "progress", "message": "    Collecting initial page data..."} #
                page_load_results = {} #
                collection_failed = False #
                try:
                    # Simplified: just collect initial events if needed, tag detection etc. can be added back if required
                    page_load_results["utag_data"] = await get_data_from_page(page, "utag_data") # Collect utag_data to potentially identify page type if needed later
                    page_load_results["initial_tealium_events"] = await get_data_from_page(page, "tealiumSpecificEvents") #
                    page_load_results["initial_general_events"] = await get_data_from_page(page, "generalTrackingEvents") #
                    page_load_results["tag_detection"] = await page.evaluate(POST_LOAD_TAG_DETECTION_SCRIPT) # Keep tag detection
                    page_load_results["vendors_on_page"] = analyze_vendors_on_page(page_load_results["tag_detection"]) # Keep vendor analysis

                    # Add load network summary
                    page_load_results["load_network_summary"] = { #
                        "total_requests": len(network_requests_load), #
                        "vendors_detected": find_vendors_in_requests(network_requests_load) #
                    }
                    results["pageLoadAnalysis"] = page_load_results # Store initial data under this key
                    results["steps"].append({"step": "Initial Data Collection", "status": "Success"}) #
                    yield {"status": "progress", "message": "    Initial data collected."} #
                except Exception as data_e: #
                    collection_failed = True #
                    error_msg = f"      ❌ Error collecting initial data: {data_e}" #
                    yield {"status": "error", "message": error_msg} #
                    results["steps"].append({"step": "Initial Data Collection", "status": "Failed", "error": str(data_e)}) #

                if not collection_failed: #
                    # Clear tracking data before interactions
                    yield {"status": "progress", "message": "    Clearing tracking data before interactions..."} #
                    await clear_tracking_data(page) #

                    # --- Interaction Loop using Agent Selectors ---
                    yield {"status": "progress", "message": f"    Analyzing {len(selectors_to_use)} agent-discovered interactions..."} #
                    interaction_analysis_results = [] # Store results here
                    results["agentInteractionAnalysis"] = interaction_analysis_results # Add key to results

                    for idx, selector_info in enumerate(selectors_to_use): #
                        selector = selector_info.get("selector") #
                        description = selector_info.get("description", f"Agent selector {idx+1}") #
                        # Assume 'click' type if not specified, agent might add 'type' later
                        interaction_type = selector_info.get("type", "click")

                        # Skip if selector is missing (already checked but good practice)
                        if not selector:
                            continue

                        interaction_result = { # Structure for each interaction
                            "selector": selector, #
                            "description": description, #
                            "type": interaction_type, # Include type
                            "status": "Pending", # Initial status
                            "tealium_events": [], #
                            "general_events": {}, # Store general events here
                            "vendors_in_network": {}, # Store network vendors here
                            "error": None #
                        }
                        interaction_analysis_results.append(interaction_result) # Add to list

                        try:
                            yield { #
                                "status": "progress", #
                                "message": f"\n      ▶️ Testing Interaction {idx+1}/{len(selectors_to_use)}: '{description}' ({selector})" #
                            }

                            # --- Simple Click Interaction (adapt if agent provides other types) ---
                            if interaction_type == "click":
                                element = page.locator(selector).first #
                                yield {"status": "progress", "message": "        Attempting to dismiss overlays before interaction..."} #
                                await dismiss_overlays(page) #

                                yield {"status": "progress", "message": f"        Waiting for element to be visible..."} #
                                await element.wait_for(state='visible', timeout=15000) # Wait for visibility
                                yield {"status": "progress", "message": "        Element is visible."} #
                                try: # Scroll into view #
                                     await element.scroll_into_view_if_needed(timeout=7000) #
                                except Exception as scroll_e: #
                                     yield {"status": "warning", "message": f"        Warning: Could not scroll element into view ({scroll_e}). Continuing click attempt."} #

                                await page.wait_for_timeout(300) # Small pause #

                                # Clear just before the specific click
                                yield {"status": "progress", "message": "        Clearing tracking data before click..."} #
                                await clear_tracking_data(page) #

                                yield {"status": "progress", "message": "        Attempting click..."} #
                                click_error_msg = None #
                                try: # Perform click with error handling #
                                    await element.click(timeout=15000) #
                                except PlaywrightError as pe: # Handle potential interception #
                                    if "intercept" in str(pe).lower(): #
                                        yield {"status": "warning", "message": "        Click intercepted, trying force=True..."} #
                                        await dismiss_overlays(page) # Try dismissing again #
                                        try: # Force click #
                                            await element.click(timeout=10000, force=True) #
                                        except Exception as force_e: #
                                            click_error_msg = f"Forced click failed: {force_e}" #
                                    else: #
                                        click_error_msg = f"Click failed (PlaywrightError): {pe}" #
                                except Exception as e: # General click exception #
                                    click_error_msg = f"Click failed (General Exception): {e}" #

                                if click_error_msg: # Check if click failed #
                                    raise Exception(click_error_msg) # Raise exception to be caught below #

                                yield {"status": "progress", "message": "        ✅ Click initiated successfully."} #
                                interaction_result["status"] = "Success" # Mark as success #

                                yield {"status": "progress", "message": f"        Waiting {POST_CLICK_WAIT_MS / 1000}s for events..."} #
                                await page.wait_for_timeout(POST_CLICK_WAIT_MS) #

                                yield {"status": "progress", "message": "        Retrieving data after click..."} #
                                # Get Tealium events after interaction
                                interaction_result["tealium_events"] = await get_data_from_page(page, "tealiumSpecificEvents") #
                                # Get other tracking data
                                interaction_result["general_events"] = await get_data_from_page(page, "generalTrackingEvents") #
                                # Analyze network requests from general events
                                if isinstance(interaction_result["general_events"], dict) and "network" in interaction_result["general_events"]: #
                                    network_data = interaction_result["general_events"]["network"] #
                                    if isinstance(network_data, list): #
                                        interaction_result["vendors_in_network"] = find_vendors_in_requests(network_data) #
                                    else: #
                                        interaction_result["vendors_in_network"] = {"error": "Network data is not a list"} #
                                else: #
                                    interaction_result["vendors_in_network"] = {"error": "General events or network data missing/invalid"} #

                                yield { #
                                    "status": "progress", #
                                    "message": f"        Data retrieved. Tealium events: {len(interaction_result['tealium_events'] if isinstance(interaction_result['tealium_events'], list) else [])}", # Check type #
                                }

                            else:
                                 yield {"status": "warning", "message": f"        Skipping unsupported interaction type from agent: '{interaction_type}'"} #
                                 interaction_result["status"] = "Skipped" #
                                 interaction_result["error"] = f"Unsupported type: {interaction_type}" #

                        except PlaywrightTimeoutError as e: # Catch timeout specifically #
                             error_msg = f"Timeout error during interaction '{description}': {e}" #
                             yield {"status": "warning", "message": f"        ❌ {error_msg}"} # Use warning for non-critical failures #
                             interaction_result["status"] = "Failure (Timeout)" # More specific status #
                             interaction_result["error"] = str(e) #
                        except Exception as e: # Catch other errors #
                            error_msg = f"Error during interaction '{description}': {str(e)}" #
                            yield { #
                                "status": "warning", # Use warning #
                                "message": f"        ❌ {error_msg}" #
                            }
                            interaction_result["status"] = "Failure" # General failure #
                            interaction_result["error"] = str(e) #
                            # Optional: Log traceback for unexpected errors
                            # traceback.print_exc()

                        # Optional: Clear tracking data again after processing each interaction's events?
                        # await clear_tracking_data(page) # Depends if events should be cumulative or per-interaction

                    results["steps"].append({"step": "Agent Interaction Analysis", "status": "Completed", "interactionsAnalyzed": len(selectors_to_use)}) # Add step result #

            else: # Handle navigation failure
                 yield {"status": "error", "message": "Skipping remaining analysis due to navigation failure."} #
                 # Ensure error is set in results if not already set by navigation try/except
                 if not results.get("error"):
                      results["error"] = "Navigation failed at start"


            # --- Final step reporting ---
            final_status_step = results["steps"][-1] if results["steps"] else {}
            if results.get("error") and final_status_step.get("status") != "Success": # Check if last step succeeded despite error key
                 yield {"status": "error", "message": f"❌ Analysis failed. Error: {results.get('error', 'Unknown final error')}"} #
                 results["steps"].append({"step": "Analysis Completion", "status": "Failed", "error": results.get('error', 'Unknown final error')})
            else:
                 yield {"status": "progress", "message": f"\n✅ Analysis finished in {time.time() - analysis_start_time:.2f} seconds."} #
                 results["steps"].append({"step": "Analysis Completion", "status": "Success"}) #


        except Exception as e: # Catch critical errors during setup/execution
            error_msg = f"\n❌ A critical error occurred during analysis setup or execution: {e}" #
            yield {"status": "error", "message": error_msg} #
            results["error"] = str(e) #
            # Ensure a step indicates the critical failure
            if not results["steps"] or results["steps"][-1].get("step") != "Critical Error":
                 results["steps"].append({"step": "Critical Error", "status": "Failed", "message": str(e)})
            traceback.print_exc() #

        finally:
            yield {"status": "progress", "message": "    Performing cleanup..."} #
            # --- Cleanup (similar to original) ---
            if page: #
                try: await page.close() #
                except Exception as e: print(f"      Error closing page: {e}") #
            if context: #
                try: await context.close() #
                except Exception as e: print(f"      Error closing context: {e}") #
            if browser: #
                try: await browser.close() #
                except Exception as e: print(f"      Error closing browser: {e}") #
            yield {"status": "progress", "message": "    Cleanup finished."} #

    # Yield the final results object at the very end with a 'complete' status
    yield {"status": "complete", "results": results} #


# --- MODIFIED: Function for running directly from terminal ---
async def run_main_analysis_terminal(): #
    """
    Loads agent selectors, extracts URL, runs analysis, and prints to terminal.
    """
    print("--- Running Agent Gemini Analyzer (Terminal Mode) ---") # Added header

    # 1. Load agent selectors first
    agent_selectors = load_agent_selectors() #

    if not agent_selectors: #
        print("❌ Error: No agent selectors found or file is invalid. Cannot proceed.") #
        print(f"   Please ensure '{AGENT_SELECTORS_FILE.name}' exists, is valid JSON, and contains selectors.") #
        print("   Run test_agent.py first to generate the selectors.") #
        return # Exit if no selectors

    # 2. Extract URL from the selectors
    url_to_analyze = None #
    # Try to find a URL from the loaded selectors
    for selector_info in agent_selectors: #
        if selector_info.get("url"): #
            url_to_analyze = selector_info["url"] #
            print(f"Found URL from agent selectors: {url_to_analyze}") #
            break # Use the first URL found

    if not url_to_analyze: #
        print(f"❌ Error: No 'url' field found in the loaded selectors in '{AGENT_SELECTORS_FILE.name}'.") #
        print("   Ensure test_agent.py is saving the URL along with the selector.") #
        # --- Optional Fallback: Ask user ---
        # fallback_url = input("Enter URL manually to proceed: ").strip()
        # if fallback_url:
        #     if not re.match(r'^https?://', fallback_url):
        #         print("Warning: Prepending https:// to manually entered URL.")
        #         fallback_url = "https://" + fallback_url
        #     url_to_analyze = fallback_url
        # else:
        #     print("No URL provided. Exiting.")
        #     return
        # --- End Optional Fallback ---
        return # Exit if no URL found and no fallback

    # 3. Run the analysis with the extracted URL
    print(f"Starting analysis for extracted URL: {url_to_analyze}") #

    start_time = time.time() #
    final_results = None #

    try:
        # Iterate through the generator to get updates and final result
        async for update in analyze_page_tags_and_events(url_to_analyze): # Pass the extracted URL
            if update.get("status") != "complete": # Print progress/warning/error messages
                  # Simple console logging for terminal mode
                  level = update.get("status", "info").upper() #
                  message = update.get("message", "") #
                  if level == "PROGRESS": # Less verbose for progress
                      print(f"  {message}") # Indent progress
                  elif level in ["ERROR", "WARNING"]: # Highlight errors/warnings
                      print(f"{level}: {message}") #
                  else: # Print other statuses like starting
                      print(f"{message}") #
            else: # Store final results when complete
                final_results = update.get("results") #
                print(f"\nAnalysis completed in {time.time() - start_time:.2f} seconds") #

        # 4. Format and Save Results (if successful)
        if final_results: #
            if final_results.get("error"): # Check final error status #
                print(f"\n*** ANALYSIS FAILED ***") #
                print(f"URL: {final_results.get('url', 'N/A')}") #
                print(f"Error: {final_results.get('error', 'Unknown error')}") #
                # Optionally print steps if available to show where it failed
                if final_results.get("steps"):
                     print("\nAnalysis Steps Trace:")
                     for step in final_results["steps"]:
                          print(f"  - Step: {step.get('step', 'N/A')}, Status: {step.get('status', 'N/A')}" + (f", Error: {step.get('error')}" if step.get('error') else ""))

            else: # Analysis seems successful
                 # Use the imported formatter
                 console_report = format_results_for_console(final_results) #
                 print("\n" + "="*80 + "\n") # Separator #
                 print(console_report) #

                 # Save results to file without timestamp to overwrite previous analysis
                 filename = f"data/tealium_ai_enhanced_analysis.json" #
                 try: #
                     with open(filename, 'w', encoding='utf-8') as f: #
                         json.dump(final_results, f, indent=2, default=str) # Use default=str #
                     print(f"\nFull analysis results saved to: {filename}") #
                 except Exception as save_e: #
                     print(f"\nError saving full results to JSON ({filename}): {save_e}") #
        else: # Should not happen if generator completes, but safety check
             print("\nAnalysis generator finished but did not yield final results.") #


    except KeyboardInterrupt: # Handle Ctrl+C
        print("\nAnalysis cancelled by user.") #
    except Exception as e: # Catch unexpected errors during execution
        print(f"\nAn unexpected error occurred in main terminal execution: {e}") #
        traceback.print_exc() #


if __name__ == "__main__": #
    try:
        # Run the terminal-specific main async function
        asyncio.run(run_main_analysis_terminal()) #

    except RuntimeError as e: # Handle asyncio errors #
         print(f"Asyncio runtime error: {e}") #
         if "cannot be called from a running event loop" in str(e): #
               print("Hint: If running in an environment like Jupyter, ensure `nest_asyncio.apply()` is called or use `await run_main_analysis_terminal()` if in an async context.") #
    except PlaywrightError as e: # Handle Playwright setup errors #
         print(f"Playwright setup or launch error: {e}") #
         print("\n--- Troubleshooting ---") #
         if "Executable doesn't exist" in str(e): #
              print("❌ ERROR: The required browser (likely Chromium) is not installed or cannot be found.") #
              print("➡️ Please run: playwright install chromium") #
         else: #
              print("Ensure Playwright is installed (`pip install playwright`) and browsers are installed (`playwright install`).") #
         print("If issues persist, check your Playwright installation and environment PATH.") #
         sys.exit(1) #
    except ImportError as e: # Handle import errors #
         if 'tealium_manual_analyzer' in str(e): # Check specifically for the reused module #
             print("❌ ERROR: Cannot import required components from `analyzers.tealium_manual_analyzer`.") #
             print("➡️ Please ensure `analyzers/tealium_manual_analyzer.py` exists in the Python path.") #
         else: #
             print(f"Import error: {e}") #
             print("➡️ Check if all required libraries (Playwright, nest_asyncio) are installed.") #
         sys.exit(1) #
    except Exception as e: # Catch any other critical startup errors #
        print(f"A critical error occurred before the main analysis loop: {e}") #
        traceback.print_exc() #
        sys.exit(1) #