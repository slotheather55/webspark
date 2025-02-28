import React from 'react';
import { Share2, Copy, ChevronDown, ChevronRight, Check, Bot, MessageSquare, FileText, Target, Layers } from 'lucide-react';
import { SECTIONS } from '../../ProductManagerEnhancer';

const SummaryTab = ({ expandedSections, toggleSection }) => {
  return (
    <div>
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-800">AI-Generated Product Enhancement Ideas</h3>
          <div className="flex space-x-2">
            <button className="flex items-center text-sm text-gray-600 hover:text-gray-800">
              <Share2 size={14} className="mr-1" />
              Share
            </button>
            <button className="flex items-center text-sm text-gray-600 hover:text-gray-800">
              <Copy size={14} className="mr-1" />
              Export
            </button>
          </div>
        </div>
        
        <div className="mt-4 p-4 bg-yellow-50 border-l-4 border-yellow-400 rounded">
          <div className="flex">
            <div className="flex-shrink-0">
              <Bot className="h-5 w-5 text-yellow-400" />
            </div>
            <div className="ml-3">
              <p className="text-sm text-yellow-700">
                AI analysis of example.com suggests <strong>18 potential product improvements</strong> across 4 categories.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Value Proposition Improvements */}
      <div className="mb-4 border border-gray-200 rounded-lg overflow-hidden">
        <button
          className="w-full flex items-center justify-between p-4 bg-gray-50"
          onClick={() => toggleSection(SECTIONS.VALUE)}
        >
          <div className="flex items-center">
            <div className="w-8 h-8 flex items-center justify-center bg-blue-100 rounded-full mr-3">
              <MessageSquare size={16} className="text-blue-600" />
            </div>
            <div>
              <h4 className="font-medium text-gray-800">Value Proposition Enhancements</h4>
              <p className="text-sm text-gray-500">5 suggestions</p>
            </div>
          </div>
          {expandedSections[SECTIONS.VALUE] ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
        </button>
        
        {expandedSections[SECTIONS.VALUE] && (
          <div className="p-4">
            <ul className="space-y-3">
              <li className="flex items-start">
                <div className="mt-0.5 flex-shrink-0 w-5 h-5 flex items-center justify-center bg-green-100 rounded-full mr-3">
                  <Check size={12} className="text-green-600" />
                </div>
                <div>
                  <p className="text-gray-800">Clarify primary value proposition on homepage</p>
                  <p className="text-sm text-gray-500 mt-1">Current headline is vague. Replace "The Solution You Need" with specific benefit statement like "Save 5 hours per week on project management tasks."</p>
                </div>
              </li>
              <li className="flex items-start">
                <div className="mt-0.5 flex-shrink-0 w-5 h-5 flex items-center justify-center bg-green-100 rounded-full mr-3">
                  <Check size={12} className="text-green-600" />
                </div>
                <div>
                  <p className="text-gray-800">Add social proof section with quantifiable results</p>
                  <p className="text-sm text-gray-500 mt-1">Missing concrete evidence of value. Add "Trusted by 500+ teams" with case studies showing measurable outcomes.</p>
                </div>
              </li>
              <li className="flex items-start">
                <div className="mt-0.5 flex-shrink-0 w-5 h-5 flex items-center justify-center bg-green-100 rounded-full mr-3">
                  <Check size={12} className="text-green-600" />
                </div>
                <div>
                  <p className="text-gray-800">Differentiate from competitors more clearly</p>
                  <p className="text-sm text-gray-500 mt-1">Add comparison section highlighting unique advantages. Current messaging doesn't address why users should choose you over alternatives.</p>
                </div>
              </li>
              <li className="mt-2">
                <button className="text-sm text-indigo-600 hover:text-indigo-800">
                  View 2 more value proposition suggestions →
                </button>
              </li>
            </ul>
          </div>
        )}
      </div>
      
      {/* Content Improvements */}
      <div className="mb-4 border border-gray-200 rounded-lg overflow-hidden">
        <button
          className="w-full flex items-center justify-between p-4 bg-gray-50"
          onClick={() => toggleSection(SECTIONS.CONTENT)}
        >
          <div className="flex items-center">
            <div className="w-8 h-8 flex items-center justify-center bg-purple-100 rounded-full mr-3">
              <FileText size={16} className="text-purple-600" />
            </div>
            <div>
              <h4 className="font-medium text-gray-800">Content Strategy Improvements</h4>
              <p className="text-sm text-gray-500">4 suggestions</p>
            </div>
          </div>
          {expandedSections[SECTIONS.CONTENT] ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
        </button>
        
        {expandedSections[SECTIONS.CONTENT] && (
          <div className="p-4">
            <ul className="space-y-3">
              <li className="flex items-start">
                <div className="mt-0.5 flex-shrink-0 w-5 h-5 flex items-center justify-center bg-green-100 rounded-full mr-3">
                  <Check size={12} className="text-green-600" />
                </div>
                <div>
                  <p className="text-gray-800">Create problem-solution content structure</p>
                  <p className="text-sm text-gray-500 mt-1">Reorganize content to first identify user pain points, then present your solution with clear benefits.</p>
                </div>
              </li>
              <li className="flex items-start">
                <div className="mt-0.5 flex-shrink-0 w-5 h-5 flex items-center justify-center bg-green-100 rounded-full mr-3">
                  <Check size={12} className="text-green-600" />
                </div>
                <div>
                  <p className="text-gray-800">Develop user-focused documentation</p>
                  <p className="text-sm text-gray-500 mt-1">Current help section is feature-oriented. Restructure around common user tasks and goals.</p>
                </div>
              </li>
              <li className="mt-2">
                <button className="text-sm text-indigo-600 hover:text-indigo-800">
                  View 2 more content suggestions →
                </button>
              </li>
            </ul>
          </div>
        )}
      </div>
      
      {/* Feature Improvements */}
      <div className="mb-4 border border-gray-200 rounded-lg overflow-hidden">
        <button
          className="w-full flex items-center justify-between p-4 bg-gray-50"
          onClick={() => toggleSection(SECTIONS.FEATURES)}
        >
          <div className="flex items-center">
            <div className="w-8 h-8 flex items-center justify-center bg-green-100 rounded-full mr-3">
              <Layers size={16} className="text-green-600" />
            </div>
            <div>
              <h4 className="font-medium text-gray-800">Product Feature Opportunities</h4>
              <p className="text-sm text-gray-500">6 suggestions</p>
            </div>
          </div>
          {expandedSections[SECTIONS.FEATURES] ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
        </button>
        
        {expandedSections[SECTIONS.FEATURES] && (
          <div className="p-4">
            <ul className="space-y-3">
              <li className="flex items-start">
                <div className="mt-0.5 flex-shrink-0 w-5 h-5 flex items-center justify-center bg-green-100 rounded-full mr-3">
                  <Check size={12} className="text-green-600" />
                </div>
                <div>
                  <p className="text-gray-800">Add collaborative workspace feature</p>
                  <p className="text-sm text-gray-500 mt-1">Competitors offer team collaboration spaces. Add shared workspaces with real-time editing capabilities.</p>
                </div>
              </li>
              <li className="flex items-start">
                <div className="mt-0.5 flex-shrink-0 w-5 h-5 flex items-center justify-center bg-green-100 rounded-full mr-3">
                  <Check size={12} className="text-green-600" />
                </div>
                <div>
                  <p className="text-gray-800">Develop mobile companion app</p>
                  <p className="text-sm text-gray-500 mt-1">Website mentions "access anywhere" but lacks dedicated mobile experience. Create companion app with core functionality.</p>
                </div>
              </li>
              <li className="flex items-start">
                <div className="mt-0.5 flex-shrink-0 w-5 h-5 flex items-center justify-center bg-green-100 rounded-full mr-3">
                  <Check size={12} className="text-green-600" />
                </div>
                <div>
                  <p className="text-gray-800">Implement data visualization dashboard</p>
                  <p className="text-sm text-gray-500 mt-1">Current reporting is text-heavy. Add interactive charts and customizable dashboards for better data insights.</p>
                </div>
              </li>
              <li className="mt-2">
                <button className="text-sm text-indigo-600 hover:text-indigo-800">
                  View 3 more feature suggestions →
                </button>
              </li>
            </ul>
          </div>
        )}
      </div>
      
      {/* Conversion Improvements */}
      <div className="mb-4 border border-gray-200 rounded-lg overflow-hidden">
        <button
          className="w-full flex items-center justify-between p-4 bg-gray-50"
          onClick={() => toggleSection(SECTIONS.CONVERSION)}
        >
          <div className="flex items-center">
            <div className="w-8 h-8 flex items-center justify-center bg-red-100 rounded-full mr-3">
              <Target size={16} className="text-red-600" />
            </div>
            <div>
              <h4 className="font-medium text-gray-800">Conversion Optimization</h4>
              <p className="text-sm text-gray-500">3 suggestions</p>
            </div>
          </div>
          {expandedSections[SECTIONS.CONVERSION] ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
        </button>
        
        {expandedSections[SECTIONS.CONVERSION] && (
          <div className="p-4">
            <ul className="space-y-3">
              <li className="flex items-start">
                <div className="mt-0.5 flex-shrink-0 w-5 h-5 flex items-center justify-center bg-green-100 rounded-full mr-3">
                  <Check size={12} className="text-green-600" />
                </div>
                <div>
                  <p className="text-gray-800">Simplify signup process</p>
                  <p className="text-sm text-gray-500 mt-1">Current form requests 8 fields. Reduce to essential information only (email, password) and move other fields to post-signup profile completion.</p>
                </div>
              </li>
              <li className="flex items-start">
                <div className="mt-0.5 flex-shrink-0 w-5 h-5 flex items-center justify-center bg-green-100 rounded-full mr-3">
                  <Check size={12} className="text-green-600" />
                </div>
                <div>
                  <p className="text-gray-800">Add pricing calculator</p>
                  <p className="text-sm text-gray-500 mt-1">Create interactive calculator showing potential savings/ROI based on user inputs to make value proposition concrete.</p>
                </div>
              </li>
              <li className="flex items-start">
                <div className="mt-0.5 flex-shrink-0 w-5 h-5 flex items-center justify-center bg-green-100 rounded-full mr-3">
                  <Check size={12} className="text-green-600" />
                </div>
                <div>
                  <p className="text-gray-800">Implement competitive trial period</p>
                  <p className="text-sm text-gray-500 mt-1">Current 7-day trial is shorter than industry standard. Extend to 14 or 30 days to align with competitors and give users more time to experience value.</p>
                </div>
              </li>
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

export default SummaryTab; 