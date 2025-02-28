import React, { useEffect, useState } from 'react';
import { AlertCircle, CheckCircle, Database, FileCode, Clock, BarChart2, Layers, Code } from 'lucide-react';
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
        const response = await getTealiumAnalysis(analysisId);
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
  if (!tealiumData || !tealiumData.data_layer) {
    return (
      <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
        <p className="text-yellow-700">No Tealium implementation detected on this website.</p>
      </div>
    );
  }

  const { 
    data_layer = {}, 
    events = [], 
    tags = [], 
    issues = [], 
    recommendations = [],
    performance = {}
  } = tealiumData;

  return (
    <div>
      <h3 className="text-lg font-medium text-gray-800 mb-4">Tealium Implementation Analysis</h3>
      
      <div className="space-y-6">
        {/* Data Layer Overview */}
        <div className="border rounded-lg overflow-hidden">
          <div className="bg-gray-50 px-4 py-3 border-b flex items-center justify-between">
            <div className="flex items-center">
              <Database size={16} className="text-teal-600 mr-2" />
              <h4 className="font-medium text-gray-700">Tealium Data Layer</h4>
            </div>
            <span className="text-xs bg-teal-100 text-teal-800 px-2.5 py-0.5 rounded-full">
              {data_layer.type || "utag_data"} detected
            </span>
          </div>
          <div className="p-4">
            <div className="mb-4">
              <div className="flex justify-between items-center mb-2">
                <p className="text-sm font-medium text-gray-700">Data Layer Variables</p>
                <span className="text-xs text-gray-500">
                  {data_layer.variables ? Object.keys(data_layer.variables).length : 0} variables found
                </span>
              </div>
              <div className="bg-gray-50 p-3 rounded border overflow-x-auto">
                <pre className="text-xs text-gray-800 whitespace-pre-wrap">
                  {JSON.stringify(data_layer.variables || {}, null, 2)}
                </pre>
              </div>
            </div>
            {data_layer.inconsistencies && data_layer.inconsistencies.length > 0 && (
              <div>
                <p className="text-sm font-medium text-gray-700 mb-2">Data Layer Inconsistencies</p>
                {data_layer.inconsistencies.map((inconsistency, index) => (
                  <div key={index} className="flex items-start">
                    <div className="mt-0.5 flex-shrink-0 w-5 h-5 flex items-center justify-center bg-yellow-100 rounded-full mr-3">
                      <AlertCircle size={12} className="text-yellow-600" />
                    </div>
                    <p className="text-sm text-gray-700">{inconsistency}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
        
        {/* Event Mapping */}
        {events && events.length > 0 && (
          <div className="border rounded-lg overflow-hidden">
            <div className="bg-gray-50 px-4 py-3 border-b flex items-center">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-indigo-600 mr-2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
              <h4 className="font-medium text-gray-700">Event Triggers & Mapping</h4>
            </div>
            <div className="p-4">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead>
                    <tr>
                      <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Event Type</th>
                      <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Trigger</th>
                      <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Data Sent</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200 text-sm">
                    {events.map((event, index) => (
                      <tr key={index}>
                        <td className="px-3 py-2">
                          <div className="flex items-center">
                            <span className={`bg-${event.color || 'blue'}-100 text-${event.color || 'blue'}-800 text-xs px-2 py-0.5 rounded`}>
                              {event.type}
                            </span>
                          </div>
                        </td>
                        <td className="px-3 py-2 text-gray-700">{event.trigger}</td>
                        <td className="px-3 py-2 text-gray-700">{event.data}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
        
        {/* Tag Analysis */}
        {tags && tags.length > 0 && (
          <div className="border rounded-lg overflow-hidden">
            <div className="bg-gray-50 px-4 py-3 border-b flex items-center">
              <Layers size={16} className="text-purple-600 mr-2" />
              <h4 className="font-medium text-gray-700">Tag Configuration Analysis</h4>
            </div>
            <div className="p-4">
              <div className="mb-4">
                <p className="text-sm font-medium text-gray-700 mb-2">Active Tags ({tags.length})</p>
                <div className="flex flex-wrap gap-2">
                  {tags.map((tag, index) => (
                    <span key={index} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      <svg className="mr-1 h-2 w-2" fill="currentColor" viewBox="0 0 8 8"><circle cx="4" cy="4" r="3" /></svg>
                      {tag.name}
                    </span>
                  ))}
                </div>
              </div>
              
              {issues && issues.length > 0 && (
                <div className="mb-4">
                  <p className="text-sm font-medium text-gray-700 mb-2">Data Mapping Issues</p>
                  <div className="space-y-3">
                    {issues.map((issue, index) => (
                      <div key={index} className="flex items-start">
                        <div className={`mt-0.5 flex-shrink-0 w-5 h-5 flex items-center justify-center bg-${issue.severity === 'high' ? 'red' : 'yellow'}-100 rounded-full mr-3`}>
                          <AlertCircle size={12} className={`text-${issue.severity === 'high' ? 'red' : 'yellow'}-600`} />
                        </div>
                        <p className="text-sm text-gray-700">{issue.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {recommendations && recommendations.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">Implementation Recommendations</p>
                  <ul className="list-disc pl-5 text-sm text-gray-700 space-y-1">
                    {recommendations.map((recommendation, index) => (
                      <li key={index}>{recommendation}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
        
        {/* Load Time Impact */}
        {performance && Object.keys(performance).length > 0 && (
          <div className="border rounded-lg overflow-hidden">
            <div className="bg-gray-50 px-4 py-3 border-b flex items-center">
              <Clock size={16} className="text-red-600 mr-2" />
              <h4 className="font-medium text-gray-700">Performance Impact</h4>
            </div>
            <div className="p-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
                <div className="bg-gray-50 p-3 rounded border">
                  <p className="text-xs text-gray-500 mb-1">Tealium Library Size</p>
                  <p className="text-lg font-medium text-gray-800">{performance.library_size || 'N/A'}</p>
                </div>
                <div className="bg-gray-50 p-3 rounded border">
                  <p className="text-xs text-gray-500 mb-1">Total Tag Load Time</p>
                  <p className="text-lg font-medium text-gray-800">{performance.load_time || 'N/A'}</p>
                </div>
                <div className="bg-gray-50 p-3 rounded border">
                  <p className="text-xs text-gray-500 mb-1">Number of Network Requests</p>
                  <p className="text-lg font-medium text-gray-800">{performance.network_requests || 'N/A'}</p>
                </div>
                <div className="bg-gray-50 p-3 rounded border">
                  <p className="text-xs text-gray-500 mb-1">Impact on Page Load</p>
                  <p className="text-lg font-medium text-gray-800">{performance.page_load_impact || 'N/A'}</p>
                </div>
              </div>
              
              {performance.recommendations && performance.recommendations.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">Performance Recommendations</p>
                  <ul className="list-disc pl-5 text-sm text-gray-700 space-y-1">
                    {performance.recommendations.map((recommendation, index) => (
                      <li key={index}>{recommendation}</li>
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