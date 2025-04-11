import React from 'react';
import { TABS } from '../ProductManagerEnhancer';

const TabsNav = ({ activeTab, setActiveTab }) => {
  return (
    <div className="flex border-b">
      <button
        className={`px-6 py-3 font-medium ${
          activeTab === TABS.SUMMARY 
            ? 'text-indigo-600 border-b-2 border-indigo-600' 
            : 'text-gray-500 hover:text-gray-700'
        }`}
        onClick={() => setActiveTab(TABS.SUMMARY)}
      >
        Enhancement Ideas
      </button>
      <button
        className={`px-6 py-3 font-medium ${
          activeTab === TABS.SCREENSHOTS 
            ? 'text-indigo-600 border-b-2 border-indigo-600' 
            : 'text-gray-500 hover:text-gray-700'
        }`}
        onClick={() => setActiveTab(TABS.SCREENSHOTS)}
      >
        Screenshots
      </button>
      <button
        className={`px-6 py-3 font-medium ${
          activeTab === TABS.CONTEXT 
            ? 'text-indigo-600 border-b-2 border-indigo-600' 
            : 'text-gray-500 hover:text-gray-700'
        }`}
        onClick={() => setActiveTab(TABS.CONTEXT)}
      >
        Content Analysis
      </button>
      <button
        className={`px-6 py-3 font-medium ${
          activeTab === TABS.TRACKING 
            ? 'text-indigo-600 border-b-2 border-indigo-600' 
            : 'text-gray-500 hover:text-gray-700'
        }`}
        onClick={() => setActiveTab(TABS.TRACKING)}
      >
        Tealium Analysis
      </button>
    </div>
  );
};

export default TabsNav; 