import asyncio
from playwright.async_api import async_playwright
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables 
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("No OpenAI API key found. Add it to your .env file")

# Hardcoded URL and elements to test
URL = "https://www.penguinrandomhouse.com/books/734292/the-very-hungry-caterpillars-peekaboo-easter-by-eric-carle-illustrated-by-eric-carle/9780593750179/"
ELEMENTS_TO_TEST = [
    "Add to Cart Button (Board Book)",
    "Amazon Retailer Link (Board Book)",
    "Barnes & Noble Retailer Link (Board Book)"
]

def ask_gpt4o(prompt, dom_structure=None):
    """Send a prompt to GPT-4o with minimal required content."""
    messages = [
        {
            "role": "system",
            "content": """You are a web testing expert that creates precise CSS selectors.
            Create selectors that include parent context (IDs, form attributes) and are specific to the
            correct book format section (like #collapse2 for Board Book format).
            
            Use proven working selector patterns like:
            - '#collapse2 form[action*="prhcart.php"] button:has-text("Add to Cart")'
            - '#collapse2 .affiliate-buttons a:has-text("Amazon")'
            - '#collapse2 .affiliate-buttons a:has-text("Barnes & Noble")'
            
            Keep selectors as simple as possible while ensuring specificity to the correct section.
            """
        }
    ]
    
    content = prompt
    if dom_structure:
        content += f"\n\nHere is the DOM structure containing the relevant elements:\n\n```\n{dom_structure}\n```"
    
    messages.append({"role": "user", "content": content})
    
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        },
        json={
            "model": "gpt-4o",
            "messages": messages,
            "temperature": 0.1,
        }
    )
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return "Error communicating with OpenAI API"
    
    return response.json()['choices'][0]['message']['content']

async def extract_relevant_dom_structure(url):
    """Extract only the relevant DOM structure for the elements we're looking for."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print(f"Navigating to {url}...")
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(3000)  # Allow JS to finish rendering
        
        # Attempt to dismiss cookie banner
        print("Attempting to dismiss cookie banner...")
        try:
            # Look for common cookie acceptance buttons
            cookie_selectors = [
                'button:has-text("Accept All")', 
                'button:has-text("Accept")', 
                '#truste-consent-button',
                '.cookie-banner button',
                'button:has-text("I Accept")',
                'button:has-text("Agree")'
            ]
            for selector in cookie_selectors:
                button_count = await page.locator(selector).count()
                if button_count > 0:
                    print(f"Found cookie button with selector: {selector}")
                    await page.locator(selector).click()
                    await page.wait_for_timeout(1000)
                    print(f"Clicked cookie banner using selector: {selector}")
                    break
        except Exception as e:
            print(f"Could not dismiss cookie banner: {e}")
        
        # Scroll down to make sure the format sections are visible
        print("Scrolling to see relevant elements...")
        await page.evaluate("""
            () => {
                // Try to find and scroll to the book format section
                const formatSection = document.querySelector('[id^="collapse"]');
                if (formatSection) {
                    formatSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    return 'Scrolled to format section';
                } else {
                    // If format section not found, scroll down a bit anyway
                    window.scrollBy(0, 500);
                    return 'Scrolled down 500px';
                }
            }
        """)
        
        await page.wait_for_timeout(1000)  # Wait after scrolling
        
        # Take a screenshot for reference
        print("Taking screenshot...")
        await page.screenshot(path="page_snapshot.png")
        
        # Find relevant format sections and extract their simplified structure
        format_sections = await page.evaluate("""
            () => {
                // Helper function to get a simplified representation of an element
                function getElementInfo(el, depth = 0, maxDepth = 4) {
                    if (!el || depth > maxDepth) return null;
                    
                    // Basic element info
                    const info = {
                        tag: el.tagName.toLowerCase(),
                        id: el.id || undefined,
                        classes: el.className && typeof el.className === 'string' ? 
                                el.className.split(/\\s+/).filter(c => c) : undefined,
                        text: el.textContent?.trim().slice(0, 30) || undefined
                    };
                    
                    // Add relevant attributes (focus on the ones useful for selectors)
                    const relevantAttrs = ['name', 'type', 'role', 'aria-label', 'action', 'href'];
                    for (const attr of relevantAttrs) {
                        if (el.hasAttribute(attr)) {
                            info[attr] = el.getAttribute(attr);
                        }
                    }
                    
                    // Only include children that might be relevant
                    const relevantChildren = Array.from(el.children)
                        .filter(child => {
                            // Keep elements that might be our targets or their containers
                            const text = child.textContent.toLowerCase();
                            return child.tagName === 'BUTTON' || 
                                   child.tagName === 'A' ||
                                   text.includes('add to cart') ||
                                   text.includes('amazon') ||
                                   text.includes('barnes & noble') ||
                                   (child.className && child.className.includes('affiliate')) ||
                                   child.querySelectorAll('button, a').length > 0;
                        });
                    
                    if (relevantChildren.length > 0) {
                        info.children = relevantChildren
                            .map(child => getElementInfo(child, depth + 1, maxDepth))
                            .filter(c => c !== null);
                    }
                    
                    return info;
                }
                
                // Look for sections that might contain book formats
                const result = {};
                document.querySelectorAll('[id^="collapse"]').forEach(section => {
                    // Check if this section is likely to be relevant
                    const hasAddToCart = Array.from(section.querySelectorAll('button'))
                        .some(btn => btn.textContent.toLowerCase().includes('add to cart'));
                    
                    const hasAmazonLink = Array.from(section.querySelectorAll('a'))
                        .some(a => a.textContent.toLowerCase().includes('amazon'));
                    
                    const hasBarnesNobleLink = Array.from(section.querySelectorAll('a'))
                        .some(a => a.textContent.toLowerCase().includes('barnes & noble'));
                    
                    if (hasAddToCart || hasAmazonLink || hasBarnesNobleLink) {
                        // This section contains at least one of our target elements
                        result[section.id] = {
                            id: section.id,
                            structure: getElementInfo(section),
                            info: {
                                formatName: section.querySelector('h3, h4, .format-name, .title')?.innerText || 'Unknown Format',
                                hasAddToCart,
                                hasAmazonLink,
                                hasBarnesNobleLink
                            }
                        };
                    }
                });
                
                return result;
            }
        """)
        
        # Extract basic info about the book for context
        book_info = await page.evaluate("""
            () => {
                return {
                    title: document.querySelector('h1')?.innerText || 'Unknown Title',
                    author: document.querySelector('.contributor')?.innerText || 'Unknown Author',
                    formats: Array.from(document.querySelectorAll('.format-header')).map(el => el.innerText)
                };
            }
        """)
        
        # Use Playwright's API to more directly locate the elements we're looking for
        # This helps verify that our selectors will work with Playwright
        print("Checking for elements with Playwright directly...")
        
        # Try a few possible selectors for each element
        add_to_cart_selectors = [
  #          '#collapse2 form[action*="prhcart.php"] button:has-text("Add to Cart")',
            '#collapse2 button:has-text("Add to Cart")',
            'button:has-text("Add to Cart")'
        ]
        
        amazon_selectors = [
   #         '#collapse2 .affiliate-buttons a:has-text("Amazon")',
            '#collapse2 a:has-text("Amazon")',
            'a:has-text("Amazon")'
        ]
        
        barnes_noble_selectors = [
   #         '#collapse2 .affiliate-buttons a:has-text("Barnes & Noble")',
            '#collapse2 a:has-text("Barnes & Noble")',
            'a:has-text("Barnes & Noble")'
        ]
        
        working_selectors = {
            "add_to_cart": None,
            "amazon": None, 
            "barnes_noble": None
        }
        
        # Check each selector
        for selector in add_to_cart_selectors:
            count = await page.locator(selector).count()
            if count > 0:
                working_selectors["add_to_cart"] = selector
                print(f"Found Add to Cart button with selector: {selector}")
                break
        
        for selector in amazon_selectors:
            count = await page.locator(selector).count()
            if count > 0:
                working_selectors["amazon"] = selector
                print(f"Found Amazon link with selector: {selector}")
                break
        
        for selector in barnes_noble_selectors:
            count = await page.locator(selector).count()
            if count > 0:
                working_selectors["barnes_noble"] = selector
                print(f"Found Barnes & Noble link with selector: {selector}")
                break
        
        await browser.close()
        
        # Add some context about which section is likely the Board Book format
        board_book_section = None
        for section_id, data in format_sections.items():
            format_name = data['info']['formatName']
            if 'board' in format_name.lower() or 'board book' in format_name.lower():
                board_book_section = section_id
                print(f"Found likely Board Book section: {section_id} - {format_name}")
                break
        
        return {
            "book_info": book_info,
            "format_sections": format_sections,
            "board_book_section": board_book_section,
            "working_selectors": working_selectors
        }

async def main():
    print(f"Starting optimized analysis for: {URL}")
    
    # Extract only the relevant DOM structure
    dom_data = await extract_relevant_dom_structure(URL)
    
    # Convert the DOM data to a string representation
    dom_structure = json.dumps(dom_data, indent=2)
    
    # Create a targeted prompt with context about the page structure
    elements_list = "\n".join([f"{i+1}. {element}" for i, element in enumerate(ELEMENTS_TO_TEST)])
    
    # Include working selectors if found
    working_selectors_info = ""
    if dom_data.get("working_selectors"):
        ws = dom_data["working_selectors"]
        working_selectors_info = "\nPlaywright successfully found these elements with the following selectors:\n"
        if ws.get("add_to_cart"):
            working_selectors_info += f"- Add to Cart: `{ws['add_to_cart']}`\n"
        if ws.get("amazon"):
            working_selectors_info += f"- Amazon link: `{ws['amazon']}`\n"
        if ws.get("barnes_noble"):
            working_selectors_info += f"- Barnes & Noble link: `{ws['barnes_noble']}`\n"
    
    prompt = f"""
    Find precise CSS selectors for these elements on a Penguin Random House book page:

    {elements_list}
    
    Based on the DOM structure I've extracted, the book is "{dom_data['book_info']['title']}" by {dom_data['book_info']['author']}.
    
    The likely Board Book format section has ID: {dom_data['board_book_section'] or 'unknown'}
    {working_selectors_info}
    
    Provide specific selectors that target elements within the correct format section, with this format:
    
    ## Element: [Element Name]
    **Selector:** `[exact CSS selector]`
    
    Use the working selectors from Playwright if found, as these are proven to work.
    Otherwise, create precise selectors that uniquely identify the elements.
    """
    
    # Ask GPT-4o to analyze the DOM structure
    print("\nSending targeted DOM structure to GPT-4o...")
    analysis = ask_gpt4o(prompt, dom_structure)
    
    # Output the results
    print("\n=== SELECTOR ANALYSIS RESULTS ===\n")
    print(analysis)
    
    # Save results to a file
    with open("selector_analysis.txt", "w", encoding="utf-8") as f:
        f.write(f"URL: {URL}\n\n")
        f.write(f"Elements to test:\n{elements_list}\n\n")
        f.write(analysis)
    
    print("\nAnalysis saved to selector_analysis.txt")
    print("Screenshot saved to page_snapshot.png")

if __name__ == "__main__":
    asyncio.run(main())