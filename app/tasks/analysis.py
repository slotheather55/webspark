from typing import Dict, Any, Optional
import logging
import uuid

from app.services.tasks.analysis import analyze_website

logger = logging.getLogger(__name__)

def trigger_website_analysis(
    analysis_id: uuid.UUID,
    url: str,
    options: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Trigger asynchronous website analysis via Celery
    
    Args:
        analysis_id: ID of the analysis record
        url: URL to analyze
        options: Analysis options
    
    Returns:
        True if analysis task was scheduled successfully
    """
    try:
        logger.info(f"Triggering analysis task for URL: {url}")
        
        # Set default options if none provided
        if options is None:
            options = {
                "device_types": ["desktop", "mobile"],
                "modules": ["screenshots", "content", "tealium"]
            }
            
        # Dispatch analysis task to Celery
        analyze_website.delay(analysis_id, url, options)
        
        return True
    except Exception as e:
        logger.error(f"Failed to trigger analysis: {str(e)}")
        return False 