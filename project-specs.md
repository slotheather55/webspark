# Product Manager Enhancer - Backend Specifications

## Overview

This document outlines the backend specifications for the Product Manager Enhancer application, which allows users to analyze websites and generate AI-powered product improvement recommendations. The backend will be developed in Python and will leverage OpenAI's GPT-4o model for AI analysis.

## Tech Stack

- **Language**: Python 3.9+
- **Web Framework**: FastAPI
- **LLM Integration**: OpenAI API (GPT-4o model)
- **Web Scraping**: Playwright
- **Database**: PostgreSQL (for storing analysis history)
- **Authentication**: JWT-based authentication
- **Caching**: Redis (for caching analysis results)
- **Queue System**: Celery (for handling long-running tasks)

## Core Features & Implementation Details

### 1. Website Analysis Engine

#### Headless Browser Analysis

The backend will use Playwright to visit and analyze websites through a headless browser.

```python
# Example core function
async def analyze_website(url: str, device_types: List[str] = ["desktop", "tablet", "mobile"]):
    """
    Analyze a website using Playwright headless browser across different device types
    """
    results = {
        "url": url,
        "timestamp": datetime.now().isoformat(),
        "screenshots": {},
        "content_analysis": {},
        "tag_detection": {}
    }
    
    async with async_playwright() as p:
        for device_type in device_types:
            browser = await p.chromium.launch()
            # Use appropriate device emulation based on device_type
            context = await browser.new_context(**get_device_config(device_type))
            page = await context.new_page()
            
            # Navigate to URL with timeout
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                
                # Take screenshots
                screenshot = await page.screenshot()
                results["screenshots"][device_type] = save_screenshot(screenshot, url, device_type)
                
                # Extract page content
                content = await extract_page_content(page)
                results["content_analysis"][device_type] = content
                
                # Analyze tag management implementation
                tag_data = await analyze_tags(page)
                results["tag_detection"] = tag_data
                
                await browser.close()
            except Exception as e:
                results["errors"] = f"Error analyzing {url} on {device_type}: {str(e)}"
                
    return results
```

#### Features

1. **Multi-Device Analysis**: 
   - Emulate desktop, tablet, and mobile devices
   - Capture responsive design issues
   - Store viewport size information

2. **Screenshot Capture**:
   - Take full-page screenshots for each device type
   - Store screenshots in cloud storage with unique identifiers
   - Generate thumbnail versions for preview

3. **Content Extraction**:
   - Extract main content elements (headings, paragraphs, CTAs)
   - Extract navigation structure
   - Identify UI components and their hierarchy
   - Detect forms and input fields

4. **Performance Analysis**:
   - Measure page load time
   - Track critical rendering path
   - Identify resource-heavy elements

### 2. Tealium & Tag Management Analysis

This module will analyze tag management implementations with a focus on Tealium.

```python
# Example core function
async def analyze_tags(page):
    """Analyze tag management implementation with focus on Tealium"""
    
    # Inject tag detection script
    detection_script = load_asset("tag_detection_script.js")
    result = await page.evaluate(detection_script)
    
    # Analyze data layer
    data_layer = await page.evaluate("() => { return window.utag_data || {} }")
    
    # Extract tags and vendor information
    tags = await extract_tag_information(page)
    
    # Measure performance impact
    perf_impact = await measure_tag_performance(page)
    
    return {
        "detected_tags": result,
        "data_layer": data_layer,
        "tags": tags,
        "performance_impact": perf_impact
    }
```

#### Features

1. **Data Layer Analysis**:
   - Detect and extract data layer variables
   - Identify variable naming conventions and inconsistencies
   - Map data layer variables to common analytics standards

2. **Tag Detection**:
   - Identify installed tags (GA, Facebook, etc.)
   - Detect tag management solutions (Tealium, GTM)
   - Analyze tag configuration and loading patterns

3. **Implementation Quality Assessment**:
   - Check for tag loading efficiency
   - Identify redundant or conflicting tags
   - Measure performance impact of tag implementation

4. **Event Tracking Analysis**:
   - Detect configured event listeners
   - Map events to data layer variables
   - Identify tracking gaps in user journey

### 3. AI Analysis & Enhancement Generation

This module leverages the OpenAI GPT-4o model to analyze the website data and generate improvement recommendations.

```python
# Example core function
async def generate_enhancements(analysis_results: dict, enhancement_categories: List[str]):
    """
    Generate AI-powered enhancement recommendations based on analysis results
    """
    
    # Prepare prompt with analysis results
    prompt = prepare_enhancement_prompt(analysis_results, enhancement_categories)
    
    # Call OpenAI API with structured prompt
    response = await openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=4000,
        response_format={"type": "json_object"}
    )
    
    # Parse and structure the recommendations
    enhancement_data = json.loads(response.choices[0].message.content)
    
    # Post-process and validate the recommendations
    processed_data = post_process_recommendations(enhancement_data)
    
    return processed_data
```

#### Features

1. **Enhancement Categories**:
   - Value Proposition Improvements
   - Content Strategy Recommendations
   - Feature Enhancement Opportunities
   - Conversion Rate Optimization
   - Technical Implementation Improvements

2. **AI Prompt Engineering**:
   - Specialized prompts for each category
   - Inclusion of context from website analysis
   - Competitive analysis suggestions
   - Industry-specific recommendations

3. **Response Formatting**:
   - Structured JSON responses
   - Prioritized recommendations
   - Implementation difficulty scoring
   - Expected impact assessment

4. **Recommendation Quality Control**:
   - Filter generic recommendations
   - Ensure relevance to analyzed website
   - Generate actionable, specific suggestions
   - Include implementation guidance

### 4. API Endpoints

The backend will expose the following RESTful API endpoints:

#### Core Analysis Endpoints

```
POST /api/analyze
    Request: { url: string, options: AnalysisOptions }
    Response: { analysisId: string, status: "pending" }

GET /api/analysis/{analysisId}
    Response: { status: string, results?: AnalysisResults, error?: string }

GET /api/analysis/{analysisId}/screenshots
    Response: { screenshots: { [deviceType: string]: string } }

GET /api/analysis/{analysisId}/enhancements
    Response: { categories: EnhancementCategory[] }

GET /api/analysis/history
    Response: { analyses: AnalysisSummary[] }
```

#### Tealium Specific Endpoints

```
GET /api/analysis/{analysisId}/tealium
    Response: { 
        dataLayer: object,
        tags: TagInfo[],
        events: EventMapping[],
        performance: PerformanceMetrics
    }

POST /api/tealium/validate
    Request: { dataLayer: object, expectedSchema: object }
    Response: { valid: boolean, issues: ValidationIssue[] }
```

#### Enhancement Generation Endpoints

```
POST /api/enhancements/generate
    Request: { analysisId: string, categories: string[] }
    Response: { enhancementId: string, status: "pending" }

GET /api/enhancements/{enhancementId}
    Response: { status: string, recommendations: Recommendation[] }

POST /api/enhancements/export
    Request: { enhancementId: string, format: "pdf"|"docx"|"html" }
    Response: { downloadUrl: string }
```

### 5. AI Model Integration (OpenAI GPT-4o)

The backend will integrate with OpenAI's GPT-4o model for generating intelligent analyses and recommendations.

#### System Prompts

Different specialized system prompts will be used for each analysis type:

1. **Content Analysis Prompt**: 
```
You are an expert product manager and UX specialist. Analyze the website content provided and identify:
1. Key strengths and weaknesses in the current value proposition
2. Clarity and effectiveness of messaging
3. User journey friction points
4. Content structure and organization issues
5. Competitive positioning opportunities

Format your response as JSON with the following structure:
{
  "content_analysis": {
    "value_proposition": { "strengths": [], "weaknesses": [] },
    "messaging": { "effective_elements": [], "improvement_areas": [] },
    "user_journey": { "friction_points": [] },
    "content_structure": { "issues": [], "recommendations": [] },
    "competitive_positioning": { "opportunities": [] }
  }
}
```

2. **Tealium Analysis Prompt**:
```
You are an expert analytics and tag management consultant specializing in Tealium implementations. Analyze the provided tag management data and identify:
1. Data layer quality and completeness
2. Implementation best practices adherence
3. Tag loading performance issues
4. Data governance concerns
5. Optimization opportunities

Format your response as JSON with the following structure:
{
  "tealium_analysis": {
    "data_layer": { "strengths": [], "issues": [], "recommendations": [] },
    "tag_implementation": { "conforming_elements": [], "issues": [], "recommendations": [] },
    "performance": { "metrics": {}, "impact_assessment": "", "optimization_steps": [] },
    "governance": { "issues": [], "recommendations": [] }
  }
}
```

3. **Enhancement Recommendations Prompt**:
```
You are a strategic product innovation consultant. Based on the website analysis provided, generate specific, actionable product enhancement recommendations in the following categories:
1. Value proposition clarification and improvement
2. Content strategy optimization
3. Feature development opportunities
4. Conversion rate optimization
5. Technical implementation improvements

For each recommendation:
- Provide a clear, specific title
- Include detailed explanation of the issue
- Offer concrete implementation steps
- Assess expected impact (High/Medium/Low)
- Estimate implementation difficulty (Easy/Medium/Hard)

Format your response as JSON with the following structure:
{
  "recommendations": [
    {
      "category": "value_proposition|content_strategy|feature_development|conversion_optimization|technical_implementation",
      "title": "Specific recommendation title",
      "explanation": "Detailed explanation of the issue and opportunity",
      "implementation_steps": ["Step 1", "Step 2", ...],
      "expected_impact": "High|Medium|Low",
      "implementation_difficulty": "Easy|Medium|Hard"
    },
    ...
  ]
}
```

#### Prompt Construction

The backend will construct detailed prompts that include:

1. Extracted website content
2. Screenshots descriptions
3. Tag management data
4. Competitive context (if available)
5. User-specified focus areas

#### Response Processing

- Parse and validate JSON responses
- Handle potential model hallucinations or inaccuracies
- Structure responses to match frontend display requirements
- Cache processed results for performance

### 6. Asynchronous Task Processing

Long-running tasks will be handled asynchronously using Celery.

```python
# Example task definition
@celery_app.task(bind=True, max_retries=3)
def analyze_website_task(self, url, options):
    try:
        # Run the analysis
        analysis_results = run_analysis(url, options)
        
        # Store results in database
        analysis_id = store_analysis_results(analysis_results)
        
        # Update task status
        update_task_status(analysis_id, "completed", analysis_results)
        
        return analysis_id
    except Exception as e:
        # Retry on failure
        self.retry(exc=e, countdown=60 * 5)  # Retry after 5 minutes
```

#### Features

1. **Task Queue Management**:
   - Prioritize tasks based on user tier
   - Limit concurrent analyses per user
   - Implement retry logic for failed tasks

2. **Progress Tracking**:
   - Provide detailed progress updates
   - Track subtask completion
   - Estimate remaining time

3. **Error Handling**:
   - Graceful failure recovery
   - Detailed error reporting
   - Automated retry for transient issues

4. **Resource Management**:
   - Control concurrency limits
   - Implement rate limiting
   - Monitor system resource usage

### 7. Data Storage & Caching

```python
# Example caching implementation
async def get_cached_or_analyze(url, options):
    # Generate cache key
    cache_key = f"analysis:{url}:{hash(json.dumps(options))}"
    
    # Try to get from cache
    cached_result = await redis_client.get(cache_key)
    if cached_result:
        return json.loads(cached_result)
    
    # If not in cache, perform analysis
    result = await analyze_website(url, options)
    
    # Store in cache with expiration
    await redis_client.set(
        cache_key, 
        json.dumps(result),
        ex=60*60*24  # 24-hour expiration
    )
    
    return result
```

#### Features

1. **Analysis History Storage**:
   - Store complete analysis results
   - Index by URL and timestamp
   - Implement data retention policies

2. **Result Caching**:
   - Cache analysis results for repeated URLs
   - Implement cache invalidation strategies
   - Tiered caching (memory/Redis)

3. **Screenshot Storage**:
   - Store in cloud object storage
   - Generate thumbnail versions
   - Implement access controls

4. **User Preferences & Settings**:
   - Store user-specific settings
   - Save favorite analyses
   - Custom analysis templates

### 8. Tealium Integration Script

The backend will include a specialized JavaScript script that will be injected into the browser context to detect and analyze Tealium implementations.

```javascript
// Example of the tag detection script (to be injected)
function detectTealiumImplementation() {
  const results = {
    tealium: {},
    dataLayer: {},
    tags: [],
    events: [],
    performance: {}
  };
  
  // Detect Tealium presence
  if (window.utag) {
    results.tealium.version = window.utag.cfg?.v || 'Unknown';
    results.tealium.environment = detectTealiumEnvironment();
    results.tealium.profile = detectTealiumProfile();
  }
  
  // Extract data layer
  if (window.utag_data) {
    results.dataLayer = {...window.utag_data};
  }
  
  // Extract configured tags
  if (window.utag?.loader?.cfg) {
    Object.entries(window.utag.loader.cfg).forEach(([id, config]) => {
      if (!/^\d+$/.test(id)) return;
      
      results.tags.push({
        id: id,
        name: config.name || `Tag ${id}`,
        active: config.load !== 0,
        loadRule: config.load_rule || "default"
      });
    });
  }
  
  // Analyze tag loading performance
  results.performance = analyzeTealiumPerformance();
  
  // Detect event listeners
  results.events = detectTealiumEvents();
  
  return results;
}
```

#### Features

1. **Tealium Detection**:
   - Detect Tealium versions
   - Identify environment and profile
   - Extract configuration details

2. **Data Layer Extraction**:
   - Capture data layer variables
   - Monitor data layer changes
   - Detect extension implementations

3. **Tag Loading Analysis**:
   - Track tag loading sequence
   - Measure tag loading times
   - Identify dependency chains

4. **Event Monitoring**:
   - Detect registered event listeners
   - Capture event firing patterns
   - Map events to data layer updates

### 9. Security & Compliance

```python
# Example security middleware
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    
    return response
```

#### Features

1. **URL Validation & Sanitization**:
   - Validate input URLs
   - Prevent analysis of malicious sites
   - Implement URL allowlisting/blocklisting

2. **Authentication & Authorization**:
   - JWT-based authentication
   - Role-based access control
   - API key management for integrations

3. **Rate Limiting & Throttling**:
   - Per-user rate limits
   - Graduated throttling
   - DDoS protection

4. **Data Protection**:
   - Secure storage of analysis results
   - PII detection and masking
   - GDPR-compliant data handling

## Detailed API Schemas

### Analysis Request

```json
{
  "url": "https://example.com",
  "options": {
    "devices": ["desktop", "tablet", "mobile"],
    "depth": "full",  // "basic", "full", "comprehensive"
    "checkTealium": true,
    "screenshotViewports": true,
    "includeSubpages": false,
    "maxSubpages": 0,
    "customScripts": []
  }
}
```

### Analysis Response

```json
{
  "analysisId": "a1b2c3d4-e5f6",
  "url": "https://example.com",
  "status": "completed",  // "pending", "in_progress", "completed", "failed"
  "timestamp": "2025-02-27T12:34:56Z",
  "duration": 42.5,  // seconds
  "summary": {
    "title": "Example Website Analysis",
    "pageMetadata": {
      "title": "Example Site",
      "description": "This is an example website"
    },
    "deviceResults": {
      "desktop": { "screenshot": "url-to-image", "status": "completed" },
      "tablet": { "screenshot": "url-to-image", "status": "completed" },
      "mobile": { "screenshot": "url-to-image", "status": "completed" }
    }
  },
  "contentAnalysis": {
    // Content analysis results
  },
  "tealiumAnalysis": {
    // Tealium analysis results 
  },
  "enhancements": {
    // Enhancement recommendations or reference to them
  }
}
```

### Enhancement Recommendations

```json
{
  "enhancementId": "e1f2g3h4",
  "analysisId": "a1b2c3d4-e5f6",
  "url": "https://example.com",
  "timestamp": "2025-02-27T12:40:00Z",
  "categories": {
    "valueProposition": {
      "title": "Value Proposition Enhancements",
      "count": 5,
      "recommendations": [
        {
          "id": "vp-1",
          "title": "Clarify primary value proposition on homepage",
          "description": "Current headline is vague. Replace \"The Solution You Need\" with specific benefit statement.",
          "details": "The current homepage headline \"The Solution You Need\" doesn't communicate a specific value proposition...",
          "impact": "high",
          "effort": "low",
          "implementation": "Update the H1 headline on the homepage to clearly state the primary benefit...",
          "examples": ["Save 5 hours per week on project management tasks", "Increase conversion rates by 15% with our AI-powered solution"]
        },
        // More value proposition recommendations...
      ]
    },
    "contentStrategy": {
      "title": "Content Strategy Improvements",
      "count": 4,
      "recommendations": [
        // Content strategy recommendations...
      ]
    },
    "featureOpportunities": {
      "title": "Product Feature Opportunities",
      "count": 6,
      "recommendations": [
        // Feature recommendations...
      ]
    },
    "conversionOptimization": {
      "title": "Conversion Optimization",
      "count": 3,
      "recommendations": [
        // Conversion optimization recommendations...
      ]
    }
  }
}
```

### Tealium Analysis

```json
{
  "tealiumAnalysis": {
    "detected": true,
    "version": "4.43.0",
    "profile": "example-company/prod",
    "dataLayer": {
      "variables": {
        "page_name": "homepage",
        "page_type": "landing",
        // More variables...
      },
      "issues": [
        {
          "type": "inconsistent_naming",
          "description": "Mixed naming conventions detected",
          "details": "Variables use a mix of snake_case and camelCase",
          "examples": ["page_name vs pageType", "user_id vs userType"],
          "recommendation": "Standardize on snake_case for all variables"
        },
        // More issues...
      ]
    },
    "tags": {
      "total": 24,
      "active": 21,
      "inactive": 3,
      "vendorDistribution": {
        "analytics": 3,
        "advertising": 12,
        "uxAnalytics": 2,
        "other": 7
      },
      "details": [
        {
          "id": "1",
          "name": "Google Analytics",
          "vendor": "Google",
          "category": "analytics",
          "status": "active",
          "loadTime": 128,  // ms
          "requests": 3
        },
        // More tags...
      ],
      "issues": [
        // Tag-specific issues...
      ]
    },
    "performance": {
      "totalSize": 184,  // KB
      "loadTime": 1.4,  // seconds
      "requestCount": 57,
      "pageLoadImpact": "+22.3%",
      "recommendations": [
        "Consider server-side implementation for advertising tags",
        "Evaluate necessity of multiple advertising pixels",
        // More recommendations...
      ]
    }
  }
}
```

## OpenAI API Integration

### GPT-4o Configuration

```python
class GPT4oConfig:
    MODEL = "gpt-4o"
    MAX_TOKENS = 4000
    TEMPERATURE = 0.7
    SYSTEM_PROMPTS = {
        "content_analysis": CONTENT_ANALYSIS_PROMPT,
        "tealium_analysis": TEALIUM_ANALYSIS_PROMPT,
        "enhancements": ENHANCEMENT_PROMPT
    }
    RESPONSE_FORMAT = {"type": "json_object"}
```

### Example Function for Generating Enhancements

```python
async def generate_enhancements_with_gpt4o(analysis_data, categories):
    """
    Generate enhancement recommendations using GPT-4o
    """
    # Construct the prompt with analysis data
    prompt = f"""
    I need you to analyze this website and provide product enhancement recommendations.
    
    Website URL: {analysis_data['url']}
    
    Content Analysis:
    {json.dumps(analysis_data['contentAnalysis'], indent=2)}
    
    Tag Management Analysis:
    {json.dumps(analysis_data['tealiumAnalysis'], indent=2)}
    
    Please generate specific recommendations for the following categories:
    {', '.join(categories)}
    
    For each recommendation, include:
    1. A clear, specific title
    2. Detailed explanation of the issue/opportunity
    3. Implementation steps
    4. Expected impact (High/Medium/Low)
    5. Implementation difficulty (Easy/Medium/Hard)
    """
    
    try:
        # Call OpenAI API
        response = await openai.ChatCompletion.create(
            model=GPT4oConfig.MODEL,
            messages=[
                {"role": "system", "content": GPT4oConfig.SYSTEM_PROMPTS["enhancements"]},
                {"role": "user", "content": prompt}
            ],
            temperature=GPT4oConfig.TEMPERATURE,
            max_tokens=GPT4oConfig.MAX_TOKENS,
            response_format=GPT4oConfig.RESPONSE_FORMAT
        )
        
        # Parse response
        content = response.choices[0].message.content
        recommendations = json.loads(content)
        
        # Post-process and validate recommendations
        processed_recommendations = process_gpt4o_recommendations(recommendations)
        
        return processed_recommendations
    except Exception as e:
        logger.error(f"Error generating recommendations with GPT-4o: {str(e)}")
        raise
```

## Error Handling

### Error Categories

1. **URL Access Errors**:
   - Invalid URL format
   - Site not accessible
   - Access forbidden (403)
   - Site requires authentication

2. **Analysis Process Errors**:
   - Timeout during analysis
   - JavaScript execution errors
   - Resource loading failures
   - Memory limit exceeded

3. **OpenAI API Errors**:
   - API rate limiting
   - Token limit exceeded
   - Model unavailable
   - Content policy violations

4. **Result Processing Errors**:
   - Invalid JSON response
   - Missing required fields
   - Schema validation failures

### Error Response Format

```json
{
  "error": {
    "code": "analysis_timeout",
    "message": "The analysis process timed out after 60 seconds",
    "details": "The website at example.com took too long to respond",
    "timestamp": "2025-02-27T12:34:56Z",
    "requestId": "req-abcd1234",
    "suggestions": [
      "Try analyzing a specific page rather than the homepage",
      "Check if the site is currently experiencing issues",
      "Consider using the 'basic' analysis depth option"
    ]
  }
}
```

## Deployment Considerations

1. **Containerization**:
   - Docker-based deployment
   - Kubernetes orchestration
   - Scalable microservices architecture

2. **Cloud Services**:
   - AWS/GCP/Azure compatible
   - Auto-scaling configuration
   - Load balancing requirements

3. **Monitoring & Logging**:
   - Prometheus metrics
   - ELK stack integration
   - Performance tracking
   - Error alerting

4. **Security Considerations**:
   - API key rotation
   - OpenAI API key management
   - Input validation
   - Output sanitization

## Conclusion

This specification outlines the core backend functionality needed to power the Product Manager Enhancer application. The implementation will be in Python using FastAPI, with OpenAI's GPT-4o model providing the AI-powered analysis and recommendations. The system is designed to be scalable, maintainable, and secure, with a focus on providing high-quality analysis and actionable recommendations.