import React from 'react';
import { Monitor, Tablet, Smartphone } from 'lucide-react';

function ScreenshotsTab() {
  return (
    <div>
      <h3 className="text-lg font-medium text-gray-800 mb-4">Captured Screenshots (via Headless Browser)</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="border rounded-lg overflow-hidden shadow-sm">
          <div className="bg-gray-50 px-4 py-2 border-b flex items-center justify-between">
            <div className="flex items-center">
              <Monitor size={16} className="text-gray-600 mr-2" />
              <span className="text-sm font-medium text-gray-700">Desktop View</span>
            </div>
            <span className="text-xs text-gray-500">1920×1080px</span>
          </div>
          <div className="p-2">
            <div className="w-full h-64 bg-gray-200 rounded flex items-center justify-center">
              <span className="text-gray-500 text-sm">Desktop screenshot would appear here</span>
            </div>
          </div>
        </div>
        
        <div className="border rounded-lg overflow-hidden shadow-sm">
          <div className="bg-gray-50 px-4 py-2 border-b flex items-center justify-between">
            <div className="flex items-center">
              <Tablet size={16} className="text-gray-600 mr-2" />
              <span className="text-sm font-medium text-gray-700">Tablet View</span>
            </div>
            <span className="text-xs text-gray-500">768×1024px</span>
          </div>
          <div className="p-2">
            <div className="w-full h-64 bg-gray-200 rounded flex items-center justify-center">
              <span className="text-gray-500 text-sm">Tablet screenshot would appear here</span>
            </div>
          </div>
        </div>
        
        <div className="border rounded-lg overflow-hidden shadow-sm">
          <div className="bg-gray-50 px-4 py-2 border-b flex items-center justify-between">
            <div className="flex items-center">
              <Smartphone size={16} className="text-gray-600 mr-2" />
              <span className="text-sm font-medium text-gray-700">Mobile View</span>
            </div>
            <span className="text-xs text-gray-500">375×667px</span>
          </div>
          <div className="p-2">
            <div className="w-full h-64 bg-gray-200 rounded flex items-center justify-center">
              <span className="text-gray-500 text-sm">Mobile screenshot would appear here</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ScreenshotsTab; 