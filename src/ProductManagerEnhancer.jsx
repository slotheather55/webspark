import React, { useState } from 'react';
import { Zap, Globe, Camera, Brain, Eye } from 'lucide-react';
import Header from './components/Header';
import URLInputSection from './components/URLInputSection';
import AnalysisProgress from './components/AnalysisProgress';
import AnalysisResults from './components/AnalysisResults';
import { analyzeWebsite, getAnalysisResults } from './services/api';

// Define tab IDs as constants
export const TABS = {
  SUMMARY: 'summary',
  SCREENSHOTS: 'screenshots',
  CONTEXT: 'context',
  TRACKING: 'tracking'
};

// Define section IDs as constants to avoid typos and string literals
export const SECTIONS = {
  VALUE: 'value',
  CONTENT: 'content',
  FEATURES: 'features',
  CONVERSION: 'conversion'
};

const ProductManagerEnhancer = () => {
  const [url, setUrl] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisComplete, setAnalysisComplete] = useState(false);
  const [activeTab, setActiveTab] = useState(TABS.SUMMARY);
  const [expandedSections, setExpandedSections] = useState({
    [SECTIONS.VALUE]: true,
    [SECTIONS.CONTENT]: false,
    [SECTIONS.FEATURES]: false,
    [SECTIONS.CONVERSION]: false
  });
  const [analysisId, setAnalysisId] = useState(null);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(0);

  const toggleSection = (section) => {
    setExpandedSections({
      ...expandedSections,
      [section]: !expandedSections[section]
    });
  };

  const handleAnalyze = async () => {
    if (!url) return;
    setIsAnalyzing(true);
    setError(null);
    setProgress(0);
    
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
      setError(`Error: ${error.message}`);
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
        setProgress(100);
      } else if (result.status === 'failed') {
        setIsAnalyzing(false);
        setError(`Analysis failed: ${result.message || 'Unknown error'}`);
        console.error("Analysis failed:", result.message);
      } else {
        // Still in progress, update progress if available
        if (result.progress) {
          setProgress(result.progress);
        }
        // Check again in a few seconds
        setTimeout(() => checkAnalysisStatus(analysisId), 3000);
      }
    } catch (error) {
      setIsAnalyzing(false);
      setError(`Error checking analysis status: ${error.message}`);
      console.error("Error checking analysis status:", error);
    }
  };

  const resetAnalysis = () => {
    setUrl('');
    setIsAnalyzing(false);
    setAnalysisComplete(false);
    setAnalysisId(null);
    setAnalysisResults(null);
    setError(null);
    setProgress(0);
  };

  return (
    <div className="flex flex-col w-full max-w-6xl mx-auto bg-gray-50 rounded-lg shadow-lg overflow-hidden">
      <Header />

      <div className="flex flex-col p-6">
        {error && (
          <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-4">
            <p>{error}</p>
          </div>
        )}

        <URLInputSection 
          url={url} 
          setUrl={setUrl} 
          isAnalyzing={isAnalyzing} 
          analysisComplete={analysisComplete}
          handleAnalyze={handleAnalyze}
          resetAnalysis={resetAnalysis}
        />

        {isAnalyzing && <AnalysisProgress progress={progress} />}

        {analysisComplete && (
          <AnalysisResults 
            activeTab={activeTab}
            setActiveTab={setActiveTab}
            expandedSections={expandedSections}
            toggleSection={toggleSection}
            analysisId={analysisId}
            analysisResults={analysisResults}
          />
        )}
      </div>
    </div>
  );
};

export default ProductManagerEnhancer;