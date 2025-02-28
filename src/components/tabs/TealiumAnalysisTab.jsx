import React from 'react';
import { AlertCircle, CheckCircle, Database, FileCode, Clock, BarChart2, Layers, Code } from 'lucide-react';

function TealiumAnalysisTab() {
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
            <span className="text-xs bg-teal-100 text-teal-800 px-2.5 py-0.5 rounded-full">utag_data detected</span>
          </div>
          <div className="p-4">
            <div className="mb-4">
              <div className="flex justify-between items-center mb-2">
                <p className="text-sm font-medium text-gray-700">Data Layer Variables</p>
                <span className="text-xs text-gray-500">14 variables found</span>
              </div>
              <div className="bg-gray-50 p-3 rounded border overflow-x-auto">
                <pre className="text-xs text-gray-800 whitespace-pre-wrap">
{`{
  "page_name": "homepage",
  "page_type": "landing",
  "user_id": "anonymous",
  "visitor_type": "new",
  "site_section": "product",
  "product_category": "enterprise",
  "ab_test_id": "homepage-cta-test-43",
  "ab_test_variant": "variant-b",
  "device_type": "desktop",
  "traffic_source": "organic",
  "utm_campaign": null,
  "utm_source": null,
  "language": "en-us",
  "country_code": "us"
}`}
                </pre>
              </div>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-700 mb-2">Data Layer Inconsistencies</p>
              <div className="flex items-start">
                <div className="mt-0.5 flex-shrink-0 w-5 h-5 flex items-center justify-center bg-yellow-100 rounded-full mr-3">
                  <AlertCircle size={12} className="text-yellow-600" />
                </div>
                <p className="text-sm text-gray-700">Non-standard variable naming convention detected: "product_category" vs "productCategory" on other pages</p>
              </div>
            </div>
          </div>
        </div>
        
        {/* Event Mapping */}
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
                  <tr>
                    <td className="px-3 py-2">
                      <div className="flex items-center">
                        <span className="bg-green-100 text-green-800 text-xs px-2 py-0.5 rounded">Page View</span>
                      </div>
                    </td>
                    <td className="px-3 py-2 text-gray-700">Page Load</td>
                    <td className="px-3 py-2 text-gray-700">Base data layer + page_name, page_type</td>
                  </tr>
                  <tr>
                    <td className="px-3 py-2">
                      <div className="flex items-center">
                        <span className="bg-blue-100 text-blue-800 text-xs px-2 py-0.5 rounded">Click</span>
                      </div>
                    </td>
                    <td className="px-3 py-2 text-gray-700">CTA Button Click</td>
                    <td className="px-3 py-2 text-gray-700">event_name: "cta_click", cta_text, cta_location</td>
                  </tr>
                  <tr>
                    <td className="px-3 py-2">
                      <div className="flex items-center">
                        <span className="bg-blue-100 text-blue-800 text-xs px-2 py-0.5 rounded">Click</span>
                      </div>
                    </td>
                    <td className="px-3 py-2 text-gray-700">Navigation Link Click</td>
                    <td className="px-3 py-2 text-gray-700">event_name: "nav_click", link_text, link_url</td>
                  </tr>
                  <tr>
                    <td className="px-3 py-2">
                      <div className="flex items-center">
                        <span className="bg-purple-100 text-purple-800 text-xs px-2 py-0.5 rounded">Form</span>
                      </div>
                    </td>
                    <td className="px-3 py-2 text-gray-700">Form Submission</td>
                    <td className="px-3 py-2 text-gray-700">event_name: "form_submit", form_name, form_step</td>
                  </tr>
                  <tr>
                    <td className="px-3 py-2">
                      <div className="flex items-center">
                        <span className="bg-orange-100 text-orange-800 text-xs px-2 py-0.5 rounded">Video</span>
                      </div>
                    </td>
                    <td className="px-3 py-2 text-gray-700">Video Play</td>
                    <td className="px-3 py-2 text-gray-700">event_name: "video_play", video_title, video_duration</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
        
        {/* Tag Analysis */}
        <div className="border rounded-lg overflow-hidden">
          <div className="bg-gray-50 px-4 py-3 border-b flex items-center">
            <Layers size={16} className="text-purple-600 mr-2" />
            <h4 className="font-medium text-gray-700">Tag Configuration Analysis</h4>
          </div>
          <div className="p-4">
            <div className="mb-4">
              <p className="text-sm font-medium text-gray-700 mb-2">Active Tags (7)</p>
              <div className="flex flex-wrap gap-2">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  <svg className="mr-1 h-2 w-2" fill="currentColor" viewBox="0 0 8 8"><circle cx="4" cy="4" r="3" /></svg>
                  Google Analytics 4
                </span>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  <svg className="mr-1 h-2 w-2" fill="currentColor" viewBox="0 0 8 8"><circle cx="4" cy="4" r="3" /></svg>
                  Google Ads
                </span>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  <svg className="mr-1 h-2 w-2" fill="currentColor" viewBox="0 0 8 8"><circle cx="4" cy="4" r="3" /></svg>
                  Facebook Pixel
                </span>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  <svg className="mr-1 h-2 w-2" fill="currentColor" viewBox="0 0 8 8"><circle cx="4" cy="4" r="3" /></svg>
                  Hotjar
                </span>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  <svg className="mr-1 h-2 w-2" fill="currentColor" viewBox="0 0 8 8"><circle cx="4" cy="4" r="3" /></svg>
                  LinkedIn Insight
                </span>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  <svg className="mr-1 h-2 w-2" fill="currentColor" viewBox="0 0 8 8"><circle cx="4" cy="4" r="3" /></svg>
                  Marketo
                </span>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  <svg className="mr-1 h-2 w-2" fill="currentColor" viewBox="0 0 8 8"><circle cx="4" cy="4" r="3" /></svg>
                  Custom Vendor Script
                </span>
              </div>
            </div>
            
            <div className="mb-4">
              <p className="text-sm font-medium text-gray-700 mb-2">Data Mapping Issues</p>
              <div className="space-y-3">
                <div className="flex items-start">
                  <div className="mt-0.5 flex-shrink-0 w-5 h-5 flex items-center justify-center bg-red-100 rounded-full mr-3">
                    <AlertCircle size={12} className="text-red-600" />
                  </div>
                  <p className="text-sm text-gray-700">Google Analytics 4 conversion event missing required parameters: Missing "value" parameter for purchase events</p>
                </div>
                <div className="flex items-start">
                  <div className="mt-0.5 flex-shrink-0 w-5 h-5 flex items-center justify-center bg-yellow-100 rounded-full mr-3">
                    <AlertCircle size={12} className="text-yellow-600" />
                  </div>
                  <p className="text-sm text-gray-700">Facebook Pixel using non-standard event names: Using "started_registration" instead of standard "initiate_checkout"</p>
                </div>
              </div>
            </div>
            
            <div>
              <p className="text-sm font-medium text-gray-700 mb-2">Implementation Recommendations</p>
              <ul className="list-disc pl-5 text-sm text-gray-700 space-y-1">
                <li>Standardize variable naming convention across all pages</li>
                <li>Add missing "value" parameter to GA4 purchase events</li>
                <li>Use Facebook standard event names for better integration</li>
                <li>Update event naming convention to follow camelCase for consistency</li>
                <li>Consider consolidating redundant events firing on the same user actions</li>
              </ul>
            </div>
          </div>
        </div>
        
        {/* Load Time Impact */}
        <div className="border rounded-lg overflow-hidden">
          <div className="bg-gray-50 px-4 py-3 border-b flex items-center">
            <Clock size={16} className="text-red-600 mr-2" />
            <h4 className="font-medium text-gray-700">Performance Impact</h4>
          </div>
          <div className="p-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
              <div className="bg-gray-50 p-3 rounded border">
                <p className="text-xs text-gray-500 mb-1">Tealium Library Size</p>
                <p className="text-lg font-medium text-gray-800">156 KB</p>
              </div>
              <div className="bg-gray-50 p-3 rounded border">
                <p className="text-xs text-gray-500 mb-1">Total Tag Load Time</p>
                <p className="text-lg font-medium text-gray-800">1.2s</p>
              </div>
              <div className="bg-gray-50 p-3 rounded border">
                <p className="text-xs text-gray-500 mb-1">Number of Network Requests</p>
                <p className="text-lg font-medium text-gray-800">14</p>
              </div>
              <div className="bg-gray-50 p-3 rounded border">
                <p className="text-xs text-gray-500 mb-1">Impact on Page Load</p>
                <p className="text-lg font-medium text-gray-800">+18.7%</p>
              </div>
            </div>
            
            <div>
              <p className="text-sm font-medium text-gray-700 mb-2">Performance Recommendations</p>
              <ul className="list-disc pl-5 text-sm text-gray-700 space-y-1">
                <li>Consider using server-side tag manager to reduce client-side impact</li>
                <li>Remove redundant tags firing identical data to the same platform</li>
                <li>Implement tag loading prioritization for critical vs. non-critical tags</li>
                <li>Consolidate multiple analytics vendors where functionality overlaps</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default TealiumAnalysisTab; 