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
          
          // Show empty state
          const emptyState = document.querySelector('.results-empty-state');
          if (emptyState) emptyState.style.display = 'flex';
          
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
          // Add class to layout to show streak
          const analysisLayout = document.querySelector('.analysis-layout');
          if (analysisLayout) analysisLayout.classList.add('running');
          break;
          
        case 'completed':
          analysisInProgress = false;
          analysisStatus.textContent = 'Analysis completed';
          analysisStatus.className = 'status-badge completed';
          loadingDiv.style.display = 'none';
          resultsContainer.style.display = 'block'; // Show results
          
          // Hide empty state
          const emptyStateCompleted = document.querySelector('.results-empty-state');
          if (emptyStateCompleted) emptyStateCompleted.style.display = 'none';
          
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
          // Remove running class from layout to hide streak
          const analysisLayoutWaiting = document.querySelector('.analysis-layout');
          if (analysisLayoutWaiting) analysisLayoutWaiting.classList.remove('running');
          break;
          
        case 'error':
          analysisInProgress = false;
          analysisStatus.textContent = 'Analysis failed';
          analysisStatus.className = 'status-badge error';
          loadingDiv.style.display = 'none';
          errorMessageDiv.style.display = 'block';
          errorMessageDiv.textContent = message || 'An error occurred during analysis.';
          
          // Hide empty state
          const emptyStateError = document.querySelector('.results-empty-state');
          if (emptyStateError) emptyStateError.style.display = 'none';
          
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
          
          // Remove running class from layout to hide streak
          const analysisLayoutError = document.querySelector('.analysis-layout');
          if (analysisLayoutError) analysisLayoutError.classList.remove('running');
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
        const sanitizedMessage = escapeHtml(message); // Use escapeHtml on the original message

        const li = document.createElement('li');
        li.classList.add('live-log-item'); // Use new class

        // Determine class based on content if not provided explicitly
        if (statusClass === 'info') {
            statusClass = determineMessageType(sanitizedMessage);
        }
        li.classList.add(statusClass);

        // Set textContent directly with the (potentially escaped) message from backend
        li.textContent = sanitizedMessage;

        liveLogList.appendChild(li);

        // Optional: Limit log length to prevent memory issues
        const maxLogItems = 500; // Example limit
        while (liveLogList.children.length > maxLogItems) {
            liveLogList.removeChild(liveLogList.firstChild);
        }

        // Auto-scroll to the bottom
        scrollToBottom();

        // Determine stage based on message content
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
  
      // Remove redundant status message added before SSE connection
      // addStatusMessage(`🚀 Starting Analysis for: ${urlToAnalyze}`, 'starting');
  
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
            
            // Format and display the raw data in the summary tab
            resultsPre.textContent = formatResultsForConsole(update.results);
            
            // Format and display the click events
            formatClickEventsForTable(update.results);
            
            // Populate the page view tab
            populatePageViewTab(update.results);
            
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
  
    // Renamed from formatResultsForSummary to formatClickEventsForTable to better reflect its purpose
    function formatClickEventsForTable(resultsData) {
        // Get element references INSIDE the function
        const eventTypeTabsContainer = document.getElementById('event-type-tabs');
        const eventTypeContentContainer = document.getElementById('event-type-content');

        if (!eventTypeTabsContainer || !eventTypeContentContainer) {
            console.error('Click events tab containers not found in DOM when formatting results.');
            return; // Exit if containers aren't found
        }

        // Clear previous tabs and content
        eventTypeTabsContainer.innerHTML = '';
        eventTypeContentContainer.innerHTML = '';

        // --- ADAPTATION: Process the actual results structure --- 
        // We expect resultsData to be the object from the backend
        // Let's focus on clickAnalysis for the tabbed table for now
        const clickEvents = resultsData?.clickAnalysis;

        if (!clickEvents || !Array.isArray(clickEvents) || clickEvents.length === 0) {
            eventTypeTabsContainer.innerHTML = '<p><i>No click events to display.</i></p>';
            eventTypeContentContainer.innerHTML = '<p>No click event summary data available.</p>';
            return;
        }

        // Add a single tab for "Click Events"
        const button = document.createElement('button');
        button.className = 'event-type-tab-button active'; // Only one tab, so active
        button.textContent = 'All Events';
        button.dataset.eventType = 'click'; // Assign a type
        eventTypeTabsContainer.appendChild(button);

        // Display the table for click events
        // We need to slightly adapt displayEventTable or the data passed to it
        // Let's adapt the data here to match expected structure
        const formattedClickEvents = clickEvents.map(click => {
            const data_variables = { // Start with base data
                'Vendors Detected (Network)': Object.keys(click.vendors_in_network || {}).join(', ') || 'None',
                ...(click.clickError ? { 'Click Error': click.clickError } : {})
            };

            // Check for Tealium events and extract data from the first one
            const firstTealiumEvent = click.tealium_events?.[0];
            if (firstTealiumEvent && typeof firstTealiumEvent.data === 'object' && firstTealiumEvent.data !== null) {
                const firstEventData = firstTealiumEvent.data;
                // Add specific event data to data_variables
                for (const [key, value] of Object.entries(firstEventData)) {
                    // Use original keys directly
                    data_variables[key] = value;
                }
            } else {
                data_variables['Tealium Event Data'] = 'None or Invalid'; // Placeholder if no data
            }

            return {
                event_type: 'click', // Add the event_type
                description: click.elementDescription || 'N/A',
                selector: click.selector || 'N/A',
                status: click.clickStatus || 'N/A',
                data_variables: data_variables // Use the populated object
            };
        });

        displayEventTable('click', formattedClickEvents, eventTypeContentContainer);
    }

    // Function to display page view data (utag_data)
    function populatePageViewTab(resultsData) {
        const pageViewContent = document.getElementById('pageview-data-content');
        const utagDataTable = document.getElementById('utag-data-table');
        
        if (!pageViewContent || !utagDataTable) {
            console.error('Page view tab elements not found in DOM.');
            return;
        }
        
        const utagData = resultsData?.pageLoadAnalysis?.utag_data;
        
        if (!utagData || Object.keys(utagData).length === 0) {
            pageViewContent.innerHTML = '<p><i>No utag_data available for this page.</i></p>';
            return;
        }
        
        // Get the tbody element to populate
        const tbody = utagDataTable.querySelector('tbody');
        if (!tbody) return;
        
        // Clear previous data
        tbody.innerHTML = '';
        
        // Sort keys for better readability
        const sortedKeys = Object.keys(utagData).sort();
        
        // Populate table with utag_data key-value pairs
        for (const key of sortedKeys) {
            const value = utagData[key];
            const row = document.createElement('tr');
            
            // Create key cell
            const keyCell = document.createElement('td');
            keyCell.textContent = key;
            row.appendChild(keyCell);
            
            // Create value cell
            const valueCell = document.createElement('td');
            if (typeof value === 'object' && value !== null) {
                // For arrays and objects, format as JSON
                valueCell.innerHTML = `<pre>${escapeHtml(JSON.stringify(value, null, 2))}</pre>`;
            } else {
                valueCell.textContent = value;
            }
            row.appendChild(valueCell);
            
            tbody.appendChild(row);
        }
        
        // Add a title with the count of variables
        const title = document.createElement('div');
        title.className = 'section-info';
        title.innerHTML = `<p>Found ${sortedKeys.length} utag_data variables on page load</p>`;
        pageViewContent.insertBefore(title, utagDataTable);
    }

    // New function to display the table for a specific event type
    function displayEventTable(eventType, events, eventTypeContentContainer) {
        if (!eventTypeContentContainer) return;

        let tableHTML = `<table class="event-table"><thead><tr>
                            <th></th> <!-- For expand button -->
                            <th>Description</th>
                            <th>Selector</th>
                            <th>Status</th>
                         </tr></thead><tbody>`;

        events.forEach((event, index) => {
            const description = event.description || 'N/A';
            const selector = event.selector || 'N/A';
            const status = event.status || 'N/A';
            const statusClass = status.toLowerCase() === 'success' ? 'status-success' : (status.toLowerCase() === 'failure' ? 'status-error' : '');
            const hasDetails = event.data_variables && Object.keys(event.data_variables).length > 0;

            // Main Row
            tableHTML += `<tr>
                            <td>`;
            if (hasDetails) {
                 tableHTML += `<button class="expand-details-btn" aria-expanded="false" title="Toggle Details">
                                 <i class="fas fa-chevron-right"></i>
                               </button>`;
            }
             tableHTML += `</td>
                            <td>${escapeHtml(description)}</td>
                            <td><code class="code-inline">${escapeHtml(selector)}</code></td>
                            <td class="${statusClass}">${escapeHtml(status)}</td>
                         </tr>`;

            // Details Row (Hidden by default)
            if (hasDetails) {
                tableHTML += `<tr class="event-details" style="display: none;">
                                <td colspan="4">`; // Span all columns
                // Render data_variables (can be simple pre or another table)
                // Option 1: Simple <pre>
                // tableHTML += `<h5>Data Variables:</h5><pre>${escapeHtml(JSON.stringify(event.data_variables, null, 2))}</pre>`;

                // Option 2: Nicer table
                tableHTML += `<h5>Data Variables:</h5><table class="data-variables-table"><tbody>`;
                for (const [key, value] of Object.entries(event.data_variables)) {
                    tableHTML += `<tr><th>${escapeHtml(key)}</th><td>${escapeHtml(JSON.stringify(value))}</td></tr>`;
                }
                tableHTML += `</tbody></table>`;

                tableHTML += `</td>
                             </tr>`;
            }
        });

        tableHTML += `</tbody></table>`;
        eventTypeContentContainer.innerHTML = tableHTML;

        // Attach event listener for expand/collapse AFTER table is rendered
        const tableBody = eventTypeContentContainer.querySelector('.event-table tbody');
        if (tableBody) {
            tableBody.addEventListener('click', (e) => {
                const button = e.target.closest('.expand-details-btn');
                if (button) {
                    const mainRow = button.closest('tr');
                    const detailsRow = mainRow.nextElementSibling;
                    if (detailsRow && detailsRow.classList.contains('event-details')) {
                        const isExpanded = button.getAttribute('aria-expanded') === 'true';
                        detailsRow.style.display = isExpanded ? 'none' : 'table-row';
                        button.setAttribute('aria-expanded', !isExpanded);
                        button.classList.toggle('expanded', !isExpanded);
                    }
                }
            });
        }
    }

    // Simple HTML escaping helper
    function escapeHtml(unsafe) {
        if (typeof unsafe !== 'string') {
            try {
              unsafe = JSON.stringify(unsafe); // Try to stringify non-strings
            } catch (e) {
              return '[Invalid Data]';
            }
        }
        return unsafe
             .replace(/&/g, "&amp;")
             .replace(/</g, "&lt;")
             .replace(/>/g, "&gt;")
             .replace(/"/g, "&quot;")
             .replace(/'/g, "&#039;");
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

    // --- REVERTED: AI Agent Animation --- 
    function animateAIAgentToStage(targetStageName) {
      if (!aiAgentElement || !stages[targetStageName]) {
        console.warn(`Cannot animate AI Agent: element or stage ${targetStageName} not found.`);
        return;
      }
      
      const agentRect = aiAgentElement.getBoundingClientRect();
      const targetStageElement = stages[targetStageName];
      const targetRect = targetStageElement.getBoundingClientRect();
      
      // Calculate center of agent and target stage RELATIVE to viewport
      const agentCenterX = agentRect.left + agentRect.width / 2;
      const targetCenterX = targetRect.left + targetRect.width / 2;
      
      // Get current transform to calculate relative movement
      const currentTransform = window.getComputedStyle(aiAgentElement).transform;
      let currentTranslateX = 0;
      if (currentTransform && currentTransform !== 'none') {
          const matrix = new DOMMatrix(currentTransform);
          currentTranslateX = matrix.m41;
      }
      
      // Required final translation = difference in centers + current translation amount
      const requiredTranslateX = (targetCenterX - agentCenterX) + currentTranslateX;
      
      console.log(`Animating AI Agent to ${targetStageName}. Target Center: ${targetCenterX}, Agent Center: ${agentCenterX}, Current X: ${currentTranslateX}, Required TranslateX: ${requiredTranslateX}`);
      
      // Apply only translateX
      aiAgentElement.style.transform = `translateX(${requiredTranslateX}px)`;
    }
    // --- END: AI Agent Animation ---

    // Reset AI Agent position (if needed, maybe call animation function)
    // animateAIAgentToStage(null); // Or reset transform directly
    if (aiAgentElement) {
        // Reset transform instantly without animation for reset
        aiAgentElement.style.transition = 'none'; // Disable transition temporarily
        aiAgentElement.style.transform = 'translateX(0px)'; // Reset translation only
        aiAgentElement.offsetHeight; // Force reflow
        aiAgentElement.style.transition = ''; // Re-enable transition
    }

    // Update status badge
    // ... existing code ...

    // --- Update resetStreamUI to reset transform --- 
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
            aiAgentElement.style.transition = 'none'; // Disable transition temporarily
            aiAgentElement.style.transform = 'translateX(0px)'; // Reset translation only
            aiAgentElement.offsetHeight; // Force reflow
            aiAgentElement.style.transition = ''; // Re-enable transition
        }

        // Reset analyzing label and live log visibility (set by updateUIState('waiting'))
        // if (analyzingLabel) analyzingLabel.style.opacity = '0';
        // if (liveLogPanel) liveLogPanel.style.opacity = '0';

        console.log('Stream UI reset complete.');
      }
      // --- END Update resetStreamUI to reset transform ---

      // Event listener for SSE messages
      // ... rest of the file ...
});
