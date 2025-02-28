import React, { useEffect, useState } from 'react';
import { Monitor, Tablet, Smartphone } from 'lucide-react';
import { getScreenshots } from '../../services/api';

function ScreenshotsTab({ analysisId }) {
  const [screenshots, setScreenshots] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchScreenshots = async () => {
      try {
        if (!analysisId) return;
        
        setLoading(true);
        const response = await getScreenshots(analysisId);
        setScreenshots(response.screenshots || {});
        setLoading(false);
      } catch (error) {
        setError('Failed to load screenshots');
        setLoading(false);
        console.error('Error fetching screenshots:', error);
      }
    };

    fetchScreenshots();
  }, [analysisId]);

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

  return (
    <div>
      <h3 className="text-lg font-medium text-gray-800 mb-4">Captured Screenshots (via Headless Browser)</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {screenshots.desktop ? (
          <div className="border rounded-lg overflow-hidden shadow-sm">
            <div className="bg-gray-50 px-4 py-2 border-b flex items-center justify-between">
              <div className="flex items-center">
                <Monitor size={16} className="text-gray-600 mr-2" />
                <span className="text-sm font-medium text-gray-700">Desktop View</span>
              </div>
              <span className="text-xs text-gray-500">1920×1080px</span>
            </div>
            <div className="p-2">
              <img 
                src={screenshots.desktop} 
                alt="Desktop screenshot" 
                className="w-full h-64 object-cover"
              />
            </div>
          </div>
        ) : (
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
                <span className="text-gray-500 text-sm">No desktop screenshot available</span>
              </div>
            </div>
          </div>
        )}
        
        {screenshots.tablet ? (
          <div className="border rounded-lg overflow-hidden shadow-sm">
            <div className="bg-gray-50 px-4 py-2 border-b flex items-center justify-between">
              <div className="flex items-center">
                <Tablet size={16} className="text-gray-600 mr-2" />
                <span className="text-sm font-medium text-gray-700">Tablet View</span>
              </div>
              <span className="text-xs text-gray-500">768×1024px</span>
            </div>
            <div className="p-2">
              <img 
                src={screenshots.tablet} 
                alt="Tablet screenshot" 
                className="w-full h-64 object-cover"
              />
            </div>
          </div>
        ) : (
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
                <span className="text-gray-500 text-sm">No tablet screenshot available</span>
              </div>
            </div>
          </div>
        )}
        
        {screenshots.mobile ? (
          <div className="border rounded-lg overflow-hidden shadow-sm">
            <div className="bg-gray-50 px-4 py-2 border-b flex items-center justify-between">
              <div className="flex items-center">
                <Smartphone size={16} className="text-gray-600 mr-2" />
                <span className="text-sm font-medium text-gray-700">Mobile View</span>
              </div>
              <span className="text-xs text-gray-500">375×667px</span>
            </div>
            <div className="p-2">
              <img 
                src={screenshots.mobile} 
                alt="Mobile screenshot" 
                className="w-full h-64 object-cover"
              />
            </div>
          </div>
        ) : (
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
                <span className="text-gray-500 text-sm">No mobile screenshot available</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ScreenshotsTab; 