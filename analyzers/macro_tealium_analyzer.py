import asyncio
import json
import re
import traceback
from datetime import datetime
from typing import Dict, List, Any, AsyncGenerator
from urllib.parse import parse_qs, unquote

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError, Page, Browser, BrowserContext

# Reuse scripts, helpers, and vendor definitions from the manual analyzer to ensure identical reporting
from .tealium_manual_analyzer import (
    TEALIUM_PAYLOAD_MONITOR_SCRIPT,
    GENERAL_EVENT_TRACKER_SCRIPT,
    POST_LOAD_WAIT_MS,
    POST_CLICK_WAIT_MS,
    PRIVACY_PROMPT_ACCEPT_SELECTOR,
    MINICART_OVERLAY_SELECTOR,
    get_data_from_page,
    clear_tracking_data,
    dismiss_overlays,
    find_vendors_in_requests,
    analyze_vendors_on_page,
    TAG_VENDORS,
    GLOBAL_VENDOR_OBJECTS,
)

def parse_multipart_form_data(form_data: str) -> Dict[str, Any]:
    """Parse multipart form data to extract JSON tracking payload"""
    try:
        # Find the boundary
        boundary_match = re.search(r'------WebKitFormBoundary([A-Za-z0-9]+)', form_data)
        if not boundary_match:
            return {"error": "No boundary found in multipart data"}
        
        boundary = f"------WebKitFormBoundary{boundary_match.group(1)}"
        parts = form_data.split(boundary)
        
        for part in parts:
            if 'name="data"' in part:
                # Extract the JSON data between headers and boundary
                json_start = part.find('\r\n\r\n')
                if json_start != -1:
                    json_start += 4  # Skip \r\n\r\n
                    json_end = part.rfind('\r\n')
                    if json_end == -1:
                        json_end = len(part)
                    
                    json_data = part[json_start:json_end].strip()
                    if json_data:
                        try:
                            return json.loads(json_data)
                        except json.JSONDecodeError:
                            return {"raw_json_data": json_data, "error": "Failed to parse JSON"}
        
        return {"error": "No data field found in multipart form"}
    except Exception as e:
        return {"error": f"Failed to parse multipart data: {str(e)}"}

def extract_initiator_from_url(url: str) -> str:
    """Extract which Tealium tag initiated the request from URL or referrer"""
    try:
        # Look for utag patterns in the URL
        utag_match = re.search(r'utag[\._](\d+)', url)
        if utag_match:
            return f"utag.{utag_match.group(1)}.js"
        return "unknown_initiator"
    except Exception:
        return "unknown_initiator"

async def analyze_macro_selectors_against_config(macro_url: str, macro_selectors: List[Dict], macro_name: str = "Unknown Macro") -> AsyncGenerator[Dict[str, Any], None]:
    """
    Analyze Tealium events for a specific macro's click selectors.
    
    Args:
        macro_url: URL where the macro was recorded
        macro_selectors: List of selectors from the macro actions
        macro_name: Name of the macro being analyzed
    
    Yields:
        Dictionary updates for streaming response
    """
    
    browser = None
    context = None
    page = None
    
    try:
        yield {
            "status": "starting",
            "message": f"Starting Tealium analysis for macro: {macro_name}",
            "progress": 0
        }
        
        # Launch browser
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        # Inject the same init scripts as the manual analyzer for consistent event capture
        await page.add_init_script(TEALIUM_PAYLOAD_MONITOR_SCRIPT)
        await page.add_init_script(GENERAL_EVENT_TRACKER_SCRIPT)
        
        yield {
            "status": "browser_launched",
            "message": "Browser launched successfully",
            "progress": 10
        }
        
        # Set up monitoring
        network_requests = []
        console_logs = []
        javascript_errors = []
        
        # Monitor network requests
        def handle_request(request):
            network_requests.append({
                "url": request.url,
                "method": request.method,
                "timestamp": datetime.now().isoformat()
            })
        
        page.on("request", handle_request)
        
        # Capture Tealium i.gif REQUEST payloads
        tealium_i_gif_payloads = []
        
        async def _capture_tealium_request(request):
            try:
                url = request.url
                if "datacloud.tealiumiq.com" in url and "/i.gif" in url:
                    # Get the request body (contains the actual tracking data)
                    post_data = request.post_data
                    headers = request.headers
                    
                    # Parse the tracking data
                    tracking_data = None
                    if post_data:
                        try:
                            # Handle multipart form data
                            if 'multipart/form-data' in headers.get('content-type', ''):
                                tracking_data = parse_multipart_form_data(post_data)
                            elif 'application/x-www-form-urlencoded' in headers.get('content-type', ''):
                                # Handle URL encoded data
                                tracking_data = parse_qs(unquote(post_data))
                            else:
                                # Try to parse as JSON
                                tracking_data = json.loads(post_data)
                        except Exception as e:
                            # Store raw data if parsing fails
                            tracking_data = {"raw_data": post_data[:5000], "parse_error": str(e)}
                    
                    payload_entry = {
                        "url": url,
                        "method": request.method,
                        "timestamp": datetime.now().isoformat(),
                        "headers": dict(headers),
                        "tracking_data": tracking_data,
                        "initiator": extract_initiator_from_url(url)
                    }
                    tealium_i_gif_payloads.append(payload_entry)
            except Exception:
                # Never fail analysis due to request parsing
                pass
        
        def handle_request(request):
            try:
                asyncio.create_task(_capture_tealium_request(request))
            except Exception:
                pass
        
        page.on("request", handle_request)
        
        # Monitor console logs
        def handle_console(msg):
            console_logs.append({
                "type": msg.type,
                "text": msg.text,
                "timestamp": datetime.now().isoformat()
            })
        
        page.on("console", handle_console)
        
        # Monitor JavaScript errors
        def handle_page_error(error):
            javascript_errors.append({
                "message": str(error),
                "timestamp": datetime.now().isoformat()
            })
        
        page.on("pageerror", handle_page_error)
        
        # Navigate to the page
        yield {
            "status": "navigating",
            "message": f"Loading page: {macro_url}",
            "progress": 20
        }
        
        await page.goto(macro_url, wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(POST_LOAD_WAIT_MS)
        
        # Dismiss cookie banners and overlays automatically
        await dismiss_cookie_overlays_advanced(page)
        
        yield {
            "status": "page_loaded",
            "message": "Page loaded successfully",
            "progress": 30
        }
        
        # Handle privacy prompts if they exist
        try:
            privacy_button = await page.query_selector(PRIVACY_PROMPT_ACCEPT_SELECTOR)
            if privacy_button:
                await privacy_button.click()
                await page.wait_for_timeout(1000)
                yield {
                    "status": "privacy_handled",
                    "message": "Privacy prompt accepted",
                    "progress": 35
                }
        except Exception as e:
            # Privacy prompt handling is optional
            pass
        
        # Get baseline state
        initial_tags = await detect_tags_and_vendors(page)
        initial_objects = await detect_vendor_objects(page)
        
        yield {
            "status": "baseline_captured",
            "message": f"Baseline captured: {len(initial_tags)} tags, {len(initial_objects)} vendor objects",
            "progress": 40
        }
        
        # Process each macro selector
        macro_results = []
        total_selectors = len(macro_selectors)
        
        for i, selector_info in enumerate(macro_selectors):
            selector = selector_info.get('selector', '')
            description = selector_info.get('description', f'Action {i+1}')
            locator_bundle = selector_info.get('locator_bundle') or {}
            
            if not selector:
                continue
                
            yield {
                "status": "testing_selector",
                "message": f"Testing: {description}",
                "progress": 40 + (i / total_selectors) * 50,
                "current_selector": selector,
                "selector_description": description
            }
            
            console_logs.clear()
            network_requests.clear()
            
            try:
                clicked = False
                pre_click_tags = []
                pre_click_objects = []
                strategy_used = None
                clicked_handle = None
                pre_tealium_payload_count = len(tealium_i_gif_payloads)
                click_timestamp = None
                
                role = locator_bundle.get('role')
                name = locator_bundle.get('name')
                if isinstance(role, str) and isinstance(name, str) and role and name:
                    try:
                        yield {
                            "status": "progress",
                            "message": f"    Trying ARIA role+name locator ({role}, '{name}')..."
                        }
                        scope = page.locator('div[id^="collapse"].in').first
                        target = page.get_by_role(role, name=name).filter(has=scope).first
                        await target.scroll_into_view_if_needed()
                        await target.wait_for(state='visible', timeout=4000)
                        pre_click_tags = await detect_tags_and_vendors(page)
                        pre_click_objects = await detect_vendor_objects(page)
                        await clear_tracking_data(page)
                        clicked_handle = target
                        click_timestamp = datetime.now()
                        await target.click()
                        # Fast polling for events instead of fixed wait only
                        waited = 0
                        while waited < POST_CLICK_WAIT_MS:
                            events_len = await page.evaluate("() => (window.tealiumSpecificEvents||[]).length")
                            if isinstance(events_len, int) and events_len > 0:
                                break
                            await page.wait_for_timeout(100)
                            waited += 100
                        if waited >= POST_CLICK_WAIT_MS:
                            await page.wait_for_timeout(100)  # small grace
                        clicked = True
                        strategy_used = 'role_name'
                    except Exception:
                        yield {"status": "progress", "message": "    Role+name not found/visible. Trying href heuristic..."}
                
                # Try direct selector first (most reliable)
                if not clicked and selector:
                    try:
                        yield {"status": "progress", "message": "    Trying recorded selector directly..."}
                        target = page.locator(selector).first
                        await target.wait_for(state='visible', timeout=3000)
                        await target.scroll_into_view_if_needed()
                        pre_click_tags = await detect_tags_and_vendors(page)
                        pre_click_objects = await detect_vendor_objects(page)
                        await clear_tracking_data(page)
                        clicked_handle = target
                        click_timestamp = datetime.now()
                        await target.click()
                        waited = 0
                        while waited < POST_CLICK_WAIT_MS:
                            events_len = await page.evaluate("() => (window.tealiumSpecificEvents||[]).length")
                            if isinstance(events_len, int) and events_len > 0:
                                break
                            await page.wait_for_timeout(100)
                            waited += 100
                        if waited >= POST_CLICK_WAIT_MS:
                            await page.wait_for_timeout(100)
                        clicked = True
                        strategy_used = 'recorded_selector'
                    except Exception:
                        yield {"status": "progress", "message": "    Direct selector failed. Trying scoped CSS in expanded panel..."}

                if not clicked and selector:
                    try:
                        yield {"status": "progress", "message": "    Trying scoped CSS in expanded panel..."}
                        scoped = page.locator(f'div[id^="collapse"].in {selector}')
                        target = scoped.first
                        await target.wait_for(state='visible', timeout=3000)
                        await target.scroll_into_view_if_needed()
                        pre_click_tags = await detect_tags_and_vendors(page)
                        pre_click_objects = await detect_vendor_objects(page)
                        await clear_tracking_data(page)
                        clicked_handle = target
                        click_timestamp = datetime.now()
                        await target.click()
                        waited = 0
                        while waited < POST_CLICK_WAIT_MS:
                            events_len = await page.evaluate("() => (window.tealiumSpecificEvents||[]).length")
                            if isinstance(events_len, int) and events_len > 0:
                                break
                            await page.wait_for_timeout(100)
                            waited += 100
                        if waited >= POST_CLICK_WAIT_MS:
                            await page.wait_for_timeout(100)
                        clicked = True
                        strategy_used = 'scoped_css'
                    except Exception:
                        yield {"status": "progress", "message": "    Scoped CSS not clickable. Trying text-based approach..."}
                
                # Try text-based matching for buttons/links
                if not clicked and locator_bundle.get('text'):
                    text = locator_bundle['text']
                    try:
                        yield {"status": "progress", "message": f"    Trying text-based locator: '{text}'..."}
                        # Try multiple text-based strategies
                        candidates = [
                            page.get_by_text(text, exact=True),
                            page.get_by_text(text, exact=False),
                            page.locator(f'button:has-text("{text}")'),
                            page.locator(f'a:has-text("{text}")'),
                            page.locator(f'[aria-label*="{text}"]'),
                            page.locator(f'[title*="{text}"]')
                        ]
                        
                        for candidate in candidates:
                            try:
                                target = candidate.first
                                await target.wait_for(state='visible', timeout=1000)
                                await target.scroll_into_view_if_needed()
                                pre_click_tags = await detect_tags_and_vendors(page)
                                pre_click_objects = await detect_vendor_objects(page)
                                await clear_tracking_data(page)
                                clicked_handle = target
                                click_timestamp = datetime.now()
                                await target.click()
                                waited = 0
                                while waited < POST_CLICK_WAIT_MS:
                                    events_len = await page.evaluate("() => (window.tealiumSpecificEvents||[]).length")
                                    if isinstance(events_len, int) and events_len > 0:
                                        break
                                    await page.wait_for_timeout(100)
                                    waited += 100
                                if waited >= POST_CLICK_WAIT_MS:
                                    await page.wait_for_timeout(100)
                                clicked = True
                                strategy_used = 'text_based'
                                break
                            except Exception:
                                continue
                    except Exception:
                        yield {"status": "progress", "message": "    Text-based approach failed. Trying href heuristic..."}

                if not clicked and isinstance(locator_bundle.get('href'), str):
                    href = locator_bundle['href']
                    try:
                        yield {"status": "progress", "message": f"    Looking for anchor with href containing host from target..."}
                        host = href.split('/')[2] if '//' in href else href
                        candidate = page.locator(f'a[href*="{host}"]')
                        if name:
                            candidate = candidate.filter(has_text=name)
                        target = candidate.first
                        await target.wait_for(state='visible', timeout=3000)
                        pre_click_tags = await detect_tags_and_vendors(page)
                        pre_click_objects = await detect_vendor_objects(page)
                        await clear_tracking_data(page)
                        clicked_handle = target
                        click_timestamp = datetime.now()
                        await target.click()
                        waited = 0
                        while waited < POST_CLICK_WAIT_MS:
                            events_len = await page.evaluate("() => (window.tealiumSpecificEvents||[]).length")
                            if isinstance(events_len, int) and events_len > 0:
                                break
                            await page.wait_for_timeout(100)
                            waited += 100
                        if waited >= POST_CLICK_WAIT_MS:
                            await page.wait_for_timeout(100)
                        clicked = True
                        strategy_used = 'href_heuristic'
                    except Exception:
                        yield {"status": "progress", "message": "    Href heuristic failed. Trying XPath fallback..."}
                
                if not clicked and isinstance(locator_bundle.get('xpath'), str):
                    try:
                        yield {"status": "progress", "message": "    Trying XPath locator..."}
                        target = page.locator(f'xpath={locator_bundle["xpath"]}').first
                        await target.wait_for(state='visible', timeout=3000)
                        pre_click_tags = await detect_tags_and_vendors(page)
                        pre_click_objects = await detect_vendor_objects(page)
                        await clear_tracking_data(page)
                        clicked_handle = target
                        click_timestamp = datetime.now()
                        await target.click()
                        waited = 0
                        while waited < POST_CLICK_WAIT_MS:
                            events_len = await page.evaluate("() => (window.tealiumSpecificEvents||[]).length")
                            if isinstance(events_len, int) and events_len > 0:
                                break
                            await page.wait_for_timeout(100)
                            waited += 100
                        if waited >= POST_CLICK_WAIT_MS:
                            await page.wait_for_timeout(100)
                        clicked = True
                        strategy_used = 'xpath'
                    except Exception:
                        yield {"status": "progress", "message": "    XPath fallback failed."}
                
                if clicked:
                    try:
                        overlay = await page.query_selector(MINICART_OVERLAY_SELECTOR)
                        if overlay and await overlay.is_visible():
                            await overlay.click()
                            await page.wait_for_timeout(500)
                    except:
                        pass
                    
                    post_click_tags = await detect_tags_and_vendors(page)
                    post_click_objects = await detect_vendor_objects(page)
                    
                    new_tags = [tag for tag in post_click_tags if tag not in pre_click_tags]
                    new_objects = [obj for obj in post_click_objects if obj not in pre_click_objects]
                    
                    tealium_requests = [req for req in network_requests 
                                      if any(vendor in req['url'].lower() for vendor in ['tealium', 'collect', 'utag'])]
                    vendors_in_network = find_vendors_in_requests(network_requests)
                    
                    tealium_logs = [log for log in console_logs 
                                  if any(keyword in log['text'].lower() for keyword in ['utag', 'tealium', 'track', 'event'])]
                    tealium_events = await get_data_from_page(page, "tealiumSpecificEvents")
                    # New: pull only the i.gif payloads captured during this selector
                    new_tealium_i_gif_payloads = tealium_i_gif_payloads[pre_tealium_payload_count:]
                    
                    # Correlate i.gif requests with the click that triggered them
                    correlated_payloads = []
                    if click_timestamp:
                        for payload in new_tealium_i_gif_payloads:
                            try:
                                payload_time = datetime.fromisoformat(payload['timestamp'])
                                delay_ms = (payload_time - click_timestamp).total_seconds() * 1000
                                
                                # Add correlation info if within reasonable time window (0-2000ms)
                                if 0 <= delay_ms <= 2000:
                                    payload['click_correlation'] = {
                                        'selector': selector,
                                        'strategy_used': strategy_used,
                                        'delay_ms': round(delay_ms, 2),
                                        'clicked_element': {
                                            'text': clicked_text,
                                            'href': clicked_href
                                        }
                                    }
                                correlated_payloads.append(payload)
                            except Exception:
                                correlated_payloads.append(payload)
                    else:
                        correlated_payloads = new_tealium_i_gif_payloads
                    yield {
                        "status": "progress",
                        "message": f"    Post-click: captured {len(tealium_events) if isinstance(tealium_events, list) else 0} Tealium events; {len(new_tealium_i_gif_payloads)} i.gif payload(s); {len(tealium_requests)} network hits to Tealium/vendors"
                    }
                    general_events = await get_data_from_page(page, "generalTrackingEvents")
                    
                    # Capture brief info about the clicked element
                    clicked_href = None
                    clicked_text = None
                    try:
                        if clicked_handle is not None:
                            clicked_href = await clicked_handle.get_attribute('href')
                            clicked_text = await clicked_handle.inner_text()
                    except Exception:
                        pass

                    selector_result = {
                        "selector": selector,
                        "description": description,
                        "success": True,
                        "element_found": True,
                        "element_visible": True,
                        "clicked": True,
                        "strategy_used": strategy_used,
                        "clicked_element": {
                            "href": clicked_href,
                            "text": clicked_text
                        },
                        "tags_detected": {
                            "before": len(pre_click_tags),
                            "after": len(post_click_tags),
                            "new": new_tags
                        },
                        "vendor_objects": {
                            "before": len(pre_click_objects),
                            "after": len(post_click_objects), 
                            "new": new_objects
                        },
                        "network_activity": {
                            "total_requests": len(network_requests),
                            "tealium_requests": tealium_requests
                        },
                        "console_activity": {
                            "total_logs": len(console_logs),
                            "tealium_logs": tealium_logs
                        },
                        "vendors_in_network": vendors_in_network,
                        "tealium_events": tealium_events,
                        "tealium_i_gif_payloads": correlated_payloads,
                        "general_events": general_events
                    }
                else:
                    selector_result = {
                        "selector": selector,
                        "description": description,
                        "success": False,
                        "element_found": False,
                        "error": "Element not found or not visible via robust strategies"
                    }
            
            except Exception as e:
                selector_result = {
                    "selector": selector,
                    "description": description,
                    "success": False,
                    "error": str(e)
                }
            
            macro_results.append(selector_result)
            
            yield {
                "status": "selector_completed",
                "message": f"Completed: {description}",
                "result": selector_result,
                "progress": 40 + ((i + 1) / total_selectors) * 50
            }
        
        # Generate final analysis
        successful_clicks = [r for r in macro_results if r.get('success', False)]
        tealium_active_clicks = [r for r in successful_clicks if r.get('tealium_events', False)]
        
        final_analysis = {
            "macro_name": macro_name,
            "macro_url": macro_url,
            "total_selectors": total_selectors,
            "successful_clicks": len(successful_clicks),
            "tealium_active_clicks": len(tealium_active_clicks),
            "tealium_coverage": (len(tealium_active_clicks) / total_selectors * 100) if total_selectors > 0 else 0,
            "selector_results": macro_results,
            "summary": {
                "elements_found": len([r for r in macro_results if r.get('element_found', False)]),
                "elements_visible": len([r for r in macro_results if r.get('element_visible', False)]),
                "clicks_successful": len(successful_clicks),
                "tealium_events_triggered": len(tealium_active_clicks)
            },
            "timestamp": datetime.now().isoformat()
        }
        
        yield {
            "status": "complete",
            "message": f"Analysis complete: {len(tealium_active_clicks)}/{total_selectors} selectors triggered Tealium events",
            "progress": 100,
            "results": final_analysis
        }
        
    except Exception as e:
        error_message = f"Error during macro analysis: {str(e)}"
        yield {
            "status": "error",
            "message": error_message,
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        
    finally:
        # Clean up browser resources
        try:
            if page:
                await page.close()
            if context:
                await context.close()
            if browser:
                await browser.close()
        except Exception as cleanup_error:
            print(f"Error during cleanup: {cleanup_error}")


async def detect_tags_and_vendors(page: Page) -> List[Dict[str, str]]:
    """Detect marketing tags and vendors on the page"""
    try:
        # Get all script tags
        scripts = await page.evaluate("""
            () => {
                const scripts = Array.from(document.querySelectorAll('script[src]'));
                return scripts.map(script => ({
                    src: script.src,
                    type: script.type || 'text/javascript'
                }));
            }
        """)
        
        detected_tags = []
        for script in scripts:
            src = script.get('src', '')
            for vendor in TAG_VENDORS:
                if vendor['pattern'] in src:
                    detected_tags.append({
                        'vendor': vendor['name'],
                        'category': vendor['category'],
                        'url': src,
                        'type': 'script'
                    })
                    break
        
        return detected_tags
        
    except Exception as e:
        print(f"Error detecting tags: {e}")
        return []


async def detect_vendor_objects(page: Page) -> List[Dict[str, str]]:
    """Detect vendor-specific JavaScript objects on the page"""
    try:
        # Check for global vendor objects
        vendor_objects = await page.evaluate("""
            () => {
                const objects = [];
                const vendors = """ + json.dumps(GLOBAL_VENDOR_OBJECTS) + """;
                
                vendors.forEach(vendor => {
                    try {
                        if (window[vendor.object] !== undefined) {
                            objects.push({
                                name: vendor.name,
                                category: vendor.category,
                                object: vendor.object,
                                type: typeof window[vendor.object]
                            });
                        }
                    } catch (e) {
                        // Object might be protected, skip it
                    }
                });
                
                return objects;
            }
        """)
        
        return vendor_objects
        
    except Exception as e:
        print(f"Error detecting vendor objects: {e}")
        return []


# Wrapper with the name expected by app.py
async def dismiss_cookie_overlays_advanced(page: Page):
    """Enhanced cookie dismissal for macro analyzer"""
    try:
        await page.wait_for_timeout(1000)  # Wait for overlays to appear
        
        # Common cookie banner selectors
        dismiss_selectors = [
            'button:has-text("Accept All")',
            'button:has-text("Accept")', 
            'button:has-text("I Agree")',
            'button:has-text("Allow All")',
            'button:has-text("Continue")',
            'button:has-text("OK")',
            'button:has-text("Close")',
            'button[id*="accept"]',
            'button[class*="accept"]',
            'button[id*="consent"]',
            'button[class*="consent"]',
            'a:has-text("Accept")',
            'a:has-text("Close")',
            '.cookie-banner button',
            '.gdpr-banner button',
            '[role="dialog"] button',
            '.modal button:has-text("Accept")',
            '.overlay button:has-text("Close")'
        ]
        
        for selector in dismiss_selectors:
            try:
                element = await page.locator(selector).first
                if await element.is_visible():
                    await element.click()
                    await page.wait_for_timeout(500)
                    print(f"Dismissed overlay with selector: {selector}")
                    break
            except Exception:
                continue
                
        # Try Escape key as fallback
        try:
            await page.keyboard.press('Escape')
            await page.wait_for_timeout(300)
        except Exception:
            pass
            
    except Exception as e:
        print(f"Cookie dismissal failed: {e}")

async def analyze_macro_tealium_events(macro_url: str, macro_selectors: List[Dict], macro_name: str = "Unknown Macro") -> AsyncGenerator[Dict[str, Any], None]:
    async for update in analyze_macro_selectors_against_config(macro_url, macro_selectors, macro_name):
        yield update