import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

def validate_data_layer(data_layer: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate Tealium data layer structure and values
    
    Args:
        data_layer: Tealium data layer object to validate
        
    Returns:
        Dictionary with validation results
    """
    results = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "recommendations": []
    }
    
    # Check for required fields
    required_fields = ["page_name", "site_section"]
    for field in required_fields:
        if field not in data_layer:
            results["valid"] = False
            results["errors"].append(f"Missing required field: {field}")
    
    # Check for recommended fields
    recommended_fields = ["page_type", "user_id", "visitor_type"]
    for field in recommended_fields:
        if field not in data_layer:
            results["warnings"].append(f"Missing recommended field: {field}")
    
    # Check data types
    if "page_view" in data_layer and not isinstance(data_layer["page_view"], bool):
        results["errors"].append("page_view should be a boolean")
        results["valid"] = False
    
    if "user_id" in data_layer and not isinstance(data_layer["user_id"], str):
        results["errors"].append("user_id should be a string")
        results["valid"] = False
    
    # Add recommendations
    if results["valid"] and not results["warnings"]:
        results["recommendations"].append("Data layer structure looks good!")
    elif results["valid"]:
        results["recommendations"].append("Consider adding the recommended fields for better tracking")
    else:
        results["recommendations"].append("Fix the validation errors to ensure proper tracking")
    
    return results 