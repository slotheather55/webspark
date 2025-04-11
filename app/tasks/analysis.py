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
    from app.services.browser.playwright import analyze_website, PlaywrightBrowser
    
    try:
        logger.info(f"Running real-time analysis for URL: {url}")
        
        # Update database status
        db = SessionLocal()
        crud.analysis.update_analysis_status(db, analysis_id, "in_progress")
        db.close()
        
        # Force a real browser analysis - no mock data
        logger.info("Initializing Playwright browser for real data extraction")
        browser = PlaywrightBrowser()
        
        try:
            await browser.initialize()
            logger.info("Playwright browser initialized successfully")
            
            # Extract device types from options
            device_types = options.get("devices", ["desktop"]) if options else ["desktop"]
            check_tealium = options.get("check_tealium", True) if options else True
            
            logger.info(f"Analysis options: device_types={device_types}, check_tealium={check_tealium}")
            
            # Real results container
            results = {
                "url": url,
                "screenshots": {},
                "content_analysis": {},
                "tealium_analysis": None
            }
            
            # Analyze on desktop for Tealium
            logger.info("Creating desktop browser context")
            desktop_context = await browser.browser.new_context(**{
                "viewport": {"width": 1920, "height": 1080},
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36"
            })
            page = await desktop_context.new_page()
            
            # Set timeout for navigation
            page.set_default_timeout(60000)  # 60 seconds
            
            logger.info(f"Navigating to {url} for Tealium analysis")
            try:
                await page.goto(url, wait_until="networkidle")
                logger.info(f"Successfully loaded {url}")
                
                # Extract Tealium data
                if check_tealium:
                    logger.info(f"Extracting Tealium data from {url}")
                    from app.services.browser.playwright import analyze_tealium
                    tealium_data = await analyze_tealium(page)
                    
                    # Store Tealium data
                    results["tealium_analysis"] = tealium_data
                    
                    # Log what we found
                    logger.info(f"Tealium analysis results: detected={tealium_data.get('detected')}, version={tealium_data.get('version')}")
                    if tealium_data.get("tags"):
                        logger.info(f"Found {len(tealium_data['tags'].get('details', []))} tag details")
                else:
                    logger.info("Tealium analysis skipped based on options")
            except Exception as e:
                logger.error(f"Error during page navigation or analysis: {str(e)}", exc_info=True)
                results["error"] = f"Failed to analyze page: {str(e)}"
                
            await desktop_context.close()
            
            # Store real results in database
            logger.info(f"Storing analysis results in database for analysis_id={analysis_id}")
            db = SessionLocal()
            crud.analysis.update_analysis_results(
                db,
                analysis_id,
                tealium_analysis=results["tealium_analysis"]
            )
            crud.analysis.update_analysis_status(db, analysis_id, "completed")
            db.close()
            logger.info(f"Analysis completed successfully for {url}")
            
        except Exception as e:
            logger.error(f"Error during browser analysis: {str(e)}", exc_info=True)
            # Update status with error
            db = SessionLocal()
            crud.analysis.update_analysis_status(db, analysis_id, "failed", error=f"Browser error: {str(e)}")
            db.close()
        finally:
            logger.info("Closing browser")
            await browser.close()
            
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        
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