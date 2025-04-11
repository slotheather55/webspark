import asyncio
import json
import sys
import re
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, AsyncGenerator # Added AsyncGenerator
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError, Page, Browser, BrowserContext
import traceback
import nest_asyncio

# Import the selector configuration
from selectors_config import PAGE_TYPE_SELECTORS

nest_asyncio.apply()

# --- Vendor Definitions ---
TAG_VENDORS = [
    {"pattern": "google-analytics.com", "name": "Google Analytics", "category": "analytics"},
    {"pattern": "googletagmanager.com", "name": "Google Tag Manager", "category": "tag_manager"},
    {"pattern": "facebook.net", "name": "Facebook Pixel", "category": "advertising"},
    {"pattern": "connect.facebook.net", "name": "Facebook", "category": "advertising"},
    {"pattern": "bat.bing.com", "name": "Microsoft Advertising", "category": "advertising"},
    {"pattern": "script.hotjar.com", "name": "Hotjar", "category": "analytics"},
    {"pattern": "cdn.amplitude.com", "name": "Amplitude", "category": "analytics"},
    {"pattern": "js.intercomcdn.com", "name": "Intercom", "category": "customer_support"},
    {"pattern": "cdn.heapanalytics.com", "name": "Heap Analytics", "category": "analytics"},
    {"pattern": "js.hs-scripts.com", "name": "HubSpot", "category": "marketing"},
    {"pattern": "snap.licdn.com", "name": "LinkedIn Insight", "category": "advertising"},
    {"pattern": "cdn.optimizely.com", "name": "Optimizely", "category": "ab_testing"},
    {"pattern": "cdn.mxpnl.com", "name": "Mixpanel", "category": "analytics"},
    {"pattern": "clarity.ms", "name": "Microsoft Clarity", "category": "analytics"},
    {"pattern": "unpkg.com/tealium", "name": "Tealium (unpkg)", "category": "tag_manager"},
    {"pattern": "tags.tiqcdn.com", "name": "Tealium iQ", "category": "tag_manager"},
    {"pattern": "collect.tealiumiq.com", "name": "Tealium Collect", "category": "tag_manager"},
    {"pattern": "sentry", "name": "Sentry", "category": "error_tracking"},
    {"pattern": "fullstory.com", "name": "FullStory", "category": "session_recording"},
    {"pattern": "static.klaviyo.com", "name": "Klaviyo", "category": "email_marketing"},
    {"pattern": "static.ads-twitter.com", "name": "Twitter Ads", "category": "advertising"},
    {"pattern": "d.adroll.com", "name": "AdRoll", "category": "advertising"},
    {"pattern": "secure.adnxs.com", "name": "AppNexus", "category": "advertising"},
    {"pattern": "secure.quantserve.com", "name": "Quantcast", "category": "analytics"},
    {"pattern": "cdn.segment.com", "name": "Segment", "category": "customer_data_platform"},
    {"pattern": "static.criteo.net", "name": "Criteo", "category": "advertising"},
    {"pattern": "static.scrollstack.com", "name": "Scroll", "category": "content"},
    {"pattern": "cdn.attn.tv", "name": "ATTN", "category": "advertising"},
    {"pattern": "analytics.tiktok.com", "name": "TikTok Analytics", "category": "advertising"},
    {"pattern": "sc-static.net", "name": "Snapchat Pixel", "category": "advertising"},
    {"pattern": "googleadservices.com", "name": "Google Ads", "category": "advertising"},
    {"pattern": "doubleclick.net", "name": "Google DoubleClick", "category": "advertising"},
    {"pattern": "js.driftt.com", "name": "Drift", "category": "customer_support"},
    {"pattern": "log.outbrain.com", "name": "Outbrain", "category": "advertising"},
    {"pattern": "cdn.taboola.com", "name": "Taboola", "category": "advertising"},
    {"pattern": "moatads", "name": "Moat", "category": "advertising"},
    {"pattern": "chartbeat", "name": "Chartbeat", "category": "analytics"},
    {"pattern": "pardot", "name": "Pardot", "category": "marketing"},
    {"pattern": "marketo", "name": "Marketo", "category": "marketing"},
    {"pattern": "bizible", "name": "Bizible", "category": "marketing"},
    {"pattern": "demdex.net", "name": "Adobe Audience Manager", "category": "dmp"},
    {"pattern": "omtrdc.net", "name": "Adobe Experience Cloud", "category": "analytics"}
]

GLOBAL_VENDOR_OBJECTS = [
    {"object": "ga", "name": "Google Analytics", "category": "analytics"},
    {"object": "gtag", "name": "Google Tags", "category": "analytics"},
    {"object": "fbq", "name": "Facebook Pixel", "category": "advertising"},
    {"object": "hj", "name": "Hotjar", "category": "analytics"},
    {"object": "pintrk", "name": "Pinterest Tag", "category": "advertising"},
    {"object": "snaptr", "name": "Snapchat Pixel", "category": "advertising"},
    {"object": "ttq", "name": "TikTok Pixel", "category": "advertising"},
    {"object": "clarity", "name": "Microsoft Clarity", "category": "analytics"},
    {"object": "amplitude", "name": "Amplitude", "category": "analytics"},
    {"object": "heap", "name": "Heap Analytics", "category": "analytics"},
    {"object": "mixpanel", "name": "Mixpanel", "category": "analytics"},
    {"object": "_hsq", "name": "HubSpot", "category": "marketing"},
    {"object": "Intercom", "name": "Intercom", "category": "customer_support"},
    {"object": "pendo", "name": "Pendo", "category": "analytics"},
    {"object": "optimizely", "name": "Optimizely", "category": "ab_testing"},
    {"object": "adobe.target", "name": "Adobe Target", "category": "ab_testing"},
    {"object": "s_c_il", "name": "Adobe Analytics", "category": "analytics"},
    {"object": "s", "name": "Adobe Analytics", "category": "analytics"},
    {"object": "Kissmetrics", "name": "Kissmetrics", "category": "analytics"},
    {"object": "Mparticle", "name": "mParticle", "category": "customer_data_platform"},
    {"object": "Bugsnag", "name": "Bugsnag", "category": "error_tracking"},
    {"object": "LogRocket", "name": "LogRocket", "category": "session_recording"},
    {"object": "FS", "name": "FullStory", "category": "session_recording"},
    {"object": "Rollbar", "name": "Rollbar", "category": "error_tracking"},
    {"object": "Sentry", "name": "Sentry", "category": "error_tracking"},
    {"object": "_kmq", "name": "Klaviyo", "category": "email_marketing"},
    {"object": "criteo_q", "name": "Criteo", "category": "advertising"},
    {"object": "__adroll", "name": "AdRoll", "category": "advertising"}
]

# --- Configuration ---
POST_LOAD_WAIT_MS = 1500 # Reduced from 4000
POST_CLICK_WAIT_MS = 1000 # Reduced from 3000

PRIVACY_PROMPT_ACCEPT_SELECTOR = 'button#truste-consent-button'
MINICART_OVERLAY_SELECTOR = '#prh-minicart-overlay' # Example, adjust if needed

# --- JavaScript Snippets ---
TEALIUM_PAYLOAD_MONITOR_SCRIPT = """
(() => {
    window.tealiumSpecificEvents = []; const MAX_DEPTH = 5;
    const safeStringify = (obj, depth = 0) => {
        if (depth > MAX_DEPTH) return '"[Max Depth Reached]"';
        if (obj === undefined) return 'null'; // Return null for undefined for valid JSON
        if (obj === null || typeof obj !== 'object') { try { if (typeof obj === 'bigint') return `"${obj.toString()}n"`; if (typeof obj === 'function') return '"[Function]"'; if (typeof obj === 'symbol') return '"[Symbol]"'; return JSON.stringify(obj); } catch (e) { return `"[Stringify Error: ${e.message}]"`; } }
        const cache = new Set(); // Use Set for efficient cycle detection
        const stringifyRecursive = (currentObj, currentDepth) => {
            if (currentDepth > MAX_DEPTH) return '"[Max Depth Reached]"';
            if (currentObj === null || typeof currentObj !== 'object') { try { if (typeof currentObj === 'bigint') return `"${currentObj.toString()}n"`; if (typeof currentObj === 'function') return '"[Function]"'; if (typeof currentObj === 'symbol') return '"[Symbol]"'; return JSON.stringify(currentObj); } catch (e) { return `"[Stringify Error: ${e.message}]"`; } }
            if (cache.has(currentObj)) return '"[Circular Reference]"';
            cache.add(currentObj);
            let result;
            if (Array.isArray(currentObj)) { result = '[' + currentObj.map(item => stringifyRecursive(item, currentDepth + 1)).join(',') + ']'; }
            else { result = '{' + Object.keys(currentObj).map(key => `${JSON.stringify(key)}:${stringifyRecursive(currentObj[key], currentDepth + 1)}`).join(',') + '}'; }
            cache.delete(currentObj);
            return result;
        };
        return stringifyRecursive(obj, depth);
    };
    const logTealiumEvent = (type, data) => { let dataCopy = {}; try { const jsonString = safeStringify(data || {}); dataCopy = JSON.parse(jsonString); } catch (e) { console.error(`Tealium Payload Monitor: Error parsing data for ${type}`, e, data); dataCopy = { serialization_error: `Failed to serialize: ${e.message}` }; } window.tealiumSpecificEvents.push({ type: type, timestamp: new Date().toISOString(), data: dataCopy }); };
    let utag_obj = window.utag; let view_hooked = false; let link_hooked = false; const hookFunctions = (utagInstance) => { if (!utagInstance) return; if (utagInstance.view && typeof utagInstance.view === 'function' && !utagInstance.view.__tm_hooked) { let originalView = utagInstance.view; utagInstance.view = function(data) { logTealiumEvent('utag.view', data); return originalView.apply(this, arguments); }; utagInstance.view.__tm_hooked = true; view_hooked = true; console.log('Tealium Payload Monitor: utag.view hooked.'); } else if (utagInstance.view?.__tm_hooked) { view_hooked = true; } if (utagInstance.link && typeof utagInstance.link === 'function' && !utagInstance.link.__tm_hooked) { let originalLink = utagInstance.link; utagInstance.link = function(data) { logTealiumEvent('utag.link', data); return originalLink.apply(this, arguments); }; utagInstance.link.__tm_hooked = true; link_hooked = true; console.log('Tealium Payload Monitor: utag.link hooked.'); } else if (utagInstance.link?.__tm_hooked) { link_hooked = true; } }; if (utag_obj) { hookFunctions(utag_obj); } if (!view_hooked || !link_hooked) { let intervalCheck = setInterval(() => { if (window.utag && (!view_hooked || !link_hooked)) { hookFunctions(window.utag); if (view_hooked && link_hooked) { clearInterval(intervalCheck); } } }, 500); setTimeout(() => { if(intervalCheck) clearInterval(intervalCheck); console.log('Tealium Payload Monitor: Hooking check timed out.'); }, 15000); } console.log('Tealium Payload Monitor: Initialized.');
})();"""

GENERAL_EVENT_TRACKER_SCRIPT = """
(() => {
    console.log('General Event Tracker: Initializing...'); window.generalTrackingEvents = { network: [], analyticsCalls: [], dataLayer: [] }; const originalFetch = window.fetch; window.fetch = function(input, init) { const url = typeof input === 'string' ? input : input?.url; if (url) { window.generalTrackingEvents.network.push({ url: url, method: init?.method || 'GET', type: 'fetch', timestamp: new Date().toISOString() }); } return originalFetch.apply(this, arguments); }; const originalXhrOpen = XMLHttpRequest.prototype.open; const originalXhrSend = XMLHttpRequest.prototype.send; XMLHttpRequest.prototype.open = function(method, url) { this.__url = url; this.__method = method; return originalXhrOpen.apply(this, arguments); }; XMLHttpRequest.prototype.send = function() { if (this.__url) { window.generalTrackingEvents.network.push({ url: this.__url, method: this.__method || 'GET', type: 'xhr', timestamp: new Date().toISOString() }); } return originalXhrSend.apply(this, arguments); }; if (window.dataLayer && Array.isArray(window.dataLayer) && typeof window.dataLayer.push === 'function') { const originalPush = window.dataLayer.push; window.dataLayer.push = function() { try { const data = arguments[0] ? JSON.parse(JSON.stringify(arguments[0])) : null; window.generalTrackingEvents.dataLayer.push({ data: data, timestamp: new Date().toISOString() }); } catch (e) { console.error('General Event Tracker: Error processing dataLayer push', e); } return originalPush.apply(this, arguments); }; console.log('General Event Tracker: dataLayer.push hooked.'); } const monitorFunction = (objPath, funcName, type) => { try { const parts = objPath.split('.'); let obj = window; for(const part of parts) { if (!obj || typeof obj[part] === 'undefined') { obj = null; break; } obj = obj[part]; } if (obj && typeof obj[funcName] === 'function' && !obj[funcName].__ge_hooked) { const original = obj[funcName]; obj[funcName] = function() { try { const args = Array.from(arguments).map(arg => { try { return JSON.parse(JSON.stringify(arg)); } catch(e){ return '[Non-serializable Arg]'; } }); window.generalTrackingEvents.analyticsCalls.push({ type: type, function: `${objPath}.${funcName}`, args: args, timestamp: new Date().toISOString() }); } catch (e) { console.error(`General Event Tracker: Error in hooked function ${objPath}.${funcName}`, e); } return original.apply(this, arguments); }; obj[funcName].__ge_hooked = true; console.log(`General Event Tracker: ${type} (${objPath}.${funcName}) hooked.`); } } catch (e) { console.error(`General Event Tracker: Error hooking ${objPath}.${funcName}`, e); } }; monitorFunction('ga', 'send', 'Google Analytics'); monitorFunction('gtag', 'event', 'Google Tags'); monitorFunction('fbq', 'track', 'Facebook Pixel'); monitorFunction('hj', 'event', 'Hotjar'); monitorFunction('pintrk', 'track', 'Pinterest Tag'); monitorFunction('snaptr', 'track', 'Snapchat Pixel'); monitorFunction('ttq', 'track', 'TikTok Pixel'); console.log('General Event Tracker: Setup complete.');
})();"""

POST_LOAD_TAG_DETECTION_SCRIPT = """
() => {
    console.log('Post-Load Detector: Running...'); const results = { globalObjects: [], scriptTags: [], tealiumInfo: null, gtmInfo: null }; const objectsToCheck = [ {"object": "ga", "name": "Google Analytics"}, {"object": "gtag", "name": "Google Tags"}, {"object": "fbq", "name": "Facebook Pixel"}, {"object": "hj", "name": "Hotjar"}, {"object": "pintrk", "name": "Pinterest Tag"}, {"object": "snaptr", "name": "Snapchat Pixel"}, {"object": "ttq", "name": "TikTok Pixel"}, {"object": "clarity", "name": "Microsoft Clarity"}, {"object": "amplitude", "name": "Amplitude"}, {"object": "heap", "name": "Heap Analytics"}, {"object": "mixpanel", "name": "Mixpanel"}, {"object": "_hsq", "name": "HubSpot"}, {"object": "Intercom", "name": "Intercom"}, {"object": "pendo", "name": "Pendo"}, {"object": "optimizely", "name": "Optimizely"}, {"object": "adobe.target", "name": "Adobe Target"}, {"object": "s_c_il", "name": "Adobe Analytics"}, {"object": "s", "name": "Adobe Analytics"}, {"object": "Kissmetrics", "name": "Kissmetrics"}, {"object": "Mparticle", "name": "mParticle"}, {"object": "Bugsnag", "name": "Bugsnag"}, {"object": "LogRocket", "name": "LogRocket"}, {"object": "FS", "name": "FullStory"}, {"object": "Rollbar", "name": "Rollbar"}, {"object": "Sentry", "name": "Sentry"}, {"object": "_kmq", "name": "Klaviyo"}, {"object": "criteo_q", "name": "Criteo"}, {"object": "__adroll", "name": "AdRoll"} ]; objectsToCheck.forEach(objInfo => { try { const parts = objInfo.object.split('.'); let current = window; let exists = true; for (const part of parts) { if (typeof current[part] === 'undefined') { exists = false; break; } current = current[part]; } if (exists) { results.globalObjects.push({ name: objInfo.name, path: objInfo.object }); } } catch (e) { console.error(`Post-Load Detector: Error checking object ${objInfo.object}`, e); } }); try { results.scriptTags = Array.from(document.querySelectorAll('script[src]')).map(s => s.src); } catch(e) { console.error('Post-Load Detector: Error getting script tags', e); } if (typeof window.utag !== 'undefined') { results.tealiumInfo = { detected: true, version: window.utag.cfg?.v || null, profile: window.utag.cfg?.profile || null, account: window.utag.cfg?.utagAccount || null, tagsLoaded: Object.keys(window.utag.loader?.cfg || {}).filter(k => /^\\d+$/.test(k)).length }; } else { results.tealiumInfo = { detected: false }; } if (typeof window.google_tag_manager !== 'undefined' || typeof window.dataLayer !== 'undefined') { results.gtmInfo = { detected: true, containers: typeof window.google_tag_manager !== 'undefined' ? Object.keys(window.google_tag_manager).filter(key => key.startsWith('GTM-')) : [] }; } else { results.gtmInfo = { detected: false }; } console.log('Post-Load Detector: Finished.'); return results;
}"""

# --- Python Helper Functions ---
async def get_data_from_page(page: Page, var_name: str) -> Dict[str, Any]:
    """Safely retrieves data from a window variable on the page."""
    try:
        data_json = await page.evaluate(f"""
            () => {{
                try {{
                    const MAX_DEPTH = 5; // Limit recursion depth
                    const safeStringify = (obj, depth = 0) => {{
                        if (depth > MAX_DEPTH) return '"[Max Depth Reached]"';
                        if (obj === undefined) return 'null';
                        const cache = new Set();
                        return JSON.stringify(obj, (key, value) => {{
                             if (typeof value === 'object' && value !== null) {{
                                 if (cache.has(value)) return '[Circular Reference]';
                                 cache.add(value);
                             }}
                             if (typeof value === 'function') return '[Function]';
                             if (typeof value === 'symbol') return '[Symbol]';
                             if (typeof value === 'bigint') return `[BigInt: ${{value.toString()}}]`;
                             // Check for DOM elements (simple check, might need refinement)
                             if (value instanceof Element || value instanceof Node) return '[DOM Element]';
                             return value;
                        }});
                    }};
                    return safeStringify(window.{var_name} || null, 0); // Return null if undefined
                }} catch (e) {{
                    // Attempt to return error as valid JSON string
                    try {{
                       return JSON.stringify({{ error: `Failed to access or stringify window.{var_name}: ${{e.message}}` }});
                    }} catch (jsonError) {{
                        return '{{"error": "Failed to stringify error message"}}';
                    }}
                }}
            }}
        """)
        # Parse the JSON string returned from evaluate
        return json.loads(data_json) if data_json else {"info": f"{var_name} not found or empty"}
    except PlaywrightError as pe: # More specific error catching
        print(f"      Playwright Error retrieving {var_name}: {pe}")
        return {"error": f"PlaywrightError: Failed to retrieve or parse {var_name}: {pe}"}
    except json.JSONDecodeError as je:
        print(f"      JSON Decode Error retrieving {var_name}: {je}")
        print(f"      Raw data received: {data_json[:500]}...") # Log snippet of raw data
        return {"error": f"JSONDecodeError: Failed to parse {var_name}: {je}", "raw_data_snippet": data_json[:500]}
    except Exception as e:
        print(f"      Unexpected Error retrieving {var_name}: {e}")
        return {"error": f"Unexpected Error: Failed to retrieve or parse {var_name}: {e}"}


async def clear_tracking_data(page: Page):
    """Clears the event logs created by the injected scripts."""
    try:
        await page.evaluate("""() => {
            if (window.tealiumSpecificEvents) { window.tealiumSpecificEvents = []; }
            if (window.generalTrackingEvents) { window.generalTrackingEvents = { network: [], analyticsCalls: [], dataLayer: [] }; }
            console.log('Tracking data arrays cleared.'); // Add console log
        }""")
    except Exception as e:
        print(f"      Error clearing tracking data: {e}")

async def dismiss_overlays(page: Page):
    """Attempts to find and click common overlay/prompt accept buttons."""
    print("        Attempting to dismiss overlays...")
    overlay_dismissed, minicart_dismissed = False, False
    # Privacy Prompt
    try:
        privacy_button = page.locator(PRIVACY_PROMPT_ACCEPT_SELECTOR).first
        if await privacy_button.is_visible(timeout=2000):
            await privacy_button.click(timeout=5000, force=True)
            await page.wait_for_timeout(500)
            print("        Clicked privacy prompt.")
            overlay_dismissed = True
    except Exception:
        pass # Ignore errors

    # Minicart Overlay (Example - uncomment and adjust selector if needed)
    # try:
    #     minicart_overlay = page.locator(MINICART_OVERLAY_SELECTOR).first
    #     if await minicart_overlay.is_visible(timeout=2000):
    #         await minicart_overlay.click(timeout=5000, force=True)
    #         await page.wait_for_timeout(500)
    #         print("        Clicked minicart overlay.")
    #         minicart_dismissed = True
    # except Exception:
    #     pass

    if not overlay_dismissed and not minicart_dismissed:
        print("        No overlays found/dismissed.")
    # else: # Only print if something was dismissed? Optional.
    #     print("        Finished overlay dismissal attempts.")


def analyze_vendors_on_page(tag_detection_results: Dict[str, Any]) -> Dict[str, List[str]]:
    """Analyzes tag detection results to categorize vendors found on the page."""
    identified = {}
    if not isinstance(tag_detection_results, dict):
        print("Warning: Invalid tag_detection_results format in analyze_vendors_on_page.")
        return identified

    # Analyze script tags
    for script_src in tag_detection_results.get("scriptTags", []):
        if not script_src or not isinstance(script_src, str) or script_src.startswith("data:"): continue
        for vendor in TAG_VENDORS:
            if vendor["pattern"].lower() in script_src.lower():
                cat = vendor["category"]
                identified.setdefault(cat, []).append(vendor["name"])
                break # Found a match for this script, move to next script

    # Analyze global objects
    for obj in tag_detection_results.get("globalObjects", []):
         if not isinstance(obj, dict) or "path" not in obj: continue # Basic validation
         for vendor_def in GLOBAL_VENDOR_OBJECTS:
            if obj.get("path") == vendor_def["object"]:
                cat = vendor_def["category"]
                identified.setdefault(cat, []).append(vendor_def["name"])
                break # Found a match for this object

    # Add TMS based on detection flags
    if tag_detection_results.get("tealiumInfo", {}).get("detected"):
        identified.setdefault("tag_manager", []).append("Tealium iQ")
    if tag_detection_results.get("gtmInfo", {}).get("detected"):
        identified.setdefault("tag_manager", []).append("Google Tag Manager")

    # Deduplicate and sort names within each category
    final_identified = {}
    for cat, names in identified.items():
        final_identified[cat] = sorted(list(set(names)))
    return final_identified


def find_vendors_in_requests(network_requests: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Identifies vendors based on URL patterns in network requests."""
    vendors = {}
    if not isinstance(network_requests, list): return vendors # Basic type check
    for req in network_requests:
        if not isinstance(req, dict): continue # Ensure req is a dict
        url = req.get("url", "")
        if not url or not isinstance(url, str): continue # Ensure url is a non-empty string
        for vendor in TAG_VENDORS:
            if vendor["pattern"].lower() in url.lower():
                vendors.setdefault(vendor["name"], []).append(url)
                break # Found a match for this URL, move to next request
    return vendors

# --- Main Analysis Function (MODIFIED TO BE ASYNC GENERATOR) ---
async def analyze_page_tags_and_events(url: str) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Main async generator function to perform page analysis and yield status updates.
    Yields: Status dictionaries or the final results dictionary.
    """
    yield {"status": "starting", "message": f"🚀 Starting Analysis for: {url}"}
    analysis_start_time = time.time()
    results = {"url": url, "analysisTimestamp": datetime.now().isoformat(), "steps": []}

    browser: Optional[Browser] = None
    context: Optional[BrowserContext] = None
    page: Optional[Page] = None
    nav_success = False # Track navigation status

    async with async_playwright() as p:
        try:
            yield {"status": "progress", "message": "    Launching browser..."}
            browser = await p.chromium.launch(headless=True)
            yield {"status": "progress", "message": "    >>> Browser launched successfully."}
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                java_script_enabled=True,
                ignore_https_errors=True
            )
            page = await context.new_page()
            page.set_default_timeout(45000) # Set default timeout for actions like goto, click

            await page.add_init_script(TEALIUM_PAYLOAD_MONITOR_SCRIPT)
            await page.add_init_script(GENERAL_EVENT_TRACKER_SCRIPT)

            yield {"status": "progress", "message": "    Navigating and loading page..."}
            load_start_time = time.time()
            network_requests_load = []
            def log_request(request):
                if request.url and not request.url.startswith('data:'):
                     network_requests_load.append({"url": request.url, "method": request.method})
            page.on("request", log_request)

            try:
                await page.goto(url, wait_until='networkidle', timeout=60000)
                nav_success = True
            except PlaywrightTimeoutError as nav_error:
                yield {"status": "warning", "message": f"      Warning: Navigation with 'networkidle' timed out after 60s. Page might still be usable. ({nav_error})"}
                nav_success = True # Treat as potentially usable
            except PlaywrightError as nav_error:
                 yield {"status": "warning", "message": f"      Error during navigation: {nav_error}. Trying 'load' state."}
                 try:
                      await page.goto(url, wait_until='load', timeout=40000)
                      nav_success = True
                 except Exception as fallback_nav_error:
                       error_msg = f"      ❌ Fallback navigation ('load' state) also failed: {fallback_nav_error}"
                       yield {"status": "error", "message": error_msg}
                       results["steps"].append({"step": "Page Navigation", "status": "Failed", "error": str(fallback_nav_error)})
                       # Let finally block clean up, nav_success remains False

            # Detach listener safely
            try:
                 page.remove_listener("request", log_request)
            except Exception as detach_err:
                 yield {"status": "warning", "message": f"      Warning: Could not detach request listener: {detach_err}"}


            load_duration = time.time() - load_start_time
            if nav_success:
                yield {"status": "progress", "message": f"    Page load attempt finished in {load_duration:.2f} seconds."}
                results["steps"].append({"step": "Page Load", "duration_sec": load_duration, "status": "Completed (or Timeout)"}) # More accurate status

                yield {"status": "progress", "message": "    Attempting to dismiss overlays..."}
                await dismiss_overlays(page)

                yield {"status": "progress", "message": f"    Waiting {POST_LOAD_WAIT_MS / 1000}s for async scripts..."}
                await page.wait_for_timeout(POST_LOAD_WAIT_MS)

                yield {"status": "progress", "message": "    Collecting initial page data..."}
                page_load_results = {}
                collection_failed = False
                try:
                    page_load_results["utag_data"] = await get_data_from_page(page, "utag_data")
                    page_load_results["tealium_events"] = await get_data_from_page(page, "tealiumSpecificEvents")
                    page_load_results["general_events"] = await get_data_from_page(page, "generalTrackingEvents")
                    page_load_results["tag_detection"] = await page.evaluate(POST_LOAD_TAG_DETECTION_SCRIPT)
                    # Check if tag_detection returned an error before analyzing
                    if isinstance(page_load_results["tag_detection"], dict) and 'error' in page_load_results["tag_detection"]:
                         yield {"status": "warning", "message": f"      Warning: Error during tag detection script execution: {page_load_results['tag_detection']['error']}"}
                         page_load_results["vendors_on_page"] = {"error": "Tag detection script failed"}
                    else:
                         page_load_results["vendors_on_page"] = analyze_vendors_on_page(page_load_results["tag_detection"])

                    page_load_results["load_network_summary"] = {
                        "total_requests": len(network_requests_load),
                        "vendors_detected": find_vendors_in_requests(network_requests_load)
                    }
                    results["pageLoadAnalysis"] = page_load_results
                    results["steps"].append({"step": "Initial Data Collection", "status": "Success"})
                    yield {"status": "progress", "message": "    Initial data collected."}
                except Exception as data_e:
                    collection_failed = True
                    error_msg = f"      ❌ Error collecting initial data: {data_e}"
                    yield {"status": "error", "message": error_msg}
                    results["steps"].append({"step": "Initial Data Collection", "status": "Failed", "error": str(data_e)})

                if not collection_failed:
                    # --- Determine Page Type and Select Elements ---
                    utag_data = page_load_results.get("utag_data", {})
                    page_type = utag_data.get("page_type") if isinstance(utag_data, dict) else None
                    yield {"status": "progress", "message": f"    Detected page_type: {page_type}"}

                    elements_to_test_for_this_page = PAGE_TYPE_SELECTORS.get(page_type, PAGE_TYPE_SELECTORS.get("DEFAULT", []))

                    if not page_type:
                        yield {"status": "warning", "message": "      Warning: page_type not found. Using DEFAULT selectors."}
                        results["steps"].append({"step": "Page Type Detection", "status": "Warning", "message": "page_type not found"})
                    elif page_type not in PAGE_TYPE_SELECTORS:
                        yield {"status": "warning", "message": f"      Warning: No specific selectors for '{page_type}'. Using DEFAULT."}
                        results["steps"].append({"step": "Page Type Detection", "status": "Warning", "message": f"No selectors for '{page_type}', using DEFAULT"})
                    else:
                        results["steps"].append({"step": "Page Type Detection", "status": "Success", "detected_type": page_type})


                    yield {"status": "progress", "message": "    Analyzing click events..."}
                    click_analysis_results = []
                    if not elements_to_test_for_this_page:
                        yield {"status": "progress", "message": f"      No elements configured for click testing on page type: '{page_type or 'Unknown/Default'}'"}
                    else:
                        yield {"status": "progress", "message": f"      Found {len(elements_to_test_for_this_page)} elements to test for '{page_type or 'Unknown/Default'}'"}
                        # --- Click Loop ---
                        for i, element_config in enumerate(elements_to_test_for_this_page):
                            description = element_config["description"]
                            selector = element_config["selector"]
                            click_result = {"elementDescription": description, "selector": selector}
                            yield {"status": "progress", "message": f"\n      ▶️ Testing Click {i+1}/{len(elements_to_test_for_this_page)}: '{description}'"}
                            try:
                                element = page.locator(selector).first
                                yield {"status": "progress", "message": "        Attempting to dismiss overlays before interaction..."}
                                await dismiss_overlays(page)

                                yield {"status": "progress", "message": f"        Waiting for element ('{selector}') to be visible..."}
                                # Increased wait time slightly for visibility check
                                await element.wait_for(state='visible', timeout=15000)
                                yield {"status": "progress", "message": "        Element is visible."}
                                try:
                                    await element.scroll_into_view_if_needed(timeout=7000)
                                except Exception as scroll_e:
                                     yield {"status": "warning", "message": f"        Warning: Could not scroll element into view ({scroll_e}). Continuing click attempt."}

                                await page.wait_for_timeout(300) # Short pause after scroll

                                yield {"status": "progress", "message": "        Clearing tracking data..."}
                                await clear_tracking_data(page)

                                yield {"status": "progress", "message": "        Attempting click..."}
                                click_error_msg = None
                                try:
                                    # Consider adding trial=True if clicks are flaky and might need retries
                                    await element.click(timeout=15000)
                                except PlaywrightError as pe:
                                    if "intercept" in str(pe).lower(): # Broader check for interception
                                        yield {"status": "warning", "message":"        Click intercepted, trying force=True..."}
                                        await dismiss_overlays(page)
                                        try:
                                            await element.click(timeout=10000, force=True)
                                            # No error means forced click succeeded
                                        except Exception as force_e:
                                            click_error_msg = f"Forced click failed: {force_e}"
                                    else:
                                        click_error_msg = f"Click failed (PlaywrightError): {pe}"
                                except Exception as e:
                                    click_error_msg = f"Click failed (General Exception): {e}"

                                if click_error_msg:
                                    yield {"status": "warning", "message": f"        ❌ Click attempt resulted in error: {click_error_msg}"}
                                    click_result["clickStatus"] = "Failure"
                                    click_result["clickError"] = click_error_msg
                                else:
                                    yield {"status": "progress", "message": "        ✅ Click initiated successfully."}
                                    click_result["clickStatus"] = "Success" # Mark as success if click didn't error
                                    yield {"status": "progress", "message": f"        Waiting {POST_CLICK_WAIT_MS / 1000}s for events..."}
                                    await page.wait_for_timeout(POST_CLICK_WAIT_MS)

                                yield {"status": "progress", "message": "        Retrieving data after click attempt..."}
                                click_result["tealium_events"] = await get_data_from_page(page, "tealiumSpecificEvents")
                                click_result["general_events"] = await get_data_from_page(page, "generalTrackingEvents")

                                # Network Vendor Analysis
                                if isinstance(click_result["general_events"], dict) and "network" in click_result["general_events"]:
                                    network_data = click_result["general_events"]["network"]
                                    if isinstance(network_data, list):
                                        click_result["vendors_in_network"] = find_vendors_in_requests(network_data)
                                    else:
                                        click_result["vendors_in_network"] = {"error": "Network data is not a list"}
                                else:
                                    click_result["vendors_in_network"] = {"error": "General events or network data missing/invalid"}

                            except PlaywrightTimeoutError as e:
                                error_msg = f"        ❌ Timeout error finding/interacting with '{description}': {e}"
                                yield {"status": "error", "message": error_msg}
                                click_result["clickStatus"] = "Error (Timeout)"
                                click_result["clickError"] = str(e)
                            except Exception as e:
                                error_msg = f"        ❌ Unexpected error testing '{description}': {e}"
                                yield {"status": "error", "message": error_msg}
                                click_result["clickStatus"] = "Error (General)"
                                click_result["clickError"] = str(e)
                                traceback.print_exc() # Print stack trace for unexpected errors
                            finally:
                                click_analysis_results.append(click_result)

                        results["clickAnalysis"] = click_analysis_results
                        results["steps"].append({"step": "Click Event Analysis", "status": "Completed", "clicksTested": len(elements_to_test_for_this_page)})
            else: # Handle critical navigation failure
                 yield {"status": "error", "message": "Skipping remaining analysis due to navigation failure."}
                 results["error"] = results.get("error", "Navigation failed")

            # --- Final step reporting ---
            if results.get("error") and results.get("steps", [])[-1].get("status") == "Failed":
                 yield {"status": "error", "message": f"❌ Analysis failed. Error: {results['error']}"}
            else:
                 yield {"status": "progress", "message": f"\n✅ Analysis finished in {time.time() - analysis_start_time:.2f} seconds."}
                 results["steps"].append({"step": "Analysis Completion", "status": "Success"})


        except Exception as e:
            error_msg = f"\n❌ A critical error occurred during analysis setup or execution: {e}"
            yield {"status": "error", "message": error_msg}
            results["error"] = str(e)
            results["steps"].append({"step": "Critical Error", "status": "Failed", "message": str(e)})
            traceback.print_exc()

        finally:
            yield {"status": "progress", "message": "    Performing cleanup..."}
            # --- Cleanup ---
            if page:
                try: await page.close()
                except Exception as e: print(f"      Error closing page: {e}")
            if context:
                try: await context.close()
                except Exception as e: print(f"      Error closing context: {e}")
            if browser:
                try: await browser.close()
                except Exception as e: print(f"      Error closing browser: {e}")
            yield {"status": "progress", "message": "    Cleanup finished."}

    # Yield the final results object at the very end with a 'complete' status
    yield {"status": "complete", "results": results}


# --- Console Formatting Function ---
def format_results_for_console(results: Dict[str, Any]) -> str:
    """Formats the analysis results into a readable string for the console."""
    if "error" in results and any(step.get("status") == "Failed" for step in results.get("steps", [])):
        # Check if a 'Failed' step exists, indicating a true failure
        return f"*** ANALYSIS FAILED ***\nURL: {results.get('url', 'N/A')}\nError: {results.get('error', 'Unknown error')}"

    url = results.get("url", "N/A")
    load_analysis = results.get("pageLoadAnalysis", {})
    click_analysis = results.get("clickAnalysis", [])
    vendors_on_page = load_analysis.get("vendors_on_page", {})
    load_network_summary = load_analysis.get("load_network_summary", {})
    utag_data = load_analysis.get("utag_data", {})
    load_tealium_events = load_analysis.get("tealium_events", [])

    page_type = utag_data.get("page_type", "Unknown") if isinstance(utag_data, dict) else "Unknown"

    report = [
        f"=================================================",
        f" ANALYSIS REPORT for: {url}",
        f" Detected Page Type: {page_type}",
        f" Analyzed at: {results.get('analysisTimestamp', 'N/A')}",
        f"=================================================\n",
        f"--- Page Load Analysis ---"
    ]

    # TMS
    tealium_info = load_analysis.get("tag_detection", {}).get("tealiumInfo", {})
    gtm_info = load_analysis.get("tag_detection", {}).get("gtmInfo", {})
    report.append("Tag Management Systems:")
    if tealium_info.get("detected"):
        report.append(f"  ✓ Tealium iQ (Profile: {tealium_info.get('profile', 'N/A')}, Account: {tealium_info.get('account', 'N/A')}, Version: {tealium_info.get('version', 'N/A')}, Tags Loaded: {tealium_info.get('tagsLoaded', 'N/A')})")
    else:
        report.append("  - Tealium iQ: Not Detected")
    if gtm_info.get("detected"):
        report.append(f"  ✓ Google Tag Manager (Containers: {', '.join(gtm_info.get('containers',[])) or 'N/A'})")
    else:
        report.append("  - Google Tag Manager: Not Detected")
    report.append("")

    # Vendors on Page
    report.append("Vendors Detected on Page Load (Scripts/Objects):")
    if vendors_on_page and isinstance(vendors_on_page, dict) and not vendors_on_page.get("error"):
        if vendors_on_page: # Check if not empty after error check
            for category, names in sorted(vendors_on_page.items()):
                report.append(f"  - {category.replace('_', ' ').title()}: {', '.join(names)}")
        else:
            report.append("  None")
    elif isinstance(vendors_on_page, dict) and vendors_on_page.get("error"):
         report.append(f"  Error detecting vendors: {vendors_on_page['error']}")
    else:
         report.append("  None or invalid data")
    report.append("")

     # Vendors in Network (Load)
    load_network_vendors = load_network_summary.get("vendors_detected", {})
    report.append(f"Vendors Detected in Network Requests (During Load - {load_network_summary.get('total_requests','N/A')} total):")
    if load_network_vendors and isinstance(load_network_vendors, dict):
         if load_network_vendors: # Check if not empty
             for name, urls in sorted(load_network_vendors.items()):
                 report.append(f"  - {name} ({len(urls)} reqs)")
         else:
             report.append("  None")
    else:
        report.append("  None or invalid data")
    report.append("")

    # Initial Utag Data Summary
    if utag_data and not (isinstance(utag_data, dict) and utag_data.get('error')):
        key_count = len(utag_data) if isinstance(utag_data, dict) else 'N/A'
        report.append(f"Initial Utag Data: Found {key_count} keys (See JSON for details).")
    elif isinstance(utag_data, dict) and utag_data.get('error'):
         report.append(f"Initial Utag Data: Error retrieving ({utag_data.get('error', 'Unknown issue')}).")
    else:
         report.append(f"Initial Utag Data: Not found or empty.")
    report.append("")

    # Initial Tealium Events
    if load_tealium_events and isinstance(load_tealium_events, list):
        report.append(f"Tealium Events Captured During Load ({len(load_tealium_events)}):")
        if load_tealium_events:
            for event in load_tealium_events:
                event_type = event.get('type', 'N/A')
                event_data = event.get('data', {})
                # Extract description, handling potential non-dict data
                desc = ''
                if isinstance(event_data, dict):
                    desc = event_data.get('event_name', event_data.get('event_type', event_data.get('event', event_data.get('link_id',''))))
                report.append(f"  - {event_type} {'('+desc+')' if desc else ''}")
        else:
            report.append("  None captured.")
    elif isinstance(load_tealium_events, dict) and 'error' in load_tealium_events:
         report.append(f"Tealium Events Captured During Load: Error retrieving ({load_tealium_events['error']})")
    else:
        report.append("Tealium Events Captured During Load: None or invalid data")
    report.append("")


    # --- Click Analysis Summary ---
    report.append("--- Click Event Analysis ---")
    if not click_analysis:
        report.append(f"No click events were configured or analyzed for page type '{page_type}'.")
    else:
        for i, click in enumerate(click_analysis):
            report.append(f"\n▶ Click {i+1}: {click.get('elementDescription')} ({click.get('clickStatus')})")
            report.append(f"  Selector: {click.get('selector')}")
            if click.get('clickError'):
                 report.append(f"  Error: {click.get('clickError')}")

            # Tealium Events
            tealium_events = click.get('tealium_events', [])
            if isinstance(tealium_events, list):
                 report.append(f"  Tealium Events Triggered: {len(tealium_events)}")
                 if tealium_events:
                     for event in tealium_events:
                         event_type = event.get('type', 'N/A')
                         event_data = event.get('data', {})
                         desc = ''
                         if isinstance(event_data, dict):
                             desc = event_data.get('event_name', event_data.get('event_type', event_data.get('event', event_data.get('link_id',''))))
                         report.append(f"    - {event_type} {'('+desc+')' if desc else ''}")
            elif isinstance(tealium_events, dict) and 'error' in tealium_events:
                 report.append(f"  Tealium Events Triggered: Error retrieving ({tealium_events['error']})")
            else:
                 report.append("  Tealium Events Triggered: None or invalid data")


            # Network Vendors
            network_vendors = click.get('vendors_in_network', {})
            if isinstance(network_vendors, dict) and 'error' not in network_vendors:
                 report.append(f"  Network Requests to Vendors After Click: {len(network_vendors)}")
                 if network_vendors:
                     for name, urls in sorted(network_vendors.items()):
                         report.append(f"    - {name} ({len(urls)} reqs)")
            elif isinstance(network_vendors, dict) and 'error' in network_vendors:
                 report.append(f"  Network Requests to Vendors After Click: Error ({network_vendors['error']})")
            else:
                 report.append("  Network Requests to Vendors After Click: None or invalid data")


    report.append("\n=================================================")
    return "\n".join(report)


# --- Main Execution Block (for running directly) ---
async def run_main_analysis_terminal():
    """Gets URL input and runs the analysis, printing to terminal."""
    default_url = "https://www.penguinrandomhouse.com/books/734292/the-very-hungry-caterpillars-peekaboo-easter-by-eric-carle-illustrated-by-eric-carle/9780593750179/"
    try:
        url_to_analyze = input(f"Enter URL to analyze (or press Enter for default: {default_url}): ").strip()
        if not url_to_analyze:
            url_to_analyze = default_url

        if not re.match(r'^https?://', url_to_analyze):
             print(f"Warning: URL doesn't start with http:// or https://. Prepending https://")
             url_to_analyze = 'https://' + url_to_analyze

        final_results = None
        # Iterate through the generator to print status updates
        async for update in analyze_page_tags_and_events(url_to_analyze):
             if update.get("status") != "complete": # Print progress/warning/error messages
                  print(update.get("message", "")) # Print message directly from the yielded dict
             else: # Store final results when complete
                  final_results = update.get("results")

        # Once the generator is exhausted, print the final report
        if final_results:
             console_report = format_results_for_console(final_results)
             print("\n" + console_report)

             # Save results to JSON file
             sanitized_url_part = re.sub(r'^https?://', '', final_results.get('url','unknown_url'))
             sanitized_url_part = re.sub(r'[/:*?"<>|\\.]', '_', sanitized_url_part)[:50] # Added '.' to sanitize
             filename = f"tealium_analysis_{sanitized_url_part}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
             try:
                 with open(filename, 'w', encoding='utf-8') as f:
                     json.dump(final_results, f, indent=2, default=str) # Use default=str for safety
                 print(f"\nFull analysis results saved to: {filename}")
             except Exception as e:
                 print(f"\nError saving full results to JSON: {e}")
        else:
             print("\nAnalysis did not complete successfully or yield final results.")


    except KeyboardInterrupt:
        print("\nAnalysis cancelled by user.")
    except Exception as e:
        print(f"\nAn unexpected error occurred in main terminal execution: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    try:
        # Run the terminal-specific main async function
        asyncio.run(run_main_analysis_terminal())

    except RuntimeError as e:
         print(f"Asyncio runtime error: {e}")
         if "cannot be called from a running event loop" in str(e):
               print("Hint: If running in an environment like Jupyter, ensure `nest_asyncio.apply()` is called or use `await run_main_analysis_terminal()` if in an async context.")
    except PlaywrightError as e:
         print(f"Playwright setup or launch error: {e}")
         print("\n--- Troubleshooting ---")
         if "Executable doesn't exist" in str(e):
              print("❌ ERROR: The required browser (likely Chromium) is not installed or cannot be found.")
              print("➡️ Please run: playwright install chromium")
         else:
              print("Ensure Playwright is installed (`pip install playwright`) and browsers are installed (`playwright install`).")
         print("If issues persist, check your Playwright installation and environment PATH.")
         sys.exit(1)
    except ImportError as e:
         if 'selectors_config' in str(e):
             print("❌ ERROR: Cannot find the `selectors_config.py` file.")
             print("➡️ Please ensure `selectors_config.py` exists in the same directory as `gemini_analyzer.py`.")
         else:
             print(f"Import error: {e}")
             print("➡️ Check if all required libraries (Playwright, nest_asyncio) are installed.")
         sys.exit(1)
    except Exception as e:
        print(f"A critical error occurred before the main analysis loop: {e}")
        traceback.print_exc()
        sys.exit(1)