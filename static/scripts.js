document.addEventListener('DOMContentLoaded', () => {
    // Core DOM Elements
    const form = document.getElementById('analyze-form');
    const urlInput = document.getElementById('url');
    const statusList = document.getElementById('status-list');
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
    const liveLogPanel = document.querySelector('.live-log-panel');
    
    // Premium Stream UI Elements
    const autoScrollBtn = document.getElementById('auto-scroll');
    const clearLogBtn = document.getElementById('clear-log');
    const elapsedTimeEl = document.getElementById('elapsed-time');
    const stepsCountEl = document.getElementById('steps-count');
    const progressBar = document.getElementById('progress-bar');
    const progressPercentage = document.getElementById('progress-percentage');
    const stagesProgressBar = document.getElementById('stages-progress-bar');
    
    // Stage Elements
    const stages = {
      setup: document.getElementById('stage-setup'),
      loading: document.getElementById('stage-loading'),
      data: document.getElementById('stage-data'),
      clicks: document.getElementById('stage-clicks'),
      complete: document.getElementById('stage-complete')
    };
    
    // State Variables
    let analysisInProgress = false;
    let eventSource = null;
    let analysisResults = null;
    let autoScroll = true;
    let stepCount = 0;
    let analysisStartTime = null;
    let timerInterval = null;
    let currentStage = null;
    let stageOrder = ['setup', 'loading', 'data', 'clicks', 'complete'];
    let totalSteps = 0;
    let completedSteps = 0;
    let lastMessageTime = null;
    
    // Message Type Patterns
    const messagePatterns = {
      section: [/^---.+---.?$/, /^===.+===$/, /Testing Click/],
      starting: [/Starting Analysis/, /Launching/, /Starting/, /Initializing/],
      success: [/✓/, /✅/, /successfully/, /Success/, /Completed/],
      error: [/❌/, /Error/, /Failed/, /failed/, /error/],
      warning: [/Warning/, /⚠️/]
    };
    
    // FUTURISTIC UI ENHANCEMENT FUNCTIONS
    
    // Create an animated star field in the terminal background
    function createStarField() {
      const terminalContent = document.querySelector('.terminal-content');
      if (!terminalContent) return;
      
      // Create a star field container
      const starField = document.createElement('div');
      starField.className = 'terminal-star-field';
      starField.style.position = 'absolute';
      starField.style.top = '0';
      starField.style.left = '0';
      starField.style.width = '100%';
      starField.style.height = '100%';
      starField.style.pointerEvents = 'none';
      starField.style.zIndex = '0';
      
      // Add stars
      for (let i = 0; i < 50; i++) {
        const star = document.createElement('div');
        const size = Math.random() * 2 + 1;
        
        star.style.position = 'absolute';
        star.style.width = `${size}px`;
        star.style.height = `${size}px`;
        star.style.borderRadius = '50%';
        star.style.backgroundColor = 'rgba(79, 121, 255, 0.4)';
        star.style.boxShadow = '0 0 3px rgba(79, 121, 255, 0.8)';
        star.style.top = `${Math.random() * 100}%`;
        star.style.left = `${Math.random() * 100}%`;
        star.style.opacity = Math.random() * 0.5 + 0.3;
        
        // Add subtle animation
        star.style.animation = `twinkle ${(Math.random() * 4 + 2).toFixed(2)}s infinite ease-in-out`;
        
        starField.appendChild(star);
      }
      
      // Add keyframes for twinkling
      if (!document.getElementById('twinkle-animation')) {
        const style = document.createElement('style');
        style.id = 'twinkle-animation';
        style.textContent = `
          @keyframes twinkle {
            0%, 100% { opacity: 0.2; transform: scale(0.8); }
            50% { opacity: 0.8; transform: scale(1.2); }
          }
          @keyframes fadeOut {
            from { opacity: 1; }
            to { opacity: 0; }
          }
        `;
        document.head.appendChild(style);
      }
      
      // Add the star field to the terminal
      terminalContent.prepend(starField);
    }
    
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
    
      // Add animation to stage icons
      const stageIcons = document.querySelectorAll('.stage-icon');
      stageIcons.forEach(icon => {
        icon.addEventListener('mouseenter', () => {
          if (!icon.parentElement.classList.contains('active') && 
              !icon.parentElement.classList.contains('completed')) {
            icon.style.transform = 'scale(1.1)';
            icon.style.borderColor = 'rgba(79, 121, 255, 0.4)';
          }
        });
        
        icon.addEventListener('mouseleave', () => {
          if (!icon.parentElement.classList.contains('active') && 
              !icon.parentElement.classList.contains('completed')) {
            icon.style.transform = '';
            icon.style.borderColor = '';
          }
        });
      });
    
      // Add dynamic star field to terminal
      createStarField();
      
      // Clear sample terminal messages if present
      if (statusList) {
        statusList.innerHTML = '';
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
      
      // Set up auto-scroll toggle
      autoScrollBtn.addEventListener('click', () => {
        autoScroll = !autoScroll;
        autoScrollBtn.classList.toggle('active', autoScroll);
        autoScrollBtn.querySelector('i').className = autoScroll 
          ? 'fas fa-angle-double-down' 
          : 'fas fa-times';
        autoScrollBtn.title = autoScroll ? 'Disable auto-scroll' : 'Enable auto-scroll';
        
        // If re-enabling auto-scroll, scroll to bottom immediately
        if (autoScroll) {
          scrollToBottom();
        }
      });
      
      // Set up clear log button
      clearLogBtn.addEventListener('click', () => {
        statusList.innerHTML = '';
        stepCount = 0;
        stepsCountEl.textContent = '0';
        
        // Add a cleared message
        addStatusMessage('Log cleared by user', 'info');
      });
  
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
          if (aiAgentElement) aiAgentElement.style.opacity = '0.12';
          if (analyzingLabel) analyzingLabel.style.opacity = '0';
          if (liveLogPanel) liveLogPanel.style.display = 'none';
          
          resetStreamUI();
          break;
          
        case 'running':
          analysisInProgress = true;
          analysisStatus.textContent = 'Analysis in progress';
          analysisStatus.className = 'status-badge running';
          loadingDiv.style.display = 'flex';
          statusList.innerHTML = '';
          resultsContainer.style.display = 'none';
          errorMessageDiv.style.display = 'none';
          downloadLink.style.display = 'none';
          
          // Futuristic UI elements
          if (aiAgentElement) {
            aiAgentElement.style.opacity = '0.8';
            // Add pulsing animation to the AI Agent circle
            const agentCircle = document.querySelector('.ai-agent-circle');
            if (agentCircle) {
              agentCircle.style.animation = 'pulse 2s infinite';
            }
          }
          if (analyzingLabel) analyzingLabel.style.opacity = '0.5';
          if (liveLogPanel) liveLogPanel.style.display = 'block';
          
          startAnalysisTimer();
          updateStage('setup');
          progressBar.style.width = '0%';
          progressPercentage.textContent = '0%';
          break;
          
        case 'completed':
          analysisInProgress = false;
          analysisStatus.textContent = 'Analysis completed';
          analysisStatus.className = 'status-badge completed';
          loadingDiv.style.display = 'none';
          resultsContainer.style.display = 'block';
          
          // Futuristic UI elements
          if (aiAgentElement) {
            aiAgentElement.style.opacity = '0.12';
            // Remove animation
            const agentCircle = document.querySelector('.ai-agent-circle');
            if (agentCircle) {
              agentCircle.style.animation = '';
            }
          }
          if (analyzingLabel) {
            analyzingLabel.textContent = "ANALYSIS COMPLETE";
            analyzingLabel.style.color = 'rgba(54, 238, 224, 0.8)';
            analyzingLabel.style.opacity = '0.5';
          }
          if (liveLogPanel) {
            // Fade out log panel after completion
            liveLogPanel.style.animation = 'fadeOut 1s forwards';
            setTimeout(() => {
              if (liveLogPanel) liveLogPanel.style.display = 'none';
            }, 1000);
          }
          
          stopAnalysisTimer();
          updateStage('complete');
          progressBar.style.width = '100%';
          progressPercentage.textContent = '100%';
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
            aiAgentElement.style.opacity = '0.12';
            // Remove animation
            const agentCircle = document.querySelector('.ai-agent-circle');
            if (agentCircle) {
              agentCircle.style.animation = '';
            }
          }
          if (analyzingLabel) {
            analyzingLabel.textContent = "ANALYSIS FAILED";
            analyzingLabel.style.color = 'rgba(255, 79, 121, 0.8)';
            analyzingLabel.style.opacity = '0.5';
          }
          if (liveLogPanel) liveLogPanel.style.display = 'none';
          
          stopAnalysisTimer();
          break;
      }
    }
    
    // Start the analysis timer
    function startAnalysisTimer() {
      analysisStartTime = Date.now();
      timerInterval = setInterval(updateTimer, 1000);
      lastMessageTime = Date.now();
    }
    
    // Stop the analysis timer
    function stopAnalysisTimer() {
      if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
      }
    }
    
    // Update the elapsed time
    function updateTimer() {
      if (!analysisStartTime) return;
      
      const elapsed = Math.floor((Date.now() - analysisStartTime) / 1000);
      const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0');
      const seconds = (elapsed % 60).toString().padStart(2, '0');
      elapsedTimeEl.textContent = `${minutes}:${seconds}`;
      
      // Check if analysis appears to be stalled (no messages in last 30 seconds)
      const idleTime = Date.now() - lastMessageTime;
      if (analysisInProgress && idleTime > 30000) {
        // Add a "waiting" message every 30 seconds
        lastMessageTime = Date.now(); // Reset the timer
        addStatusMessage('Still waiting for response...', 'warning');
      }
    }
    
    // Scroll the terminal to the bottom
    function scrollToBottom() {
      const container = document.querySelector('.terminal-content');
      if (container) {
        container.scrollTop = container.scrollHeight;
      }
    }
    
    // Update the active stage
    function updateStage(stageName) {
      if (currentStage === stageName) return;
      
      // Find the index of the current and new stages
      const currentIndex = stageOrder.indexOf(currentStage);
      const newIndex = stageOrder.indexOf(stageName);
      
      // Mark previous stages as completed
      if (currentStage) {
        stages[currentStage].classList.remove('active');
        
        // Only mark as completed if moving forward
        if (newIndex > currentIndex) {
          stages[currentStage].classList.add('completed');
          
          // Mark any skipped stages as completed
          for (let i = currentIndex + 1; i < newIndex; i++) {
            stages[stageOrder[i]].classList.remove('active');
            stages[stageOrder[i]].classList.add('completed');
          }
        }
      }
      
      // Set the new active stage
      currentStage = stageName;
      
      // Remove pending from the current stage and add active
      stages[stageName].classList.remove('pending');
      stages[stageName].classList.add('active');
      
      // Update stage progress bar
      const stageIndex = stageOrder.indexOf(stageName);
      const totalStages = stageOrder.length;
      const progressPercentage = Math.round((stageIndex / (totalStages - 1)) * 100);
      stagesProgressBar.style.width = `${progressPercentage}%`;
      
      // Update progress bar with a slight offset based on messages
      updateProgress(progressPercentage + (completedSteps / totalSteps) * (100 / totalStages));
      
      // Update Live Log Panel with stage change (if available)
      updateLiveLogPanel(stageName);
    }
    
    // Update the Live Log Panel with relevant information
    function updateLiveLogPanel(stage) {
      if (!liveLogPanel) return;
      
      // Keep track of log items
      if (!window.liveLogItems) {
        window.liveLogItems = [];
      }
      
      // Add stage-specific messages to the log panel
      let message = '';
      switch(stage) {
        case 'setup':
          message = 'INITIALIZING ANALYSIS ENGINE...';
          break;
        case 'loading':
          message = 'PAGE LOADED SUCCESSFULLY';
          break;
        case 'data':
          message = 'DETECTED 12 TAGS...';
          break;
        case 'clicks':
          message = 'TESTING INTERACTION POINTS';
          break;
        case 'complete':
          message = 'ALL CRITICAL TAGS PASSED QA';
          break;
      }
      
      if (message && !window.liveLogItems.includes(message)) {
        window.liveLogItems.push(message);
        const logItem = document.createElement('div');
        logItem.className = 'live-log-item';
        logItem.textContent = message;
        liveLogPanel.appendChild(logItem);
      }
    }
    
    // Update the progress bar
    function updateProgress(percent) {
      const clampedPercent = Math.min(100, Math.max(0, percent));
      progressBar.style.width = `${clampedPercent}%`;
      progressPercentage.textContent = `${Math.round(clampedPercent)}%`;
    }
    
    // Reset the stream UI for a new analysis
    function resetStreamUI() {
      stopAnalysisTimer();
      elapsedTimeEl.textContent = '00:00';
      stepsCountEl.textContent = '0';
      stepCount = 0;
      currentStage = null;
      totalSteps = 0;
      completedSteps = 0;
      lastMessageTime = null;
      progressBar.style.width = '0%';
      progressPercentage.textContent = '0%';
      stagesProgressBar.style.width = '0%';
      
      // Reset all stages
      Object.values(stages).forEach(stage => {
        stage.classList.remove('active', 'completed');
        stage.classList.add('pending');
      });
      
      // Reset live log panel
      if (liveLogPanel) {
        while (liveLogPanel.children.length > 1) { // Keep the header
          liveLogPanel.removeChild(liveLogPanel.lastChild);
        }
        window.liveLogItems = [];
      }
      
      // Reset analyzing label
      if (analyzingLabel) {
        analyzingLabel.textContent = "ANALYZING TAG PERFORMANCE";
        analyzingLabel.style.color = '';
      }
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
      // Clean up potential escape characters or extra formatting from logs
      const cleanedMessage = message.replace(/\\n/g, '\n').replace(/^      /, '').trim();
      if (!cleanedMessage) return;
      
      // Record the message time for stall detection
      lastMessageTime = Date.now();
      
      // Increment step counter
      stepCount++;
      stepsCountEl.textContent = stepCount.toString();
      completedSteps++;
      
      // Estimate total steps for the first time
      if (totalSteps === 0 && cleanedMessage.includes('Starting Analysis')) {
        // Rough estimate based on typical analysis
        totalSteps = 50;
      }
      
      // Determine stage based on message content
      if (cleanedMessage.includes('Launching browser') || cleanedMessage.includes('Starting Analysis')) {
        updateStage('setup');
      } else if (cleanedMessage.includes('Navigating') || cleanedMessage.includes('Page load')) {
        updateStage('loading');
      } else if (cleanedMessage.includes('Collecting initial page data') || cleanedMessage.includes('Detected page_type')) {
        updateStage('data');
      } else if (cleanedMessage.includes('Testing Click') || cleanedMessage.includes('Analyzing click events')) {
        updateStage('clicks');
      } else if (cleanedMessage.includes('Analysis finished') || cleanedMessage.includes('Analysis completed')) {
        updateStage('complete');
      }
      
      // Auto-detect message type if none is provided or is generic
      if (statusClass === 'info' || statusClass === 'progress') {
        statusClass = determineMessageType(cleanedMessage);
      }
      
      // Create the list item
      const li = document.createElement('li');
      li.textContent = cleanedMessage;
      li.className = `terminal-message ${statusClass}`;
      
      // Add to DOM
      statusList.appendChild(li);
      
      // Auto-scroll to the bottom if enabled
      if (autoScroll) {
        scrollToBottom();
      }
      
      // Update progress based on steps completed
      const progressValue = Math.min(95, (completedSteps / totalSteps) * 100);
      updateProgress(progressValue);
      
      // Update Live Log Panel with key findings (if available)
      updateLiveLogFromMessage(cleanedMessage);
    }
    
    // Update the Live Log Panel based on message content
    function updateLiveLogFromMessage(message) {
      if (!liveLogPanel) return;
      
      // Check for key patterns that should be highlighted in the live log
      const keyPatterns = [
        { regex: /detected.*(\d+).*tag/i, text: (match) => `DETECTED ${match[1]} TAGS...` },
        { regex: /dom mutation/i, text: () => "DOM MUTATION OBSERVER ACTIVE" },
        { regex: /(\d+).*gtm event/i, text: (match) => `${match[1]} GTM EVENTS FIRED` },
        { regex: /missing pixel/i, text: () => "PIXEL MISSING ON CTA BUTTON!" },
        { regex: /warning/i, text: (match) => `WARNING: ${message.toUpperCase()}` },
        { regex: /error/i, text: (match) => `ERROR: ${message.toUpperCase()}` }
      ];
      
      for (const pattern of keyPatterns) {
        const match = message.match(pattern.regex);
        if (match) {
          const logText = pattern.text(match);
          
          // Only add if not already in log
          if (!window.liveLogItems) window.liveLogItems = [];
          if (!window.liveLogItems.includes(logText)) {
            window.liveLogItems.push(logText);
            const logItem = document.createElement('div');
            logItem.className = 'live-log-item';
            logItem.textContent = logText;
            liveLogPanel.appendChild(logItem);
          }
          
          break;
        }
      }
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
});
