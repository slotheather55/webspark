import React from 'react';
import { Globe, Camera, Eye, Brain } from 'lucide-react';

const AnalysisProgress = ({ progress = 0 }) => {
  // Calculate individual step progress based on overall progress
  const visitingProgress = Math.min(100, progress * 5); // First 20% of total progress
  const screenshotProgress = progress > 20 ? Math.min(100, (progress - 20) * 2.5) : 0; // Next 40% of total progress
  const contentProgress = progress > 60 ? Math.min(100, (progress - 60) * 2.5) : 0; // Next 40% of total progress
  const tealiumProgress = progress > 80 ? Math.min(100, (progress - 80) * 5) : 0; // Last 20% of total progress
  const enhancementProgress = progress === 100 ? 100 : 0; // Only complete when everything is done

  // Helper function to determine status text
  const getStatusText = (stepProgress) => {
    if (stepProgress === 100) return 'Complete';
    if (stepProgress > 0) return `${Math.round(stepProgress)}%`;
    return 'Waiting...';
  };

  return (
    <div className="mb-6 p-6 bg-white rounded-lg shadow-sm">
      <h3 className="text-lg font-medium text-gray-800 mb-4">AI Agent Processing</h3>
      
      <div className="space-y-4">
        <div className="flex items-center">
          <div className="w-8 h-8 flex items-center justify-center bg-indigo-100 rounded-full mr-3">
            <Globe size={18} className="text-indigo-600" />
          </div>
          <div className="flex-1">
            <div className="flex justify-between mb-1">
              <span className="text-sm font-medium text-gray-700">Visiting website with headless browser</span>
              <span className="text-sm text-gray-500">{getStatusText(visitingProgress)}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className={`${visitingProgress === 100 ? 'bg-green-500' : 'bg-indigo-500'} h-2 rounded-full`} 
                style={{ width: `${visitingProgress}%` }}
              ></div>
            </div>
          </div>
        </div>
        
        <div className="flex items-center">
          <div className="w-8 h-8 flex items-center justify-center bg-indigo-100 rounded-full mr-3">
            <Camera size={18} className="text-indigo-600" />
          </div>
          <div className="flex-1">
            <div className="flex justify-between mb-1">
              <span className="text-sm font-medium text-gray-700">Capturing screenshots (mobile, tablet, desktop)</span>
              <span className="text-sm text-gray-500">{getStatusText(screenshotProgress)}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className={`${screenshotProgress === 100 ? 'bg-green-500' : 'bg-indigo-500'} h-2 rounded-full`} 
                style={{ width: `${screenshotProgress}%` }}
              ></div>
            </div>
          </div>
        </div>
        
        <div className="flex items-center">
          <div className="w-8 h-8 flex items-center justify-center bg-indigo-100 rounded-full mr-3">
            <Eye size={18} className="text-indigo-600" />
          </div>
          <div className="flex-1">
            <div className="flex justify-between mb-1">
              <span className="text-sm font-medium text-gray-700">Analyzing page content & visual elements</span>
              <span className="text-sm text-gray-500">{getStatusText(contentProgress)}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className={`${contentProgress === 100 ? 'bg-green-500' : 'bg-indigo-500'} h-2 rounded-full`} 
                style={{ width: `${contentProgress}%` }}
              ></div>
            </div>
          </div>
        </div>
        
        <div className="flex items-center">
          <div className="w-8 h-8 flex items-center justify-center bg-indigo-100 rounded-full mr-3">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-indigo-600"><circle cx="12" cy="12" r="10"></circle><circle cx="10" cy="10" r="3"></circle><path d="m21 21-9-9"></path></svg>
          </div>
          <div className="flex-1">
            <div className="flex justify-between mb-1">
              <span className="text-sm font-medium text-gray-700">Inspecting Tealium implementation</span>
              <span className="text-sm text-gray-500">{getStatusText(tealiumProgress)}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className={`${tealiumProgress === 100 ? 'bg-green-500' : 'bg-indigo-500'} h-2 rounded-full`} 
                style={{ width: `${tealiumProgress}%` }}
              ></div>
            </div>
          </div>
        </div>
        
        <div className="flex items-center">
          <div className={`w-8 h-8 flex items-center justify-center ${enhancementProgress > 0 ? 'bg-indigo-100' : 'bg-gray-100'} rounded-full mr-3`}>
            <Brain size={18} className={enhancementProgress > 0 ? 'text-indigo-600' : 'text-gray-400'} />
          </div>
          <div className="flex-1">
            <div className="flex justify-between mb-1">
              <span className={`text-sm font-medium ${enhancementProgress > 0 ? 'text-gray-700' : 'text-gray-500'}`}>Generating product enhancement ideas</span>
              <span className="text-sm text-gray-500">{getStatusText(enhancementProgress)}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className={`${enhancementProgress === 100 ? 'bg-green-500' : enhancementProgress > 0 ? 'bg-indigo-500' : 'bg-gray-300'} h-2 rounded-full`} 
                style={{ width: `${enhancementProgress}%` }}
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalysisProgress; 