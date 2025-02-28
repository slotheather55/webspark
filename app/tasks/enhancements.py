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

def generate_enhancement_suggestions(enhancement_id: int) -> bool:
    """
    Generate enhancement suggestions for a specific enhancement ID.
    
    This function is called directly from a background task.
    
    Args:
        enhancement_id: ID of the enhancement record
    
    Returns:
        True if enhancement generation was successful
    """
    try:
        from app.db import crud
        from app.db.session import SessionLocal
        
        logger.info(f"Generating enhancement suggestions for enhancement ID: {enhancement_id}")
        
        # Create a new database session
        db = SessionLocal()
        
        try:
            # Get the enhancement record
            enhancement = crud.enhancements.get_enhancement(db, enhancement_id)
            if not enhancement:
                logger.error(f"Enhancement not found: {enhancement_id}")
                return False
                
            # Get the associated analysis
            analysis = crud.analysis.get_analysis(db, enhancement.analysis_id)
            if not analysis:
                logger.error(f"Analysis not found: {enhancement.analysis_id}")
                return False
                
            # Update enhancement status to processing
            crud.enhancements.update_enhancement_status(db, enhancement_id, "processing")
            
            # Generate recommendations using the service
            recommendations = generate_recommendations(
                analysis_id=enhancement.analysis_id,
                categories=enhancement.categories,
                options={
                    "max_recommendations": 5,
                    "include_rationale": True,
                    "include_implementation": True
                }
            )
            
            # Update enhancement with recommendations
            crud.enhancements.update_enhancement(
                db, 
                enhancement_id, 
                {
                    "status": "completed",
                    "recommendations": recommendations,
                    "completed_at": "NOW()"
                }
            )
            
            logger.info(f"Successfully generated enhancement suggestions for enhancement ID: {enhancement_id}")
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to generate enhancement suggestions: {str(e)}")
        
        # Try to update enhancement status to failed
        try:
            db = SessionLocal()
            crud.enhancements.update_enhancement_status(
                db, 
                enhancement_id, 
                "failed", 
                error=str(e)
            )
            db.close()
        except Exception as update_error:
            logger.error(f"Failed to update enhancement status: {str(update_error)}")
            
        return False 