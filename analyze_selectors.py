#!/usr/bin/env python3
"""
analyze_selectors.py

Analyzes the discovered selectors and presents them in an organized way
for easy review and selection.
"""

import json
from pathlib import Path

def analyze_discovered_selectors():
    """Analyze and categorize discovered selectors"""
    
    # Load the discovered selectors
    data_file = Path("data/discovered_selectors.json")
    if not data_file.exists():
        print("No discovered selectors file found. Run discover_selectors.py first.")
        return
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    elements = data['elements']
    
    print("=== DISCOVERED SELECTOR ANALYSIS ===")
    print(f"Total elements found: {len(elements)}")
    print(f"URL: {data['url']}")
    print(f"Discovery time: {data['timestamp']}")
    print()
    
    # Categorize elements by importance
    categories = {
        "Shopping/Commerce": [],
        "Book Preview/Content": [], 
        "Navigation/Search": [],
        "User Account": [],
        "Forms/Input": [],
        "Media/Visual": [],
        "Other Links": []
    }
    
    for element in elements:
        text = element.get('text', '').lower()
        selector = element.get('selector', '')
        element_type = element.get('type', '')
        
        # Categorize based on text content and selector
        if any(word in text for word in ['cart', 'buy', 'purchase', 'shop', 'retailer']):
            categories["Shopping/Commerce"].append(element)
        elif any(word in text for word in ['look inside', 'preview', 'sample', 'read', 'excerpt']):
            categories["Book Preview/Content"].append(element)
        elif any(word in text for word in ['search', 'find', 'nav', 'menu']):
            categories["Navigation/Search"].append(element)
        elif any(word in text for word in ['account', 'login', 'sign']):
            categories["User Account"].append(element)
        elif element_type in ['forms', 'inputs']:
            categories["Forms/Input"].append(element)
        elif element_type in ['images', 'videos', 'audio']:
            categories["Media/Visual"].append(element)
        elif element_type == 'links':
            categories["Other Links"].append(element)
        else:
            # Find the most appropriate category
            if 'bookshelf' in text or 'enlarge' in text or 'cover' in text:
                categories["Book Preview/Content"].append(element)
            elif element_type == 'buttons':
                categories["Shopping/Commerce"].append(element)
            else:
                categories["Other Links"].append(element)
    
    # Print categorized results
    for category, items in categories.items():
        if items:
            print(f"\n{category} ({len(items)} elements)")
            print("-" * 50)
            
            # Show top 10 most relevant items
            for item in items[:10]:
                text = item.get('text', '').strip()[:60]
                selector = item.get('selector', '')
                tag = item.get('tag', '')
                
                print(f"  • {tag.upper()}: {text}")
                print(f"    Selector: {selector}")
                
                # Show key attributes
                attrs = item.get('attributes', {})
                if 'id' in attrs:
                    print(f"    ID: {attrs['id']}")
                if 'class' in attrs:
                    print(f"    Classes: {attrs['class']}")
                print()
    
    # Highlight recommended selectors for inclusion
    print("\n" + "="*60)
    print("RECOMMENDED SELECTORS FOR TRACKING")
    print("="*60)
    
    recommendations = []
    
    # Find key interactive elements
    for element in elements:
        text = element.get('text', '').lower()
        selector = element.get('selector', '')
        
        # High-priority elements
        if any(keyword in text for keyword in [
            'add to cart', 'look inside', 'read sample', 'bookshelf',
            'amazon', 'barnes', 'enlarge'
        ]):
            recommendations.append({
                'priority': 'HIGH',
                'element': element,
                'reason': 'Key shopping/content interaction'
            })
        # Medium-priority elements  
        elif any(keyword in text for keyword in [
            'search', 'account', 'newsletter', 'audio'
        ]):
            recommendations.append({
                'priority': 'MEDIUM', 
                'element': element,
                'reason': 'Important user interaction'
            })
    
    # Sort by priority
    recommendations.sort(key=lambda x: x['priority'])
    
    for rec in recommendations[:15]:  # Top 15 recommendations
        element = rec['element']
        priority = rec['priority']
        reason = rec['reason']
        
        text = element.get('text', '').strip()[:40]
        selector = element.get('selector', '')
        
        print(f"\n[{priority}] {text}")
        print(f"  Selector: {selector}")
        print(f"  Reason: {reason}")

if __name__ == "__main__":
    analyze_discovered_selectors()