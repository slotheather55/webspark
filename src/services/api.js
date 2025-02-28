const API_BASE_URL = '/api/v1';

export const analyzeWebsite = async (url, options = {}) => {
  try {
    // Ensure URL has a protocol
    if (url && !url.match(/^https?:\/\//)) {
      url = `https://${url}`;
    }
    
    const response = await fetch(`${API_BASE_URL}/analysis/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ url, options }),
    });
    
    if (!response.ok) {
      let errorText;
      try {
        const errorData = await response.json();
        errorText = errorData.detail || errorData.error?.message || 'Failed to analyze website';
      } catch (e) {
        // If response is not JSON, use the status text
        errorText = `Server error (${response.status}): ${response.statusText}`;
      }
      throw new Error(errorText);
    }
    
    const data = await response.json();
    
    // If needed, map id to analysis_id for backward compatibility
    if (data.id && !data.analysis_id) {
      data.analysis_id = data.id;
    }
    
    return data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};

export const getAnalysisResults = async (analysisId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/analysis/${analysisId}`);
    
    if (!response.ok) {
      let errorText;
      try {
        const errorData = await response.json();
        errorText = errorData.detail || errorData.error?.message || 'Failed to get analysis results';
      } catch (e) {
        errorText = `Server error (${response.status}): ${response.statusText}`;
      }
      throw new Error(errorText);
    }
    
    const data = await response.json();
    
    // If needed, map id to analysis_id for backward compatibility
    if (data.id && !data.analysis_id) {
      data.analysis_id = data.id;
    }
    
    return data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};

export const getScreenshots = async (analysisId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/screenshots/${analysisId}`);
    
    if (!response.ok) {
      let errorText;
      try {
        const errorData = await response.json();
        errorText = errorData.detail || errorData.error?.message || 'Failed to get screenshots';
      } catch (e) {
        errorText = `Server error (${response.status}): ${response.statusText}`;
      }
      throw new Error(errorText);
    }
    
    const data = await response.json();
    
    // If needed, map id to analysis_id for backward compatibility
    if (data.id && !data.analysis_id) {
      data.analysis_id = data.id;
    }
    
    return data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};

export const getTealiumAnalysis = async (analysisId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/tealium/analysis/${analysisId}`);
    
    if (!response.ok) {
      let errorText;
      try {
        const errorData = await response.json();
        errorText = errorData.detail || errorData.error?.message || 'Failed to get Tealium analysis';
      } catch (e) {
        errorText = `Server error (${response.status}): ${response.statusText}`;
      }
      throw new Error(errorText);
    }
    
    const data = await response.json();
    
    // If needed, map id to analysis_id for backward compatibility
    if (data.id && !data.analysis_id) {
      data.analysis_id = data.id;
    }
    
    return data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};

export const generateEnhancements = async (analysisId, categories) => {
  try {
    const response = await fetch(`${API_BASE_URL}/enhancements/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ analysis_id: analysisId, categories }),
    });
    
    if (!response.ok) {
      let errorText;
      try {
        const errorData = await response.json();
        errorText = errorData.detail || errorData.error?.message || 'Failed to generate enhancements';
      } catch (e) {
        errorText = `Server error (${response.status}): ${response.statusText}`;
      }
      throw new Error(errorText);
    }
    
    const data = await response.json();
    
    // If needed, map id to enhancement_id for backward compatibility
    if (data.id && !data.enhancement_id) {
      data.enhancement_id = data.id;
    }
    
    return data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};

export const getEnhancement = async (enhancementId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/enhancements/${enhancementId}`);
    
    if (!response.ok) {
      let errorText;
      try {
        const errorData = await response.json();
        errorText = errorData.detail || errorData.error?.message || 'Failed to get enhancement details';
      } catch (e) {
        errorText = `Server error (${response.status}): ${response.statusText}`;
      }
      throw new Error(errorText);
    }
    
    const data = await response.json();
    
    // If needed, map id to enhancement_id for backward compatibility
    if (data.id && !data.enhancement_id) {
      data.enhancement_id = data.id;
    }
    
    return data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};