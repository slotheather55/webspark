import React from 'react';
import { TABS } from '../ProductManagerEnhancer';
import TabsNav from './TabsNav';
import SummaryTab from './tabs/SummaryTab';
import ScreenshotsTab from './tabs/ScreenshotsTab';
import ContentAnalysisTab from './tabs/ContentAnalysisTab';
import TealiumAnalysisTab from './tabs/TealiumAnalysisTab';

const AnalysisResults = ({ 
  activeTab, 
  setActiveTab, 
  expandedSections, 
  toggleSection,
  analysisId,
  analysisResults
}) => {
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

export default AnalysisResults; 