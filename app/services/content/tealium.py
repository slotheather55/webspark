import logging
import re
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


async def analyze_tealium_implementation(html: str, page_url: str) -> Dict[str, Any]:
    """
    Analyze Tealium tag management implementation from HTML content
    
    Args:
        html: HTML content to analyze
        page_url: URL of the page being analyzed
        
    Returns:
        Dictionary with Tealium analysis data
    """
    try:
        logger.info(f"Analyzing Tealium implementation for {page_url}")
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check if Tealium is present
        tealium_detected = detect_tealium(soup, html)
        
        if not tealium_detected:
            logger.info(f"No Tealium implementation detected for {page_url}")
            return {
                "detected": False,
                "version": None,
                "profile": None,
                "environment": None,
                "data_layer": {
                    "variables": {},
                    "issues": []
                },
                "tags": {
                    "total": 0,
                    "active": 0,
                    "inactive": 0,
                    "details": [],
                    "issues": []
                }
            }
        
        # Extract Tealium configuration
        tealium_config = extract_tealium_config(soup, html)
        
        # Extract data layer
        data_layer = extract_data_layer(soup, html)
        
        # Extract tag information
        tags = extract_tags(soup, html)
        
        return {
            "detected": True,
            "version": tealium_config.get("version", "Unknown"),
            "profile": tealium_config.get("profile", "Unknown"),
            "environment": tealium_config.get("environment", "Unknown"),
            "data_layer": data_layer,
            "tags": tags
        }
    except Exception as e:
        logger.error(f"Error analyzing Tealium implementation: {str(e)}")
        return {
            "detected": False,
            "error": str(e)
        }


def detect_tealium(soup: BeautifulSoup, html: str) -> bool:
    """Detect if Tealium is implemented on the page"""
    # Check for Tealium script tags
    tealium_scripts = soup.find_all('script', src=lambda x: x and ('tealium' in x.lower() or 'tiq' in x.lower() or 'utag' in x.lower()))
    
    # Check for Tealium variables in inline scripts
    utag_pattern = re.compile(r'utag|tealium', re.IGNORECASE)
    inline_tealium = any(utag_pattern.search(script.string) for script in soup.find_all('script') if script.string)
    
    # Check for Tealium in HTML comments
    tealium_comments = re.search(r'<!--\s*tealium|\bute?tag\b', html, re.IGNORECASE)
    
    return bool(tealium_scripts or inline_tealium or tealium_comments)


def extract_tealium_config(soup: BeautifulSoup, html: str) -> Dict[str, str]:
    """Extract Tealium configuration details"""
    config = {
        "version": "Unknown",
        "profile": "Unknown",
        "environment": "Unknown"
    }
    
    # Try to find Tealium version from script tags
    tealium_scripts = soup.find_all('script', src=lambda x: x and ('tealium' in x.lower() or 'utag' in x.lower()))
    
    for script in tealium_scripts:
        src = script.get('src', '')
        
        # Extract profile from script src
        profile_match = re.search(r'/([^/]+)/utag\.js', src)
        if profile_match:
            config["profile"] = profile_match.group(1)
        
        # Extract environment from script src
        if 'prod' in src or 'production' in src:
            config["environment"] = "production"
        elif 'dev' in src or 'development' in src:
            config["environment"] = "development"
        elif 'qa' in src or 'test' in src:
            config["environment"] = "test"
    
    # Try to find Tealium version from inline scripts
    for script in soup.find_all('script'):
        if script.string:
            # Look for version info
            version_match = re.search(r'tealium.*?(\d+\.\d+\.\d+)', script.string, re.IGNORECASE)
            if version_match:
                config["version"] = version_match.group(1)
                
            # Look for profile info
            profile_match = re.search(r'utag_data\.tealium_profile\s*=\s*[\'"]([^\'"]+)[\'"]', script.string)
            if profile_match:
                config["profile"] = profile_match.group(1)
    
    return config


def extract_data_layer(soup: BeautifulSoup, html: str) -> Dict[str, Any]:
    """Extract Tealium data layer variables"""
    data_layer = {
        "variables": {},
        "issues": []
    }
    
    # Look for data layer in inline scripts
    utag_data_pattern = re.compile(r'var\s+utag_data\s*=\s*({[^;]+});', re.DOTALL)
    
    for script in soup.find_all('script'):
        if script.string:
            # Check for utag_data object
            utag_data_match = utag_data_pattern.search(script.string)
            if utag_data_match:
                # We found the data layer, but we can't safely eval it
                # Just extract individual variables using regex
                data_layer_str = utag_data_match.group(1)
                
                # Extract variable names and values
                var_matches = re.finditer(r'[\'"]([\w\.\-]+)[\'"]:\s*[\'"]?([^\'",:}]+)[\'"]?', data_layer_str)
                
                for match in var_matches:
                    key = match.group(1)
                    value = match.group(2).strip('"\'')
                    data_layer["variables"][key] = value
    
    # Check for common issues in data layer
    if not data_layer["variables"]:
        data_layer["issues"].append({
            "issue": "No data layer detected or empty data layer",
            "severity": "High",
            "description": "Tealium implementation requires a data layer with required variables"
        })
    else:
        # Check for common required variables
        required_vars = ["page_name", "site_section", "page_type"]
        for var in required_vars:
            if var not in data_layer["variables"]:
                data_layer["issues"].append({
                    "issue": f"Missing recommended variable: {var}",
                    "severity": "Medium",
                    "description": f"The {var} variable is recommended for analytics tracking"
                })
    
    return data_layer


def extract_tags(soup: BeautifulSoup, html: str) -> Dict[str, Any]:
    """Extract information about implemented tags"""
    tags = {
        "total": 0,
        "active": 0,
        "inactive": 0,
        "details": [],
        "issues": []
    }
    
    # Look for tag information in inline scripts
    utag_list_pattern = re.compile(r'utag\.loader\.cfg\s*=\s*({[^;]+});', re.DOTALL)
    
    for script in soup.find_all('script'):
        if script.string:
            # Check for utag.loader.cfg object
            utag_list_match = utag_list_pattern.search(script.string)
            if utag_list_match:
                # Found tag configuration
                tag_config_str = utag_list_match.group(1)
                
                # Extract tag IDs using regex
                tag_matches = re.finditer(r'[\'"]([\w\.\-]+)[\'"]:\s*{([^}]+)}', tag_config_str)
                
                for match in tag_matches:
                    tag_id = match.group(1)
                    tag_config = match.group(2)
                    
                    # Check if tag is active
                    is_active = 'load:"0"' not in tag_config
                    
                    # Identify tag type based on ID
                    tag_type = identify_tag_type(tag_id)
                    
                    tags["details"].append({
                        "id": tag_id,
                        "type": tag_type,
                        "active": is_active
                    })
                    
                    if is_active:
                        tags["active"] += 1
                    else:
                        tags["inactive"] += 1
    
    tags["total"] = tags["active"] + tags["inactive"]
    
    # Check for common tag implementation issues
    if tags["total"] == 0:
        tags["issues"].append({
            "issue": "No tags detected",
            "severity": "High",
            "description": "Tealium implementation has no tags configured"
        })
    elif tags["active"] == 0:
        tags["issues"].append({
            "issue": "No active tags",
            "severity": "High",
            "description": "All tags are inactive"
        })
    
    # Look for basic analytics tags
    required_tag_types = ["analytics", "google_analytics", "adobe_analytics"]
    has_analytics = any(tag["type"] in required_tag_types for tag in tags["details"])
    
    if not has_analytics:
        tags["issues"].append({
            "issue": "No analytics tags found",
            "severity": "Medium",
            "description": "No primary analytics tool detected"
        })
    
    return tags


def identify_tag_type(tag_id: str) -> str:
    """Identify tag type based on ID"""
    tag_id = tag_id.lower()
    
    tag_mapping = {
        "ga": "google_analytics",
        "google": "google_analytics",
        "adobe": "adobe_analytics",
        "omniture": "adobe_analytics",
        "sitecatalyst": "adobe_analytics",
        "floodlight": "google_floodlight",
        "doubleclick": "google_doubleclick",
        "facebook": "facebook_pixel",
        "fb": "facebook_pixel",
        "twitter": "twitter_pixel",
        "linkedin": "linkedin_pixel",
        "bing": "bing_ads",
        "gtm": "google_tag_manager",
        "optimizely": "optimizely",
        "hotjar": "hotjar",
        "crazyegg": "crazyegg",
        "clicktale": "clicktale",
        "sessioncam": "sessioncam",
        "medallia": "medallia",
        "qualtrics": "qualtrics"
    }
    
    for key, value in tag_mapping.items():
        if key in tag_id:
            return value
    
    return "other" 