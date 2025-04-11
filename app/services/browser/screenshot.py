import io
import os
import uuid
from typing import Dict, Optional, Tuple
from pathlib import Path

from PIL import Image

from app.services.storage.cloud import save_to_cloud_storage


async def process_screenshot(
    screenshot_data: Dict,
    analysis_id: str
) -> Dict:
    """
    Process a screenshot:
    1. Save original to cloud storage
    2. Create thumbnail
    3. Save thumbnail to cloud storage
    4. Return paths and dimensions
    """
    if "error" in screenshot_data:
        return {"error": screenshot_data["error"]}
    
    device_type = screenshot_data["device_type"]
    screenshot_buffer = screenshot_data.get("screenshot_buffer")
    
    if not screenshot_buffer:
        return {"error": "No screenshot data found"}
    
    # Generate a unique filename
    filename = f"{analysis_id}_{device_type}_{uuid.uuid4().hex}.png"
    thumbnail_filename = f"{analysis_id}_{device_type}_thumb_{uuid.uuid4().hex}.png"
    
    # Create thumbnail
    thumbnail_buffer = create_thumbnail(screenshot_buffer)
    
    # Save original screenshot to cloud storage
    screenshot_path = f"screenshots/{analysis_id}/{filename}"
    await save_to_cloud_storage(screenshot_buffer, screenshot_path)
    
    # Save thumbnail to cloud storage
    thumbnail_path = f"screenshots/{analysis_id}/thumbnails/{thumbnail_filename}"
    await save_to_cloud_storage(thumbnail_buffer, thumbnail_path)
    
    # Extract dimensions
    dimensions = screenshot_data.get("dimensions", {})
    viewport = screenshot_data.get("viewport", {})
    
    return {
        "device_type": device_type,
        "storage_path": screenshot_path,
        "thumbnail_path": thumbnail_path,
        "width": dimensions.get("width") or viewport.get("width"),
        "height": dimensions.get("height") or viewport.get("height")
    }


def create_thumbnail(screenshot_buffer: bytes, max_width: int = 300) -> bytes:
    """Create a thumbnail of the screenshot"""
    try:
        img = Image.open(io.BytesIO(screenshot_buffer))
        
        # Calculate new height while maintaining aspect ratio
        width, height = img.size
        ratio = max_width / width
        new_height = int(height * ratio)
        
        # Resize image
        img = img.resize((max_width, new_height), Image.LANCZOS)
        
        # Save to bytes buffer
        output = io.BytesIO()
        img.save(output, format="PNG")
        return output.getvalue()
    except Exception as e:
        # Return original if there's an error
        return screenshot_buffer


async def save_screenshot_locally(
    screenshot_buffer: bytes, 
    filename: str,
    directory: str = "temp_screenshots"
) -> str:
    """Save a screenshot to local filesystem (for development/testing)"""
    # Create directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)
    
    # Generate full path
    filepath = os.path.join(directory, filename)
    
    # Write file
    with open(filepath, "wb") as f:
        f.write(screenshot_buffer)
    
    return filepath 