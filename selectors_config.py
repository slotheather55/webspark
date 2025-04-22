from playwright.sync_api import Page

# A helper to reveal the "prev" arrow on recommendation carousel
def reveal_prev(page: Page):
    page.click("#recommendationCarousel button.slick-next.slick-arrow")
    page.wait_for_selector("#recommendationCarousel button.slick-prev.slick-arrow", state='visible')

# A helper to open the Quick‑View modal for a recommendation
def open_quickview(page: Page):
    # Try clicking the Quick View trigger; supports both aria-label and class selectors
    page.click('div#recommendationCarousel button[aria-label="Quick View"], div#recommendationCarousel .quick-view')
    # Wait for the modal dialog to become visible
    page.wait_for_selector('div.dk-modal-dialog.quickview-modal, div[role="dialog"]', state='visible')

PAGE_TYPE_SELECTORS = {
    # --- Selectors for Product Detail Pages ---
    "Product Detail Page": [
        {
            "description": "Add to Cart Button (Main Format)",
            "selector": 'div[id^="collapse"].in form[action*="prhcart.php"] button:has-text("Add to cart")'
        },
        {
            "description": "Amazon Retailer Link (Main Format)",
            "selector": 'div[id^="collapse"].in .affiliate-buttons a:has-text("Amazon")'
        },
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
            "description": "Quick View Add to Cart Button",
            "preAction": open_quickview,
            "selector": 'div.dk-modal-dialog.quickview-modal form[action*="prhcart.php"] button:has-text("ADD TO CART")'
        },
        {
            "description": "Barnes & Noble Retailer Link (Main Format)",
            "selector": 'div[id^="collapse"].in .affiliate-buttons a:has-text("Barnes & Noble")'
        },
        {
            "description": "Look Inside Link (PDP)",
            "selector": 'a.insight:has-text("Look Inside")'
        },
        {
            "description": "Add to Bookshelf (PDP)",
            "selector": 'div.book-shelf-add'
        },
        # Sequence for interacting with the Quick View modal via carousel
        {
            "description": "Add to Cart via Carousel Quick View",
            "type": "sequence",
            "steps": [
                {
                    "action": "waitFor",
                    "description": "Wait for First Quick View button in Rec Carousel to be visible",
                    "selector": 'div#recommendationCarousel .element-wrapper:first-child .quick-view',
                    "state": "visible",
                    "timeout": 3000
                },
                {
                    "action": "click",
                    "description": "Click First Quick View button in Recommendation Carousel",
                    "selector": 'div#recommendationCarousel .element-wrapper:first-child .quick-view'
                },
                {
                    "action": "waitFor",
                    "description": "Wait for Quick View Modal to appear",
                    "selector": 'div.dk-modal-dialog.quickview-modal, div[role="dialog"]',
                    "state": "visible",
                    "timeout": 10000
                },
                {
                    "action": "click",
                    "description": "Click Add to Cart button inside Quick View Modal",
                    "selector": 'div.dk-modal-dialog.quickview-modal form[action*="prhcart.php"] button:has-text("ADD TO CART")',
                    "check_visibility_after_previous": True
                }
            ]
        }
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
