document.addEventListener('DOMContentLoaded', () => {
    // Core DOM Elements
    const form = document.getElementById('analyze-form');
    const urlInput = document.getElementById('url');
    const liveLogList = document.getElementById('live-log-list');
    const loadingDiv = document.getElementById('loading');
    const resultsPre = document.getElementById('results-pre');
    const resultsSummary = document.getElementById('results-summary');
    const visualizationArea = document.getElementById('visualization-area');
    const errorMessageDiv = document.getElementById('error-message');
    const downloadLink = document.getElementById('download-json');
    const resultsContainer = document.getElementById('results-container');
    const analysisStatus = document.getElementById('analysis-status');
    const resultsCard = document.getElementById('results-card');
    const toggleExpandBtn = document.getElementById('toggle-expand-btn');
    const copyResultsBtn = document.getElementById('copy-results');
    const notification = document.getElementById('notification');
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    // Enhanced UI Elements
    const aiAgentElement = document.querySelector('.ai-agent-element');
    const analyzingLabel = document.querySelector('.analyzing-label');
    const liveLogPanel = document.getElementById('live-log-panel');
    
    // Stage Elements
    const stages = {
      setup: document.getElementById('stage-setup'),
      loading: document.getElementById('stage-loading'),
      data: document.getElementById('stage-data'),
      complete: document.getElementById('stage-complete')
    };
    
    // State Variables
    let analysisInProgress = false;
    let eventSource = null;
    let analysisResults = null;
    let autoScroll = true;
    let currentStage = null;
    let stageOrder = ['setup', 'loading', 'data', 'complete'];
    let lastMessageTime = null;
    let lastMessage = null;
    
    // Message Type Patterns
    const messagePatterns = {
      section: [/^---.+---.?$/, /^===.+===$/, /Testing Click/],
      starting: [/Starting Analysis/, /Launching/, /Starting/, /Initializing/],
      success: [/✓/, /✅/, /successfully/, /Success/, /Completed/],
      error: [/❌/, /Error/, /Failed/, /failed/, /error/],
      warning: [/Warning/, /⚠️/]
    };
    
    // FUTURISTIC UI ENHANCEMENT FUNCTIONS
    
    // Function to enhance the Analysis Engine UI with modern animations
    function enhanceFuturisticUI() {
      // Set up the analysis card hover effects
      const analysisCard = document.querySelector('.analysis-card');
      if (analysisCard) {
        analysisCard.addEventListener('mouseenter', () => {
          // Add subtle glow effect on hover
          analysisCard.style.boxShadow = '0 0 40px rgba(0, 0, 0, 0.6), 0 0 25px rgba(79, 121, 255, 0.3)';
        });
        
        analysisCard.addEventListener('mouseleave', () => {
          // Reset to original shadow
          analysisCard.style.boxShadow = '';
        });
      }
    
      // Clear sample terminal messages if present
      if (liveLogList) {
        liveLogList.innerHTML = '';
      }
    }
    
    // Initialize UI
    initUI();
    
    // Apply futuristic enhancements
    enhanceFuturisticUI();
  
    function initUI() {
      // Tab functionality
      tabButtons.forEach(button => {
        button.addEventListener('click', () => {
          // Remove active class from all tabs
          tabButtons.forEach(btn => btn.classList.remove('active'));
          tabPanes.forEach(pane => pane.classList.remove('active'));
          
          // Add active class to clicked tab
          button.classList.add('active');
          document.getElementById(button.dataset.tab).classList.add('active');
        });
      });
  
      // Toggle expand functionality
      if (toggleExpandBtn) {
        toggleExpandBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          resultsCard.classList.toggle('expanded');
          toggleExpandBtn.querySelector('i').classList.toggle('fa-expand-alt');
          toggleExpandBtn.querySelector('i').classList.toggle('fa-compress-alt');
        });
        
        // Make whole header clickable for expand/collapse
        const toggleExpand = document.querySelector('.toggle-expand');
        if (toggleExpand) {
          toggleExpand.addEventListener('click', () => {
            toggleExpandBtn.click();
          });
        }
      }
  
      // Copy results functionality
      if (copyResultsBtn) {
        copyResultsBtn.addEventListener('click', () => {
          const textToCopy = resultsPre.textContent;
          navigator.clipboard.writeText(textToCopy).then(() => {
            showNotification();
          });
        });
      }
      
      // Initial UI state
      updateUIState('waiting');
    }
  
    function updateUIState(state, message = '') {
      switch (state) {
        case 'waiting':
          analysisStatus.textContent = 'Waiting to start';
          analysisStatus.className = 'status-badge';
          loadingDiv.style.display = 'none';
          resultsContainer.style.display = 'none';
          errorMessageDiv.style.display = 'none';
          downloadLink.style.display = 'none';
          
          // Futuristic UI elements
          if (aiAgentElement) aiAgentElement.style.opacity = '0.8'; // Keep agent slightly visible
          if (analyzingLabel) analyzingLabel.style.opacity = '0';
          if (liveLogPanel) liveLogPanel.style.opacity = '0'; // Hide via opacity for transition
          if (liveLogPanel) liveLogPanel.style.display = 'flex'; // Keep display:flex for layout calculation
          
          resetStreamUI();
          break;
          
        case 'running':
          analysisInProgress = true;
          analysisStatus.textContent = 'Analysis in progress';
          analysisStatus.className = 'status-badge running';
          loadingDiv.style.display = 'flex';
          errorMessageDiv.style.display = 'none';
          downloadLink.style.display = 'none';
          
          // Futuristic UI elements
          if (aiAgentElement) {
            aiAgentElement.style.opacity = '1'; // Full opacity when running
            // Re-ensure animation is running (might be stopped on complete/error)
            const agentCircle = aiAgentElement.querySelector('.ai-agent-circle');
            if (agentCircle) {
              agentCircle.style.animation = 'agentPulse 2.5s infinite ease-in-out'; // Use correct animation name
            }
          }
          if (analyzingLabel) analyzingLabel.style.opacity = '0.7';
          if (liveLogPanel) liveLogPanel.style.opacity = '0.9'; // Show via opacity
          
          updateStage('setup'); // Set initial stage
          break;
          
        case 'completed':
          analysisInProgress = false;
          analysisStatus.textContent = 'Analysis completed';
          analysisStatus.className = 'status-badge completed';
          loadingDiv.style.display = 'none';
          resultsContainer.style.display = 'block'; // Show results
          
          // Futuristic UI elements
          if (aiAgentElement) {
            aiAgentElement.style.opacity = '0.6'; // Dim slightly on complete
            // Stop animation
            const agentCircle = aiAgentElement.querySelector('.ai-agent-circle');
            if (agentCircle) {
              agentCircle.style.animation = 'none';
            }
          }
          if (analyzingLabel) {
            analyzingLabel.textContent = "ANALYSIS COMPLETE";
            analyzingLabel.style.color = 'var(--stage-text-completed)'; // Use completed color
            analyzingLabel.style.opacity = '0.7';
          }
          if (liveLogPanel) liveLogPanel.style.opacity = '0.9'; // Keep log visible
          
          updateStage('complete'); // Ensure final stage is marked
          break;
          
        case 'error':
          analysisInProgress = false;
          analysisStatus.textContent = 'Analysis failed';
          analysisStatus.className = 'status-badge error';
          loadingDiv.style.display = 'none';
          errorMessageDiv.style.display = 'block';
          errorMessageDiv.textContent = message || 'An error occurred during analysis.';
          
          // Futuristic UI elements
          if (aiAgentElement) {
            aiAgentElement.style.opacity = '0.6'; // Dim slightly on error
             // Stop animation
            const agentCircle = aiAgentElement.querySelector('.ai-agent-circle');
            if (agentCircle) {
              agentCircle.style.animation = 'none';
            }
          }
          if (analyzingLabel) {
            analyzingLabel.textContent = "ANALYSIS FAILED";
            analyzingLabel.style.color = 'var(--error-color)'; // Use error color
            analyzingLabel.style.opacity = '0.7';
          }
          if (liveLogPanel) liveLogPanel.style.opacity = '0'; // Hide log on error
          
          break;
      }
    }
    
    // Scroll the terminal to the bottom
    function scrollToBottom() {
      if (liveLogList && autoScroll) {
        liveLogList.scrollTop = liveLogList.scrollHeight;
      }
    }
    
    // Update the active stage
    function updateStage(stageName) {
      if (!stages[stageName] || stageName === currentStage) {
        // console.log(`Stage update skipped: ${stageName} (current: ${currentStage})`);
        return; // Ignore if stage doesn't exist or is already active
      }
      console.log(`Updating stage to: ${stageName}`);

      // Mark previous stages as completed
      const currentStageIndex = stageOrder.indexOf(currentStage);
      const newStageIndex = stageOrder.indexOf(stageName);

      for (let i = 0; i < newStageIndex; i++) {
          const completedStageName = stageOrder[i];
          if (stages[completedStageName]) {
              stages[completedStageName].className = 'stage completed';
          }
      }

      // Mark current stage as active
      if (stages[stageName]) {
          stages[stageName].className = 'stage active';
      }
      currentStage = stageName;

      // Animate AI Agent to this stage (Function to be implemented next)
      animateAIAgentToStage(stageName);
    }
  
    function showNotification() {
      notification.classList.add('show');
      setTimeout(() => {
        notification.classList.remove('show');
      }, 3000);
    }
  
    // Determine the message type based on content
    function determineMessageType(message) {
      if (!message) return 'info';
      
      // Check patterns for each type
      for (const [type, patterns] of Object.entries(messagePatterns)) {
        for (const pattern of patterns) {
          if (pattern.test(message)) {
            return type;
          }
        }
      }
      
      return 'info'; // Default type
    }
  
    // Add a message to the status list
    function addStatusMessage(message, statusClass = 'info') {
        if (!liveLogList) {
            console.warn('Live log list element not found.');
            return;
        }

        // Simple rate limiting: Ignore identical consecutive messages within 100ms
        const now = Date.now();
        if (message === lastMessage && (now - lastMessageTime < 100)) {
            return;
        }
        lastMessage = message;
        lastMessageTime = now;

        // Sanitize message slightly (prevent basic HTML injection)
        const sanitizedMessage = message.replace(/</g, '&lt;').replace(/>/g, '&gt;');

        const li = document.createElement('li');
        li.classList.add('live-log-item'); // Use new class

        // Determine class based on content if not provided explicitly
        if (statusClass === 'info') {
            statusClass = determineMessageType(sanitizedMessage);
        }
        li.classList.add(statusClass);

        // Create timestamp (optional, but good for logs)
        // const timestamp = new Date().toLocaleTimeString();
        // li.innerHTML = `<span class="log-timestamp">[${timestamp}]</span> ${sanitizedMessage}`;
        li.textContent = `> ${sanitizedMessage}`; // Add simple prefix like in the image

        liveLogList.appendChild(li);

        // Optional: Limit log length to prevent memory issues
        const maxLogItems = 500; // Example limit
        while (liveLogList.children.length > maxLogItems) {
            liveLogList.removeChild(liveLogList.firstChild);
        }

        // Auto-scroll to the bottom
        scrollToBottom();

        // Determine stage based on message content (moved logic here or call helper)
        determineStageFromMessage(sanitizedMessage);
    }
    
    // Helper function to determine stage from message content
    function determineStageFromMessage(message) {
        // Check in order of expected occurrence
        if (message.includes('Launching browser') || message.includes('Starting Analysis') || message.includes('Initializing')) {
            updateStage('setup');
        } else if (message.includes('Navigating') || message.includes('Page load') || message.includes('Loading page')) {
            updateStage('loading');
        } else if (message.includes('Collecting initial page data') || message.includes('Analyzing tags') || message.includes('GTM data') || message.includes('page_type')) {
            updateStage('data');
        } else if (message.includes('Analysis finished') || message.includes('Analysis complete') || message.includes('Cleanup finished')) {
            updateStage('complete');
        }
        // Note: If a message doesn't trigger a stage change, the current stage remains active.
    }
  
    // Handle form submission
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
  
      // If analysis is already running, prevent starting another one
      if (analysisInProgress) {
        return;
      }
  
      // Update UI for analysis start
      updateUIState('running');
  
      // Close any existing connection
      if (eventSource) {
        eventSource.close();
      }
  
      // Get URL to analyze
      let urlToAnalyze = urlInput.value.trim();
      if (!urlToAnalyze) {
        urlToAnalyze = urlInput.placeholder;
      }
  
      // Basic check if it needs https:// prepended
      if (!urlToAnalyze.startsWith('http://') && !urlToAnalyze.startsWith('https://')) {
        urlToAnalyze = 'https://' + urlToAnalyze;
      }
  
      // Add first status message
      addStatusMessage(`🚀 Starting Analysis for: ${urlToAnalyze}`, 'starting');
  
      // Setup Server-Sent Events (SSE)
      const encodedUrl = encodeURIComponent(urlToAnalyze);
      eventSource = new EventSource(`/stream?url=${encodedUrl}`);
  
      // Event handlers for SSE
      eventSource.onopen = () => {
        addStatusMessage("Connected to analysis server", 'info');
      };
  
      eventSource.onmessage = (event) => {
        try {
          const update = JSON.parse(event.data);
  
          // Display status messages
          if (update.message) {
            addStatusMessage(update.message, update.status || 'info');
          }
  
          // Check if this is the final result
          if (update.status === 'complete' && update.results) {
            // Store the results
            analysisResults = update.results;
            
            // Format and display results
            const formattedReport = formatResultsForSummary(update.results);
            resultsSummary.innerHTML = formattedReport;
            
            // Set the raw data as well
            resultsPre.textContent = formatResultsForConsole(update.results);
            
            // Create visualization
            createVisualization(update.results);
            
            // Make JSON downloadable
            const jsonBlob = new Blob([JSON.stringify(update.results, null, 2)], { type: 'application/json' });
            downloadLink.href = URL.createObjectURL(jsonBlob);
            
            // Create a filename from the URL
            let filename = 'analysis_results.json';
            try {
              const urlObj = new URL(update.results.url);
              filename = `analysis_${urlObj.hostname.replace(/[^a-z0-9]/gi, '_')}.json`;
            } catch (e) {
              /* Use default if URL parsing fails */
            }
            downloadLink.download = filename;
            downloadLink.style.display = 'inline-flex';
            
            // Update UI state
            updateUIState('completed');
            
            // Close the connection
            eventSource.close();
            
            // Add final status message
            addStatusMessage("✅ Analysis complete!", 'success');
          } else if (update.status === 'error') {
            // Display error from backend
            addStatusMessage(`ERROR: ${update.message}`, 'error');
            updateUIState('error', update.message);
            eventSource.close();
          }
  
        } catch (e) {
          console.error("Error parsing SSE message:", e);
          addStatusMessage("Received unparseable message from server", "error");
        }
      };
  
      eventSource.onerror = (error) => {
        console.error("SSE Error:", error);
        addStatusMessage("Connection error or stream closed", "error");
        updateUIState('error', "Lost connection to the analysis server. Please try again.");
        eventSource.close();
      };
    });
  
    function formatResultsForSummary(results) {
      if (!results || (results.error && results.steps?.slice(-1)[0]?.status === "Failed")) {
        return `<div class="error-summary">
            <h3>Analysis Failed</h3>
            <p>URL: ${results?.url || 'N/A'}</p>
            <p>Error: ${results?.error || 'Unknown error'}</p>
        </div>`;
      }
  
      const url = results.url || "N/A";
      const load_analysis = results.pageLoadAnalysis || {};
      const click_analysis = results.clickAnalysis || [];
      const vendors_on_page = load_analysis.vendors_on_page || {};
      const load_network_summary = load_analysis.load_network_summary || {};
      const utag_data = load_analysis.utag_data || {};
      const load_tealium_events = load_analysis.tealium_events || [];
      const page_type = utag_data.page_type || "Unknown";
  
      let html = `
          <div class="section-header">
              <i class="fas fa-info-circle"></i> Overview
          </div>
          <dl>
              <dt>URL Analyzed</dt>
              <dd><a href="${url}" target="_blank">${url}</a></dd>
              
              <dt>Page Type</dt>
              <dd>${page_type}</dd>
              
              <dt>Analysis Time</dt>
              <dd>${results.analysisTimestamp || 'N/A'}</dd>
          </dl>
          
          <div class="section-header">
              <i class="fas fa-server"></i> Tag Management Systems
          </div>`;
  
      // TMS
        // TMS
        const tealium_info = load_analysis.tag_detection?.tealiumInfo || {};
        const gtm_info = load_analysis.tag_detection?.gtmInfo || {};
        
        html += `<dl>`;
        html += `<dt>${tealium_info.detected ? '✓' : '✗'} Tealium iQ</dt>`;
        if (tealium_info.detected) {
            html += `<dd>
                Profile: ${tealium_info.profile || 'N/A'}<br>
                Account: ${tealium_info.account || 'N/A'}<br>
                Version: ${tealium_info.version || 'N/A'}<br>
                Tags: ${tealium_info.tagsLoaded || 'N/A'}
            </dd>`;
        } else {
            html += `<dd>Not detected</dd>`;
        }
        
        html += `<dt>${gtm_info.detected ? '✓' : '✗'} Google Tag Manager</dt>`;
        if (gtm_info.detected) {
            html += `<dd>Containers: ${gtm_info.containers?.join(', ') || 'N/A'}</dd>`;
        } else {
            html += `<dd>Not detected</dd>`;
        }
        html += `</dl>`;
    
        // Vendors on Page
        html += `<div class="section-header">
            <i class="fas fa-tags"></i> Vendors Detected on Page Load
        </div>`;
        
        if (Object.keys(vendors_on_page).length > 0) {
            Object.entries(vendors_on_page).sort().forEach(([category, names]) => {
                const formattedCategory = category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                
                html += `<div class="vendor-category">
                    <div class="vendor-category-title">${formattedCategory}</div>
                    <div class="vendor-list">`;
                
                names.forEach(name => {
                    html += `<span class="vendor-tag">${name}</span>`;
                });
                
                html += `</div></div>`;
            });
        } else {
            html += `<p>No vendors detected on page load</p>`;
        }
    
        // Network Requests
        html += `<div class="section-header">
            <i class="fas fa-network-wired"></i> Network Requests
        </div>`;
        
        const load_network_vendors = load_network_summary.vendors_detected || {};
        html += `<p>Total requests during page load: ${load_network_summary.total_requests || 'N/A'}</p>`;
        
        if (Object.keys(load_network_vendors).length > 0) {
            html += `<ul>`;
            Object.entries(load_network_vendors).sort().forEach(([name, urls]) => {
                html += `<li>${name} (${urls.length} requests)</li>`;
            });
            html += `</ul>`;
        } else {
            html += `<p>No vendor network requests detected</p>`;
        }
    
        // Tealium Events on Load
        html += `<div class="section-header">
            <i class="fas fa-code"></i> Tealium Events During Load
        </div>`;
        
        if (Array.isArray(load_tealium_events) && load_tealium_events.length > 0) {
            html += `<ul>`;
            load_tealium_events.forEach(event => {
                const event_type = event?.type || 'N/A';
                const data = event?.data || {};
                const desc = data.event_name || data.event_type || data.event || data.link_id || '';
                html += `<li>${event_type} ${desc ? `(${desc})` : ''}</li>`;
            });
            html += `</ul>`;
        } else if (load_tealium_events?.error) {
            html += `<p>Error retrieving events: ${load_tealium_events.error}</p>`;
        } else {
            html += `<p>No Tealium events captured during page load</p>`;
        }
    
        // Click Events Analysis
        html += `<div class="section-header">
            <i class="fas fa-mouse-pointer"></i> Click Events Analysis
        </div>`;
        
        if (Array.isArray(click_analysis) && click_analysis.length > 0) {
            click_analysis.forEach((click, i) => {
                const clickStatus = click.clickStatus || 'N/A';
                const statusClass = clickStatus.toLowerCase().includes('error') || 
                                    clickStatus.toLowerCase().includes('fail') ? 'error' : '';
                
                html += `<div class="click-event">
                    <div class="click-event-title">
                        <i class="fas fa-mouse-pointer"></i> ${click.elementDescription || 'Click Event'}
                        <span class="click-event-status ${statusClass}">${clickStatus}</span>
                    </div>
                    <div class="click-event-details">
                        <p><strong>Selector:</strong> ${click.selector || 'N/A'}</p>`;
                
                if (click.clickError) {
                    html += `<p><strong>Error:</strong> ${click.clickError}</p>`;
                }
                
                // Tealium Events After Click
                const click_tealium_events = click.tealium_events || [];
                html += `<p><strong>Tealium Events Triggered:</strong> ${click_tealium_events?.length || 0}</p>`;
                
                if (Array.isArray(click_tealium_events) && click_tealium_events.length > 0) {
                    html += `<ul>`;
                    click_tealium_events.forEach(event => {
                        const event_type = event?.type || 'N/A';
                        const data = event?.data || {};
                        const desc = data.event_name || data.event_type || data.event || data.link_id || '';
                        html += `<li>${event_type} ${desc ? `(${desc})` : ''}</li>`;
                    });
                    html += `</ul>`;
                }
                
                html += `</div></div>`;
            });
        } else {
            html += `<p>No click events were configured or analyzed for page type '${page_type}'.</p>`;
        }
    
        return html;
      }
    
      function createVisualization(results) {
        // This is a placeholder for a more sophisticated visualization
        // In a real implementation, you might use D3.js or Chart.js
        visualizationArea.innerHTML = `
            <div style="text-align: center;">
                <p>Advanced visualization could be implemented here with D3.js or Chart.js</p>
                <p>Consider visualizing:</p>
                <ul style="list-style: none; padding: 0; margin-top: 1rem;">
                    <li>• Tag distribution by category</li>
                    <li>• Network request timeline</li>
                    <li>• Event flow diagram</li>
                </ul>
            </div>
        `;
      }
    
      // This is the original function from your code, kept for backward compatibility
      function formatResultsForConsole(results) {
        if (!results || (results.error && results.steps?.slice(-1)[0]?.status === "Failed")) {
          return `*** ANALYSIS FAILED ***\nURL: ${results?.url || 'N/A'}\nError: ${results?.error || 'Unknown error'}`;
        }

        const url = results.url || "N/A";
        const load_analysis = results.pageLoadAnalysis || {};
        const click_analysis = results.clickAnalysis || [];
        const vendors_on_page = load_analysis.vendors_on_page || {};
        const load_network_summary = load_analysis.load_network_summary || {};
        const utag_data = load_analysis.utag_data || {};
        const load_tealium_events = load_analysis.tealium_events || [];

        const page_type = utag_data.page_type || "Unknown";

        let report = [
          `=================================================`,
          ` ANALYSIS REPORT for: ${url}`,
          ` Detected Page Type: ${page_type}`,
          ` Analyzed at: ${results.analysisTimestamp || 'N/A'}`,
          `=================================================\n`,
          `--- Page Load Analysis ---`
        ];

        // TMS
        const tealium_info = load_analysis.tag_detection?.tealiumInfo || {};
        const gtm_info = load_analysis.tag_detection?.gtmInfo || {};
        report.push("Tag Management Systems:");
        report.push(`  ${tealium_info.detected ? '✓' : '-'} Tealium iQ (Profile: ${tealium_info.profile || 'N/A'}, Account: ${tealium_info.account || 'N/A'}, Version: ${tealium_info.version || 'N/A'}, Tags: ${tealium_info.tagsLoaded || 'N/A'})`);
        report.push(`  ${gtm_info.detected ? '✓' : '-'} Google Tag Manager (Containers: ${gtm_info.containers?.join(', ') || 'N/A'})`);
        report.push("");

        // Vendors in Network (Load)
        const load_network_vendors = load_network_summary.vendors_detected || {};
        report.push(`Vendors Detected in Network Requests (During Load - ${load_network_summary.total_requests ?? 'N/A'} total):`);
        if (Object.keys(load_network_vendors).length > 0) {
          for (const [name, urls] of Object.entries(load_network_vendors).sort()) {
            report.push(`  - ${name} (${urls.length} reqs)`);
          }
        } else {
          report.push("  None");
        }
        report.push("");

        // Initial Utag Data
        if (utag_data && !utag_data.error) {
          report.push(`Initial Utag Data: Found ${Object.keys(utag_data).length} keys (See JSON download for details).`);
        } else {
          report.push(`Initial Utag Data: ${utag_data?.error ? `Error (${utag_data.error})` : 'Not found or empty.'}`);
        }
        report.push("");

        // Initial Tealium Events
        report.push(`Tealium Events Captured During Load (${load_tealium_events?.length ?? 0}):`);
        if (Array.isArray(load_tealium_events) && load_tealium_events.length > 0) {
          load_tealium_events.forEach(event => {
            const event_type = event?.type || 'N/A';
            const data = event?.data || {};
            const desc = data.event_name || data.event_type || data.event || data.link_id || '';
            report.push(`  - ${event_type} ${desc ? `(${desc})` : ''}`);
          });
        } else if (load_tealium_events?.error) {
          report.push(`  Error retrieving events (${load_tealium_events.error})`);
        } else {
          report.push("  None captured.");
        }
        report.push("");

        // Vendors on Page
        report.push("Vendors Detected on Page Load (Scripts/Objects):");
        if (Object.keys(vendors_on_page).length > 0) {
          for (const [category, names] of Object.entries(vendors_on_page).sort()) {
            report.push(`  - ${category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}: ${names.join(', ')}`);
          }
        } else {
          report.push("  None");
        }
        report.push("");

        // Click Analysis
        report.push("--- Click Event Analysis ---");
        if (!click_analysis || click_analysis.length === 0) {
          report.push(`No click events were configured or analyzed for page type '${page_type}'.`);
        } else {
          click_analysis.forEach((click, i) => {
            report.push(`\n▶ Click ${i + 1}: ${click.elementDescription || 'N/A'} (${click.clickStatus || 'N/A'})`);
            report.push(`  Selector: ${click.selector || 'N/A'}`);
            if (click.clickError) {
              report.push(`  Error: ${click.clickError}`);
            }

            // Tealium Events After Click
            const click_tealium_events = click.tealium_events || [];
            report.push(`  Tealium Events Triggered: ${click_tealium_events?.length ?? 0}`);
            if (Array.isArray(click_tealium_events) && click_tealium_events.length > 0) {
              click_tealium_events.forEach(event => {
                const event_type = event?.type || 'N/A';
                const data = event?.data || {};
                const desc = data.event_name || data.event_type || data.event || data.link_id || '';
                report.push(`    - ${event_type} ${desc ? `(${desc})` : ''}`);
              });
            } else if (click_tealium_events?.error) {
              report.push(`    Error retrieving events (${click_tealium_events.error})`);
            }

            // Network Vendors After Click
            const click_network_vendors = click.vendors_in_network || {};
            if (click_network_vendors.error) {
              report.push(`  Network Requests to Vendors After Click: Error (${click_network_vendors.error})`);
            } else {
              report.push(`  Network Requests to Vendors After Click: ${Object.keys(click_network_vendors).length}`);
              if (Object.keys(click_network_vendors).length > 0) {
                for (const [name, urls] of Object.entries(click_network_vendors).sort()) {
                  report.push(`    - ${name} (${urls.length} reqs)`);
                }
              }
            }
          });
        }

        report.push("\n=================================================");
        return report.join("\n");
      }

      // --- NEW: AI Agent Animation --- 
      function animateAIAgentToStage(targetStageName) {
        if (!aiAgentElement || !stages[targetStageName]) {
          console.warn(`Cannot animate AI Agent: element or stage ${targetStageName} not found.`);
          return;
        }
        
        const agentRect = aiAgentElement.getBoundingClientRect();
        const targetStageElement = stages[targetStageName];
        const targetRect = targetStageElement.getBoundingClientRect();
        
        // Calculate the center of the agent and the target stage RELATIVE to the viewport
        const agentCenterX = agentRect.left + agentRect.width / 2;
        const targetCenterX = targetRect.left + targetRect.width / 2;
        
        // Calculate the required translation
        // Get the current transform value (if any) to calculate relative movement
        const currentTransform = window.getComputedStyle(aiAgentElement).transform;
        let currentTranslateX = 0;
        if (currentTransform && currentTransform !== 'none') {
          const matrix = new DOMMatrix(currentTransform);
          currentTranslateX = matrix.m41; // Translation X value
        }
        
        // The desired final translation is the difference between target and agent centers,
        // PLUS the current translation amount (because translateX is relative to original position)
        const requiredTranslateX = (targetCenterX - agentCenterX) + currentTranslateX;
        
        console.log(`Animating AI Agent to ${targetStageName}. Current X: ${currentTranslateX}, Target Center: ${targetCenterX}, Agent Center: ${agentCenterX}, Required TranslateX: ${requiredTranslateX}`);
        
        aiAgentElement.style.transform = `translateX(${requiredTranslateX}px)`;
      }
      // --- END: AI Agent Animation ---

      // Reset AI Agent position (if needed, maybe call animation function)
      // animateAIAgentToStage(null); // Or reset transform directly
      if (aiAgentElement) {
          // Reset transform instantly without animation for reset
          aiAgentElement.style.transition = 'none'; // Disable transition temporarily
          aiAgentElement.style.transform = 'translateX(0)'; // Reset position instantly
          // Force reflow/repaint to apply the style immediately before re-enabling transition
          aiAgentElement.offsetHeight; // Reading offsetHeight forces reflow
          aiAgentElement.style.transition = ''; // Re-enable transition (uses CSS value)
      }

      // Update status badge
      // ... existing code ...

      // --- RE-ADD resetStreamUI FUNCTION ---
      function resetStreamUI() {
        console.log('Resetting Stream UI for new analysis');
        // Reset stages
        Object.values(stages).forEach(stage => {
          if (stage) { // Check if stage exists
              stage.className = 'stage pending';
          }
        });
        currentStage = null;

        // Clear the live log
        if (liveLogList) liveLogList.innerHTML = '';
        if (errorMessageDiv) errorMessageDiv.textContent = '';
        if (errorMessageDiv) errorMessageDiv.style.display = 'none';

        // Reset AI Agent position instantly
        if (aiAgentElement) {
            aiAgentElement.style.transition = 'none';
            aiAgentElement.style.transform = 'translateX(0)';
            aiAgentElement.offsetHeight; // Force reflow
            aiAgentElement.style.transition = ''; // Re-enable transition
        }

        // Reset analyzing label and live log visibility (set by updateUIState('waiting'))
        // if (analyzingLabel) analyzingLabel.style.opacity = '0';
        // if (liveLogPanel) liveLogPanel.style.opacity = '0';

        console.log('Stream UI reset complete.');
      }
      // --- END RE-ADD resetStreamUI FUNCTION ---

      // Event listener for SSE messages
      // ... rest of the file ...
});
