import React, { useEffect, useState } from 'react';
import { AlertCircle, CheckCircle, Database, FileCode, Clock, BarChart2, Layers, Info } from 'lucide-react';
import { getTealiumAnalysis } from '../../services/api';

function TealiumAnalysisTab({ analysisId }) {
  const [tealiumData, setTealiumData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchTealiumData = async () => {
      try {
        if (!analysisId) return;
        
        setLoading(true);
        console.log('Fetching Tealium data for analysis ID:', analysisId);
        
        // Use the existing getTealiumAnalysis function (which now includes cache busting)
        const response = await getTealiumAnalysis(analysisId);
        
        console.log('Tealium API full response:', response);
        console.log('Tealium detected:', response.detected);
        console.log('Tealium version:', response.version);
        console.log('Tags total count:', response.tags?.total);
        console.log('Tags details array (length):', response.tags?.details?.length);
        if (response.tags?.details?.length > 0) {
          console.log('First few tag details:', JSON.stringify(response.tags.details.slice(0, 3), null, 2));
        } else {
          console.log('No tag details found in the response');
        }
        
        setTealiumData(response);
        setLoading(false);
      } catch (error) {
        setError('Failed to load Tealium analysis data');
        setLoading(false);
        console.error('Error fetching Tealium data:', error);
      }
    };
  
    fetchTealiumData();
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

  // If no Tealium data was found
  if (!tealiumData || !tealiumData.detected) {
    return (
      <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
        <p className="text-yellow-700">No Tealium implementation detected on this website.</p>
      </div>
    );
  }

  const { 
    version = "Unknown", 
    profile = "Unknown",
    data_layer = { variables: {}, issues: [] }, 
    tags = { total: 0, active: 0, inactive: 0, details: [], issues: [] }, 
    performance = {}
  } = tealiumData;

  return (
    <div>
      <h3 className="text-lg font-medium text-gray-800 mb-4">Tealium Implementation Analysis</h3>
      
      <div className="bg-blue-50 border-l-4 border-blue-400 p-4 mb-6 rounded">
        <div className="flex items-center">
          <Info size={18} className="text-blue-600 mr-2" />
          <div>
            <p className="text-sm font-medium text-blue-800">
              Tealium detected
              <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full">Version: {version}</span>
              <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full">Profile: {profile}</span>
            </p>
            <p className="text-sm text-blue-700 mt-1">
              Analysis detected {tags.total} tags ({tags.active} active, {tags.inactive} inactive)
            </p>
          </div>
        </div>
      </div>
      
      <div className="space-y-6">
        {/* Data Layer Overview */}
        <div className="border rounded-lg overflow-hidden">
          <div className="bg-gray-50 px-4 py-3 border-b flex items-center justify-between">
            <div className="flex items-center">
              <Database size={16} className="text-teal-600 mr-2" />
              <h4 className="font-medium text-gray-700">Tealium Data Layer</h4>
            </div>
            <span className="text-xs bg-teal-100 text-teal-800 px-2.5 py-0.5 rounded-full">
              {Object.keys(data_layer.variables).length} variables found
            </span>
          </div>
          <div className="p-4">
            <div className="mb-4">
              <div className="flex justify-between items-center mb-2">
                <p className="text-sm font-medium text-gray-700">Data Layer Variables</p>
              </div>
              <div className="bg-gray-50 p-3 rounded border overflow-x-auto">
                <pre className="text-xs text-gray-800 whitespace-pre-wrap">
                  {JSON.stringify(data_layer.variables || {}, null, 2)}
                </pre>
              </div>
            </div>
            {data_layer.issues && data_layer.issues.length > 0 && (
              <div>
                <p className="text-sm font-medium text-gray-700 mb-2">Data Layer Issues</p>
                {data_layer.issues.map((issue, index) => (
                  <div key={index} className="flex items-start mb-2">
                    <div className="mt-0.5 flex-shrink-0 w-5 h-5 flex items-center justify-center bg-yellow-100 rounded-full mr-3">
                      <AlertCircle size={12} className="text-yellow-600" />
                    </div>
                    <p className="text-sm text-gray-700">{issue.description}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
        
        {/* Tag Configuration Analysis */}
        // Modified section of TealiumAnalysisTab.jsx
{/* Tag Configuration Analysis */}
<div className="border rounded-lg overflow-hidden">
  <div className="bg-gray-50 px-4 py-3 border-b flex items-center justify-between">
    <div className="flex items-center">
      <Layers size={16} className="text-purple-600 mr-2" />
      <h4 className="font-medium text-gray-700">Tag Configuration Analysis</h4>
    </div>
    <div className="flex space-x-2">
      <span className="text-xs bg-green-100 text-green-800 px-2.5 py-0.5 rounded-full">
        {tags.active} active
      </span>
      <span className="text-xs bg-gray-100 text-gray-800 px-2.5 py-0.5 rounded-full">
        {tags.inactive} inactive
      </span>
    </div>
  </div>
  <div className="p-4">
    {tags.details && tags.details.length > 0 ? (
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tag Number</th>
              <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
              <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
              <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {tags.details.map((tag, index) => (
              <tr key={index}>
                <td className="px-3 py-2 whitespace-nowrap text-sm font-medium text-gray-900">{tag.id}</td>
                <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">{tag.name}</td>
                <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    tag.category === 'analytics' ? 'bg-blue-100 text-blue-800' :
                    tag.category === 'advertising' ? 'bg-red-100 text-red-800' :
                    tag.category === 'user_experience' ? 'bg-green-100 text-green-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {tag.category}
                  </span>
                </td>
                <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                  {(tag.status === 'active' || tag.active === true) ? (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      <svg className="-ml-0.5 mr-1.5 h-2 w-2 text-green-400" fill="currentColor" viewBox="0 0 8 8">
                        <circle cx="4" cy="4" r="3" />
                      </svg>
                      Active
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                      <svg className="-ml-0.5 mr-1.5 h-2 w-2 text-gray-400" fill="currentColor" viewBox="0 0 8 8">
                        <circle cx="4" cy="4" r="3" />
                      </svg>
                      Inactive
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    ) : (
      <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <Info size={18} className="text-yellow-400" />
          </div>
          <div className="ml-3">
            <p className="text-sm text-yellow-700">
              <strong>Tags detected but no detailed information available.</strong>
            </p>
            <p className="text-sm text-yellow-700 mt-1">
              The analysis detected {tags.total} tags ({tags.active} active, {tags.inactive} inactive) 
              but detailed tag information was not captured during the analysis.
            </p>
          </div>
        </div>
      </div>
    )}
    
    {tags.issues && tags.issues.length > 0 && (
      <div className="mt-4">
        <p className="text-sm font-medium text-gray-700 mb-2">Tag Implementation Issues</p>
        <div className="space-y-3">
          {tags.issues.map((issue, index) => (
            <div key={index} className="flex items-start">
              <div className="mt-0.5 flex-shrink-0 w-5 h-5 flex items-center justify-center bg-yellow-100 rounded-full mr-3">
                <AlertCircle size={12} className="text-yellow-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-700">{issue.issue}</p>
                <p className="text-xs text-gray-500 mt-1">{issue.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    )}
  </div>
</div>  
        {/* Performance Impact */}
        {performance && (performance.total_size || performance.load_time || performance.request_count) && (
          <div className="border rounded-lg overflow-hidden">
            <div className="bg-gray-50 px-4 py-3 border-b flex items-center">
              <Clock size={16} className="text-red-600 mr-2" />
              <h4 className="font-medium text-gray-700">Performance Impact</h4>
            </div>
            <div className="p-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
                <div className="bg-gray-50 p-3 rounded border">
                  <p className="text-xs text-gray-500 mb-1">Total Size</p>
                  <p className="text-lg font-medium text-gray-800">{performance.total_size || 'N/A'} KB</p>
                </div>
                <div className="bg-gray-50 p-3 rounded border">
                  <p className="text-xs text-gray-500 mb-1">Load Time</p>
                  <p className="text-lg font-medium text-gray-800">{performance.load_time ? `${performance.load_time.toFixed(2)}s` : 'N/A'}</p>
                </div>
                <div className="bg-gray-50 p-3 rounded border">
                  <p className="text-xs text-gray-500 mb-1">Request Count</p>
                  <p className="text-lg font-medium text-gray-800">{performance.request_count || 'N/A'}</p>
                </div>
              </div>
              
              {performance.recommendations && performance.recommendations.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">Performance Recommendations</p>
                  <ul className="space-y-2">
                    {performance.recommendations.map((recommendation, index) => (
                      <li key={index} className="flex items-start">
                        <div className={`mt-0.5 flex-shrink-0 w-5 h-5 flex items-center justify-center bg-${recommendation.impact === 'high' ? 'red' : recommendation.impact === 'medium' ? 'yellow' : 'green'}-100 rounded-full mr-3`}>
                          <AlertCircle size={12} className={`text-${recommendation.impact === 'high' ? 'red' : recommendation.impact === 'medium' ? 'yellow' : 'green'}-600`} />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-700">{recommendation.description}</p>
                          {recommendation.implementation && (
                            <p className="text-xs text-gray-500 mt-1">{recommendation.implementation}</p>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}



export default TealiumAnalysisTab;