import React, { useState } from 'react';
import TealiumAnalysisTab from './components/tabs/TealiumAnalysisTab';
import ContentAnalysisTab from './components/tabs/ContentAnalysisTab';
import ScreenshotsTab from './components/tabs/ScreenshotsTab';

function App() {
  const [activeTab, setActiveTab] = useState('tealium');

  return (
    <div className="container mx-auto p-4">
      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'tealium' ? 'active' : ''}`}
          onClick={() => setActiveTab('tealium')}
        >
          Tealium Analysis
        </button>
        <button 
          className={`tab ${activeTab === 'content' ? 'active' : ''}`}
          onClick={() => setActiveTab('content')}
        >
          Content Analysis
        </button>
        <button 
          className={`tab ${activeTab === 'screenshots' ? 'active' : ''}`}
          onClick={() => setActiveTab('screenshots')}
        >
          Screenshots
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'tealium' && <TealiumAnalysisTab />}
        {activeTab === 'content' && <ContentAnalysisTab />}
        {activeTab === 'screenshots' && <ScreenshotsTab />}
      </div>
    </div>
  );
}

export default App;