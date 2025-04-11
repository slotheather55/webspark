import React, { useEffect, useState } from 'react';
import { Eye, Target, FileText } from 'lucide-react';

function ContentAnalysisTab({ analysisId, analysisResults }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Extract content analysis from the analysis results
  const contentAnalysis = analysisResults?.content_analysis || {};
  const { 
    observations = [], 
    user_journey = {}, 
    extracted_content = {} 
  } = contentAnalysis;

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-4">
        <p className="text-red-700">{error}</p>
      </div>
    );
  }

  // If no content analysis data was found
  if (!contentAnalysis || Object.keys(contentAnalysis).length === 0) {
    return (
      <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
        <p className="text-yellow-700">No content analysis data available for this website.</p>
      </div>
    );
  }

  return (
    <div>
      <h3 className="text-lg font-medium text-gray-800 mb-4">AI Content Analysis</h3>
      
      <div className="space-y-6">
        {observations && observations.length > 0 && (
          <div className="border rounded-lg overflow-hidden">
            <div className="bg-gray-50 px-4 py-3 border-b flex items-center">
              <Eye size={16} className="text-gray-600 mr-2" />
              <h4 className="font-medium text-gray-700">Key Content Observations</h4>
            </div>
            <div className="p-4">
              <div className="prose max-w-none text-gray-700">
                <p>After analyzing the website, the following key observations inform my recommendations:</p>
                
                <ul className="mt-3 space-y-2">
                  {observations.map((observation, index) => (
                    <li key={index}>{observation}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}
        
        {user_journey && Object.keys(user_journey).length > 0 && (
          <div className="border rounded-lg overflow-hidden">
            <div className="bg-gray-50 px-4 py-3 border-b flex items-center">
              <Target size={16} className="text-gray-600 mr-2" />
              <h4 className="font-medium text-gray-700">User Journey Analysis</h4>
            </div>
            <div className="p-4">
              <div className="prose max-w-none text-gray-700">
                <p>The current user journey has several points of friction:</p>
                
                <ol className="mt-3 space-y-2">
                  {Object.entries(user_journey).map(([stage, description], index) => (
                    <li key={index}><strong>{stage}:</strong> {description}</li>
                  ))}
                </ol>
                
                <p className="mt-4">These observations support the product enhancement recommendations in the summary tab.</p>
              </div>
            </div>
          </div>
        )}
        
        {extracted_content && Object.keys(extracted_content).length > 0 && (
          <div className="border rounded-lg overflow-hidden">
            <div className="bg-gray-50 px-4 py-3 border-b flex items-center">
              <FileText size={16} className="text-gray-600 mr-2" />
              <h4 className="font-medium text-gray-700">Extracted Key Content</h4>
            </div>
            <div className="p-4">
              <div className="space-y-3">
                {Object.entries(extracted_content).map(([key, value], index) => (
                  <div key={index}>
                    <p className="text-sm text-gray-500">{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</p>
                    <p className="text-gray-800 font-medium">{value}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ContentAnalysisTab; 