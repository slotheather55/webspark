# Frontend-Backend Integration Plan

## 1. API Connection Changes

### Frontend Changes

1. **Create API client service**:
   - Create a new file `src/services/api.js` to centralize API calls
   ```javascript
   // src/services/api.js
   const API_BASE_URL = '/api/v1';

   export const analyzeWebsite = async (url, options = {}) => {
     try {
       const response = await fetch(`${API_BASE_URL}/analysis`, {
         method: 'POST',
         headers: {
           'Content-Type': 'application/json',
         },
         body: JSON.stringify({ url, options }),
       });
       
       if (!response.ok) {
         const error = await response.json();
         throw new Error(error.error?.message || 'Failed to analyze website');
       }
       
       return await response.json();
     } catch (error) {
       console.error('API Error:', error);
       throw error;
     }
   };

   export const getAnalysisResults = async (analysisId) => {
     try {
       const response = await fetch(`${API_BASE_URL}/analysis/${analysisId}`);
       
       if (!response.ok) {
         const error = await response.json();
         throw new Error(error.error?.message || 'Failed to get analysis results');
       }
       
       return await response.json();
     } catch (error) {
       console.error('API Error:', error);
       throw error;
     }
   };

   export const getScreenshots = async (analysisId) => {
     try {
       const response = await fetch(`${API_BASE_URL}/screenshots/${analysisId}`);
       
       if (!response.ok) {
         const error = await response.json();
         throw new Error(error.error?.message || 'Failed to get screenshots');
       }
       
       return await response.json();
     } catch (error) {
       console.error('API Error:', error);
       throw error;
     }
   };

   export const getTealiumAnalysis = async (analysisId) => {
     try {
       const response = await fetch(`${API_BASE_URL}/tealium/analysis/${analysisId}`);
       
       if (!response.ok) {
         const error = await response.json();
         throw new Error(error.error?.message || 'Failed to get Tealium analysis');
       }
       
       return await response.json();
     } catch (error) {
       console.error('API Error:', error);
       throw error;
     }
   };

   export const generateEnhancements = async (analysisId, categories) => {
     try {
       const response = await fetch(`${API_BASE_URL}/enhancements/generate`, {
         method: 'POST',
         headers: {
           'Content-Type': 'application/json',
         },
         body: JSON.stringify({ analysis_id: analysisId, categories }),
       });
       
       if (!response.ok) {
         const error = await response.json();
         throw new Error(error.error?.message || 'Failed to generate enhancements');
       }
       
       return await response.json();
     } catch (error) {
       console.error('API Error:', error);
       throw error;
     }
   };

   export const getEnhancement = async (enhancementId) => {
     try {
       const response = await fetch(`${API_BASE_URL}/enhancements/${enhancementId}`);
       
       if (!response.ok) {
         const error = await response.json();
         throw new Error(error.error?.message || 'Failed to get enhancement details');
       }
       
       return await response.json();
     } catch (error) {
       console.error('API Error:', error);
       throw error;
     }
   };
   ```

2. **Modify `ProductManagerEnhancer.jsx` to use real API**:
   - Replace the simulated analysis with actual API calls
   ```javascript
   import { analyzeWebsite, getAnalysisResults } from './services/api';

   // In the handleAnalyze function
   const handleAnalyze = async () => {
     if (!url) return;
     setIsAnalyzing(true);
     
     try {
       // Call the real API instead of setTimeout
       const response = await analyzeWebsite(url, {
         devices: ["desktop", "tablet", "mobile"],
         check_tealium: true,
       });
       
       // Store the analysis ID for polling
       setAnalysisId(response.analysis_id);
       
       // Start polling for analysis completion
       checkAnalysisStatus(response.analysis_id);
     } catch (error) {
       setIsAnalyzing(false);
       // Handle error (show error message to user)
       console.error("Analysis failed:", error);
     }
   };
   
   // Add a function to poll for analysis status
   const checkAnalysisStatus = async (analysisId) => {
     try {
       const result = await getAnalysisResults(analysisId);
       
       if (result.status === 'completed') {
         setIsAnalyzing(false);
         setAnalysisComplete(true);
         setAnalysisResults(result);
       } else if (result.status === 'failed') {
         setIsAnalyzing(false);
         // Handle failure
         console.error("Analysis failed:", result.error);
       } else {
         // Still in progress, check again in a few seconds
         setTimeout(() => checkAnalysisStatus(analysisId), 5000);
       }
     } catch (error) {
       setIsAnalyzing(false);
       console.error("Error checking analysis status:", error);
     }
   };
   ```

3. **Update component state to store API response data**:
   - Add new state variables to `ProductManagerEnhancer.jsx`:
   ```javascript
   const [analysisId, setAnalysisId] = useState(null);
   const [analysisResults, setAnalysisResults] = useState(null);
   const [enhancementId, setEnhancementId] = useState(null);
   const [error, setError] = useState(null);
   ```

4. **Update the `AnalysisResults` component to use API data**:
   - Modify the component to receive and display real data
   ```javascript
   const AnalysisResults = ({ 
     activeTab, 
     setActiveTab, 
     expandedSections, 
     toggleSection,
     analysisResults,
     analysisId 
   }) => {
     // Pass the data to child components
     return (
       <div className="bg-white rounded-lg shadow-sm">
         <TabsNav activeTab={activeTab} setActiveTab={setActiveTab} />
         
         <div className="p-6">
           {activeTab === TABS.SUMMARY && (
             <SummaryTab 
               expandedSections={expandedSections} 
               toggleSection={toggleSection} 
               analysisId={analysisId}
               analysisResults={analysisResults}
             />
           )}

           {activeTab === TABS.SCREENSHOTS && (
             <ScreenshotsTab 
               analysisId={analysisId}
             />
           )}

           {activeTab === TABS.CONTEXT && (
             <ContentAnalysisTab 
               analysisId={analysisId}
               analysisResults={analysisResults}
             />
           )}
           
           {activeTab === TABS.TRACKING && (
             <TealiumAnalysisTab 
               analysisId={analysisId}
               analysisResults={analysisResults}
             />
           )}
         </div>
       </div>
     );
   };
   ```

5. **Update tab components to fetch and display real data**:
   - For example, modify the `ScreenshotsTab.jsx`:
   ```javascript
   import React, { useEffect, useState } from 'react';
   import { Monitor, Tablet, Smartphone } from 'lucide-react';
   import { getScreenshots } from '../../services/api';

   function ScreenshotsTab({ analysisId }) {
     const [screenshots, setScreenshots] = useState({});
     const [loading, setLoading] = useState(true);
     const [error, setError] = useState(null);

     useEffect(() => {
       const fetchScreenshots = async () => {
         try {
           if (!analysisId) return;
           
           setLoading(true);
           const response = await getScreenshots(analysisId);
           setScreenshots(response.screenshots);
           setLoading(false);
         } catch (error) {
           setError('Failed to load screenshots');
           setLoading(false);
         }
       };

       fetchScreenshots();
     }, [analysisId]);

     // Render with real data
     return (
       <div>
         <h3 className="text-lg font-medium text-gray-800 mb-4">Captured Screenshots (via Headless Browser)</h3>
         
         {loading && <p>Loading screenshots...</p>}
         {error && <p className="text-red-500">{error}</p>}
         
         <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
           {screenshots.desktop && (
             <div className="border rounded-lg overflow-hidden shadow-sm">
               <div className="bg-gray-50 px-4 py-2 border-b flex items-center justify-between">
                 <div className="flex items-center">
                   <Monitor size={16} className="text-gray-600 mr-2" />
                   <span className="text-sm font-medium text-gray-700">Desktop View</span>
                 </div>
                 <span className="text-xs text-gray-500">1920×1080px</span>
               </div>
               <div className="p-2">
                 <img 
                   src={screenshots.desktop} 
                   alt="Desktop screenshot" 
                   className="w-full h-64 object-cover"
                 />
               </div>
             </div>
           )}
           
           {/* Similar blocks for tablet and mobile screenshots */}
         </div>
       </div>
     );
   }

   export default ScreenshotsTab;
   ```

6. **Similar updates for other tabs**:
   - Make equivalent changes to `TealiumAnalysisTab.jsx`, `ContentAnalysisTab.jsx`, and `SummaryTab.jsx`

### Backend Changes

1. **Add CORS handling to FastAPI app**:
   - Modify the CORS configuration in `main.py` to allow requests from the frontend:
   ```python
   # Set up CORS with more appropriate settings
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],  # In production, limit this to your frontend domain
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. **Update API routes to return consistent data format**:
   - Ensure all API endpoints return data in a consistent format
   - For example, in `app/api/endpoints/analysis.py`:
   ```python
   @router.post("/", response_model=analysis_schema.AnalysisResponse, status_code=status.HTTP_201_CREATED)
   async def create_analysis(
       data: analysis_schema.AnalysisCreate,
       background_tasks: BackgroundTasks,
       db: Session = Depends(get_db),
       current_user: Optional[models.User] = Depends(get_current_active_user)
   ):
       """
       Create a new website analysis job
       """
       # Create analysis record in database
       analysis = crud.analysis.create(
           db=db,
           obj_in={
               "url": data.url,
               "user_id": current_user.id if current_user else None,
               "status": "pending",
               "options": data.options.dict() if data.options else {}
           }
       )
       
       # Trigger the analysis task in background
       background_tasks.add_task(
           trigger_website_analysis,
           analysis_id=str(analysis.id),
           url=analysis.url,
           options=data.options.dict() if data.options else None
       )
       
       return {
           "analysis_id": analysis.id,
           "url": analysis.url,
           "status": analysis.status,
           "created_at": analysis.created_at,
           "updated_at": analysis.updated_at,
           "message": "Analysis started successfully"
       }
   ```

## 2. Error Handling and Loading States

1. **Add loading and error states to components**:
   ```javascript
   // For example, in ProductManagerEnhancer.jsx:
   const [error, setError] = useState(null);
   
   // In the handleAnalyze function:
   try {
     // API call logic
   } catch (error) {
     setError(`Error: ${error.message}`);
     setIsAnalyzing(false);
   }
   
   // In the render function:
   {error && (
     <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-4">
       <p>{error}</p>
     </div>
   )}
   ```

2. **Update `AnalysisProgress` component to show real progress**:
   - Modify to display actual progress from backend

## 3. Authentication (Optional)

1. **If you want to implement authentication**:
   - Add login/signup components
   - Update API client to include authentication tokens
   - Add authentication state management

## 4. Proxy Configuration for Development

1. **Configure development proxy**:
   - Add a proxy configuration in `package.json`:
   ```json
   "proxy": "http://localhost:8000"
   ```

2. **Or add setupProxy.js**:
   - Create `src/setupProxy.js`:
   ```javascript
   const { createProxyMiddleware } = require('http-proxy-middleware');

   module.exports = function(app) {
     app.use(
       '/api',
       createProxyMiddleware({
         target: 'http://localhost:8000',
         changeOrigin: true,
       })
     );
   };
   ```

## 5. Integration Testing

1. **Test the complete flow**:
   - Enter a URL and submit
   - See the analysis progress
   - View analysis results
   - Generate and view enhancement recommendations

## 6. Cross-Browser Testing

1. **Test on different browsers**:
   - Chrome, Firefox, Safari, Edge
   - Mobile browsers if relevant

## 7. Deployment Configuration

1. **Configure for production deployment**:
   - Update API base URL for production
   - Set up proper CORS headers
   - Configure proper authentication