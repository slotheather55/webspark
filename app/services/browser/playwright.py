import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from playwright.async_api import async_playwright, Page, Browser, BrowserContext

from app.core.errors import URLAccessError, AnalysisProcessError
from app.services.browser.screenshot import process_screenshot

logger = logging.getLogger(__name__)

# Device configurations
DEVICE_CONFIGS = {
    "desktop": {
        "viewport": {"width": 1920, "height": 1080},
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "device_scale_factor": 1
    },
    "tablet": {
        "viewport": {"width": 1024, "height": 768},
        "user_agent": "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
        "device_scale_factor": 2
    },
    "mobile": {
        "viewport": {"width": 375, "height": 812},
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
        "device_scale_factor": 3
    }
}


class PlaywrightBrowser:
    """
    Browser automation service using Playwright
    """
    
    def __init__(self):
        self.browser = None
        self.playwright = None
    
    async def initialize(self):
        """Initialize the browser"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
            logger.info("Playwright browser initialized")
        except Exception as e:
            logger.error(f"Error initializing browser: {str(e)}")
            raise AnalysisProcessError(
                detail="Failed to initialize browser",
                error_code="browser_init_error",
                details=str(e)
            )
    
    async def close(self):
        """Close browser and clean up resources"""
        if self.browser:
            await self.browser.close()
        
        if self.playwright:
            await self.playwright.stop()
        
        logger.info("Playwright browser closed")
    
    async def capture_screenshot(self, url: str, device_type: str = "desktop") -> Dict[str, Any]:
        """
        Capture a screenshot of a webpage
        
        Args:
            url: URL to capture
            device_type: Device type (desktop, mobile, tablet)
            
        Returns:
            Dictionary with screenshot data and metadata
        """
        if device_type not in DEVICE_CONFIGS:
            raise ValueError(f"Invalid device type: {device_type}. Valid types are: {list(DEVICE_CONFIGS.keys())}")
        
        try:
            # Create a new context with the device configuration
            context_options = DEVICE_CONFIGS[device_type]
            context = await self.browser.new_context(**context_options)
            
            # Create a new page
            page = await context.new_page()
            
            # Navigate to the URL
            logger.info(f"Navigating to {url} on {device_type}")
            response = await page.goto(url, wait_until="networkidle", timeout=60000)
            
            if not response:
                raise URLAccessError(
                    detail=f"Failed to navigate to {url}",
                    error_code="navigation_error"
                )
            
            if response.status >= 400:
                raise URLAccessError(
                    detail=f"Error accessing URL: HTTP {response.status}",
                    error_code="http_error"
                )
            
            # Take screenshot
            screenshot_buffer = await page.screenshot(full_page=True)
            
            # Get page dimensions
            dimensions = await page.evaluate("""
                () => {
                    return {
                        width: document.documentElement.scrollWidth,
                        height: document.documentElement.scrollHeight
                    };
                }
            """)
            
            # Get HTML content
            html_content = await page.content()
            
            # Clean up
            await context.close()
            
            # Generate a unique ID for the screenshot
            screenshot_id = f"{device_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Process the screenshot
            processed_screenshot = await process_screenshot({
                "device_type": device_type,
                "dimensions": dimensions,
                "screenshot_buffer": screenshot_buffer
            }, screenshot_id)
            
            return {
                "path": processed_screenshot["storage_path"],
                "thumbnail_path": processed_screenshot["thumbnail_path"],
                "dimensions": dimensions,
                "device_type": device_type,
                "html": html_content
            }
        except URLAccessError:
            # Re-raise URL access errors
            raise
        except Exception as e:
            logger.error(f"Error capturing screenshot: {str(e)}")
            raise AnalysisProcessError(
                detail=f"Error capturing screenshot for {url}",
                error_code="screenshot_error",
                details=str(e)
            )


def get_device_config(device_type: str) -> Dict[str, Any]:
    """Get playwright configuration for a specific device type"""
    if device_type not in DEVICE_CONFIGS:
        raise ValueError(f"Invalid device type: {device_type}")
    
    config = DEVICE_CONFIGS[device_type]
    return {
        "viewport": config["viewport"],
        "user_agent": config["user_agent"],
        "device_scale_factor": config["device_scale_factor"]
    }


async def analyze_website(
    url: str, 
    device_types: List[str] = ["desktop", "tablet", "mobile"],
    check_tealium: bool = True,
    include_subpages: bool = False,
    max_subpages: int = 0,
    custom_scripts: List[str] = []
) -> Dict[str, Any]:
    """
    Analyze a website using Playwright headless browser across different device types
    """
    try:
        results = {
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "screenshots": {},
            "content_analysis": {},
            "tealium_analysis": None if not check_tealium else {}
        }
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            for device_type in device_types:
                try:
                    context_options = get_device_config(device_type)
                    context = await browser.new_context(**context_options)
                    page = await context.new_page()
                    
                    # Set timeout for navigation
                    page.set_default_timeout(60000)  # 60 seconds
                    
                    # Navigate to URL
                    logger.info(f"Analyzing {url} on {device_type}...")
                    await page.goto(url, wait_until="networkidle")
                    
                    # Extract page information
                    results["content_analysis"][device_type] = await extract_page_content(page)
                    
                    # Take screenshot and get dimensions
                    screenshot_info = await take_screenshot(page, device_type)
                    results["screenshots"][device_type] = screenshot_info
                    
                    # Analyze Tealium if requested
                    if check_tealium and device_type == "desktop":  # Only check once
                        results["tealium_analysis"] = await analyze_tealium(page)
                    
                    # Run custom scripts if provided
                    if custom_scripts:
                        for script in custom_scripts:
                            try:
                                await page.evaluate(script)
                            except Exception as e:
                                logger.error(f"Error running custom script: {str(e)}")
                    
                    await context.close()
                except Exception as e:
                    logger.error(f"Error analyzing {url} on {device_type}: {str(e)}")
                    results["content_analysis"][device_type] = {"error": str(e)}
            
            await browser.close()
            
        return results
    except Exception as e:
        logger.error(f"Error during website analysis: {str(e)}")
        raise AnalysisProcessError(
            detail="Failed to analyze website",
            error_code="analysis_process_error",
            details=str(e)
        )


async def extract_page_content(page: Page) -> Dict[str, Any]:
    """Extract content and structure from a page"""
    try:
        # Get page metadata
        title = await page.title()
        
        # Extract meta description
        description = await page.evaluate("""
            () => {
                const metaDesc = document.querySelector('meta[name="description"]');
                return metaDesc ? metaDesc.getAttribute('content') : '';
            }
        """)
        
        # Extract headings structure
        headings = await page.evaluate("""
            () => {
                const headings = {};
                ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'].forEach(tag => {
                    const elements = Array.from(document.querySelectorAll(tag));
                    headings[tag] = elements.map(el => ({
                        text: el.innerText.trim(),
                        visible: el.offsetParent !== null
                    }));
                });
                return headings;
            }
        """)
        
        # Extract navigation structure
        navigation = await page.evaluate("""
            () => {
                const navElements = Array.from(document.querySelectorAll('nav, [role="navigation"]'));
                return navElements.map(nav => {
                    const links = Array.from(nav.querySelectorAll('a'));
                    return {
                        position: nav.getBoundingClientRect(),
                        links: links.map(link => ({
                            text: link.innerText.trim(),
                            href: link.href,
                            visible: link.offsetParent !== null
                        }))
                    };
                });
            }
        """)
        
        # Extract forms
        forms = await page.evaluate("""
            () => {
                const forms = Array.from(document.querySelectorAll('form'));
                return forms.map(form => {
                    const inputs = Array.from(form.querySelectorAll('input, select, textarea'));
                    return {
                        action: form.action,
                        method: form.method,
                        inputs: inputs.map(input => ({
                            type: input.type || input.tagName.toLowerCase(),
                            name: input.name,
                            id: input.id,
                            required: input.required,
                            placeholder: input.placeholder
                        }))
                    };
                });
            }
        """)
        
        # Extract main content areas
        main_content = await page.evaluate("""
            () => {
                const contentElements = [
                    document.querySelector('main'),
                    document.querySelector('[role="main"]'),
                    document.querySelector('#main-content'),
                    document.querySelector('.main-content')
                ].filter(Boolean);
                
                return contentElements.map(el => ({
                    tag: el.tagName.toLowerCase(),
                    id: el.id,
                    class: el.className,
                    text_length: el.innerText.length,
                    child_elements: el.children.length
                }));
            }
        """)
        
        # Extract call-to-action buttons
        cta_buttons = await page.evaluate("""
            () => {
                // Look for elements likely to be CTAs
                const selectors = [
                    'a.btn', 'a.button', 'button', 
                    'a.cta', '[class*="cta"]', 
                    'a.primary', 'button.primary'
                ];
                
                const ctaElements = [];
                selectors.forEach(selector => {
                    Array.from(document.querySelectorAll(selector)).forEach(el => {
                        if (el.offsetParent !== null) {  // Check if visible
                            ctaElements.push({
                                tag: el.tagName.toLowerCase(),
                                text: el.innerText.trim(),
                                position: el.getBoundingClientRect(),
                                classes: el.className
                            });
                        }
                    });
                });
                
                return ctaElements;
            }
        """)
        
        # Measure performance
        performance_metrics = await page.evaluate("""
            () => {
                const perf = window.performance;
                if (!perf) return null;
                
                const timing = perf.timing;
                if (!timing) return null;
                
                return {
                    dns_lookup: timing.domainLookupEnd - timing.domainLookupStart,
                    connection_time: timing.connectEnd - timing.connectStart,
                    ttfb: timing.responseStart - timing.connectEnd,
                    download_time: timing.responseEnd - timing.responseStart,
                    dom_interactive: timing.domInteractive - timing.navigationStart,
                    dom_complete: timing.domComplete - timing.navigationStart,
                    onload_time: timing.loadEventEnd - timing.navigationStart
                };
            }
        """)
        
        return {
            "metadata": {
                "title": title,
                "description": description
            },
            "structure": {
                "headings": headings,
                "navigation": navigation,
                "forms": forms,
                "main_content": main_content,
                "cta_buttons": cta_buttons
            },
            "performance": performance_metrics,
            "viewport": await page.viewport_size()
        }
    except Exception as e:
        logger.error(f"Error extracting page content: {str(e)}")
        return {"error": str(e)}


async def take_screenshot(page: Page, device_type: str) -> Dict[str, Any]:
    """Take a screenshot of the page and return its info"""
    try:
        # Take screenshot (will be processed and saved elsewhere)
        screenshot_buffer = await page.screenshot(full_page=True)
        
        # Get viewport dimensions
        viewport = await page.viewport_size()
        
        # Get page dimensions
        page_dimensions = await page.evaluate("""
            () => {
                return {
                    width: document.documentElement.scrollWidth,
                    height: document.documentElement.scrollHeight
                };
            }
        """)
        
        return {
            "device_type": device_type,
            "viewport": viewport,
            "dimensions": page_dimensions,
            "screenshot_buffer": screenshot_buffer
        }
    except Exception as e:
        logger.error(f"Error taking screenshot: {str(e)}")
        return {"error": str(e)}


async def analyze_tealium(page: Page) -> Dict[str, Any]:
    """Analyze Tealium implementation on a page"""
    try:
        # Check if Tealium is present
        tealium_detected = await page.evaluate("""
            () => {
                return {
                    utag_present: typeof window.utag !== 'undefined',
                    data_layer_present: typeof window.utag_data !== 'undefined'
                };
            }
        """)
        
        if not tealium_detected["utag_present"]:
            return {
                "detected": False,
                "data_layer": {"variables": {}, "issues": []},
                "tags": {"total": 0, "active": 0, "inactive": 0, "vendor_distribution": {}, "details": [], "issues": []},
                "performance": {"recommendations": []}
            }
        
        # Extract Tealium info when present
        tealium_info = await page.evaluate("""
            () => {
                // Extract Tealium version and profile
                let version = null;
                let profile = null;
                
                if (window.utag && window.utag.cfg) {
                    version = window.utag.cfg.v || null;
                    
                    // Try to extract profile from script sources
                    const tealiumScripts = Array.from(document.querySelectorAll('script[src*="tealium"]'));
                    for (const script of tealiumScripts) {
                        const src = script.src;
                        const profileMatch = src.match(/\/([^\/]+)\/utag\.js/);
                        if (profileMatch && profileMatch[1]) {
                            profile = profileMatch[1];
                            break;
                        }
                    }
                }
                
                // Extract data layer
                const dataLayer = window.utag_data ? {...window.utag_data} : {};
                
                // Extract tags
                const tags = [];
                if (window.utag && window.utag.loader && window.utag.loader.cfg) {
                    Object.entries(window.utag.loader.cfg).forEach(([id, config]) => {
                        if (!/^\d+$/.test(id)) return;
                        
                        tags.push({
                            id: id,
                            name: config.name || `Tag ${id}`,
                            active: config.load !== 0,
                            load_rule: config.load_rule || "default"
                        });
                    });
                }
                
                return {
                    version,
                    profile,
                    data_layer: dataLayer,
                    tags
                };
            }
        """)
        
        # Process the data layer
        data_layer_analysis = analyze_data_layer(tealium_info.get("data_layer", {}))
        
        # Process tags
        tags_analysis = analyze_tags(tealium_info.get("tags", []))
        
        # Create performance recommendations
        performance_recommendations = []
        if len(tags_analysis["details"]) > 15:
            performance_recommendations.append({
                "description": "High number of tags detected",
                "impact": "high",
                "implementation": "Consider consolidating tags or implementing server-side tag management"
            })
        
        return {
            "detected": True,
            "version": tealium_info.get("version"),
            "profile": tealium_info.get("profile"),
            "data_layer": data_layer_analysis,
            "tags": tags_analysis,
            "performance": {
                "total_size": None,  # Would require more detailed calculation
                "load_time": None,  # Would require more detailed timing
                "request_count": len(tags_analysis["details"]),
                "page_load_impact": None,  # Would require more detailed analysis
                "recommendations": performance_recommendations
            }
        }
    except Exception as e:
        logger.error(f"Error analyzing Tealium: {str(e)}")
        return {
            "detected": False,
            "error": str(e)
        }


def analyze_data_layer(data_layer: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze Tealium data layer structure and identify issues"""
    variables = data_layer
    issues = []
    
    # Check for naming conventions
    snake_case_count = 0
    camel_case_count = 0
    
    for key in variables.keys():
        if "_" in key:
            snake_case_count += 1
        elif any(c.isupper() for c in key[1:]):
            camel_case_count += 1
    
    if snake_case_count > 0 and camel_case_count > 0:
        # Mixed naming conventions
        issues.append({
            "type": "inconsistent_naming",
            "description": "Mixed naming conventions detected",
            "details": "Variables use a mix of snake_case and camelCase",
            "examples": [],  # Would populate with examples
            "recommendation": "Standardize on a single naming convention"
        })
    
    # Check for common required variables
    required_vars = ["page_name", "page_type", "site_section"]
    missing_vars = [var for var in required_vars if var not in variables and var.replace("_", "") not in variables]
    
    if missing_vars:
        issues.append({
            "type": "missing_variables",
            "description": "Missing recommended data layer variables",
            "details": f"Common variables are missing from data layer",
            "examples": missing_vars,
            "recommendation": "Add these standard variables to your data layer"
        })
    
    return {
        "variables": variables,
        "issues": issues
    }


def analyze_tags(tags: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze Tealium tags and identify issues"""
    active_tags = [tag for tag in tags if tag.get("active", False)]
    inactive_tags = [tag for tag in tags if not tag.get("active", False)]
    
    # Categorize tags (simplified version)
    vendor_distribution = {}
    details = []
    
    for tag in tags:
        tag_name = tag.get("name", "Unknown")
        vendor = "Unknown"
        category = "Unknown"
        
        # Simple vendor detection based on name
        if "google" in tag_name.lower():
            vendor = "Google"
            if "analytics" in tag_name.lower():
                category = "analytics"
            elif "ads" in tag_name.lower() or "adwords" in tag_name.lower():
                category = "advertising"
        elif "facebook" in tag_name.lower() or "fb" in tag_name.lower():
            vendor = "Facebook"
            category = "advertising"
        elif "adobe" in tag_name.lower():
            vendor = "Adobe"
            category = "analytics"
        
        # Update vendor distribution
        vendor_distribution[category] = vendor_distribution.get(category, 0) + 1
        
        # Add to details
        details.append({
            "id": tag.get("id"),
            "name": tag_name,
            "vendor": vendor,
            "category": category,
            "status": "active" if tag.get("active", False) else "inactive",
            "load_time": None,  # Would require actual timing
            "requests": None  # Would require request tracking
        })
    
    # Identify issues
    issues = []
    
    # Check for duplicate analytics tools
    analytics_tools = [tag for tag in details if tag["category"] == "analytics"]
    if len(analytics_tools) > 1:
        issues.append({
            "type": "duplicate_analytics",
            "description": "Multiple analytics tools detected",
            "details": "Running multiple analytics tools may cause performance issues and data discrepancies",
            "recommendation": "Consider consolidating analytics platforms"
        })
    
    return {
        "total": len(tags),
        "active": len(active_tags),
        "inactive": len(inactive_tags),
        "vendor_distribution": vendor_distribution,
        "details": details,
        "issues": issues
    } 