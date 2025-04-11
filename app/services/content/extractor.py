import logging
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


async def extract_content_from_html(html: str, device_type: str) -> Dict[str, Any]:
    """
    Extract content and structure from HTML
    
    Args:
        html: HTML content to analyze
        device_type: Device type (desktop, mobile, tablet)
        
    Returns:
        Dictionary with extracted content
    """
    try:
        logger.info(f"Extracting content from HTML for {device_type}")
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract metadata
        metadata = extract_metadata(soup)
        
        # Extract structure
        structure = extract_structure(soup)
        
        return {
            "metadata": metadata,
            "structure": structure,
            "stats": calculate_content_stats(soup)
        }
    except Exception as e:
        logger.error(f"Error extracting content: {str(e)}")
        return {
            "metadata": {"title": "", "description": ""},
            "structure": {
                "headings": [],
                "navigation": {},
                "main_content": [],
                "cta_buttons": [],
                "forms": []
            },
            "stats": {"word_count": 0, "links_count": 0, "image_count": 0},
            "error": str(e)
        }


def extract_metadata(soup: BeautifulSoup) -> Dict[str, str]:
    """Extract metadata from HTML"""
    title = soup.title.text.strip() if soup.title else ""
    
    # Get meta description
    description = ""
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc:
        description = meta_desc.get('content', '')
    
    # Get OG metadata
    og_title = soup.find('meta', property='og:title')
    og_description = soup.find('meta', property='og:description')
    og_image = soup.find('meta', property='og:image')
    
    if og_title:
        og_title = og_title.get('content', '')
    
    if og_description:
        og_description = og_description.get('content', '')
    
    if og_image:
        og_image = og_image.get('content', '')
    
    # Get canonical URL
    canonical = soup.find('link', rel='canonical')
    canonical_url = canonical.get('href', '') if canonical else ''
    
    return {
        "title": title,
        "description": description,
        "canonical_url": canonical_url,
        "og_title": og_title,
        "og_description": og_description,
        "og_image": og_image
    }


def extract_structure(soup: BeautifulSoup) -> Dict[str, Any]:
    """Extract page structure from HTML"""
    # Extract headings
    headings = extract_headings(soup)
    
    # Extract navigation
    navigation = extract_navigation(soup)
    
    # Extract main content areas
    main_content = extract_main_content(soup)
    
    # Extract CTA buttons
    cta_buttons = extract_cta_buttons(soup)
    
    # Extract forms
    forms = extract_forms(soup)
    
    return {
        "headings": headings,
        "navigation": navigation,
        "main_content": main_content,
        "cta_buttons": cta_buttons,
        "forms": forms
    }


def extract_headings(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """Extract headings from HTML"""
    headings = []
    
    for h_level in range(1, 7):  # h1 to h6
        for heading in soup.find_all(f'h{h_level}'):
            headings.append({
                "level": h_level,
                "text": heading.get_text().strip(),
                "id": heading.get('id', ''),
                "classes": heading.get('class', [])
            })
    
    return headings


def extract_navigation(soup: BeautifulSoup) -> Dict[str, Any]:
    """Extract navigation from HTML"""
    nav_elements = soup.find_all(['nav', 'header', 'menu'])
    
    primary_nav = {}
    nav_items = []
    
    # Find primary navigation
    for nav in nav_elements:
        # Look for navigation items
        links = nav.find_all('a')
        if links:
            for link in links:
                nav_items.append({
                    "text": link.get_text().strip(),
                    "url": link.get('href', ''),
                    "classes": link.get('class', [])
                })
            
            # Assume the first substantial navigation is primary
            if len(links) > 3 and not primary_nav:
                primary_nav = {
                    "items": nav_items,
                    "location": "header" if nav.find_parent('header') else "other",
                    "classes": nav.get('class', [])
                }
                break
    
    # Look for footer navigation
    footer = soup.find('footer')
    footer_nav = []
    
    if footer:
        footer_links = footer.find_all('a')
        for link in footer_links:
            footer_nav.append({
                "text": link.get_text().strip(),
                "url": link.get('href', ''),
                "classes": link.get('class', [])
            })
    
    return {
        "primary": primary_nav,
        "footer": footer_nav,
        "total_links": len(soup.find_all('a'))
    }


def extract_main_content(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """Extract main content areas from HTML"""
    content_areas = []
    
    # Try to find main content by common selectors
    main_selectors = ['main', 'article', '#content', '.content', '[role="main"]']
    
    for selector in main_selectors:
        elements = soup.select(selector)
        for element in elements:
            # Skip if too small
            if len(element.get_text().strip()) < 50:
                continue
                
            content_areas.append({
                "selector": selector,
                "text_length": len(element.get_text().strip()),
                "heading": element.find(['h1', 'h2', 'h3']),
                "paragraphs": len(element.find_all('p')),
                "images": len(element.find_all('img')),
                "classes": element.get('class', [])
            })
    
    return content_areas


def extract_cta_buttons(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """Extract CTA buttons from HTML"""
    cta_buttons = []
    
    # Common CTA selectors
    cta_selectors = [
        'a.btn', 'a.button', 'button', '.cta', '[class*="cta"]', 
        '[class*="btn"]', '[class*="button"]'
    ]
    
    for selector in cta_selectors:
        elements = soup.select(selector)
        for element in elements:
            # Skip if hidden or likely not a CTA
            if 'hidden' in element.get('class', []) or 'disabled' in element.get('class', []):
                continue
                
            # Get CTA text
            text = element.get_text().strip()
            
            # Skip navigation buttons and common non-CTAs
            if text.lower() in ['menu', 'close', 'next', 'prev', 'previous', 'cancel']:
                continue
                
            # Get URL if it's a link
            url = element.get('href', '') if element.name == 'a' else ''
            
            cta_buttons.append({
                "text": text,
                "url": url,
                "element_type": element.name,
                "classes": element.get('class', []),
                "location": identify_element_location(element)
            })
    
    return cta_buttons


def extract_forms(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """Extract forms from HTML"""
    forms = []
    
    for form in soup.find_all('form'):
        # Get all input fields
        inputs = []
        for input_field in form.find_all(['input', 'select', 'textarea']):
            field_type = input_field.get('type', '')
            if field_type in ['hidden', 'submit']:
                continue
                
            inputs.append({
                "name": input_field.get('name', ''),
                "id": input_field.get('id', ''),
                "type": field_type or input_field.name,
                "required": input_field.has_attr('required')
            })
        
        # Extract submit button
        submit_button = form.find(['input[type="submit"]', 'button[type="submit"]', 'button'])
        submit_text = ""
        
        if submit_button:
            if submit_button.name == 'input':
                submit_text = submit_button.get('value', 'Submit')
            else:
                submit_text = submit_button.get_text().strip() or 'Submit'
        
        forms.append({
            "id": form.get('id', ''),
            "action": form.get('action', ''),
            "method": form.get('method', 'get'),
            "classes": form.get('class', []),
            "inputs": inputs,
            "submit_text": submit_text,
            "location": identify_element_location(form)
        })
    
    return forms


def identify_element_location(element) -> str:
    """Identify the location of an element in the page"""
    # Check if element is in header
    if element.find_parent('header'):
        return "header"
    
    # Check if element is in footer
    if element.find_parent('footer'):
        return "footer"
    
    # Check if element is in main content
    if element.find_parent(['main', 'article']):
        return "main_content"
    
    # Check if element is in sidebar
    if element.find_parent(['aside', '.sidebar', '#sidebar']):
        return "sidebar"
    
    # Default to unknown
    return "unknown"


def calculate_content_stats(soup: BeautifulSoup) -> Dict[str, int]:
    """Calculate content statistics"""
    # Count words
    text = soup.get_text()
    words = text.split()
    word_count = len(words)
    
    # Count links
    links_count = len(soup.find_all('a'))
    
    # Count images
    image_count = len(soup.find_all('img'))
    
    # Count buttons
    button_count = len(soup.find_all(['button', 'a.btn', 'a.button', '.btn', '.button']))
    
    # Count form fields
    form_field_count = len(soup.find_all(['input', 'select', 'textarea']))
    
    return {
        "word_count": word_count,
        "links_count": links_count,
        "image_count": image_count,
        "button_count": button_count,
        "form_field_count": form_field_count
    } 