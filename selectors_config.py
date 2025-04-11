# Define page-specific selectors for different types of pages
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

    # --- Default / Fallback Selectors (Optional) ---
    "DEFAULT": [
        {
            "description": "Click Main Logo (Default Fallback)",
            "selector": 'div.logo a > img.condensed-logo-image'
        }
    ]
}
