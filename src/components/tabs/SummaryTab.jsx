import React, { useState, useEffect } from 'react';
import { Share2, Copy, ChevronDown, ChevronRight, Check, Bot, MessageSquare, FileText, Target, Layers } from 'lucide-react';
import { SECTIONS } from '../../ProductManagerEnhancer';
import { generateEnhancements } from '../../services/api';

const SummaryTab = ({ expandedSections, toggleSection, analysisId, analysisResults }) => {
  const [enhancements, setEnhancements] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showAllSuggestions, setShowAllSuggestions] = useState({});

  useEffect(() => {
    const fetchEnhancements = async () => {
      if (!analysisId) return;
      
      try {
        setLoading(true);
        // If enhancements are already in the analysis results, use them
        if (analysisResults?.enhancements) {
          setEnhancements(analysisResults.enhancements);
        } else {
          // Otherwise, generate them
          const response = await generateEnhancements(analysisId, [
            'value_proposition', 'content', 'features', 'conversion'
          ]);
          setEnhancements(response.enhancements);
        }
        setLoading(false);
      } catch (error) {
        setError('Failed to load enhancement suggestions');
        setLoading(false);
        console.error('Error fetching enhancements:', error);
      }
    };

    fetchEnhancements();
  }, [analysisId, analysisResults]);

  const toggleShowAll = (section) => {
    setShowAllSuggestions({
      ...showAllSuggestions,
      [section]: !showAllSuggestions[section]
    });
  };

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

  // If no enhancements data was found
  if (!enhancements) {
    return (
      <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
        <p className="text-yellow-700">No enhancement suggestions available yet. Please generate enhancements first.</p>
      </div>
    );
  }

  const {
    value_proposition = [],
    content = [],
    features = [],
    conversion = []
  } = enhancements;

  // Calculate total number of suggestions
  const totalSuggestions = value_proposition.length + content.length + features.length + conversion.length;

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
                AI analysis of {analysisResults?.url || 'this website'} suggests <strong>{totalSuggestions} potential product improvements</strong> across 4 categories.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Value Proposition Improvements */}
      {value_proposition.length > 0 && (
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
                <p className="text-sm text-gray-500">{value_proposition.length} suggestions</p>
              </div>
            </div>
            {expandedSections[SECTIONS.VALUE] ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
          </button>
          
          {expandedSections[SECTIONS.VALUE] && (
            <div className="p-4">
              <ul className="space-y-3">
                {(showAllSuggestions[SECTIONS.VALUE] ? value_proposition : value_proposition.slice(0, 3)).map((suggestion, index) => (
                  <li key={index} className="flex items-start">
                    <div className="mt-0.5 flex-shrink-0 w-5 h-5 flex items-center justify-center bg-green-100 rounded-full mr-3">
                      <Check size={12} className="text-green-600" />
                    </div>
                    <div>
                      <p className="text-gray-800">{suggestion.title}</p>
                      <p className="text-sm text-gray-500 mt-1">{suggestion.description}</p>
                    </div>
                  </li>
                ))}
                {value_proposition.length > 3 && !showAllSuggestions[SECTIONS.VALUE] && (
                  <li className="mt-2">
                    <button 
                      className="text-sm text-indigo-600 hover:text-indigo-800"
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleShowAll(SECTIONS.VALUE);
                      }}
                    >
                      View {value_proposition.length - 3} more value proposition suggestions →
                    </button>
                  </li>
                )}
                {showAllSuggestions[SECTIONS.VALUE] && (
                  <li className="mt-2">
                    <button 
                      className="text-sm text-indigo-600 hover:text-indigo-800"
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleShowAll(SECTIONS.VALUE);
                      }}
                    >
                      Show fewer suggestions
                    </button>
                  </li>
                )}
              </ul>
            </div>
          )}
        </div>
      )}
      
      {/* Content Improvements */}
      {content.length > 0 && (
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
                <p className="text-sm text-gray-500">{content.length} suggestions</p>
              </div>
            </div>
            {expandedSections[SECTIONS.CONTENT] ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
          </button>
          
          {expandedSections[SECTIONS.CONTENT] && (
            <div className="p-4">
              <ul className="space-y-3">
                {(showAllSuggestions[SECTIONS.CONTENT] ? content : content.slice(0, 3)).map((suggestion, index) => (
                  <li key={index} className="flex items-start">
                    <div className="mt-0.5 flex-shrink-0 w-5 h-5 flex items-center justify-center bg-green-100 rounded-full mr-3">
                      <Check size={12} className="text-green-600" />
                    </div>
                    <div>
                      <p className="text-gray-800">{suggestion.title}</p>
                      <p className="text-sm text-gray-500 mt-1">{suggestion.description}</p>
                    </div>
                  </li>
                ))}
                {content.length > 3 && !showAllSuggestions[SECTIONS.CONTENT] && (
                  <li className="mt-2">
                    <button 
                      className="text-sm text-indigo-600 hover:text-indigo-800"
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleShowAll(SECTIONS.CONTENT);
                      }}
                    >
                      View {content.length - 3} more content suggestions →
                    </button>
                  </li>
                )}
                {showAllSuggestions[SECTIONS.CONTENT] && (
                  <li className="mt-2">
                    <button 
                      className="text-sm text-indigo-600 hover:text-indigo-800"
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleShowAll(SECTIONS.CONTENT);
                      }}
                    >
                      Show fewer suggestions
                    </button>
                  </li>
                )}
              </ul>
            </div>
          )}
        </div>
      )}
      
      {/* Feature Improvements */}
      {features.length > 0 && (
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
                <p className="text-sm text-gray-500">{features.length} suggestions</p>
              </div>
            </div>
            {expandedSections[SECTIONS.FEATURES] ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
          </button>
          
          {expandedSections[SECTIONS.FEATURES] && (
            <div className="p-4">
              <ul className="space-y-3">
                {(showAllSuggestions[SECTIONS.FEATURES] ? features : features.slice(0, 3)).map((suggestion, index) => (
                  <li key={index} className="flex items-start">
                    <div className="mt-0.5 flex-shrink-0 w-5 h-5 flex items-center justify-center bg-green-100 rounded-full mr-3">
                      <Check size={12} className="text-green-600" />
                    </div>
                    <div>
                      <p className="text-gray-800">{suggestion.title}</p>
                      <p className="text-sm text-gray-500 mt-1">{suggestion.description}</p>
                    </div>
                  </li>
                ))}
                {features.length > 3 && !showAllSuggestions[SECTIONS.FEATURES] && (
                  <li className="mt-2">
                    <button 
                      className="text-sm text-indigo-600 hover:text-indigo-800"
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleShowAll(SECTIONS.FEATURES);
                      }}
                    >
                      View {features.length - 3} more feature suggestions →
                    </button>
                  </li>
                )}
                {showAllSuggestions[SECTIONS.FEATURES] && (
                  <li className="mt-2">
                    <button 
                      className="text-sm text-indigo-600 hover:text-indigo-800"
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleShowAll(SECTIONS.FEATURES);
                      }}
                    >
                      Show fewer suggestions
                    </button>
                  </li>
                )}
              </ul>
            </div>
          )}
        </div>
      )}
      
      {/* Conversion Improvements */}
      {conversion.length > 0 && (
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
                <p className="text-sm text-gray-500">{conversion.length} suggestions</p>
              </div>
            </div>
            {expandedSections[SECTIONS.CONVERSION] ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
          </button>
          
          {expandedSections[SECTIONS.CONVERSION] && (
            <div className="p-4">
              <ul className="space-y-3">
                {(showAllSuggestions[SECTIONS.CONVERSION] ? conversion : conversion.slice(0, 3)).map((suggestion, index) => (
                  <li key={index} className="flex items-start">
                    <div className="mt-0.5 flex-shrink-0 w-5 h-5 flex items-center justify-center bg-green-100 rounded-full mr-3">
                      <Check size={12} className="text-green-600" />
                    </div>
                    <div>
                      <p className="text-gray-800">{suggestion.title}</p>
                      <p className="text-sm text-gray-500 mt-1">{suggestion.description}</p>
                    </div>
                  </li>
                ))}
                {conversion.length > 3 && !showAllSuggestions[SECTIONS.CONVERSION] && (
                  <li className="mt-2">
                    <button 
                      className="text-sm text-indigo-600 hover:text-indigo-800"
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleShowAll(SECTIONS.CONVERSION);
                      }}
                    >
                      View {conversion.length - 3} more conversion suggestions →
                    </button>
                  </li>
                )}
                {showAllSuggestions[SECTIONS.CONVERSION] && (
                  <li className="mt-2">
                    <button 
                      className="text-sm text-indigo-600 hover:text-indigo-800"
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleShowAll(SECTIONS.CONVERSION);
                      }}
                    >
                      Show fewer suggestions
                    </button>
                  </li>
                )}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SummaryTab; 