from typing import Dict, Any, List, Optional
import logging

from app.services.tasks.enhancements import generate_recommendations

logger = logging.getLogger(__name__)

def trigger_enhancement_generation(
    enhancement_id: int,
    analysis_id: int,
    categories: List[str],
    options: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Trigger asynchronous enhancement recommendation generation via Celery
    
    Args:
        enhancement_id: ID of the enhancement record
        analysis_id: ID of the analysis to use
        categories: Categories of enhancements to generate
        options: Generation options
    
    Returns:
        True if enhancement task was scheduled successfully
    """
    try:
        logger.info(f"Triggering enhancement generation for analysis: {analysis_id}")
        
        # Set default options if none provided
        if options is None:
            options = {
                "max_recommendations": 5,
                "include_rationale": True,
                "include_implementation": True
            }
            
        # Dispatch enhancement task to Celery
        generate_recommendations.delay(enhancement_id, analysis_id, categories, options)
        
        return True
    except Exception as e:
        logger.error(f"Failed to trigger enhancement generation: {str(e)}")
        return False 