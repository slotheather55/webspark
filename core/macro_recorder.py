#!/usr/bin/env python3
"""
macro_recorder.py

Handles macro recording, storage, and playback functionality.
This module manages recording sessions and provides data structures for macro storage.
"""

import asyncio
import json
import uuid
import time
import os
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass, asdict
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MacroAction:
    """Represents a single recorded action in a macro"""
    id: int
    timestamp: float
    action_type: str  # 'click', 'scroll', 'type', 'hover', 'wait'
    selector: str
    text: Optional[str] = None
    coordinates: Optional[Dict[str, int]] = None
    description: str = ""
    locator_bundle: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass 
class Macro:
    """Represents a complete macro with metadata"""
    id: str
    name: str
    url: str
    actions: List[MacroAction]
    created_at: str
    duration: float  # in milliseconds
    description: str = ""
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['actions'] = [action.to_dict() for action in self.actions]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Macro':
        actions = [MacroAction(**action) for action in data.get('actions', [])]
        data['actions'] = actions
        return cls(**data)

class RecordingSession:
    """Manages an active recording session"""
    
    def __init__(self, session_id: str, url: str, macro_name: str = ""):
        self.session_id = session_id
        self.url = url
        self.macro_name = macro_name
        self.actions = []
        self.start_time = time.time()
        self.is_active = True
        self.page: Optional[Page] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.action_listeners = []  # For streaming recorded actions
        
        # Interactive viewport properties
        self.viewport_size = {"width": 1200, "height": 800}
        self.screenshot_cache = None
        self.screenshot_cache_time = 0
        self.tealium_events = []
        self.network_beacons = []
        
    async def initialize_browser(self) -> bool:
        """Initialize the browser for this recording session"""
        try:
            # Import playwright here to ensure it's available
            from playwright.async_api import async_playwright
            
            playwright = await async_playwright().start()
            
            # Launch browser in headless mode for production compatibility
            self.browser = await playwright.chromium.launch(
                headless=True,  # Always headless for production
                args=[
                    '--no-sandbox', 
                    '--disable-web-security',
                    '--disable-dev-shm-usage',
                    '--disable-extensions',
                    '--disable-gpu',
                    '--no-first-run'
                ]
            )
            
            self.context = await self.browser.new_context(
                viewport=self.viewport_size,
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            self.page = await self.context.new_page()
            
            # Navigate to the target URL first
            logger.info(f"Navigating to {self.url}")
            await self.page.goto(self.url, wait_until='domcontentloaded', timeout=30000)
            await self.page.wait_for_timeout(2000)  # Let page settle
            
            # Dismiss cookie banners and overlays automatically
            await self.dismiss_cookie_overlays()
            
            # Then set up event listeners for recording interactions
            await self.setup_recording_listeners()
            
            logger.info(f"Browser initialized successfully for session {self.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize browser for session {self.session_id}: {e}")
            logger.error(f"Error details: {traceback.format_exc()}")
            await self.cleanup()
            return False
    
    async def setup_recording_listeners(self):
        """Set up event listeners to record user interactions"""
        if not self.page:
            return
            
        # Inject enhanced JavaScript to capture interactions with better selector generation
        js_code = """
            // Enhanced macro recorder with improved selector generation
            window.macroRecorder = {
                sessionId: '""" + self.session_id + """',
                
                generateSelector: function(element) {
                    // Enhanced selector generation with Tealium-optimized strategies
                    if (!element) return '';
                    
                    // Strategy 1: Use ID if available and unique
                    if (element.id) {
                        const idSelector = '#' + element.id;
                        if (document.querySelectorAll(idSelector).length === 1) {
                            return idSelector;
                        }
                    }
                    
                    // Strategy 2: Use data attributes if available
                    const dataAttrs = ['data-testid', 'data-cy', 'data-test', 'data-automation'];
                    for (const attr of dataAttrs) {
                        if (element.hasAttribute(attr)) {
                            const value = element.getAttribute(attr);
                            const selector = `[${attr}="${value}"]`;
                            if (document.querySelectorAll(selector).length === 1) {
                                return selector;
                            }
                        }
                    }
                    
                    // Strategy 2.5: Enhanced Tealium-optimized selectors for commerce tracking
                    const text = element.textContent ? element.textContent.trim().toLowerCase() : '';
                    const href = element.getAttribute('href') || '';
                    
                    // CRITICAL: Add to Cart button detection (highest priority for Tealium)
                    if (text.includes('add to cart') || element.className.includes('buy')) {
                        // Priority 1: Form with cart action
                        let parent = element.parentElement;
                        while (parent && parent.tagName !== 'BODY') {
                            if (parent.tagName === 'FORM' && parent.action && parent.action.includes('cart')) {
                                return `form[action*="cart"] button:has-text("${element.textContent.trim()}")`;
                            }
                            // Priority 2: Look for collapse/expandable sections (common on PRH)
                            if (parent.id && parent.id.startsWith('collapse')) {
                                return `div[id^="collapse"].in form button:has-text("${element.textContent.trim()}")`;
                            }
                            parent = parent.parentElement;
                        }
                        // Priority 3: Class-based fallback
                        if (element.className) {
                            const mainClass = element.className.split(' ')[0];
                            return `button.${mainClass}:has-text("${element.textContent.trim()}")`;
                        }
                    }
                    
                    // CRITICAL: Retailer link detection (high priority for Tealium commerce tracking)
                    if (element.tagName === 'A' && (text.includes('amazon') || text.includes('barnes') || href.includes('amazon.com') || href.includes('barnesandnoble.com'))) {
                        // Priority 1: Affiliate buttons container
                        let parent = element.parentElement;
                        while (parent && parent.tagName !== 'BODY') {
                            if (parent.className && parent.className.includes('affiliate')) {
                                return `.affiliate-buttons a:has-text("${element.textContent.trim()}")`;
                            }
                            if (parent.className && parent.className.includes('buy')) {
                                return `.buy_clmn a:has-text("${element.textContent.trim()}")`;
                            }
                            if (parent.className && parent.className.includes('isbn-related')) {
                                return `.isbn-related a:has-text("${element.textContent.trim()}")`;
                            }
                            parent = parent.parentElement;
                        }
                        // Priority 2: Direct href-based selector
                        if (href.includes('amazon.com')) {
                            return `a[href*="amazon.com"]:has-text("${element.textContent.trim()}")`;
                        }
                        if (href.includes('barnesandnoble.com')) {
                            return `a[href*="barnesandnoble.com"]:has-text("${element.textContent.trim()}")`;
                        }
                    }
                    
                    // HIGH PRIORITY: Preview/Sample buttons (important for engagement tracking)
                    if (text.includes('look inside') || text.includes('preview') || text.includes('sample') || text.includes('read sample')) {
                        if (element.className.includes('look-inside')) {
                            return `.product-look-inside.insight`;
                        }
                        if (element.className.includes('read-sample') || element.className.includes('excerpt')) {
                            return `.product-read-sample.excerpt-button`;
                        }
                        if (element.className) {
                            const mainClass = element.className.split(' ')[0];
                            return `button.${mainClass}:has-text("${element.textContent.trim()}")`;
                        }
                    }
                    
                    // MEDIUM PRIORITY: Newsletter and engagement elements
                    if (element.tagName === 'INPUT' && (element.type === 'email' || element.id.includes('newsletter'))) {
                        if (element.id.includes('newsletter')) {
                            return `input[id*="newsletter"][type="email"]`;
                        }
                    }
                    
                    // Strategy 3: Generate CSS path with intelligent class selection
                    const path = [];
                    let current = element;
                    
                    while (current && current.nodeType === Node.ELEMENT_NODE && current !== document.body) {
                        let selector = current.nodeName.toLowerCase();
                        
                        // Add meaningful classes (avoid generic ones)
                        if (current.className) {
                            const classes = current.className.split(/\s+/).filter(cls => {
                                // Filter out common generic classes
                                return cls && !cls.match(/^(active|selected|hover|focus|disabled|btn|button|link)$/i);
                            });
                            
                            if (classes.length > 0) {
                                selector += '.' + classes.slice(0, 2).join('.');
                            }
                        }
                        
                        // Add position if element has siblings with same tag
                        const parent = current.parentElement;
                        if (parent) {
                            const siblings = Array.from(parent.children).filter(child => 
                                child.nodeName === current.nodeName
                            );
                            
                            if (siblings.length > 1) {
                                const index = siblings.indexOf(current) + 1;
                                selector += `:nth-child(${index})`;
                            }
                        }
                        
                        path.unshift(selector);
                        current = current.parentElement;
                        
                        // Test if current path is unique
                        if (path.length >= 2) {
                            const testSelector = path.join(' > ');
                            try {
                                if (document.querySelectorAll(testSelector).length === 1) {
                                    return testSelector;
                                }
                            } catch (e) {
                                // Invalid selector, continue building
                            }
                        }
                        
                        // Prevent overly long selectors
                        if (path.length > 5) break;
                    }
                    
                    // Strategy 4: Use text content as fallback for links and buttons
                    if (element.tagName === 'A' || element.tagName === 'BUTTON' || 
                        element.getAttribute('role') === 'button') {
                        const text = element.textContent.trim();
                        if (text.length > 0 && text.length < 50) {
                            const textSelector = `${element.tagName.toLowerCase()}:has-text("${text}")`;
                            return textSelector;
                        }
                    }
                    
                    return path.join(' > ') || element.tagName.toLowerCase();
                },

                computeLocatorBundle: function(element) {
                    if (!element) return null;
                    const tag = element.tagName.toLowerCase();
                    const text = (element.textContent || '').trim();
                    const ariaLabel = element.getAttribute && element.getAttribute('aria-label');
                    const role = (function() {
                        if (tag === 'a') return 'link';
                        if (tag === 'button') return 'button';
                        if (tag === 'input' && (element.type === 'submit' || element.type === 'button')) return 'button';
                        const explicit = element.getAttribute && element.getAttribute('role');
                        return explicit || null;
                    })();
                    const name = ariaLabel || (text && text.length <= 100 ? text : (text ? text.substring(0, 100) : null));
                    const href = element.getAttribute && element.getAttribute('href');
                    const id = element.id || null;
                    const classes = element.className ? ('' + element.className).split(/\s+/).filter(Boolean) : [];
                    const makeXPath = function(el){
                        if (el.id) return '//*[@id="' + el.id + '"]';
                        const parts = [];
                        for (; el && el.nodeType === 1; el = el.parentNode) {
                            let ix = 1;
                            for (let sib = el.previousSibling; sib; sib = sib.previousSibling) {
                                if (sib.nodeType === 1 && sib.nodeName === el.nodeName) ix++;
                            }
                            parts.unshift(el.nodeName.toLowerCase() + '[' + ix + ']');
                        }
                        return '//' + parts.join('/');
                    };
                    const xpath = makeXPath(element);
                    // Capture up to 5 ancestors with id/classes for scoping
                    const ancestors = [];
                    let cur = element.parentElement;
                    while (cur && ancestors.length < 5) {
                        ancestors.push({
                            tag: cur.tagName.toLowerCase(),
                            id: cur.id || null,
                            classes: cur.className ? ('' + cur.className).split(/\s+/).filter(Boolean) : []
                        });
                        cur = cur.parentElement;
                    }
                    return { role, name, href, tag, id, classes, text: name, xpath, ancestors };
                },
                
                recordAction: function(action) {
                    // Enhanced action recording with validation
                    if (!action.selector) return;
                    
                    // Add action to console for Playwright to capture
                    console.log('MACRO_ACTION:' + JSON.stringify(action));
                    
                    // Also try to post message (for future iframe support)
                    try {
                        window.postMessage({
                            type: 'MACRO_ACTION',
                            sessionId: this.sessionId,
                            action: action
                        }, '*');
                    } catch (e) {
                        // Ignore postMessage errors
                    }
                },
                
                addVisualFeedback: function(element, type = 'click') {
                    if (!element) return;
                    
                    // Create visual feedback overlay
                    const overlay = document.createElement('div');
                    overlay.style.cssText = `
                        position: absolute;
                        pointer-events: none;
                        z-index: 10000;
                        border: 3px solid #4f79ff;
                        border-radius: 4px;
                        background: rgba(79, 121, 255, 0.1);
                        box-shadow: 0 0 10px rgba(79, 121, 255, 0.5);
                        transition: all 0.3s ease;
                    `;
                    
                    const rect = element.getBoundingClientRect();
                    overlay.style.left = (rect.left + window.scrollX - 2) + 'px';
                    overlay.style.top = (rect.top + window.scrollY - 2) + 'px';
                    overlay.style.width = (rect.width + 4) + 'px';
                    overlay.style.height = (rect.height + 4) + 'px';
                    
                    document.body.appendChild(overlay);
                    
                    // Add animation and remove
                    setTimeout(() => {
                        overlay.style.opacity = '0';
                        overlay.style.transform = 'scale(1.1)';
                    }, 100);
                    
                    setTimeout(() => {
                        if (overlay.parentNode) {
                            overlay.parentNode.removeChild(overlay);
                        }
                    }, 1500);
                    
                    // Also add a small notification
                    this.showActionNotification(type, element);
                },
                
                showActionNotification: function(type, element) {
                    const notification = document.createElement('div');
                    const text = element.textContent ? element.textContent.trim().substring(0, 30) : element.tagName;
                    
                    notification.innerHTML = `
                        <div style="
                            position: fixed;
                            top: 20px;
                            right: 20px;
                            background: #4f79ff;
                            color: white;
                            padding: 8px 16px;
                            border-radius: 6px;
                            font-size: 14px;
                            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                            z-index: 10001;
                            animation: slideInFade 0.3s ease;
                        ">
                            🎯 Recorded: ${type} on "${text}"
                        </div>
                    `;
                    
                    if (!document.getElementById('macro-notification-style')) {
                        const style = document.createElement('style');
                        style.id = 'macro-notification-style';
                        style.textContent = `
                            @keyframes slideInFade {
                                from { transform: translateX(100%); opacity: 0; }
                                to { transform: translateX(0); opacity: 1; }
                            }
                        `;
                        document.head.appendChild(style);
                    }
                    
                    document.body.appendChild(notification);
                    
                    setTimeout(() => {
                        if (notification.parentNode) {
                            notification.parentNode.removeChild(notification);
                        }
                    }, 2000);
                }
            };
            
            // Enhanced click listener with better event handling
            document.addEventListener('click', function(event) {
                try {
                    const selector = window.macroRecorder.generateSelector(event.target);
                    const text = event.target.textContent ? event.target.textContent.trim().substring(0, 100) : '';
                    const bundle = window.macroRecorder.computeLocatorBundle(event.target);
                    
                    const action = {
                        type: 'click',
                        selector: selector,
                        text: text,
                        locator_bundle: bundle,
                        coordinates: {
                            x: event.clientX,
                            y: event.clientY,
                            pageX: event.pageX,
                            pageY: event.pageY
                        },
                        timestamp: Date.now(),
                        tagName: event.target.tagName,
                        href: event.target.href || '',
                        className: event.target.className || ''
                    };
                    
                    window.macroRecorder.recordAction(action);
                    window.macroRecorder.addVisualFeedback(event.target, 'click');
                } catch (error) {
                    console.error('Error recording click:', error);
                }
            }, true);
            
            // Scroll recording disabled - focusing on click events only for Tealium analysis
            
            // Enhanced input listener for typing
            let inputTimeout = {};
            document.addEventListener('input', function(event) {
                if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
                    try {
                        const selector = window.macroRecorder.generateSelector(event.target);
                        const inputId = selector + event.target.type;
                        
                        // Debounce input events to avoid recording every keystroke
                        clearTimeout(inputTimeout[inputId]);
                        inputTimeout[inputId] = setTimeout(() => {
                            window.macroRecorder.recordAction({
                                type: 'type',
                                selector: selector,
                                text: event.target.value,
                                timestamp: Date.now(),
                                inputType: event.target.type,
                                placeholder: event.target.placeholder || ''
                            });
                            
                            window.macroRecorder.addVisualFeedback(event.target, 'type');
                        }, 500);
                    } catch (error) {
                        console.error('Error recording input:', error);
                    }
                }
            });
            
            // Note: Hover events disabled to reduce noise - only recording clicks, scrolls, and typing
            
            console.log('✅ Macro recorder initialized successfully');
        """
        
        await self.page.evaluate(js_code)
        
        # Set up Playwright event listeners
        self.page.on("console", self.handle_console_message)
        self.page.on("framenavigated", self.handle_navigation)
        
        # Add page lifecycle listeners
        self.page.on("load", lambda: asyncio.create_task(self.record_page_load()))
        
        # Add browser close detection
        self.page.on("close", self.handle_page_close)
    
    # Interactive Viewport Methods
    async def get_screenshot(self) -> Optional[str]:
        """Get base64 encoded screenshot for interactive viewport"""
        if not self.page:
            return None
            
        try:
            # Check cache (200ms cache to improve performance)
            current_time = time.time()
            if (self.screenshot_cache and 
                current_time - self.screenshot_cache_time < 0.2):
                return self.screenshot_cache
            
            # Take new screenshot
            screenshot = await self.page.screenshot(
                type='jpeg',
                quality=70,
                full_page=False
            )
            
            # Encode and cache
            screenshot_b64 = base64.b64encode(screenshot).decode()
            self.screenshot_cache = screenshot_b64
            self.screenshot_cache_time = current_time
            
            return screenshot_b64
            
        except Exception as e:
            logger.error(f"Screenshot capture failed: {e}")
            return None
    
    async def dismiss_cookie_overlays(self):
        """Automatically dismiss cookie banners, GDPR notices, and modal overlays"""
        if not self.page:
            return
            
        try:
            # Wait a bit for any overlays to appear
            await self.page.wait_for_timeout(1000)
            
            # Common cookie banner and overlay selectors
            dismiss_selectors = [
                # Generic cookie/GDPR dismissal
                'button[id*="accept"]', 'button[class*="accept"]',
                'button[id*="consent"]', 'button[class*="consent"]', 
                'button[id*="cookie"]', 'button[class*="cookie"]',
                'button[id*="agree"]', 'button[class*="agree"]',
                'button[id*="close"]', 'button[class*="close"]',
                'button[id*="dismiss"]', 'button[class*="dismiss"]',
                'button[id*="ok"]', 'button[class*="ok"]',
                
                # Text-based selectors
                'button:has-text("Accept")', 'button:has-text("Accept All")',
                'button:has-text("I Agree")', 'button:has-text("Agree")',
                'button:has-text("OK")', 'button:has-text("Close")',
                'button:has-text("Dismiss")', 'button:has-text("Got it")',
                'button:has-text("Continue")', 'button:has-text("Allow")',
                
                # Links that act as buttons
                'a:has-text("Accept")', 'a:has-text("I Agree")', 
                'a:has-text("Close")', 'a:has-text("Dismiss")',
                
                # Modal close buttons
                '.modal .close', '.modal [aria-label="Close"]',
                '.overlay .close', '.popup .close',
                '[role="dialog"] button[aria-label="Close"]',
                
                # Specific common implementations
                '.cookie-banner button', '.gdpr-banner button',
                '.privacy-notice button', '.consent-banner button'
            ]
            
            for selector in dismiss_selectors:
                try:
                    # Check if element exists and is visible
                    element = await self.page.locator(selector).first
                    if await element.is_visible():
                        logger.info(f"Dismissing overlay with selector: {selector}")
                        await element.click()
                        await self.page.wait_for_timeout(500)  # Wait for overlay to disappear
                        break  # Only dismiss one overlay to avoid conflicts
                except Exception:
                    continue  # Try next selector
                    
            # Also try to dismiss any modal dialogs by pressing Escape
            try:
                await self.page.keyboard.press('Escape')
                await self.page.wait_for_timeout(500)
            except Exception:
                pass
                
        except Exception as e:
            logger.warning(f"Cookie overlay dismissal failed: {e}")
            # Don't fail the whole session for this
    
    async def handle_viewport_click(self, x: int, y: int) -> dict:
        """Handle click from interactive viewport with proper coordinate scaling"""
        if not self.page:
            return {"success": False, "error": "No active page"}
        
        try:
            # Get actual viewport size from browser (it's a property, not a method)
            viewport = self.page.viewport_size
            if not viewport:
                viewport = {"width": 1200, "height": 800}  # fallback
            
            # Scale coordinates from viewport display to actual browser viewport
            # The frontend should send us the scale factors, but for now we'll use the viewport size
            scaled_x = int(x * (viewport["width"] / self.viewport_size["width"]))
            scaled_y = int(y * (viewport["height"] / self.viewport_size["height"]))
            
            # Ensure coordinates are within bounds
            scaled_x = max(0, min(scaled_x, viewport["width"] - 1))
            scaled_y = max(0, min(scaled_y, viewport["height"] - 1))
            
            logger.info(f"Viewport click: original({x}, {y}) -> scaled({scaled_x}, {scaled_y})")
            
            # Click at scaled coordinates
            await self.page.mouse.click(scaled_x, scaled_y)
            
            # Small delay to allow any events to trigger
            await self.page.wait_for_timeout(100)
            
            # Record this as a click action
            await self.record_action({
                'type': 'click',
                'selector': f'mouse_click_at({scaled_x},{scaled_y})',
                'text': '',
                'coordinates': {'x': scaled_x, 'y': scaled_y, 'pageX': scaled_x, 'pageY': scaled_y},
                'timestamp': time.time() * 1000
            })
            
            # Capture any Tealium events that might have been triggered
            await self.capture_tealium_state()
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Viewport click failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def handle_viewport_type(self, text: str) -> dict:
        """Handle text input from interactive viewport"""
        if not self.page:
            return {"success": False, "error": "No active page"}
        
        try:
            await self.page.keyboard.type(text)
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Viewport type failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def handle_viewport_key(self, key: str) -> dict:
        """Handle key press from interactive viewport"""
        if not self.page:
            return {"success": False, "error": "No active page"}
        
        try:
            await self.page.keyboard.press(key)
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Viewport key failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def handle_viewport_scroll(self, delta_y: int) -> dict:
        """Handle scroll from interactive viewport"""
        if not self.page:
            return {"success": False, "error": "No active page"}
        
        try:
            await self.page.mouse.wheel(0, delta_y)
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Viewport scroll failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def capture_tealium_state(self) -> dict:
        """Capture current Tealium events and data layer state"""
        if not self.page:
            return {"events": [], "dataLayer": {}}
        
        try:
            # Evaluate JavaScript to get Tealium state
            tealium_state = await self.page.evaluate("""
                () => {
                    return {
                        events: window.tealiumCapture?.events || [],
                        dataLayer: window.tealiumCapture?.dataLayer || {},
                        utag_data: window.utag_data || {}
                    };
                }
            """)
            
            # Store new events
            for event in tealium_state.get('events', []):
                if event not in self.tealium_events:
                    self.tealium_events.append(event)
            
            return tealium_state
            
        except Exception as e:
            logger.error(f"Tealium state capture failed: {e}")
            return {"events": [], "dataLayer": {}}
    
    def set_viewport_size(self, width: int, height: int):
        """Update viewport size for interactive display"""
        self.viewport_size = {"width": width, "height": height}
        logger.info(f"Updated viewport size to {width}x{height} for session {self.session_id}")
    
    async def record_page_load(self):
        """Record page load event"""
        await self.record_action({
            'type': 'pageload',
            'selector': 'document',
            'text': self.page.url,
            'timestamp': time.time() * 1000
        })
    
    def handle_page_close(self):
        """Handle page close event"""
        logger.info(f"Page closed for session {self.session_id}")
        self.is_active = False
    
    def handle_context_close(self):
        """Handle browser context close event"""
        logger.info(f"Browser context closed for session {self.session_id}")
        self.is_active = False
    
    async def handle_console_message(self, msg):
        """Handle console messages from the injected recording script"""
        try:
            if msg.type == "log" and "MACRO_ACTION:" in msg.text:
                action_data = json.loads(msg.text.replace("MACRO_ACTION:", ""))
                await self.record_action(action_data)
        except Exception as e:
            logger.error(f"Error handling console message: {e}")
    
    async def handle_navigation(self, frame):
        """Handle page navigation events"""
        if frame == self.page.main_frame:
            await self.record_action({
                'type': 'navigate',
                'selector': 'window',
                'text': frame.url,
                'timestamp': time.time() * 1000
            })
    
    async def record_action(self, action_data: Dict[str, Any]):
        """Record a new action and notify listeners"""
        if not self.is_active:
            return
            
        action = MacroAction(
            id=len(self.actions) + 1,
            timestamp=action_data['timestamp'] - (self.start_time * 1000),
            action_type=action_data['type'],
            selector=action_data['selector'],
            text=action_data.get('text', ''),
            coordinates=action_data.get('coordinates'),
            description=self.generate_action_description(action_data),
            locator_bundle=action_data.get('locator_bundle')
        )
        
        self.actions.append(action)
        logger.info(f"Recorded action: {action.description}")
        
        # Notify all listeners (for streaming)
        for listener in self.action_listeners:
            await listener(action)
    
    def generate_action_description(self, action_data: Dict[str, Any]) -> str:
        """Generate a human-readable description for an action"""
        action_type = action_data['type']
        text = action_data.get('text', '')
        selector = action_data['selector']
        
        if action_type == 'click':
            return f"Click on '{text}' ({selector})" if text else f"Click element ({selector})"
        elif action_type == 'scroll':
            coords = action_data.get('coordinates', {})
            return f"Scroll to position (x:{coords.get('x', 0)}, y:{coords.get('y', 0)})"
        elif action_type == 'type':
            return f"Type '{text}' in input field ({selector})"
        elif action_type == 'navigate':
            return f"Navigate to {text}"
        else:
            return f"{action_type.title()} action on {selector}"
    
    def add_action_listener(self, listener):
        """Add a listener for recorded actions (for streaming)"""
        self.action_listeners.append(listener)
    
    def remove_action_listener(self, listener):
        """Remove an action listener"""
        if listener in self.action_listeners:
            self.action_listeners.remove(listener)
    
    async def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def to_macro(self) -> Macro:
        """Convert the recording session to a saved macro"""
        duration = 0
        if self.actions:
            duration = self.actions[-1].timestamp
        
        return Macro(
            id=str(uuid.uuid4()),
            name=self.macro_name or f"Macro for {self.url}",
            url=self.url,
            actions=self.actions.copy(),
            created_at=datetime.now().isoformat(),
            duration=duration,
            description=f"Recorded macro with {len(self.actions)} actions"
        )

class MacroStorage:
    """Handles saving and loading macros to/from filesystem"""
    
    def __init__(self, storage_dir: str = "data/macros"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.macros_index_file = self.storage_dir / "index.json"
    
    def save_macro(self, macro: Macro) -> bool:
        """Save a macro to storage"""
        try:
            # Save the individual macro file
            macro_file = self.storage_dir / f"{macro.id}.json"
            with open(macro_file, 'w', encoding='utf-8') as f:
                json.dump(macro.to_dict(), f, indent=2)
            
            # Update the index
            self._update_index(macro)
            
            logger.info(f"Saved macro: {macro.name} ({macro.id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save macro {macro.id}: {e}")
            return False
    
    def load_macro(self, macro_id: str) -> Optional[Macro]:
        """Load a specific macro by ID"""
        try:
            macro_file = self.storage_dir / f"{macro_id}.json"
            if not macro_file.exists():
                return None
                
            with open(macro_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return Macro.from_dict(data)
            
        except Exception as e:
            logger.error(f"Failed to load macro {macro_id}: {e}")
            return None
    
    def list_macros(self) -> List[Macro]:
        """List all saved macros"""
        try:
            if not self.macros_index_file.exists():
                return []
            
            with open(self.macros_index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
            
            macros = []
            for macro_id in index.get('macros', []):
                macro = self.load_macro(macro_id)
                if macro:
                    macros.append(macro)
            
            # Sort by creation date (newest first)
            macros.sort(key=lambda m: m.created_at, reverse=True)
            return macros
            
        except Exception as e:
            logger.error(f"Failed to list macros: {e}")
            return []
    
    def delete_macro(self, macro_id: str) -> bool:
        """Delete a macro"""
        try:
            macro_file = self.storage_dir / f"{macro_id}.json"
            if macro_file.exists():
                macro_file.unlink()
            
            # Remove from index
            self._remove_from_index(macro_id)
            
            logger.info(f"Deleted macro: {macro_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete macro {macro_id}: {e}")
            return False
    
    def _update_index(self, macro: Macro):
        """Update the macros index file"""
        try:
            index = {'macros': []}
            if self.macros_index_file.exists():
                with open(self.macros_index_file, 'r', encoding='utf-8') as f:
                    index = json.load(f)
            
            if macro.id not in index['macros']:
                index['macros'].append(macro.id)
            
            with open(self.macros_index_file, 'w', encoding='utf-8') as f:
                json.dump(index, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to update index: {e}")
    
    def _remove_from_index(self, macro_id: str):
        """Remove a macro ID from the index"""
        try:
            if not self.macros_index_file.exists():
                return
            
            with open(self.macros_index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
            
            if macro_id in index.get('macros', []):
                index['macros'].remove(macro_id)
                
                with open(self.macros_index_file, 'w', encoding='utf-8') as f:
                    json.dump(index, f, indent=2)
                    
        except Exception as e:
            logger.error(f"Failed to remove from index: {e}")

class MacroRecorderManager:
    """Manages recording sessions and macro storage"""
    
    def __init__(self):
        self.active_sessions: Dict[str, RecordingSession] = {}
        self.storage = MacroStorage()
    
    async def start_recording_session(self, url: str, macro_name: str = "") -> tuple[bool, str, str]:
        """Start a new recording session"""
        session_id = str(uuid.uuid4())
        
        try:
            session = RecordingSession(session_id, url, macro_name)
            
            # Initialize the browser
            if await session.initialize_browser():
                self.active_sessions[session_id] = session
                logger.info(f"Started recording session {session_id} for {url}")
                return True, session_id, "Recording session started successfully"
            else:
                return False, "", "Failed to initialize browser"
                
        except Exception as e:
            logger.error(f"Failed to start recording session: {e}")
            return False, "", str(e)
    
    def get_session(self, session_id: str) -> Optional[RecordingSession]:
        """Get an active recording session"""
        return self.active_sessions.get(session_id)
    
    async def stop_recording_session(self, session_id: str, save_macro: bool = True) -> tuple[bool, Optional[str], str]:
        """Stop a recording session and optionally save as macro"""
        session = self.active_sessions.get(session_id)
        if not session:
            return False, None, "Session not found"
        
        try:
            session.is_active = False
            
            # Convert to macro and save if requested
            macro_id = None
            if save_macro and session.actions:
                macro = session.to_macro()
                if self.storage.save_macro(macro):
                    macro_id = macro.id
                else:
                    return False, None, "Failed to save macro"
            
            # Cleanup browser resources
            await session.cleanup()
            
            # Remove from active sessions
            del self.active_sessions[session_id]
            
            # Log detailed summary of recorded actions
            logger.info(f"Recording session stopped. {len(session.actions)} actions recorded:")
            for i, action in enumerate(session.actions, 1):
                logger.info(f"  {i}. {action.description or action.action_type} - {action.selector}")
            
            message = f"Recording session stopped. {len(session.actions)} actions recorded."
            if macro_id:
                message += f" Macro saved with ID: {macro_id}"
                logger.info(f"Macro saved with ID: {macro_id}")
            
            logger.info(message)
            return True, macro_id, message
            
        except Exception as e:
            logger.error(f"Failed to stop recording session {session_id}: {e}")
            return False, None, str(e)
    
    async def cleanup_all_sessions(self):
        """Cleanup all active sessions (called on shutdown)"""
        for session_id, session in self.active_sessions.items():
            try:
                await session.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up session {session_id}: {e}")
        
        self.active_sessions.clear()

class PlaybackSession:
    """Manages macro playback"""
    
    def __init__(self, playback_id: str, macro: Macro):
        self.playback_id = playback_id
        self.macro = macro
        self.current_action_index = 0
        self.is_active = True
        self.page: Optional[Page] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.playback_listeners = []
        
    async def initialize_browser(self) -> bool:
        """Initialize browser for playback"""
        try:
            # Import playwright here to ensure it's available
            from playwright.async_api import async_playwright
            
            playwright = await async_playwright().start()
            
            # Try to launch browser with more permissive settings
            try:
                self.browser = await playwright.chromium.launch(
                    headless=False,  # Show browser during playback
                    args=[
                        '--no-sandbox', 
                        '--disable-web-security',
                        '--disable-dev-shm-usage',
                        '--disable-extensions',
                        '--disable-gpu',
                        '--no-first-run'
                    ]
                )
            except Exception as launch_error:
                logger.error(f"Failed to launch playback browser: {launch_error}")
                # Try headless mode as fallback
                logger.info("Attempting fallback to headless mode for playback...")
                self.browser = await playwright.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-web-security']
                )
            
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            self.page = await self.context.new_page()
            
            # Navigate to the original URL
            logger.info(f"Navigating to {self.macro.url} for playback")
            await self.page.goto(self.macro.url, wait_until='domcontentloaded', timeout=30000)
            await self.page.wait_for_timeout(2000)
            
            logger.info(f"Playback browser initialized successfully for {self.playback_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize playback browser: {e}")
            logger.error(f"Error details: {traceback.format_exc()}")
            await self.cleanup()
            return False
    
    async def start_playback(self) -> bool:
        """Start playing back the macro"""
        if not self.page:
            return False
            
        try:
            await self.notify_listeners({
                'type': 'start',
                'message': f'Starting playback of macro: {self.macro.name}',
                'total_actions': len(self.macro.actions)
            })
            
            for i, action in enumerate(self.macro.actions):
                if not self.is_active:
                    break
                    
                self.current_action_index = i
                
                await self.notify_listeners({
                    'type': 'action',
                    'action_index': i,
                    'description': action.description,
                    'action_type': action.action_type
                })
                
                success = await self.execute_action(action)
                
                if not success:
                    await self.notify_listeners({
                        'type': 'error',
                        'message': f'Failed to execute action: {action.description}',
                        'action_index': i
                    })
                    break
                
                # Wait between actions (simulate human timing)
                if i < len(self.macro.actions) - 1:  # Don't wait after last action
                    next_action = self.macro.actions[i + 1]
                    time_diff = next_action.timestamp - action.timestamp
                    # Cap the wait time to reasonable bounds
                    wait_time = min(max(time_diff / 1000, 0.5), 5.0)
                    await self.page.wait_for_timeout(int(wait_time * 1000))
            
            if self.is_active:
                await self.notify_listeners({
                    'type': 'complete',
                    'message': f'Macro playback completed successfully',
                    'actions_executed': len(self.macro.actions)
                })
            
            return True
            
        except Exception as e:
            logger.error(f"Playback error: {e}")
            await self.notify_listeners({
                'type': 'error',
                'message': f'Playback error: {str(e)}'
            })
            return False
    
    async def execute_action(self, action: MacroAction) -> bool:
        """Execute a single action"""
        try:
            if action.action_type == 'click':
                return await self.execute_click(action)
            elif action.action_type == 'scroll':
                return await self.execute_scroll(action)
            elif action.action_type == 'type':
                return await self.execute_type(action)
            elif action.action_type == 'hover':
                return await self.execute_hover(action)
            elif action.action_type == 'navigate':
                return await self.execute_navigate(action)
            elif action.action_type == 'pageload':
                # Page loads are already handled, just mark as successful
                return True
            else:
                logger.warning(f"Unknown action type: {action.action_type}")
                return True  # Don't fail on unknown actions
                
        except Exception as e:
            logger.error(f"Error executing action {action.action_type}: {e}")
            return False
    
    async def execute_click(self, action: MacroAction) -> bool:
        """Execute a click action"""
        try:
            # Try robust strategies in order: role+name (scoped), attribute-based, scoped CSS, raw selector, XPath, coordinates
            locator = None
            bundle = action.locator_bundle or {}
            # Build a scope based on ancestors (prefer collapse.in container on PRH)
            const_scope = None
            try:
                const_scope = self.page.locator('div[id^="collapse"].in').first
            except Exception:
                const_scope = None

            # 1) Role + name scoped
            if bundle.get('role') and bundle.get('name'):
                try:
                    locator = self.page.get_by_role(bundle['role'], name=bundle['name'])
                    if const_scope:
                        locator = locator.filter(has=const_scope)
                    await locator.first.scroll_into_view_if_needed()
                    await locator.first.wait_for(state='visible', timeout=4000)
                    await locator.first.click()
                    await self.page.wait_for_timeout(500)
                    return True
                except Exception:
                    pass

            # 2) Attribute-based
            href = bundle.get('href')
            if href:
                try:
                    locator = self.page.locator(f'a[href*="{href.split("/")[2]}"]') if '//' in href else self.page.locator(f'a[href*="{href}"]')
                    if bundle.get('name'):
                        locator = locator.filter(has_text=bundle['name'])
                    if const_scope:
                        locator = const_scope.locator(locator)
                    await locator.first.scroll_into_view_if_needed()
                    await locator.first.wait_for(state='visible', timeout=3000)
                    await locator.first.click()
                    await self.page.wait_for_timeout(500)
                    return True
                except Exception:
                    pass

            # 3) Scoped CSS within visible container
            try:
                scoped_css = 'div[id^="collapse"].in ' + action.selector
                locator = self.page.locator(scoped_css)
                await locator.first.wait_for(state='visible', timeout=3000)
                await locator.first.scroll_into_view_if_needed()
                await locator.first.click()
                await self.page.wait_for_timeout(500)
                return True
            except Exception:
                pass

            # 4) Raw selector
            try:
                element = await self.page.wait_for_selector(action.selector, timeout=3000)
                await element.scroll_into_view_if_needed()
                await element.wait_for(state='visible', timeout=2000)
                await element.click()
                await self.page.wait_for_timeout(500)
                return True
            except Exception:
                pass

            # 5) XPath fallback
            xpath = (bundle.get('xpath') if isinstance(bundle.get('xpath'), str) else None)
            if xpath:
                try:
                    locator = self.page.locator(f'xpath={xpath}')
                    await locator.first.wait_for(state='visible', timeout=3000)
                    await locator.first.scroll_into_view_if_needed()
                    await locator.first.click()
                    await self.page.wait_for_timeout(500)
                    return True
                except Exception:
                    pass
            
            # If that fails, try text-based selector
            if action.text:
                try:
                    text_selector = f":has-text('{action.text[:30]}')"
                    element = await self.page.wait_for_selector(text_selector, timeout=3000)
                    if element:
                        await element.click()
                        await self.page.wait_for_timeout(500)
                        return True
                except:
                    pass
            
            # If still fails, try clicking by coordinates
            if action.coordinates:
                try:
                    await self.page.mouse.click(
                        action.coordinates.get('pageX', action.coordinates.get('x', 0)),
                        action.coordinates.get('pageY', action.coordinates.get('y', 0))
                    )
                    await self.page.wait_for_timeout(500)
                    return True
                except:
                    pass
            
            logger.warning(f"Failed to find element for click: {action.selector}")
            return False
            
        except Exception as e:
            logger.error(f"Error in execute_click: {e}")
            return False
    
    async def execute_scroll(self, action: MacroAction) -> bool:
        """Execute a scroll action"""
        try:
            if action.coordinates:
                x = action.coordinates.get('x', 0)
                y = action.coordinates.get('y', 0)
                await self.page.evaluate(f"window.scrollTo({x}, {y})")
                await self.page.wait_for_timeout(300)
                return True
            return False
        except Exception as e:
            logger.error(f"Error in execute_scroll: {e}")
            return False
    
    async def execute_type(self, action: MacroAction) -> bool:
        """Execute a type action"""
        try:
            element = await self.page.wait_for_selector(action.selector, timeout=5000)
            if element:
                # Clear existing text first
                await element.click()
                await self.page.keyboard.press('Control+a')
                await element.type(action.text or '', delay=50)  # Slight delay between keystrokes
                await self.page.wait_for_timeout(300)
                return True
            return False
        except Exception as e:
            logger.error(f"Error in execute_type: {e}")
            return False
    
    async def execute_hover(self, action: MacroAction) -> bool:
        """Execute a hover action"""
        try:
            element = await self.page.wait_for_selector(action.selector, timeout=5000)
            if element:
                await element.hover()
                await self.page.wait_for_timeout(200)
                return True
            return False
        except Exception as e:
            logger.error(f"Error in execute_hover: {e}")
            return False
    
    async def execute_navigate(self, action: MacroAction) -> bool:
        """Execute a navigation action"""
        try:
            await self.page.goto(action.text or self.macro.url, wait_until='domcontentloaded')
            await self.page.wait_for_timeout(2000)
            return True
        except Exception as e:
            logger.error(f"Error in execute_navigate: {e}")
            return False
    
    def add_playback_listener(self, listener):
        """Add a listener for playback events"""
        self.playback_listeners.append(listener)
    
    def remove_playback_listener(self, listener):
        """Remove a playback listener"""
        if listener in self.playback_listeners:
            self.playback_listeners.remove(listener)
    
    async def notify_listeners(self, data):
        """Notify all listeners of a playback event"""
        for listener in self.playback_listeners:
            try:
                await listener(data)
            except Exception as e:
                logger.error(f"Error notifying playback listener: {e}")
    
    def stop_playback(self):
        """Stop the current playback"""
        self.is_active = False
    
    async def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
        except Exception as e:
            logger.error(f"Error during playback cleanup: {e}")

class MacroRecorderManager:
    """Manages recording sessions and macro storage"""
    
    def __init__(self):
        self.active_sessions: Dict[str, RecordingSession] = {}
        self.active_playbacks: Dict[str, PlaybackSession] = {}
        self.storage = MacroStorage()
    
    async def start_recording_session(self, url: str, macro_name: str = "") -> tuple[bool, str, str]:
        """Start a new recording session"""
        session_id = str(uuid.uuid4())
        
        try:
            session = RecordingSession(session_id, url, macro_name)
            
            # Initialize the browser
            if await session.initialize_browser():
                self.active_sessions[session_id] = session
                logger.info(f"Started recording session {session_id} for {url}")
                return True, session_id, "Recording session started successfully"
            else:
                return False, "", "Failed to initialize browser"
                
        except Exception as e:
            logger.error(f"Failed to start recording session: {e}")
            return False, "", str(e)
    
    async def start_playback_session(self, macro_id: str) -> tuple[bool, str, str]:
        """Start a new playback session"""
        try:
            macro = self.storage.load_macro(macro_id)
            if not macro:
                return False, "", "Macro not found"
            
            playback_id = f"playback_{macro_id}_{int(time.time())}"
            playback = PlaybackSession(playback_id, macro)
            
            # Initialize the browser
            if await playback.initialize_browser():
                self.active_playbacks[playback_id] = playback
                
                # Start playback in background
                asyncio.create_task(self._run_playback(playback_id))
                
                logger.info(f"Started playback session {playback_id} for macro {macro.name}")
                return True, playback_id, "Playback session started successfully"
            else:
                return False, "", "Failed to initialize playback browser"
                
        except Exception as e:
            logger.error(f"Failed to start playback session: {e}")
            return False, "", str(e)
    
    async def _run_playback(self, playback_id: str):
        """Run playback in background"""
        playback = self.active_playbacks.get(playback_id)
        if playback:
            try:
                await playback.start_playback()
            finally:
                await playback.cleanup()
                if playback_id in self.active_playbacks:
                    del self.active_playbacks[playback_id]
    
    def get_session(self, session_id: str) -> Optional[RecordingSession]:
        """Get an active recording session"""
        return self.active_sessions.get(session_id)
    
    def get_playback(self, playback_id: str) -> Optional[PlaybackSession]:
        """Get an active playback session"""
        return self.active_playbacks.get(playback_id)
    
    async def stop_recording_session(self, session_id: str, save_macro: bool = True) -> tuple[bool, Optional[str], str]:
        """Stop a recording session and optionally save as macro"""
        session = self.active_sessions.get(session_id)
        if not session:
            return False, None, "Session not found"
        
        try:
            session.is_active = False
            
            # Convert to macro and save if requested
            macro_id = None
            if save_macro and session.actions:
                macro = session.to_macro()
                if self.storage.save_macro(macro):
                    macro_id = macro.id
                else:
                    return False, None, "Failed to save macro"
            
            # Cleanup browser resources
            await session.cleanup()
            
            # Remove from active sessions
            del self.active_sessions[session_id]
            
            # Log detailed summary of recorded actions
            logger.info(f"Recording session stopped. {len(session.actions)} actions recorded:")
            for i, action in enumerate(session.actions, 1):
                logger.info(f"  {i}. {action.description or action.action_type} - {action.selector}")
            
            message = f"Recording session stopped. {len(session.actions)} actions recorded."
            if macro_id:
                message += f" Macro saved with ID: {macro_id}"
                logger.info(f"Macro saved with ID: {macro_id}")
            
            logger.info(message)
            return True, macro_id, message
            
        except Exception as e:
            logger.error(f"Failed to stop recording session {session_id}: {e}")
            return False, None, str(e)
    
    async def cleanup_all_sessions(self):
        """Cleanup all active sessions (called on shutdown)"""
        # Cleanup recording sessions
        for session_id, session in self.active_sessions.items():
            try:
                await session.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up recording session {session_id}: {e}")
        
        # Cleanup playback sessions
        for playback_id, playback in self.active_playbacks.items():
            try:
                playback.stop_playback()
                await playback.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up playback session {playback_id}: {e}")
        
        self.active_sessions.clear()
        self.active_playbacks.clear()

# Global recorder manager instance
recorder_manager = MacroRecorderManager()