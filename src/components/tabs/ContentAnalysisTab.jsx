import React from 'react';
import { Eye, Target, FileText } from 'lucide-react';

function ContentAnalysisTab() {
  return (
    <div>
      <h3 className="text-lg font-medium text-gray-800 mb-4">AI Content Analysis</h3>
      
      <div className="space-y-6">
        <div className="border rounded-lg overflow-hidden">
          <div className="bg-gray-50 px-4 py-3 border-b flex items-center">
            <Eye size={16} className="text-gray-600 mr-2" />
            <h4 className="font-medium text-gray-700">Key Content Observations</h4>
          </div>
          <div className="p-4">
            <div className="prose max-w-none text-gray-700">
              <p>After analyzing the website, the following key observations inform my recommendations:</p>
              
              <ul className="mt-3 space-y-2">
                <li>The homepage leads with technical features rather than user benefits</li>
                <li>Navigation requires 3+ clicks to reach core product information</li>
                <li>Competitor analysis shows missing features in collaboration and reporting</li>
                <li>Messaging focuses on technical specifications instead of problem-solving</li>
                <li>Call-to-action language is generic ("Learn More", "Sign Up") rather than benefit-driven</li>
                <li>Limited social proof with only text testimonials, no case studies or metrics</li>
                <li>Mobile experience shows truncated content and difficult navigation</li>
              </ul>
            </div>
          </div>
        </div>
        
        <div className="border rounded-lg overflow-hidden">
          <div className="bg-gray-50 px-4 py-3 border-b flex items-center">
            <Target size={16} className="text-gray-600 mr-2" />
            <h4 className="font-medium text-gray-700">User Journey Analysis</h4>
          </div>
          <div className="p-4">
            <div className="prose max-w-none text-gray-700">
              <p>The current user journey has several points of friction:</p>
              
              <ol className="mt-3 space-y-2">
                <li><strong>Awareness:</strong> Value proposition isn't immediately clear on landing page</li>
                <li><strong>Interest:</strong> Benefits are buried in long paragraphs of text</li>
                <li><strong>Consideration:</strong> Missing comparison information for decision-making</li>
                <li><strong>Conversion:</strong> Signup process requires unnecessary information upfront</li>
                <li><strong>Retention:</strong> Limited onboarding guidance after signup</li>
              </ol>
              
              <p className="mt-4">These observations support the product enhancement recommendations in the summary tab.</p>
            </div>
          </div>
        </div>
        
        <div className="border rounded-lg overflow-hidden">
          <div className="bg-gray-50 px-4 py-3 border-b flex items-center">
            <FileText size={16} className="text-gray-600 mr-2" />
            <h4 className="font-medium text-gray-700">Extracted Key Content</h4>
          </div>
          <div className="p-4">
            <div className="space-y-3">
              <div>
                <p className="text-sm text-gray-500">Current Headline</p>
                <p className="text-gray-800 font-medium">"The Solution You Need"</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Primary Call to Action</p>
                <p className="text-gray-800 font-medium">"Sign Up Today"</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Feature Highlights</p>
                <p className="text-gray-800">• "Customizable Dashboard" • "Advanced Reports" • "Team Management"</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ContentAnalysisTab; 