import logging
import time
import json
import asyncio
from typing import Dict, List, Any, Optional

from celery import shared_task
from app.models.enhancements import EnhancementStatus

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="enhancements.generate_recommendations")
def generate_recommendations(
    self, 
    enhancement_id: int, 
    analysis_id: int,
    categories: List[str],
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate enhancement recommendations based on analysis results
    
    Args:
        enhancement_id: ID of the enhancement record in the database
        analysis_id: ID of the analysis to use for generating recommendations
        categories: List of enhancement categories to generate
        options: Generation options
        
    Returns:
        Dictionary with enhancement results
    """
    try:
        logger.info(f"Generating enhancements for analysis {analysis_id} (ID: {enhancement_id})")
        
        # Simulated enhancement generation for testing
        results = {
            "enhancement_id": enhancement_id,
            "analysis_id": analysis_id,
            "categories": categories,
            "recommendations": {
                "value_proposition": {
                    "title": "Value Proposition Enhancements",
                    "count": 2,
                    "recommendations": [
                        {
                            "id": "vp-1",
                            "title": "Clarify primary value proposition on homepage",
                            "category": "value_proposition",
                            "description": "Current headline is vague",
                            "rationale": "Clear value propositions drive higher conversion rates",
                            "implementation": [
                                "Update the main headline to be more specific",
                                "Add supporting text that reinforces the main benefit"
                            ],
                            "impact": "High",
                            "effort": "Low"
                        },
                        {
                            "id": "vp-2",
                            "title": "Add social proof near key conversion points",
                            "category": "value_proposition",
                            "description": "No social proof visible near CTA buttons",
                            "rationale": "Social proof increases trust and conversions",
                            "implementation": [
                                "Add customer testimonials near major CTA buttons",
                                "Include key metrics or results achieved"
                            ],
                            "impact": "Medium",
                            "effort": "Medium"
                        }
                    ]
                }
            },
            "completed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        
        # Only include requested categories
        filtered_results = {
            **results,
            "recommendations": {
                category: results["recommendations"].get(category, {})
                for category in categories
                if category in results["recommendations"]
            }
        }
        
        return filtered_results
    except Exception as e:
        logger.error(f"Enhancement generation task failed: {str(e)}")
        return {"error": str(e), "enhancement_id": enhancement_id}


@shared_task(bind=True, name="enhancements.generate_implementation_plan")
def generate_implementation_plan(
    self, 
    enhancement_id: int,
    recommendation_id: str,
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate a detailed implementation plan for a specific recommendation
    
    Args:
        enhancement_id: ID of the enhancement record
        recommendation_id: ID of the recommendation to generate a plan for
        options: Generation options
        
    Returns:
        Dictionary with implementation plan
    """
    try:
        logger.info(f"Generating implementation plan for recommendation {recommendation_id}")
        
        # Create an event loop for async operations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Define async task
        async def run_plan_generation():
            try:
                # Get enhancement data
                enhancement_data = await get_enhancement_data(enhancement_id)
                
                if not enhancement_data:
                    raise ValueError(f"Enhancement data not found for ID {enhancement_id}")
                
                # Find specific recommendation
                recommendation = None
                for category in enhancement_data["recommendations"]:
                    for rec in enhancement_data["recommendations"][category]["recommendations"]:
                        if rec["id"] == recommendation_id:
                            recommendation = rec
                            break
                    if recommendation:
                        break
                
                if not recommendation:
                    raise ValueError(f"Recommendation {recommendation_id} not found")
                
                # Generate implementation plan
                from app.services.ai.openai import call_openai_api
                from app.services.ai.prompts import SYSTEM_PROMPTS
                
                # Prepare prompt with recommendation details
                prompt = f"""
                I need a detailed implementation plan for this product enhancement recommendation:
                
                Recommendation ID: {recommendation_id}
                Title: {recommendation["title"]}
                Category: {recommendation["category"]}
                Description: {recommendation["description"]}
                
                Implementation steps from the recommendation:
                {json.dumps(recommendation["implementation"], indent=2)}
                
                Expected impact: {recommendation["impact"]}
                Implementation difficulty: {recommendation["effort"]}
                
                Please provide a detailed implementation plan with phases, tasks, timeline, resources, and success metrics.
                """
                
                # Call OpenAI API
                implementation_plan = await call_openai_api(
                    prompt=prompt,
                    system_prompt=SYSTEM_PROMPTS["enhancement_detail"]
                )
                
                # Store results
                result = {
                    "enhancement_id": enhancement_id,
                    "recommendation_id": recommendation_id,
                    "implementation_plan": implementation_plan,
                    "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                }
                
                # Update the recommendation with the implementation plan
                await update_recommendation_implementation_plan(
                    enhancement_id, 
                    recommendation_id, 
                    implementation_plan
                )
                
                return result
            except Exception as e:
                logger.error(f"Error generating implementation plan: {str(e)}")
                raise
        
        # Run the plan generation
        result = loop.run_until_complete(run_plan_generation())
        loop.close()
        
        return result
    except Exception as e:
        logger.error(f"Implementation plan generation failed: {str(e)}")
        return {"error": str(e), "enhancement_id": enhancement_id, "recommendation_id": recommendation_id}


async def update_enhancement_status(
    enhancement_id: int, 
    status: EnhancementStatus,
    results: Optional[Dict[str, Any]] = None
) -> None:
    """
    Update enhancement status in the database
    
    Args:
        enhancement_id: ID of the enhancement record
        status: New status
        results: Optional results data
    """
    from app.db.crud.enhancements import update_enhancement  # Import here to avoid circular imports
    
    try:
        update_data = {"status": status.value}
        
        if results:
            # If we have results, store them as JSON
            update_data["results"] = json.dumps(results)
            
            # If enhancement generation failed, store error
            if status == EnhancementStatus.FAILED and "error" in results:
                update_data["error"] = results["error"]
        
        await update_enhancement(enhancement_id, update_data)
        logger.info(f"Updated enhancement {enhancement_id} status to {status.value}")
    except Exception as e:
        logger.error(f"Failed to update enhancement status: {str(e)}")


async def get_analysis_data(analysis_id: int) -> Dict[str, Any]:
    """
    Get analysis data from the database
    
    Args:
        analysis_id: ID of the analysis record
        
    Returns:
        Analysis data as dictionary
    """
    from app.db.crud.analysis import get_analysis  # Import here to avoid circular imports
    
    try:
        analysis = await get_analysis(analysis_id)
        
        if not analysis:
            return None
            
        # Parse results JSON
        if analysis.results:
            return json.loads(analysis.results)
        
        return None
    except Exception as e:
        logger.error(f"Error getting analysis data: {str(e)}")
        raise


async def get_enhancement_data(enhancement_id: int) -> Dict[str, Any]:
    """
    Get enhancement data from the database
    
    Args:
        enhancement_id: ID of the enhancement record
        
    Returns:
        Enhancement data as dictionary
    """
    from app.db.crud.enhancements import get_enhancement  # Import here to avoid circular imports
    
    try:
        enhancement = await get_enhancement(enhancement_id)
        
        if not enhancement:
            return None
            
        # Parse results JSON
        if enhancement.results:
            return json.loads(enhancement.results)
        
        return None
    except Exception as e:
        logger.error(f"Error getting enhancement data: {str(e)}")
        raise


def process_recommendations(
    enhancements: Dict[str, Any], 
    enhancement_id: int
) -> Dict[str, Dict[str, Any]]:
    """
    Process and organize enhancement recommendations
    
    Args:
        enhancements: Raw enhancements from OpenAI
        enhancement_id: ID of the enhancement record
        
    Returns:
        Processed recommendations organized by category
    """
    # Ensure each recommendation has a unique ID
    for category, category_data in enhancements.items():
        recs = category_data.get("recommendations", [])
        for i, rec in enumerate(recs):
            if "id" not in rec:
                # Create ID from category + unique identifier
                cat_prefix = category[:2].upper()
                rec_id = f"{cat_prefix}-{uuid.uuid4().hex[:6]}"
                rec["id"] = rec_id
    
    return enhancements


async def update_recommendation_implementation_plan(
    enhancement_id: int,
    recommendation_id: str,
    implementation_plan: Dict[str, Any]
) -> None:
    """
    Update a recommendation with its implementation plan
    
    Args:
        enhancement_id: ID of the enhancement record
        recommendation_id: ID of the recommendation to update
        implementation_plan: Implementation plan data
    """
    from app.db.crud.enhancements import update_enhancement  # Import here to avoid circular imports
    
    try:
        # Get current enhancement data
        enhancement_data = await get_enhancement_data(enhancement_id)
        
        if not enhancement_data:
            logger.error(f"Enhancement {enhancement_id} not found for updating implementation plan")
            return
        
        # Find recommendation and update it
        found = False
        for category in enhancement_data["recommendations"]:
            category_recs = enhancement_data["recommendations"][category]["recommendations"]
            for i, rec in enumerate(category_recs):
                if rec["id"] == recommendation_id:
                    # Add implementation plan to the recommendation
                    enhancement_data["recommendations"][category]["recommendations"][i]["implementation_plan"] = implementation_plan
                    found = True
                    break
            if found:
                break
        
        if not found:
            logger.warning(f"Recommendation {recommendation_id} not found in enhancement {enhancement_id}")
            return
            
        # Update enhancement record with modified data
        await update_enhancement(
            enhancement_id, 
            {"results": json.dumps(enhancement_data)}
        )
        
        logger.info(f"Updated recommendation {recommendation_id} with implementation plan")
    except Exception as e:
        logger.error(f"Error updating recommendation implementation plan: {str(e)}")
        raise 