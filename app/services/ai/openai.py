import json
import logging
from typing import Dict, List, Any, Optional

import openai
from openai import OpenAI

from app.core.config import settings
from app.core.errors import OpenAIError
from app.services.ai.prompts import SYSTEM_PROMPTS

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=settings.OPENAI_API_KEY)


class GPT4oConfig:
    """Configuration for GPT-4o model usage"""
    MODEL = "gpt-4o"
    MAX_TOKENS = 4000
    TEMPERATURE = 0.7
    RESPONSE_FORMAT = {"type": "json_object"}
    TIMEOUT = 120  # seconds


async def generate_content_analysis(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate content analysis using GPT-4o
    """
    try:
        # Prepare the prompt with content data
        prompt = f"""
        I need you to analyze this website's content and structure.
        
        Website URL: {analysis_data['url']}
        
        Metadata:
        - Title: {analysis_data['content_analysis']['desktop']['metadata']['title']}
        - Description: {analysis_data['content_analysis']['desktop']['metadata']['description']}
        
        Heading Structure:
        {json.dumps(analysis_data['content_analysis']['desktop']['structure']['headings'], indent=2)}
        
        Navigation:
        {json.dumps(analysis_data['content_analysis']['desktop']['structure']['navigation'], indent=2)}
        
        Main Content Areas:
        {json.dumps(analysis_data['content_analysis']['desktop']['structure']['main_content'], indent=2)}
        
        CTAs:
        {json.dumps(analysis_data['content_analysis']['desktop']['structure']['cta_buttons'], indent=2)}
        
        Forms:
        {json.dumps(analysis_data['content_analysis']['desktop']['structure']['forms'], indent=2)}
        
        Please analyze the content structure and provide insights on:
        1. Clarity of the value proposition
        2. Content hierarchy and organization
        3. Navigation usability
        4. CTA effectiveness
        5. Overall messaging effectiveness
        """
        
        # Call OpenAI API
        response = await call_openai_api(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPTS["content_analysis"]
        )
        
        return response
    except Exception as e:
        logger.error(f"Error generating content analysis: {str(e)}")
        raise OpenAIError(
            detail="Failed to generate content analysis",
            error_code="content_analysis_error",
            details=str(e)
        )


async def generate_tealium_analysis(tealium_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate Tealium implementation analysis using GPT-4o
    """
    if not tealium_data or not tealium_data.get("detected", False):
        return {
            "summary": "No Tealium implementation detected",
            "analysis": {}
        }
    
    try:
        # Prepare the prompt with Tealium data
        prompt = f"""
        I need you to analyze this Tealium implementation.
        
        Tealium Version: {tealium_data.get('version', 'Unknown')}
        Tealium Profile: {tealium_data.get('profile', 'Unknown')}
        
        Data Layer:
        {json.dumps(tealium_data['data_layer']['variables'], indent=2)}
        
        Data Layer Issues:
        {json.dumps(tealium_data['data_layer']['issues'], indent=2)}
        
        Tags: {tealium_data['tags']['total']} total, {tealium_data['tags']['active']} active, {tealium_data['tags']['inactive']} inactive
        
        Tag Details:
        {json.dumps(tealium_data['tags']['details'], indent=2)}
        
        Tag Issues:
        {json.dumps(tealium_data['tags']['issues'], indent=2)}
        
        Please analyze this Tealium implementation and provide insights on:
        1. Data layer quality and completeness
        2. Tag implementation best practices
        3. Performance implications
        4. Governance issues
        5. Recommendations for optimization
        """
        
        # Call OpenAI API
        response = await call_openai_api(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPTS["tealium_analysis"]
        )
        
        return response
    except Exception as e:
        logger.error(f"Error generating Tealium analysis: {str(e)}")
        raise OpenAIError(
            detail="Failed to generate Tealium analysis",
            error_code="tealium_analysis_error",
            details=str(e)
        )


async def generate_enhancements(
    analysis_data: Dict[str, Any], 
    categories: List[str]
) -> Dict[str, Any]:
    """
    Generate enhancement recommendations using GPT-4o
    """
    try:
        # Prepare the prompt with analysis data
        prompt = f"""
        I need you to analyze this website and provide product enhancement recommendations.
        
        Website URL: {analysis_data['url']}
        
        Content Analysis:
        {json.dumps(analysis_data.get('content_analysis', {}), indent=2)}
        
        Tealium Analysis:
        {json.dumps(analysis_data.get('tealium_analysis', {}), indent=2)}
        
        Please generate specific recommendations for the following categories:
        {', '.join(categories)}
        
        For each recommendation, include:
        1. A clear, specific title
        2. Detailed explanation of the issue/opportunity
        3. Implementation steps
        4. Expected impact (High/Medium/Low)
        5. Implementation difficulty (Easy/Medium/Hard)
        """
        
        # Call OpenAI API
        response = await call_openai_api(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPTS["enhancements"]
        )
        
        # Process and organize the recommendations
        processed_recommendations = process_recommendations(response, categories)
        
        return processed_recommendations
    except Exception as e:
        logger.error(f"Error generating enhancements: {str(e)}")
        raise OpenAIError(
            detail="Failed to generate enhancement recommendations",
            error_code="enhancement_generation_error",
            details=str(e)
        )


async def call_openai_api(
    prompt: str, 
    system_prompt: str, 
    model: str = GPT4oConfig.MODEL,
    temperature: float = GPT4oConfig.TEMPERATURE,
    max_tokens: int = GPT4oConfig.MAX_TOKENS,
    response_format: Dict = GPT4oConfig.RESPONSE_FORMAT
) -> Dict[str, Any]:
    """
    Call OpenAI API with structured prompt
    """
    try:
        logger.info(f"Calling OpenAI API with model {model}")
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format
        )
        
        # Parse and return JSON response
        response_text = response.choices[0].message.content
        return json.loads(response_text)
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {str(e)}")
        raise OpenAIError(
            detail="Error communicating with OpenAI API",
            error_code="openai_api_error",
            details=str(e)
        )


def process_recommendations(
    raw_recommendations: Dict[str, Any], 
    requested_categories: List[str]
) -> Dict[str, Any]:
    """
    Process and organize the raw recommendations from the AI
    """
    processed = {}
    recommendations = raw_recommendations.get("recommendations", [])
    
    # Group recommendations by category
    for category in requested_categories:
        category_recs = [r for r in recommendations if r.get("category") == category]
        
        # Get appropriate title for the category
        category_title_map = {
            "value_proposition": "Value Proposition Enhancements",
            "content_strategy": "Content Strategy Improvements",
            "feature_development": "Product Feature Opportunities",
            "conversion_optimization": "Conversion Rate Optimization",
            "technical_implementation": "Technical Implementation Improvements"
        }
        
        title = category_title_map.get(category, f"{category.replace('_', ' ').title()} Recommendations")
        
        # Add IDs to recommendations if not present
        for i, rec in enumerate(category_recs):
            if "id" not in rec:
                prefix = category[:2]
                rec["id"] = f"{prefix}-{i+1}"
                
        processed[category] = {
            "title": title,
            "count": len(category_recs),
            "recommendations": category_recs
        }
    
    return processed 