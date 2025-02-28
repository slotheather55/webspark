import React from 'react';
import { Globe, Camera, Eye, Brain } from 'lucide-react';

const AnalysisProgress = () => {
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
              <span className="text-sm text-gray-500">Complete</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-green-500 h-2 rounded-full" style={{ width: '100%' }}></div>
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
              <span className="text-sm text-gray-500">78%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-indigo-500 h-2 rounded-full" style={{ width: '78%' }}></div>
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
              <span className="text-sm text-gray-500">45%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-indigo-500 h-2 rounded-full" style={{ width: '45%' }}></div>
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
              <span className="text-sm text-gray-500">30%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-indigo-500 h-2 rounded-full" style={{ width: '30%' }}></div>
            </div>
          </div>
        </div>
        
        <div className="flex items-center">
          <div className="w-8 h-8 flex items-center justify-center bg-gray-100 rounded-full mr-3">
            <Brain size={18} className="text-gray-400" />
          </div>
          <div className="flex-1">
            <div className="flex justify-between mb-1">
              <span className="text-sm font-medium text-gray-500">Generating product enhancement ideas</span>
              <span className="text-sm text-gray-500">Waiting...</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-gray-300 h-2 rounded-full" style={{ width: '0%' }}></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalysisProgress; 