# app/tasks/analysis.py
from typing import Dict, Any, Optional
import logging
import uuid
import asyncio
from fastapi import BackgroundTasks

logger = logging.getLogger(__name__)

async def run_analysis_task(analysis_id: uuid.UUID, url: str, options: Optional[Dict[str, Any]] = None):
    """
    Run the analysis task directly (without Celery)
    """
    from app.db.session import SessionLocal
    from app.db import crud
    from app.services.browser.playwright import analyze_tealium
    from playwright.async_api import async_playwright
    
    try:
        logger.info(f"Starting REAL analysis for URL: {url} with options: {options}")
        
        # Update database status
        db = SessionLocal()
        crud.analysis.update_analysis_status(db, analysis_id, "in_progress")
        db.close()
        
        # Run real browser analysis - NO MOCK DATA!
        logger.info(f"Initializing browser for {url}")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                logger.info(f"Browser launched successfully for {url}")
                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36"
                )
                page = await context.new_page()
                
                # Navigate to the URL
                logger.info(f"Navigating to {url}")
                await page.goto(url, wait_until="networkidle", timeout=60000)
                logger.info(f"Navigation to {url} complete")
                
                # Extract Tealium data
                logger.info(f"Analyzing Tealium implementation on {url}")
                tealium_data = await analyze_tealium(page)
                logger.info(f"Tealium analysis complete: {tealium_data.get('detected')}")
                
                # Print detailed info about what was found
                if tealium_data.get("detected"):
                    logger.info(f"Detected Tealium version: {tealium_data.get('version')}")
                    tag_details = tealium_data.get("tags", {}).get("details", [])
                    logger.info(f"Found {len(tag_details)} tag details")
                    for i, tag in enumerate(tag_details[:5]):  # Log first 5 tags
                        logger.info(f"Tag {i+1}: {tag.get('id')} - {tag.get('name')} - {tag.get('status')}")
                
                # Close browser resources
                await context.close()
                
                # Update database with results
                db = SessionLocal()
                logger.info(f"Updating database with Tealium analysis results for {analysis_id}")
                crud.analysis.update_analysis_results(
                    db,
                    analysis_id,
                    tealium_analysis=tealium_data
                )
                crud.analysis.update_analysis_status(db, analysis_id, "completed")
                db.close()
                logger.info(f"Analysis for {url} completed successfully")
                
            except Exception as e:
                logger.error(f"Error during browser analysis: {str(e)}", exc_info=True)
                # Update status to failed
                db = SessionLocal()
                crud.analysis.update_analysis_status(db, analysis_id, "failed", error=str(e))
                db.close()
            finally:
                await browser.close()
                logger.info(f"Browser closed for {url}")
        
    except Exception as e:
        logger.error(f"Analysis failed with exception: {str(e)}", exc_info=True)
        
        # Update status to failed
        db = SessionLocal()
        try:
            crud.analysis.update_analysis_status(db, analysis_id, "failed", error=str(e))
        finally:
            db.close()

def trigger_website_analysis(
    background_tasks: BackgroundTasks,
    analysis_id: uuid.UUID,
    url: str,
    options: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Trigger website analysis as a background task
    """
    try:
        logger.info(f"Triggering analysis task for URL: {url}")
        
        # Add the task to background tasks
        background_tasks.add_task(
            run_analysis_task,
            analysis_id=analysis_id,
            url=url,
            options=options
        )
        
        return True
    except Exception as e:
        logger.error(f"Failed to trigger analysis: {str(e)}")
        return False


# Keep the existing analyze_website function for backwards compatibility with Celery
# but it's not used in our implementation
@asyncio.coroutine
async def analyze_website(
    analysis_id: uuid.UUID, 
    url: str,
    options: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Legacy function for Celery tasks - redirects to the new implementation
    """
    try:
        logger.info(f"Legacy analyze_website called for {url} - redirecting to new implementation")
        await run_analysis_task(analysis_id, url, options)
        return {"status": "redirected_to_new_implementation"}
    except Exception as e:
        logger.error(f"Error in legacy analyze_website: {str(e)}")
        return {"error": str(e), "analysis_id": analysis_id}


async def update_analysis_status(
    analysis_id: uuid.UUID, 
    status: str,
    results: Optional[Dict[str, Any]] = None
) -> None:
    """
    Update analysis status in the database
    
    Args:
        analysis_id: ID of the analysis record
        status: New status
        results: Optional results data
    """
    from app.db.crud.analysis import update_analysis  # Import here to avoid circular imports
    
    try:
        update_data = {"status": status}
        
        if results:
            # If analysis failed, store error
            if status == "failed" and "error" in results:
                update_data["error"] = results["error"]
        
        await update_analysis(analysis_id, update_data)
        logger.info(f"Updated analysis {analysis_id} status to {status}")
    except Exception as e:
        logger.error(f"Failed to update analysis status: {str(e)}")