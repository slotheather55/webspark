import React from 'react';

const URLInputSection = ({ 
  url, 
  setUrl, 
  isAnalyzing, 
  analysisComplete, 
  handleAnalyze, 
  resetAnalysis 
}) => {
  return (
    <div className="mb-6">
      <div className="flex items-center mb-2">
        <h2 className="text-lg font-medium text-gray-800">Analyze Website & Generate Product Improvements</h2>
        {analysisComplete && (
          <button 
            onClick={resetAnalysis}
            className="ml-4 text-sm text-indigo-600 hover:text-indigo-800"
          >
            New Analysis
          </button>
        )}
      </div>
      <div className="flex">
        <div className="relative flex-grow">
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Enter website URL (e.g., https://example.com)"
            className="w-full px-4 py-3 border border-gray-300 rounded-l-md focus:ring-indigo-500 focus:border-indigo-500"
            disabled={isAnalyzing || analysisComplete}
          />
          {url && !isAnalyzing && !analysisComplete && (
            <button 
              className="absolute right-3 top-3 text-gray-400 hover:text-gray-600"
              onClick={() => setUrl('')}
            >
              ×
            </button>
          )}
        </div>
        <button
          onClick={handleAnalyze}
          disabled={!url || isAnalyzing}
          className={`px-6 py-3 rounded-r-md font-medium text-white ${
            !url || isAnalyzing
              ? 'bg-indigo-400'
              : 'bg-indigo-600 hover:bg-indigo-700'
          }`}
        >
          {isAnalyzing ? 'Analyzing...' : 'Analyze'}
        </button>
      </div>
    </div>
  );
};

export default URLInputSection; 