import json
import os
from pathlib import Path
from playwright.sync_api import Page

# A helper to reveal the "prev" arrow on recommendation carousel
def reveal_prev(page: Page):
    page.click("#recommendationCarousel button.slick-next.slick-arrow")
    page.wait_for_selector("#recommendationCarousel button.slick-prev.slick-arrow", state='visible')

# Helper function placeholder - Quick View functionality removed
def open_quickview(page: Page):
    print("Quick View functionality has been disabled")
    pass

PAGE_TYPE_SELECTORS = {
    # --- Selectors for Product Detail Pages ---
    # 
    # IMPORTANT: Only include selectors that actually exist on the target page
    # Test new selectors manually before adding to avoid timeouts
    # Use browser dev tools to verify CSS selectors work
    #
    "Product Detail Page": [
        # === CORE SELECTORS - Only elements that generate valid Tealium events ===

        
        # CRITICAL PRIORITY - Core Commerce Actions
        {
            "description": "Add to Cart Button",
            "selector": 'div[id^="collapse"].in form[action*="prhcart.php"] button:has-text("Add to cart")',
            "priority": "CRITICAL",
            "stability": "STABLE"
        },
        {
            "description": "Look Inside Button", 
            "selector": '.product-look-inside.insight',
            "priority": "CRITICAL",
            "stability": "STABLE"
        },
        {
            "description": "Read Sample Button",
            "selector": '.product-read-sample.excerpt-button',
            "priority": "HIGH",
            "stability": "STABLE"
        },
        # HIGH PRIORITY - Retail & Engagement




        {
            "description": "Recommendations Carousel Next Arrow",
            "selector": "#recommendationCarousel button.slick-next.slick-arrow"
        },

        
        {
            "description": "Recommendations Carousel Prev Arrow",
            "preAction": reveal_prev,
            "selector": "#recommendationCarousel button.slick-prev.slick-arrow"
        },
        


        {
                "description": "Amazon Retailer Link (Main Format)",
            "selector": 'div[id^="collapse"].in .affiliate-buttons a:has-text("Amazon")'
        },


    ],

    # --- Selectors for List Detail Pages (like ReadDown) ---
    "List Detail Page": [
        {
            "description": "Add to Cart Button (First Book on List)",
            "selector": 'ol.awesome-list > li:first-child .cart-bttns button:has-text("Add to cart")'
        },
        {
            "description": "Amazon Retailer Link (First Book on List)",
            "selector": 'ol.awesome-list > li:first-child div.buy_clmn:not(.buy_small) a:has-text("Amazon")'
        },
        {
            "description": "Barnes & Noble Retailer Link (First Book on List)",
            "selector": 'ol.awesome-list > li:first-child div.buy_clmn:not(.buy_small) a:has-text("Barnes & Noble")'
        },
        {
            "description": "Add to Bookshelf (First Book on List)",
            "selector": 'ol.awesome-list > li:first-child .book-shelf-add'
        }
    ],

    # --- Default / Fallback Selectors ---
    "DEFAULT": [
        {
            "description": "Click Main Logo (Default Fallback)",
            "selector": 'div.logo a > img.condensed-logo-image'
        }
    ]
}

# Load agent-discovered selectors if available, but only when explicitly requested
# This keeps the agent flow separate from the regular analysis flow
USE_AGENT_SELECTORS = os.environ.get('USE_AGENT_SELECTORS', '').lower() == 'true'
AGENT_SELECTORS_FILE = Path(__file__).parent / "agent_discovered_selectors.json"
AGENT_DISCOVERED_SELECTORS = []

if USE_AGENT_SELECTORS and AGENT_SELECTORS_FILE.exists():
    try:
        with open(AGENT_SELECTORS_FILE, "r", encoding="utf-8") as f:
            AGENT_DISCOVERED_SELECTORS = json.load(f)
        print(f"Loaded {len(AGENT_DISCOVERED_SELECTORS)} agent-discovered selectors")
        
        # Add agent-discovered selectors to appropriate page types
        for selector in AGENT_DISCOVERED_SELECTORS:
            # For simplicity, add to DEFAULT category
            if "DEFAULT" not in PAGE_TYPE_SELECTORS:
                PAGE_TYPE_SELECTORS["DEFAULT"] = []
            PAGE_TYPE_SELECTORS["DEFAULT"].append(selector)
    except Exception as e:
        print(f"Error loading agent-discovered selectors: {e}")
