import React, { useState } from 'react';
import { Zap, Globe, Camera, Brain, Eye } from 'lucide-react';
import Header from './components/Header';
import URLInputSection from './components/URLInputSection';
import AnalysisProgress from './components/AnalysisProgress';
import AnalysisResults from './components/AnalysisResults';

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

  const toggleSection = (section) => {
    setExpandedSections({
      ...expandedSections,
      [section]: !expandedSections[section]
    });
  };

  const handleAnalyze = () => {
    if (!url) return;
    setIsAnalyzing(true);
    
    // Simulate analysis process
    setTimeout(() => {
      setIsAnalyzing(false);
      setAnalysisComplete(true);
    }, 1500);
  };

  const resetAnalysis = () => {
    setUrl('');
    setIsAnalyzing(false);
    setAnalysisComplete(false);
  };

  return (
    <div className="flex flex-col w-full max-w-6xl mx-auto bg-gray-50 rounded-lg shadow-lg overflow-hidden">
      <Header />

      <div className="flex flex-col p-6">
        <URLInputSection 
          url={url} 
          setUrl={setUrl} 
          isAnalyzing={isAnalyzing} 
          analysisComplete={analysisComplete}
          handleAnalyze={handleAnalyze}
          resetAnalysis={resetAnalysis}
        />

        {isAnalyzing && <AnalysisProgress />}

        {analysisComplete && (
          <AnalysisResults 
            activeTab={activeTab}
            setActiveTab={setActiveTab}
            expandedSections={expandedSections}
            toggleSection={toggleSection}
          />
        )}
      </div>
    </div>
  );
};

export default ProductManagerEnhancer;