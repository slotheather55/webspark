/**
 * Webspark Macro Recorder
 * Handles the recording, management, and playback of user interaction macros
 */

class MacroRecorder {
    constructor() {
        this.isRecording = false;
        this.isPaused = false;
        this.recordedActions = [];
        this.startTime = null;
        this.recordingTimer = null;
        this.currentUrl = '';
        
        this.initializeElements();
        this.bindEventListeners();
        this.loadSavedMacros();

        // Initialize message tracking for rate limiting
        this.lastMessage = null;
        this.lastMessageTime = null;

        // Message Type Patterns for better log categorization
        this.macroMessagePatterns = {
            section: [/^---.+---.?$/, /^===.+===$/, /Testing:/, /▶️/, /Analyzing.*selectors?/i],
            starting: [/Starting.*analysis/i, /Starting Tealium/i, /Launching/, /Starting/, /Initializing/],
            success: [/✓/, /✅/, /successfully/i, /Success/i, /Completed/i, /finished/i, /launched successfully/i, /loaded successfully/i, /complete:/i],
            error: [/❌/, /Error/, /Failed/, /failed/, /error/],
            warning: [/Warning/, /⚠️/, /Warning:/i, /timeout/i, /not found/i, /trying/i],
            progress: [/^\s{2,}/, /Loading page:/, /Testing:/, /Attempting/, /Retrieving/, /Collecting/, /Post-click:/]
        };

        // Inject styles for improved Analyze button and spinner if not present
        if (!document.getElementById('macro-analyze-styles')) {
            const styles = document.createElement('style');
            styles.id = 'macro-analyze-styles';
            styles.textContent = `
                .analyze-btn { display: inline-flex; align-items: center; gap: 8px; padding: 8px 14px; border-radius: 8px; border: 2px solid #28a745; background:#28a745; color:#fff; font-weight:600; cursor:pointer; }
                .analyze-btn:hover:not([disabled]) { background:#218838; border-color:#1e7e34; }
                .analyze-btn[disabled] { opacity: 0.7; cursor: not-allowed; }
                .analyze-btn .spinner { width:14px; height:14px; border:2px solid rgba(255,255,255,0.6); border-top-color:#fff; border-radius:50%; animation: ws-spin 0.8s linear infinite; display:none; }
                .analyze-btn.loading .spinner { display:inline-block; }
                @keyframes ws-spin { to { transform: rotate(360deg); } }
            `;
            document.head.appendChild(styles);
        }
    }

    async renameMacro(macroId, newName) {
        try {
            newName = (newName || '').trim();
            if (!newName) return;
            const res = await fetch(`/api/macros/${macroId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: newName })
            });
            const result = await res.json();
            if (!result.success) {
                this.showNotification('Failed to rename macro: ' + (result.error || ''), 'error');
            }
        } catch (e) {
            console.error('Rename failed', e);
            this.showNotification('Rename failed: ' + e.message, 'error');
        }
    }

    // ===== Helper methods for enhanced logging =====
    escapeHtml(unsafe) {
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

    // Determine the message type based on content
    determineMacroMessageType(message) {
        if (!message) return 'info';
        
        // Check patterns for each type
        for (const [type, patterns] of Object.entries(this.macroMessagePatterns)) {
            for (const pattern of patterns) {
                if (pattern.test(message)) {
                    return type;
                }
            }
        }
        
        return 'info'; // Default type
    }

    // ===== Analysis Engine helpers (Record page) =====
    initMacroAnalysisUI() {
        this.resetMacroStreamUI();
        if (this.resultsContainer) this.resultsContainer.style.display = 'none';
        if (this.downloadLink) this.downloadLink.style.display = 'none';
    }

    updateMacroUIState(state, message = '') {
        if (!this.analysisStatus) return;
        switch (state) {
            case 'waiting':
                this.analysisStatus.textContent = 'Waiting to start';
                this.analysisStatus.className = 'status-badge';
                if (this.loadingDiv) this.loadingDiv.style.display = 'none';
                if (this.resultsContainer) this.resultsContainer.style.display = 'none';
                if (this.downloadLink) this.downloadLink.style.display = 'none';
                if (this.liveLogPanel) { this.liveLogPanel.style.display = 'flex'; this.liveLogPanel.style.opacity = '0'; }
                if (this.analyzingLabel) this.analyzingLabel.style.opacity = '0';
                if (this.aiAgentElement) this.aiAgentElement.style.opacity = '0.8';
                this.resetMacroStreamUI();
                break;
            case 'running':
                this.analysisInProgress = true;
                this.analysisStatus.textContent = 'Analysis in progress';
                this.analysisStatus.className = 'status-badge running';
                if (this.loadingDiv) {
                    this.loadingDiv.style.display = 'flex';
                    // Update loading text for macro analysis
                    const loadingText = this.loadingDiv.querySelector('.loading-text');
                    if (loadingText) loadingText.textContent = 'Analyzing Macro Selectors...';
                }
                if (this.liveLogPanel) { 
                    this.liveLogPanel.style.display = 'flex';
                    this.liveLogPanel.style.opacity = '1';
                    this.liveLogPanel.style.visibility = 'visible';
                }
                if (this.analyzingLabel) {
                    this.analyzingLabel.textContent = 'ANALYZING MACRO SELECTORS';
                    this.analyzingLabel.style.opacity = '0.7';
                }
                if (this.aiAgentElement) {
                    this.aiAgentElement.style.opacity = '1';
                    const circle = this.aiAgentElement.querySelector('.ai-agent-circle');
                    if (circle) circle.style.animation = 'agentPulse 2.5s infinite ease-in-out';
                }
                this.updateMacroStage('setup');
                break;
            case 'completed':
                this.analysisInProgress = false;
                this.analysisStatus.textContent = 'Analysis completed';
                this.analysisStatus.className = 'status-badge completed';
                if (this.loadingDiv) {
                    this.loadingDiv.style.display = 'none';
                    // Reset loading text
                    const loadingText = this.loadingDiv.querySelector('.loading-text');
                    if (loadingText) loadingText.textContent = 'Processing';
                }
                if (this.resultsContainer) this.resultsContainer.style.display = 'block';
                if (this.liveLogPanel) { 
                    this.liveLogPanel.style.display = 'flex';
                    this.liveLogPanel.style.opacity = '0.9';
                }
                if (this.aiAgentElement) {
                    this.aiAgentElement.style.opacity = '0.6';
                    const circle = this.aiAgentElement.querySelector('.ai-agent-circle');
                    if (circle) circle.style.animation = 'none';
                }
                if (this.analyzingLabel) {
                    this.analyzingLabel.textContent = 'ANALYSIS COMPLETE';
                    this.analyzingLabel.style.opacity = '0.7';
                }
                this.updateMacroStage('complete');
                break;
            case 'error':
                this.analysisInProgress = false;
                this.analysisStatus.textContent = 'Analysis failed';
                this.analysisStatus.className = 'status-badge error';
                if (this.loadingDiv) this.loadingDiv.style.display = 'none';
                const errDiv = document.getElementById('error-message');
                if (errDiv) { errDiv.style.display = 'block'; errDiv.textContent = message || 'An error occurred during analysis.'; }
                if (this.aiAgentElement) {
                    this.aiAgentElement.style.opacity = '0.6';
                    const circle = this.aiAgentElement.querySelector('.ai-agent-circle');
                    if (circle) circle.style.animation = 'none';
                }
                if (this.analyzingLabel) {
                    this.analyzingLabel.textContent = 'ANALYSIS FAILED';
                    this.analyzingLabel.style.opacity = '0.7';
                }
                if (this.liveLogPanel) this.liveLogPanel.style.opacity = '0';
                break;
        }
    }

    addMacroStatusMessage(message, statusClass = 'info') {
        if (!this.liveLogList || !message) {
            console.warn('Live log list element not found or message is empty.');
            return;
        }

        // Simple rate limiting: Ignore identical consecutive messages within 100ms
        const now = Date.now();
        if (message === this.lastMessage && (now - this.lastMessageTime < 100)) {
            return;
        }
        this.lastMessage = message;
        this.lastMessageTime = now;

        // Sanitize message slightly (prevent basic HTML injection)
        const sanitizedMessage = this.escapeHtml(message);

        const li = document.createElement('li');
        li.classList.add('live-log-item');

        // Determine class based on content if not provided explicitly
        if (statusClass === 'info') {
            statusClass = this.determineMacroMessageType(sanitizedMessage);
        }
        li.classList.add(statusClass);

        // Set textContent directly with the original message (textContent automatically escapes)
        li.textContent = message;

        this.liveLogList.appendChild(li);

        // Optional: Limit log length to prevent memory issues
        const maxLogItems = 500;
        while (this.liveLogList.children.length > maxLogItems) {
            this.liveLogList.removeChild(this.liveLogList.firstChild);
        }

        // Auto-scroll to the bottom
        this.liveLogList.scrollTop = this.liveLogList.scrollHeight;

        // Determine stage based on message content
        this.determineMacroStageFromMessage(sanitizedMessage);
    }

    determineMacroStageFromMessage(message) {
        if (!message) return;
        
        // Check in order of expected occurrence for macro analysis
        if (message.includes('Browser launched') || message.includes('Starting Tealium') || message.includes('Connected to analysis server')) {
            this.updateMacroStage('setup');
        } else if (message.includes('Loading page:') || message.includes('Page loaded successfully') || message.includes('navigating')) {
            this.updateMacroStage('loading');
        } else if (message.includes('Baseline captured') || message.includes('Testing:') || message.includes('Trying') || message.includes('Post-click:') || message.includes('selectors triggered')) {
            this.updateMacroStage('data');
        } else if (message.includes('Analysis complete:') || message.includes('✅') || message.includes('Cleanup finished')) {
            this.updateMacroStage('complete');
        }
        // Note: If a message doesn't trigger a stage change, the current stage remains active.
    }

    updateMacroStage(stageName) {
        if (!this.stageEls[stageName] || stageName === this.currentStage) return;
        const currentIdx = this.stageOrder.indexOf(this.currentStage);
        const newIdx = this.stageOrder.indexOf(stageName);
        for (let i = 0; i < newIdx; i++) {
            const name = this.stageOrder[i];
            if (this.stageEls[name]) this.stageEls[name].className = 'stage completed';
        }
        if (this.stageEls[stageName]) this.stageEls[stageName].className = 'stage active';
        this.currentStage = stageName;
        if (this.aiAgentElement && this.stageEls[stageName]) {
            const agentRect = this.aiAgentElement.getBoundingClientRect();
            const targetRect = this.stageEls[stageName].getBoundingClientRect();
            const tf = window.getComputedStyle(this.aiAgentElement).transform;
            let currentX = 0; try { if (tf && tf !== 'none') currentX = new DOMMatrix(tf).m41; } catch (e) {}
            const translateX = (targetRect.left + targetRect.width / 2) - (agentRect.left + agentRect.width / 2) + currentX;
            this.aiAgentElement.style.transform = `translateX(${translateX}px)`;
        }
    }

    resetMacroStreamUI() {
        Object.values(this.stageEls).forEach((el) => { if (el) el.className = 'stage pending'; });
        this.currentStage = null;
        if (this.liveLogList) this.liveLogList.innerHTML = '';
        if (this.aiAgentElement) {
            this.aiAgentElement.style.transition = 'none';
            this.aiAgentElement.style.transform = 'translateX(0px)';
            void this.aiAgentElement.offsetHeight;
            this.aiAgentElement.style.transition = '';
        }
        const err = document.getElementById('error-message');
        if (err) { err.textContent = ''; err.style.display = 'none'; }
    }

    formatMacroResultsForConsole(results) {
        const url = results.macro_url || 'N/A';
        const total = results.total_selectors ?? 0;
        const success = results.successful_clicks ?? 0;
        const tealium = results.tealium_active_clicks ?? 0;
        const coverage = Math.round(results.tealium_coverage ?? 0);
        const rows = [
            '=================================================',
            ` MACRO ANALYSIS REPORT for: ${url}`,
            ` Macro Name: ${results.macro_name || 'N/A'}`,
            ` Completed at: ${results.timestamp || new Date().toISOString()}`,
            '=================================================\n',
            `--- Summary ---`,
            ` Total selectors: ${total}`,
            ` Successful clicks: ${success}`,
            ` Tealium events detected: ${tealium}`,
            ` Tealium coverage: ${coverage}%`,
            '',
            '--- Detailed Click Analysis ---'
        ];
        (results.selector_results || []).forEach((r, idx) => {
            rows.push(`\n▶ Selector ${idx + 1}: ${r.description || 'N/A'} (${r.success ? 'success' : 'failure'})`);
            rows.push(`  Selector: ${r.selector || 'N/A'}`);
            if (!r.success && r.error) rows.push(`  Error: ${r.error}`);
            const evts = Array.isArray(r.tealium_events) ? r.tealium_events : [];
            rows.push(`  Tealium Events Triggered: ${evts.length}`);
            const vendors = r.vendors_in_network && typeof r.vendors_in_network === 'object' ? Object.keys(r.vendors_in_network) : [];
            rows.push(`  Vendors in Network: ${vendors.length ? vendors.join(', ') : 'None'}`);
        });
        rows.push('\n=================================================');
        return rows.join('\n');
    }

    populateMacroClickEvents(results) {
        const tabs = document.getElementById('event-type-tabs');
        const content = document.getElementById('event-type-content');
        if (!tabs || !content) return;
        tabs.innerHTML = '';
        content.innerHTML = '';
        const btn = document.createElement('button');
        btn.className = 'event-type-tab-button active';
        btn.textContent = 'All Events';
        btn.dataset.eventType = 'click';
        tabs.appendChild(btn);

        const events = (results.selector_results || []).map((r) => {
            const firstEvent = Array.isArray(r.tealium_events) ? r.tealium_events[0] : null;
            const dataVars = {};
            if (firstEvent && firstEvent.data && typeof firstEvent.data === 'object') {
                for (const [k, v] of Object.entries(firstEvent.data)) dataVars[k] = v;
            }
            const vendors = r.vendors_in_network && typeof r.vendors_in_network === 'object' ? Object.keys(r.vendors_in_network) : [];
            if (vendors.length) dataVars['Vendors Detected (Network)'] = vendors.join(', ');
            return {
                description: r.description || 'N/A',
                selector: r.selector || 'N/A',
                status: r.success ? (Array.isArray(r.tealium_events) && r.tealium_events.length ? 'Tealium Detected' : 'Success') : 'Failure',
                data_variables: dataVars
            };
        });
        this.renderMacroEventTable(events, content);
    }

    populateMacroPageViewTab(results) {
        const pageViewContent = document.getElementById('pageview-data-content');
        if (pageViewContent) {
            pageViewContent.innerHTML = '<p><i>No page view data available for macro analysis.</i></p>';
        }
    }

    renderMacroEventTable(events, container) {
        if (!container) return;
        let html = `<table class="event-table"><thead><tr><th></th><th>Description</th><th>Selector</th><th>Status</th></tr></thead><tbody>`;
        events.forEach((ev) => {
            const hasDetails = ev.data_variables && Object.keys(ev.data_variables).length > 0;
            const statusClass = ev.status.toLowerCase().includes('fail') ? 'status-error' : (ev.status.toLowerCase().includes('tealium') ? 'status-success' : '');
            html += `<tr><td>`;
            if (hasDetails) html += `<button class="expand-details-btn" aria-expanded="false" title="Toggle Details"><i class="fas fa-chevron-right"></i></button>`;
            html += `</td><td>${this.escapeHtml(ev.description)}</td><td><code class="code-inline">${this.escapeHtml(ev.selector)}</code></td><td class="${statusClass}">${this.escapeHtml(ev.status)}</td></tr>`;
            if (hasDetails) {
                html += `<tr class="event-details" style="display:none;"><td colspan="4"><h5>Data Variables:</h5><table class="data-variables-table"><tbody>`;
                for (const [k, v] of Object.entries(ev.data_variables)) {
                    html += `<tr><th>${this.escapeHtml(k)}</th><td>${this.escapeHtml(typeof v === 'string' ? v : JSON.stringify(v))}</td></tr>`;
                }
                html += `</tbody></table></td></tr>`;
            }
        });
        html += `</tbody></table>`;
        container.innerHTML = html;
        const tbody = container.querySelector('.event-table tbody');
        if (tbody) {
            tbody.addEventListener('click', (e) => {
                const btn = e.target.closest('.expand-details-btn');
                if (!btn) return;
                const mainRow = btn.closest('tr');
                const details = mainRow.nextElementSibling;
                const expanded = btn.getAttribute('aria-expanded') === 'true';
                if (details && details.classList.contains('event-details')) {
                    details.style.display = expanded ? 'none' : 'table-row';
                    btn.setAttribute('aria-expanded', (!expanded).toString());
                    btn.classList.toggle('expanded', !expanded);
                }
            });
        }
    }

    createMacroVisualization(results) {
        const viz = document.getElementById('visualization-area');
        if (!viz) return;
        viz.innerHTML = `<div style="text-align:center;"><p>Visualization placeholder</p><p>Consider showing vendor coverage and event timelines.</p></div>`;
    }

    escapeHtml(unsafe) {
        if (typeof unsafe !== 'string') {
            try { unsafe = JSON.stringify(unsafe); } catch (e) { return '[Invalid Data]'; }
        }
        return unsafe.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\"/g,'&quot;').replace(/'/g,'&#039;');
    }
    initializeElements() {
        // Form and URL input
        this.recordForm = document.getElementById('record-form');
        this.urlInput = document.getElementById('record-url');
        
        // Control buttons (simplified)
        this.startBtn = document.getElementById('start-recording');
        
        // Status and info elements (hidden but needed for functionality)
        this.recordingStatus = document.getElementById('recording-status');
        this.actionCount = document.getElementById('action-count');
        this.recordingTime = document.getElementById('recording-time');
        this.macroName = document.getElementById('macro-name');
        this.actionList = document.getElementById('action-list');
        
        // Browser section
        this.browserSection = document.getElementById('browser-section');
        this.browserViewport = document.getElementById('browser-viewport');
        this.browserUrlDisplay = document.getElementById('browser-url-display');
        this.browserStatus = document.getElementById('browser-status');
        
        // Macros section
        this.macrosList = document.getElementById('macros-list');
        this.notification = document.getElementById('notification');

		// Analysis Engine UI elements (Record page)
		this.analysisStatus = document.getElementById('analysis-status');
		this.liveLogList = document.getElementById('live-log-list');
		this.loadingDiv = document.getElementById('loading');
		this.resultsContainer = document.getElementById('results-container');
		this.resultsCard = document.getElementById('results-card');
		this.resultsPre = document.getElementById('results-pre');
		this.copyResultsBtn = document.getElementById('copy-results');
		this.toggleExpandBtn = document.getElementById('toggle-expand-btn');
		this.downloadLink = document.getElementById('download-json');
		this.tabButtons = document.querySelectorAll('.tab-button');
		this.tabPanes = document.querySelectorAll('.tab-pane');
		this.aiAgentElement = document.querySelector('.ai-agent-element');
		this.analyzingLabel = document.querySelector('.analyzing-label');
		this.liveLogPanel = document.getElementById('live-log-panel');
		this.liveLogList = document.getElementById('live-log-list');
		
		this.stageEls = {
			setup: document.getElementById('stage-setup'),
			loading: document.getElementById('stage-loading'),
			data: document.getElementById('stage-data'),
			complete: document.getElementById('stage-complete')
		};

		// Analysis state
		this.analysisInProgress = false;
		this.analysisEventSource = null;
		this.analysisResults = null;
		this.currentStage = null;
		this.stageOrder = ['setup', 'loading', 'data', 'complete'];
    }

    bindEventListeners() {
        // Simplified recording button - toggles between start and stop
        this.startBtn.addEventListener('click', () => {
            if (this.isRecording) {
                this.stopRecording();
            } else {
                this.startRecording();
            }
        });
        
        // Load macros on page load only
        this.loadSavedMacros();
        
        // Prevent form submission
		this.recordForm.addEventListener('submit', (e) => e.preventDefault());

		// Results card controls (if Analysis Engine present on record page)
		if (this.toggleExpandBtn && this.resultsCard) {
			this.toggleExpandBtn.addEventListener('click', (e) => {
				e.stopPropagation();
				this.resultsCard.classList.toggle('expanded');
				const icon = this.toggleExpandBtn.querySelector('i');
				if (icon) {
					icon.classList.toggle('fa-expand-alt');
					icon.classList.toggle('fa-compress-alt');
				}
			});
			const header = document.querySelector('#results-card .toggle-expand');
			if (header) {
				header.addEventListener('click', () => this.toggleExpandBtn.click());
			}
		}

		if (this.copyResultsBtn && this.resultsPre) {
			this.copyResultsBtn.addEventListener('click', () => {
				navigator.clipboard.writeText(this.resultsPre.textContent || '').then(() => {
					this.showNotification('Copied to clipboard!', 'success');
				});
			});
		}

		// Tabs
		if (this.tabButtons && this.tabButtons.length) {
			this.tabButtons.forEach((btn) => {
				btn.addEventListener('click', () => {
					this.tabButtons.forEach((b) => b.classList.remove('active'));
					this.tabPanes.forEach((p) => p.classList.remove('active'));
					btn.classList.add('active');
					const pane = document.getElementById(btn.dataset.tab);
					if (pane) pane.classList.add('active');
				});
			});
		}
    }

    async startRecording() {
        const url = this.urlInput.value.trim();
        if (!url) {
            this.showNotification('Please enter a URL to record', 'error');
            return;
        }
        
        // Ensure URL has protocol
        if (!url.match(/^https?:\/\//)) {
            this.currentUrl = 'https://' + url;
        } else {
            this.currentUrl = url;
        }
        
        try {
            // First check if browser is available
            this.showNotification('Checking browser availability...', 'info');
            
            const browserCheck = await fetch('/api/record/check-browser');
            const checkResult = await browserCheck.json();
            
            if (!checkResult.success) {
                this.showNotification(
                    `Browser Error: ${checkResult.error}\n\n${checkResult.suggestion || ''}`, 
                    'error', 
                    8000
                );
                return;
            }
            
            this.isRecording = true;
            this.isPaused = false;
            this.recordedActions = [];
            this.startTime = Date.now();
            
            // Update UI
            this.updateRecordingStatus('Initializing', 'recording');
            this.updateControlButtons();
            this.showBrowserSection();
            this.startTimer();
            
            // Generate default macro name
            const urlObj = new URL(this.currentUrl);
            const defaultName = `Macro for ${urlObj.hostname} - ${new Date().toLocaleString()}`;
            this.macroName.value = defaultName;
            
            // Start the recording session
            await this.initializeRecordingSession();
            
            this.showNotification('Recording started! Interact with the page to capture actions.', 'success');
            
        } catch (error) {
            console.error('Failed to start recording:', error);
            this.showNotification('Failed to start recording: ' + error.message, 'error');
            this.isRecording = false;
            this.updateControlButtons();
            this.hideBrowserSection();
        }
    }

    async initializeRecordingSession() {
        try {
            this.updateRecordingStatus('Starting browser...', 'recording');
            
            // Call the backend to start the recording session
            const response = await fetch('/api/record/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    url: this.currentUrl,
                    macro_name: this.macroName.value
                })
            });
            
            if (!response.ok) {
                throw new Error(`Recording session failed: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.sessionId = data.session_id;
                this.browserUrlDisplay.textContent = this.currentUrl;
                this.browserStatus.textContent = 'Connected';
                this.updateRecordingStatus('Recording', 'recording');
                
                // Start listening for recorded actions
                this.startListeningForActions();
            } else {
                let errorMessage = data.error || 'Failed to initialize recording session';
                if (data.suggestion) {
                    errorMessage += '\n\nSuggestion: ' + data.suggestion;
                }
                if (data.traceback) {
                    console.error('Server traceback:', data.traceback);
                }
                throw new Error(errorMessage);
            }
            
        } catch (error) {
            console.error('Recording initialization error:', error);
            this.updateRecordingStatus('Failed to start', 'error');
            throw error;
        }
    }

    startListeningForActions() {
        if (!this.sessionId) return;
        
        // Use Server-Sent Events to listen for recorded actions
        this.eventSource = new EventSource(`/api/record/stream/${this.sessionId}`);
        
        this.eventSource.onmessage = (event) => {
            try {
                const actionData = JSON.parse(event.data);
                this.handleRecordedAction(actionData);
            } catch (error) {
                console.error('Error processing recorded action:', error);
            }
        };
        
        this.eventSource.onerror = async (error) => {
            console.error('EventSource error:', error);
            this.eventSource.close();
            
            // If we were recording and have actions, save them automatically
            if (this.isRecording && this.recordedActions.length > 0) {
                try {
                    await this.autoSaveRecordingOnDisconnect();
                } catch (saveError) {
                    console.error('Failed to auto-save recording:', saveError);
                    this.showNotification('Recording ended but failed to save. Use manual save.', 'error');
                }
            } else if (this.isRecording) {
                this.showNotification('Recording connection lost (no actions to save)', 'warning');
                this.isRecording = false;
                this.updateControlButtons();
                this.hideBrowserSection();
            }
        };
    }

    handleRecordedAction(actionData) {
        if (!this.isRecording || this.isPaused) return;
        
        // Filter out heartbeat, pageload, and scroll events - focus on meaningful interactions
        if (actionData.type === 'heartbeat' || actionData.type === 'pageload' || actionData.type === 'scroll') {
            return; // Skip these actions completely
        }
        
        // Add the action to our recorded actions list
        const action = {
            id: this.recordedActions.length + 1,
            timestamp: Date.now() - this.startTime,
            action_type: actionData.type,  // Use action_type to match backend
            selector: actionData.selector,
            text: actionData.text || '',
            coordinates: actionData.coordinates || null,
            description: this.generateActionDescription(actionData)
        };
        
        this.recordedActions.push(action);
        this.updateActionsList();
        this.updateActionCount();
        
        // Show brief notification for real actions only
        this.showNotification(`Recorded: ${action.description}`, 'info', 1500);
    }

    generateActionDescription(actionData) {
        switch (actionData.type) {
            case 'click':
                if (actionData.text && actionData.text.trim()) {
                    return `Click on "${actionData.text.trim()}"`;
                } else {
                    return `Click element (${actionData.selector})`;
                }
            case 'scroll':
                return null; // Skip scroll actions
            case 'type':
                return `Type "${actionData.text}" in input field`;
            case 'pageload':
                return `Page loaded: ${new URL(actionData.text || '').hostname}`;
            case 'navigate':
                return `Navigate to ${new URL(actionData.text || '').hostname}`;
            default:
                return `${actionData.type} action`;
        }
    }

    shortenSelector(selector) {
        if (!selector) return 'unknown';
        
        // If it's a long selector, show a shortened version
        if (selector.length > 50) {
            return selector.substring(0, 47) + '...';
        }
        return selector;
    }

    pauseRecording() {
        this.isPaused = true;
        this.updateRecordingStatus('Paused', 'paused');
        this.updateControlButtons();
        this.showNotification('Recording paused', 'info');
    }

    resumeRecording() {
        this.isPaused = false;
        this.updateRecordingStatus('Recording', 'recording');
        this.updateControlButtons();
        this.showNotification('Recording resumed', 'success');
    }

    async stopRecording() {
        try {
            this.isRecording = false;
            this.isPaused = false;
            
            // Stop the timer
            if (this.recordingTimer) {
                clearInterval(this.recordingTimer);
                this.recordingTimer = null;
            }
            
            // Close event source
            if (this.eventSource) {
                this.eventSource.close();
                this.eventSource = null;
            }
            
            // First try to force stop the recording session on the server
            if (this.sessionId) {
                try {
                    await fetch(`/api/record/stop/${this.sessionId}`, {
                        method: 'POST'
                    });
                } catch (e) {
                    console.warn('Could not force stop session:', e);
                }
            }
            
            // Save the macro if we have actions
            if (this.recordedActions.length > 0) {
                await this.saveMacro();
                
                // Show a detailed summary of what was recorded
                const actionSummary = this.recordedActions.map(action => 
                    `• ${action.description || action.type + ' on ' + action.selector}`
                ).join('\n');
                
                this.showNotification(
                    `Recording saved successfully!\n\nRecorded ${this.recordedActions.length} actions:\n${actionSummary}`, 
                    'success', 
                    8000
                );
            } else {
                this.showNotification('Recording stopped (no actions recorded)', 'info');
            }
            
            // Update UI
            this.updateRecordingStatus('Completed', 'completed');
            this.updateControlButtons();
            this.hideBrowserSection();
            
            // Refresh macros list
            await this.loadSavedMacros();
            
        } catch (error) {
            console.error('Failed to stop recording:', error);
            this.showNotification('Error stopping recording: ' + error.message, 'error');
            
            // Force UI reset even if there's an error
            this.isRecording = false;
            this.updateControlButtons();
            this.hideBrowserSection();
        }
    }

    async saveMacro() {
        console.log('Saving macro with', this.recordedActions.length, 'actions');
        
        const macroData = {
            name: this.macroName.value || `Macro for ${new URL(this.currentUrl).hostname} - ${new Date().toLocaleString()}`,
            url: this.currentUrl,
            actions: this.recordedActions,
            created_at: new Date().toISOString(),
            duration: this.recordedActions.length > 0 ? 
                this.recordedActions[this.recordedActions.length - 1].timestamp : 0
        };
        
        // Use direct import for consistent, reliable saving
        const response = await fetch('/api/macros/import', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                macro_data: macroData
            })
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Save failed:', errorText);
            throw new Error(`Failed to save macro: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || 'Failed to save macro');
        }
        
        console.log('Macro saved successfully:', result.macro_id);
        
        // Refresh the macros list
        await this.loadSavedMacros();
        
        return result;
    }

    clearRecording() {
        this.recordedActions = [];
        this.updateActionsList();
        this.updateActionCount();
        this.macroName.value = '';
        this.showNotification('Recording cleared', 'info');
    }

    // UI Update Methods
    updateRecordingStatus(status, className) {
        this.recordingStatus.textContent = status;
        this.recordingStatus.className = `status-badge ${className}`;
    }

    updateControlButtons() {
        if (this.isRecording) {
            this.startBtn.innerHTML = '<i class="fas fa-stop"></i> Stop Recording';
            this.startBtn.classList.add('recording');
        } else {
            this.startBtn.innerHTML = '<i class="fas fa-play"></i> Start Recording';
            this.startBtn.classList.remove('recording');
        }
    }
    
    async autoSaveRecordingOnDisconnect() {
        console.log('Auto-saving recording due to connection loss...');
        
        // Generate a descriptive name for the auto-saved macro
        const urlObj = new URL(this.currentUrl);
        const autoName = `Auto-saved: ${urlObj.hostname} - ${new Date().toLocaleString()}`;
        this.macroName.value = this.macroName.value || autoName;
        
        // Save the macro
        try {
            await this.saveMacro();
            
            // Update UI to show completion
            this.isRecording = false;
            this.updateRecordingStatus('Auto-saved', 'completed');
            this.updateControlButtons();
            this.hideBrowserSection();
            
            // Refresh macros list and show the saved actions
            await this.loadSavedMacros();
            
            // Show a summary of what was recorded
            const actionSummary = this.recordedActions.map(action => 
                `• ${action.description || action.type + ' on ' + action.selector}`
            ).join('\n');
            
            this.showNotification(
                `Recording auto-saved!\n\nRecorded ${this.recordedActions.length} actions:\n${actionSummary}`, 
                'success', 
                8000
            );
            
        } catch (error) {
            // Even if save fails, update UI and show the actions
            this.isRecording = false;
            this.updateControlButtons();
            this.hideBrowserSection();
            
            console.error('Auto-save failed:', error);
            this.displayUnsavedActions();
            throw error;
        }
    }
    
    displayUnsavedActions() {
        // Create a modal showing the unsaved actions
        const modal = document.createElement('div');
        modal.className = 'unsaved-actions-modal';
        modal.innerHTML = `
            <div class="modal-overlay"></div>
            <div class="modal-content">
                <div class="modal-header">
                    <h3><i class="fas fa-exclamation-triangle"></i> Recording Not Saved</h3>
                </div>
                <div class="modal-body">
                    <p>The recording connection was lost, but we captured ${this.recordedActions.length} actions:</p>
                    <div class="actions-summary">
                        ${this.recordedActions.map(action => `
                            <div class="action-summary-item">
                                <strong>${action.description || action.type}</strong><br>
                                <code>${action.selector}</code>
                            </div>
                        `).join('')}
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn-secondary" onclick="this.closest('.unsaved-actions-modal').remove()">
                        Close
                    </button>
                    <button class="btn-primary" onclick="recorder.retryManualSave(); this.closest('.unsaved-actions-modal').remove();">
                        <i class="fas fa-save"></i> Try Save Again
                    </button>
                </div>
            </div>
        `;
        
        // Add styles
        if (!document.getElementById('unsaved-actions-styles')) {
            const styles = document.createElement('style');
            styles.id = 'unsaved-actions-styles';
            styles.textContent = `
                .actions-summary {
                    max-height: 300px;
                    overflow-y: auto;
                    margin: 1rem 0;
                }
                .action-summary-item {
                    padding: 0.5rem;
                    border-left: 3px solid #4f79ff;
                    margin-bottom: 0.5rem;
                    background: #f8f9fa;
                    border-radius: 4px;
                }
                .action-summary-item code {
                    font-size: 0.8rem;
                    color: #666;
                }
            `;
            document.head.appendChild(styles);
        }
        
        document.body.appendChild(modal);
    }
    
    async retryManualSave() {
        try {
            await this.saveMacro();
            await this.loadSavedMacros();
            this.showNotification('Macro saved successfully!', 'success');
        } catch (error) {
            this.showNotification('Save failed again: ' + error.message, 'error');
        }
    }

    async forceStopRecording() {
        if (!confirm('Force stop will end recording without saving. Are you sure?')) {
            return;
        }
        
        try {
            this.isRecording = false;
            this.isPaused = false;
            
            // Stop the timer
            if (this.recordingTimer) {
                clearInterval(this.recordingTimer);
                this.recordingTimer = null;
            }
            
            // Close event source
            if (this.eventSource) {
                this.eventSource.close();
                this.eventSource = null;
            }
            
            // Force stop on server
            if (this.sessionId) {
                await fetch(`/api/record/stop/${this.sessionId}`, {
                    method: 'POST'
                });
            }
            
            // Update UI
            this.updateRecordingStatus('Force stopped', 'error');
            this.updateControlButtons();
            this.hideBrowserSection();
            
            // Clear recorded actions
            this.recordedActions = [];
            this.updateActionsList();
            this.updateActionCount();
            
            this.showNotification('Recording force stopped', 'warning');
            
        } catch (error) {
            console.error('Error force stopping:', error);
            this.showNotification('Error force stopping: ' + error.message, 'error');
            
            // Force UI reset
            this.isRecording = false;
            this.updateControlButtons();
            this.hideBrowserSection();
        }
    }

    updateActionCount() {
        this.actionCount.textContent = this.recordedActions.length;
    }

    updateActionsList() {
        if (this.recordedActions.length === 0) {
            this.actionList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-mouse-pointer"></i>
                    <p>Start recording to see captured interactions</p>
                </div>
            `;
            return;
        }
        
        const actionsHtml = this.recordedActions
            .slice(-10) // Show last 10 actions
            .map(action => `
                <div class="action-item" data-action-id="${action.id}">
                    <div class="action-icon">
                        <i class="fas ${this.getActionIcon(action.type)}"></i>
                    </div>
                    <div class="action-details">
                        <div class="action-description">${action.description}</div>
                        <div class="action-meta">
                            <span class="action-time">${this.formatTime(action.timestamp)}</span>
                            <span class="action-type">${action.type}</span>
                            ${action.selector ? `<span class="action-selector" title="${action.selector}">${action.selector}</span>` : ''}
                        </div>
                    </div>
                    <button class="action-delete" onclick="recorder.removeAction(${action.id})" title="Remove action">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `).join('');
        
        this.actionList.innerHTML = actionsHtml;
    }

    getActionIcon(actionType) {
        const iconMap = {
            'click': 'fa-mouse-pointer',
            'scroll': 'fa-arrows-alt-v',
            'type': 'fa-keyboard',
            'hover': 'fa-hand-pointer',
            'wait': 'fa-clock'
        };
        return iconMap[actionType] || 'fa-cog';
    }

    formatTime(milliseconds) {
        const seconds = Math.floor(milliseconds / 1000);
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }

    startTimer() {
        this.recordingTimer = setInterval(() => {
            if (this.isRecording && !this.isPaused) {
                const elapsed = Date.now() - this.startTime;
                this.recordingTime.textContent = this.formatTime(elapsed);
            }
        }, 1000);
    }

    showBrowserSection() {
        this.browserSection.style.display = 'block';
        this.browserSection.scrollIntoView({ behavior: 'smooth' });
    }

    hideBrowserSection() {
        this.browserSection.style.display = 'none';
    }

    // Macro Management Methods
    async loadSavedMacros() {
        try {
            console.log('Loading saved macros...');
            const response = await fetch('/api/macros/list');
            console.log('Macros API response status:', response.status);
            
            const data = await response.json();
            console.log('Macros API data:', data);
            
            if (data.success && data.macros.length > 0) {
                console.log('Displaying', data.macros.length, 'macros');
                this.displayMacros(data.macros);
            } else {
                console.log('No macros found, displaying empty state');
                this.displayEmptyMacrosState();
            }
        } catch (error) {
            console.error('Error loading macros:', error);
            this.displayEmptyMacrosState();
        }
    }

    displayMacros(macros) {
        console.log('displayMacros called with', macros.length, 'macros');
        console.log('macrosList element:', this.macrosList);
        
        const macrosHtml = macros.map((macro, index) => {
            const hostname = new URL(macro.url).hostname;
            const actionsCount = macro.actions ? macro.actions.length : 0;
            const duration = this.formatTime(macro.duration || 0);
            const createdDate = new Date(macro.created_at).toLocaleDateString();
            const macroId = macro.id;
            
            return `
            <div class="macro-item ${index < 3 ? 'new' : ''}" data-macro-id="${macroId}">
                <div class="macro-header">
                    <h4 class="macro-name" contenteditable="true" onblur="recorder.renameMacro('${macroId}', this.textContent.trim())" title="Click to edit macro name">${this.escapeHtml(macro.name)}</h4>
                    <div class="macro-actions">
                        <button class="analyze-btn" data-macro-id="${macroId}" onclick="recorder.analyzeMacroSelectors('${macroId}')" title="Analyze Tealium events for this macro">
                            <i class="fas fa-chart-line"></i> 
                            <span class="label">Analyze</span>
                            <span class="spinner" aria-hidden="true"></span>
                        </button>
                        <button class="btn-icon" onclick="recorder.deleteMacro('${macroId}')" title="Delete this macro">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
                <div class="macro-details">
                    <div class="macro-meta">
                        <span title="${macro.url}">
                            <i class="fas fa-globe"></i> 
                            ${this.escapeHtml(hostname)}
                        </span>
                        <span title="Number of recorded actions">
                            <i class="fas fa-mouse-pointer"></i> 
                            ${actionsCount} actions
                        </span>
                        <span title="Recording duration">
                            <i class="fas fa-clock"></i> 
                            ${duration}
                        </span>
                        <span title="Date created">
                            <i class="fas fa-calendar"></i> 
                            ${createdDate}
                        </span>
                    </div>
                    <div class="macro-status">
                        <div class="status-badge" title="Macro is ready to use">
                            <i class="fas fa-check-circle"></i>
                            Ready
                        </div>
                    </div>
                    <div class="analysis-progress" id="progress-${macroId}">
                        <div class="progress-bar">
                            <div class="progress-fill" id="progress-fill-${macroId}"></div>
                        </div>
                        <div class="progress-text" id="progress-text-${macroId}">Starting analysis...</div>
                    </div>
                </div>
            </div>
            `;
        }).join('');
        
        this.macrosList.innerHTML = macrosHtml;
        
        // Add entrance animation to new items
        setTimeout(() => {
            document.querySelectorAll('.macro-item.new').forEach(item => {
                item.classList.remove('new');
            });
        }, 100);
    }

    displayEmptyMacrosState() {
        this.macrosList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-folder-open"></i>
                <h3>No Macros Saved Yet</h3>
                <p>Record your first macro to see it here. Saved macros can be replayed, edited, and exported.</p>
            </div>
        `;
    }

    // Macro Management Methods
    async playMacro(macroId) {
        // Show options for regular playback vs playback with analysis
        const choice = confirm('Would you like to run this macro with tag analysis?\n\nClick OK for analysis mode, Cancel for regular playback.');
        
        try {
            this.showNotification('Starting macro playback...', 'info');
            
            const endpoint = choice ? 
                `/api/macros/play-with-analysis/${macroId}` : 
                `/api/macros/play/${macroId}`;
            
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Start listening for playback updates
                this.startPlaybackStreaming(result.playback_id, choice);
                
                const mode = choice ? 'with analysis' : 'regular';
                this.showNotification(`Macro playback started (${mode} mode)!`, 'success');
            } else {
                this.showNotification('Failed to start playback: ' + result.error, 'error');
            }
        } catch (error) {
            console.error('Error playing macro:', error);
            this.showNotification('Error starting playback: ' + error.message, 'error');
        }
    }

    startPlaybackStreaming(playbackId, withAnalysis = false) {
        const eventSource = new EventSource(`/api/macros/playback/stream/${playbackId}`);
        
        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handlePlaybackUpdate(data, playbackId, withAnalysis);
            } catch (error) {
                console.error('Error processing playback update:', error);
            }
        };
        
        eventSource.onerror = () => {
            eventSource.close();
        };
    }

    handlePlaybackUpdate(data, playbackId, withAnalysis = false) {
        if (data.type === 'action') {
            this.showNotification(`Playing: ${data.description}`, 'info', 1000);
        } else if (data.type === 'complete') {
            this.showNotification('Macro playback completed!', 'success');
            
            // If analysis was enabled, fetch and display results
            if (withAnalysis) {
                setTimeout(() => {
                    this.fetchAndDisplayAnalysisResults(playbackId);
                }, 1000); // Brief delay to allow analysis to complete
            }
        } else if (data.type === 'error') {
            this.showNotification('Playback error: ' + data.message, 'error');
        }
    }

    async fetchAndDisplayAnalysisResults(playbackId) {
        try {
            const response = await fetch(`/api/macros/playback/${playbackId}/analysis`);
            const result = await response.json();
            
            if (result.success) {
                this.displayAnalysisResults(result.analysis_results);
            } else {
                this.showNotification('Failed to load analysis results: ' + result.error, 'error');
            }
        } catch (error) {
            console.error('Error fetching analysis results:', error);
            this.showNotification('Error loading analysis results: ' + error.message, 'error');
        }
    }

    displayAnalysisResults(results) {
        // Create a modal to display analysis results
        const modal = document.createElement('div');
        modal.className = 'analysis-results-modal';
        modal.innerHTML = `
            <div class="modal-overlay" onclick="this.parentElement.remove()"></div>
            <div class="modal-content analysis-modal">
                <div class="modal-header">
                    <h3><i class="fas fa-chart-line"></i> Macro Analysis Results: ${results.macro_name}</h3>
                    <button class="modal-close" onclick="this.closest('.analysis-results-modal').remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="analysis-summary">
                        <div class="summary-cards">
                            <div class="summary-card">
                                <div class="card-icon"><i class="fas fa-mouse-pointer"></i></div>
                                <div class="card-content">
                                    <div class="card-number">${results.summary.user_interactions}</div>
                                    <div class="card-label">User Interactions</div>
                                </div>
                            </div>
                            <div class="summary-card">
                                <div class="card-icon"><i class="fas fa-tags"></i></div>
                                <div class="card-content">
                                    <div class="card-number">${results.summary.tracking_calls}</div>
                                    <div class="card-label">Tracking Events</div>
                                </div>
                            </div>
                            <div class="summary-card">
                                <div class="card-icon"><i class="fas fa-network-wired"></i></div>
                                <div class="card-content">
                                    <div class="card-number">${results.summary.network_requests}</div>
                                    <div class="card-label">Network Requests</div>
                                </div>
                            </div>
                            <div class="summary-card">
                                <div class="card-icon"><i class="fas fa-list"></i></div>
                                <div class="card-content">
                                    <div class="card-number">${results.total_events}</div>
                                    <div class="card-label">Total Events</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="analysis-sections">
                        <div class="section">
                            <h4><i class="fas fa-clock"></i> Event Timeline</h4>
                            <div class="timeline-container">
                                ${results.timeline.map(event => `
                                    <div class="timeline-item">
                                        <div class="timeline-time">${new Date(event.timestamp).toLocaleTimeString()}</div>
                                        <div class="timeline-content">
                                            <div class="timeline-type">${event.type}</div>
                                            <div class="timeline-desc">${event.description}</div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        
                        <div class="section">
                            <h4><i class="fas fa-chart-pie"></i> Events by Type</h4>
                            <div class="events-breakdown">
                                ${Object.entries(results.events_by_type).map(([type, events]) => `
                                    <div class="breakdown-item">
                                        <div class="breakdown-type">${type}</div>
                                        <div class="breakdown-count">${events.length} events</div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn-secondary" onclick="this.closest('.analysis-results-modal').remove()">Close</button>
                    <button class="btn-primary" onclick="recorder.exportAnalysisResults('${results.macro_name}', arguments[0])" 
                            data-results='${JSON.stringify(results).replace(/'/g, "&#39;")}'>
                        <i class="fas fa-download"></i> Export Results
                    </button>
                </div>
            </div>
        `;
        
        // Add enhanced styles for analysis modal
        if (!document.getElementById('analysis-modal-styles')) {
            const styles = document.createElement('style');
            styles.id = 'analysis-modal-styles';
            styles.textContent = `
                .analysis-modal {
                    max-width: 900px;
                    max-height: 85vh;
                }
                .analysis-summary {
                    margin-bottom: 2rem;
                }
                .summary-cards {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 1rem;
                    margin-bottom: 1.5rem;
                }
                .summary-card {
                    display: flex;
                    align-items: center;
                    padding: 1rem;
                    background: #f8f9fa;
                    border-radius: 8px;
                    border: 1px solid #e9ecef;
                }
                .card-icon {
                    font-size: 2rem;
                    color: #4f79ff;
                    margin-right: 1rem;
                }
                .card-number {
                    font-size: 1.5rem;
                    font-weight: bold;
                    color: #333;
                }
                .card-label {
                    font-size: 0.9rem;
                    color: #666;
                }
                .analysis-sections {
                    display: grid;
                    gap: 1.5rem;
                }
                .section h4 {
                    margin-bottom: 1rem;
                    color: #333;
                    border-bottom: 2px solid #4f79ff;
                    padding-bottom: 0.5rem;
                }
                .timeline-container {
                    max-height: 300px;
                    overflow-y: auto;
                    border: 1px solid #e9ecef;
                    border-radius: 4px;
                    padding: 1rem;
                }
                .timeline-item {
                    display: flex;
                    align-items: flex-start;
                    padding: 0.5rem 0;
                    border-bottom: 1px solid #f1f3f4;
                }
                .timeline-item:last-child {
                    border-bottom: none;
                }
                .timeline-time {
                    min-width: 100px;
                    font-size: 0.85rem;
                    color: #666;
                    margin-right: 1rem;
                }
                .timeline-type {
                    background: #4f79ff;
                    color: white;
                    padding: 2px 6px;
                    border-radius: 4px;
                    font-size: 0.8rem;
                    margin-bottom: 0.25rem;
                    display: inline-block;
                }
                .timeline-desc {
                    font-size: 0.9rem;
                    color: #555;
                }
                .events-breakdown {
                    display: grid;
                    gap: 0.5rem;
                }
                .breakdown-item {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 0.75rem;
                    background: #f8f9fa;
                    border-radius: 4px;
                    border: 1px solid #e9ecef;
                }
                .breakdown-type {
                    font-weight: 500;
                    color: #333;
                }
                .breakdown-count {
                    color: #4f79ff;
                    font-weight: bold;
                }
            `;
            document.head.appendChild(styles);
        }
        
        document.body.appendChild(modal);
        
        this.showNotification('Analysis results are ready! 📊', 'success', 3000);
    }

    exportAnalysisResults(macroName, buttonElement) {
        try {
            const results = JSON.parse(buttonElement.getAttribute('data-results').replace(/&#39;/g, "'"));
            
            const exportData = {
                ...results,
                exported_at: new Date().toISOString(),
                exported_by: 'Webspark Macro Recorder'
            };
            
            const blob = new Blob([JSON.stringify(exportData, null, 2)], 
                { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = `analysis_${macroName.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            this.showNotification('Analysis results exported successfully!', 'success');
        } catch (error) {
            console.error('Error exporting analysis results:', error);
            this.showNotification('Error exporting results: ' + error.message, 'error');
        }
    }

    async editMacro(macroId) {
        try {
            const response = await fetch(`/api/macros/${macroId}`);
            const result = await response.json();
            
            if (result.success) {
                this.openMacroEditor(result.macro);
            } else {
                this.showNotification('Failed to load macro: ' + result.error, 'error');
            }
        } catch (error) {
            console.error('Error loading macro for editing:', error);
            this.showNotification('Error loading macro: ' + error.message, 'error');
        }
    }

    openMacroEditor(macro) {
        // Create a modal for editing the macro
        const modal = document.createElement('div');
        modal.className = 'macro-editor-modal';
        modal.innerHTML = `
            <div class="modal-overlay" onclick="this.parentElement.remove()"></div>
            <div class="modal-content">
                <div class="modal-header">
                    <h3><i class="fas fa-edit"></i> Edit Macro: ${macro.name}</h3>
                    <button class="modal-close" onclick="this.closest('.macro-editor-modal').remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label for="edit-macro-name">Macro Name:</label>
                        <input type="text" id="edit-macro-name" value="${macro.name}" class="form-input">
                    </div>
                    <div class="form-group">
                        <label for="edit-macro-description">Description:</label>
                        <textarea id="edit-macro-description" class="form-textarea" rows="3">${macro.description || ''}</textarea>
                    </div>
                    <div class="form-group">
                        <label>Actions (${macro.actions.length} total):</label>
                        <div class="actions-editor" id="actions-editor">
                            ${macro.actions.map((action, index) => `
                                <div class="action-editor-item" data-action-index="${index}">
                                    <div class="action-info">
                                        <span class="action-type">${action.action_type}</span>
                                        <span class="action-desc">${action.description}</span>
                                    </div>
                                    <div class="action-controls">
                                        <button class="btn-small" onclick="recorder.editAction('${macro.id}', ${index})">Edit</button>
                                        <button class="btn-small btn-danger" onclick="recorder.deleteAction('${macro.id}', ${index})">Delete</button>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn-secondary" onclick="this.closest('.macro-editor-modal').remove()">Cancel</button>
                    <button class="btn-primary" onclick="recorder.saveMacroEdits('${macro.id}')">Save Changes</button>
                </div>
            </div>
        `;
        
        // Add styles if not already present
        if (!document.getElementById('macro-editor-styles')) {
            const styles = document.createElement('style');
            styles.id = 'macro-editor-styles';
            styles.textContent = `
                .macro-editor-modal {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    z-index: 10000;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .modal-overlay {
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.7);
                }
                .modal-content {
                    position: relative;
                    background: white;
                    border-radius: 8px;
                    max-width: 800px;
                    max-height: 80vh;
                    width: 90%;
                    display: flex;
                    flex-direction: column;
                }
                .modal-header {
                    padding: 1rem;
                    border-bottom: 1px solid #eee;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .modal-body {
                    padding: 1rem;
                    overflow-y: auto;
                    flex: 1;
                }
                .modal-footer {
                    padding: 1rem;
                    border-top: 1px solid #eee;
                    display: flex;
                    justify-content: flex-end;
                    gap: 0.5rem;
                }
                .form-group {
                    margin-bottom: 1rem;
                }
                .form-group label {
                    display: block;
                    margin-bottom: 0.25rem;
                    font-weight: 500;
                }
                .form-input, .form-textarea {
                    width: 100%;
                    padding: 0.5rem;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    font-size: 14px;
                }
                .actions-editor {
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    max-height: 300px;
                    overflow-y: auto;
                }
                .action-editor-item {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 0.5rem;
                    border-bottom: 1px solid #eee;
                }
                .action-info {
                    flex: 1;
                }
                .action-type {
                    background: #4f79ff;
                    color: white;
                    padding: 2px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                    margin-right: 0.5rem;
                }
                .btn-small {
                    padding: 4px 8px;
                    font-size: 12px;
                    border: 1px solid #ddd;
                    background: white;
                    border-radius: 4px;
                    cursor: pointer;
                    margin-left: 4px;
                }
                .btn-danger {
                    border-color: #dc3545;
                    color: #dc3545;
                }
                .btn-primary {
                    background: #4f79ff;
                    color: white;
                    border: 1px solid #4f79ff;
                    padding: 0.5rem 1rem;
                    border-radius: 4px;
                    cursor: pointer;
                }
                .btn-secondary {
                    background: white;
                    color: #666;
                    border: 1px solid #ddd;
                    padding: 0.5rem 1rem;
                    border-radius: 4px;
                    cursor: pointer;
                }
                .modal-close {
                    background: none;
                    border: none;
                    font-size: 18px;
                    color: #666;
                    cursor: pointer;
                    padding: 4px;
                }
            `;
            document.head.appendChild(styles);
        }
        
        document.body.appendChild(modal);
    }

    async saveMacroEdits(macroId) {
        try {
            const name = document.getElementById('edit-macro-name').value;
            const description = document.getElementById('edit-macro-description').value;
            
            const response = await fetch(`/api/macros/${macroId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: name,
                    description: description
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Macro updated successfully!', 'success');
                document.querySelector('.macro-editor-modal').remove();
                await this.loadSavedMacros(); // Refresh the list
            } else {
                this.showNotification('Failed to update macro: ' + result.error, 'error');
            }
        } catch (error) {
            console.error('Error saving macro edits:', error);
            this.showNotification('Error saving changes: ' + error.message, 'error');
        }
    }

    async exportMacro(macroId) {
        try {
            const response = await fetch(`/api/macros/${macroId}`);
            const result = await response.json();
            
            if (result.success) {
                const macro = result.macro;
                const exportData = {
                    ...macro,
                    exported_at: new Date().toISOString(),
                    exported_by: 'Webspark Macro Recorder'
                };
                
                // Create and download the file
                const blob = new Blob([JSON.stringify(exportData, null, 2)], 
                    { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                
                const a = document.createElement('a');
                a.href = url;
                a.download = `macro_${macro.name.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                
                this.showNotification('Macro exported successfully!', 'success');
            } else {
                this.showNotification('Failed to export macro: ' + result.error, 'error');
            }
        } catch (error) {
            console.error('Error exporting macro:', error);
            this.showNotification('Error exporting macro: ' + error.message, 'error');
        }
    }

    async deleteMacro(macroId) {
        if (!confirm('Are you sure you want to delete this macro? This action cannot be undone.')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/macros/${macroId}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Macro deleted successfully!', 'success');
                await this.loadSavedMacros(); // Refresh the list
            } else {
                this.showNotification('Failed to delete macro: ' + result.error, 'error');
            }
        } catch (error) {
            console.error('Error deleting macro:', error);
            this.showNotification('Error deleting macro: ' + error.message, 'error');
        }
    }

    // import/export removed from UI per design simplification

    removeAction(actionId) {
        this.recordedActions = this.recordedActions.filter(action => action.id !== actionId);
        this.updateActionsList();
        this.updateActionCount();
        this.showNotification('Action removed', 'info');
    }
    
    async analyzeMacroSelectors(macroId) {
        try {
            this.setAnalyzeButtonState(macroId, true);
            // Start the Tealium analysis
            const startResponse = await fetch(`/api/macros/${macroId}/analyze-tealium-events`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const startResult = await startResponse.json();
            
            if (!startResult.success) {
                this.setAnalyzeButtonState(macroId, false);
                throw new Error(startResult.error || 'Failed to start Tealium analysis');
            }
            
			// Show starting notification and initialize Analysis Engine UI
			this.showNotification(`Starting Tealium analysis for ${startResult.click_actions} click actions...`, 'info', 3000);
			this.initMacroAnalysisUI();
			this.updateMacroUIState('running');
			
			// Start streaming the analysis results into the Analysis Engine UI
			this.startTealiumAnalysisStream(macroId, startResult);

            // Auto-scroll to Analysis Engine section
            const engineSection = document.getElementById('macro-analysis-engine');
            if (engineSection) {
                engineSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
            
        } catch (error) {
            console.error('Error starting Tealium analysis:', error);
            this.showNotification('Error starting analysis: ' + error.message, 'error');
            this.setAnalyzeButtonState(macroId, false);
        }
    }
    
    startTealiumAnalysisStream(macroId, analysisInfo) {
        if (this.analysisEventSource) {
            try { this.analysisEventSource.close(); } catch (e) {}
        }
        this.analysisEventSource = new EventSource(`/api/macros/${macroId}/analyze-tealium-events/stream`);

        this.analysisEventSource.onopen = () => {
            this.addMacroStatusMessage('Connected to analysis server', 'info');
        };

        this.analysisEventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.message) {
                    this.addMacroStatusMessage(data.message, data.status || 'info');
                }

                if (data.status === 'testing_selector' && data.selector_description) {
                    this.updateMacroStage('data');
                } else if (data.status === 'browser_launched' || data.status === 'starting') {
                    this.updateMacroStage('setup');
                } else if (data.status === 'navigating' || data.status === 'page_loaded') {
                    this.updateMacroStage('loading');
                }

                if (data.status === 'complete' && data.results) {
                    this.analysisResults = data.results;
                    if (this.resultsPre) this.resultsPre.textContent = this.formatMacroResultsForConsole(data.results);
                    this.populateMacroClickEvents(data.results);
                    this.populateMacroPageViewTab(data.results);
                    this.createMacroVisualization(data.results);
                    if (this.downloadLink) {
                        const blob = new Blob([JSON.stringify(data.results, null, 2)], { type: 'application/json' });
                        this.downloadLink.href = URL.createObjectURL(blob);
                        const safe = (data.results.macro_name || 'macro_analysis').replace(/[^a-z0-9]/gi, '_').toLowerCase();
                        this.downloadLink.download = `${safe}.json`;
                        this.downloadLink.style.display = 'inline-flex';
                    }
                    this.updateMacroUIState('completed');
                    this.analysisEventSource.close();
                    this.setAnalyzeButtonState(macroId, false);
                    this.addMacroStatusMessage('✅ Analysis complete!', 'success');
                } else if (data.status === 'error') {
                    this.updateMacroUIState('error', data.message);
                    this.analysisEventSource.close();
                    this.setAnalyzeButtonState(macroId, false);
                }
            } catch (e) {
                console.error('Error processing analysis update:', e);
                this.addMacroStatusMessage('Received unparseable message from server', 'error');
            }
        };

        this.analysisEventSource.onerror = () => {
            if (this.analysisEventSource) this.analysisEventSource.close();
            this.updateMacroUIState('error', 'Connection lost during analysis');
        };
    }

    setAnalyzeButtonState(macroId, isLoading) {
        const btn = document.querySelector(`.analyze-btn[data-macro-id="${macroId}"]`);
        if (!btn) return;
        if (isLoading) {
            btn.classList.add('loading');
            btn.setAttribute('disabled', 'true');
            const label = btn.querySelector('.label');
            if (label) label.textContent = 'Analyzing…';
        } else {
            btn.classList.remove('loading');
            btn.removeAttribute('disabled');
            const label = btn.querySelector('.label');
            if (label) label.textContent = 'Analyze';
        }
    }
    
    createAnalysisProgressModal(analysisInfo) {
        const modal = document.createElement('div');
        modal.className = 'tealium-analysis-modal';
        modal.innerHTML = `
            <div class="modal-overlay"></div>
            <div class="modal-content analysis-progress-modal">
                <div class="modal-header">
                    <h3><i class="fas fa-chart-line"></i> Tealium Analysis: ${analysisInfo.macro_name}</h3>
                </div>
                <div class="modal-body">
                    <div class="analysis-info">
                        <p><strong>URL:</strong> <span class="url-display">${analysisInfo.macro_url}</span></p>
                        <p><strong>Click Actions:</strong> ${analysisInfo.click_actions}</p>
                    </div>
                    
                    <div class="progress-section">
                        <div class="progress-bar">
                            <div class="progress-fill" id="analysis-progress-fill" style="width: 0%"></div>
                        </div>
                        <div class="progress-text" id="analysis-progress-text">Preparing analysis...</div>
                    </div>
                    
                    <div class="current-action" id="current-action-display" style="display: none;">
                        <h4>Currently Testing:</h4>
                        <div class="action-detail">
                            <div class="action-description" id="current-action-description"></div>
                            <div class="action-selector" id="current-action-selector"></div>
                        </div>
                    </div>
                    
                    <div class="live-results" id="live-results" style="display: none;">
                        <h4>Live Results:</h4>
                        <div class="results-list" id="results-list"></div>
                    </div>
                </div>
            </div>
        `;
        
        return modal;
    }
    
    updateAnalysisProgress(data, modal) {
        const progressFill = modal.querySelector('#analysis-progress-fill');
        const progressText = modal.querySelector('#analysis-progress-text');
        const currentActionDisplay = modal.querySelector('#current-action-display');
        const liveResults = modal.querySelector('#live-results');
        const resultsList = modal.querySelector('#results-list');
        
        // Update progress bar
        if (data.progress !== undefined) {
            progressFill.style.width = `${data.progress}%`;
        }
        
        // Update status text
        if (data.message) {
            progressText.textContent = data.message;
        }
        
        // Show current selector being tested
        if (data.status === 'testing_selector' && data.current_selector) {
            currentActionDisplay.style.display = 'block';
            modal.querySelector('#current-action-description').textContent = data.selector_description;
            modal.querySelector('#current-action-selector').textContent = data.current_selector;
        }
        
        // Add live results
        if (data.status === 'selector_completed' && data.result) {
            liveResults.style.display = 'block';
            const resultItem = document.createElement('div');
            resultItem.className = `result-item ${data.result.success ? 'success' : 'failed'}`;
            
            const tealiumStatus = data.result.tealium_events ? 
                '<span class="tealium-active">✅ Tealium Events Detected</span>' : 
                '<span class="tealium-inactive">❌ No Tealium Events</span>';
            
            resultItem.innerHTML = `
                <div class="result-description">${data.result.description}</div>
                <div class="result-status">${tealiumStatus}</div>
                <div class="result-selector">${data.result.selector}</div>
            `;
            
            resultsList.appendChild(resultItem);
            resultsList.scrollTop = resultsList.scrollHeight;
        }
    }
    
    displayTealiumAnalysisResults(results, progressModal) {
        // Remove progress modal
        if (progressModal) {
            progressModal.remove();
        }
        
        // Create results modal
        const modal = document.createElement('div');
        modal.className = 'tealium-results-modal';
        modal.innerHTML = `
            <div class="modal-overlay" onclick="this.parentElement.remove()"></div>
            <div class="modal-content tealium-results">
                <div class="modal-header">
                    <h3><i class="fas fa-chart-line"></i> Tealium Analysis Results: ${results.macro_name}</h3>
                    <button class="modal-close" onclick="this.closest('.tealium-results-modal').remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="results-summary">
                        <div class="summary-cards">
                            <div class="summary-card success">
                                <div class="card-number">${results.tealium_active_clicks}</div>
                                <div class="card-label">Tealium Events Triggered</div>
                            </div>
                            <div class="summary-card total">
                                <div class="card-number">${results.successful_clicks}</div>
                                <div class="card-label">Successful Clicks</div>
                            </div>
                            <div class="summary-card coverage">
                                <div class="card-number">${Math.round(results.tealium_coverage)}%</div>
                                <div class="card-label">Tealium Coverage</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="detailed-results">
                        <h4><i class="fas fa-list"></i> Detailed Click Analysis</h4>
                        <div class="results-table">
                            ${results.selector_results.map((result, index) => {
                                const firstTealiumEvent = Array.isArray(result.tealium_events) ? result.tealium_events[0] : null;
                                const eventData = firstTealiumEvent && firstTealiumEvent.data && typeof firstTealiumEvent.data === 'object' ? firstTealiumEvent.data : {};
                                const vendors = result.vendors_in_network && typeof result.vendors_in_network === 'object' ? Object.keys(result.vendors_in_network) : [];
                                const statusHtml = result.success ? (Array.isArray(result.tealium_events) && result.tealium_events.length ? '<span class="status-success tealium">✅ Tealium Events Detected</span>' : '<span class="status-success">✅ Click Successful (No Tealium Events)</span>') : `<span class=\"status-failed\">❌ ${result.error || 'Click Failed'}</span>`;
                                const hasDetails = (eventData && Object.keys(eventData).length > 0) || (vendors && vendors.length > 0);
                                return `
                                <div class=\"result-row ${result.success ? 'success' : 'failed'} ${Array.isArray(result.tealium_events) && result.tealium_events.length ? 'tealium-active' : ''}\"> 
                                  <div class=\"result-index\">#${index + 1}</div>
                                  <div class=\"result-content\">
                                    <div class=\"result-description\">${result.description || ''}</div>
                                    <div class=\"result-selector\">${result.selector || ''}</div>
                                    <div class=\"result-status\">${statusHtml}</div>
                                    ${hasDetails ? `
                                      <button class=\"expand-details-btn\" aria-expanded=\"false\" title=\"Toggle Details\">
                                        <i class=\"fas fa-chevron-right\"></i>
                                      </button>
                                      <div class=\"event-details\" style=\"display:none; margin-top:8px;\">
                                        ${vendors && vendors.length ? `
                                          <h5>Vendors Detected (Network)</h5>
                                          <div>${vendors.join(', ')}</div>
                                        ` : ''}
                                        ${eventData && Object.keys(eventData).length ? `
                                          <h5 style=\"margin-top:8px;\">Data Variables</h5>
                                          <table class=\"data-variables-table\"><tbody>
                                            ${Object.entries(eventData).map(([k,v]) => `
                                              <tr><th>${k}</th><td>${(typeof v === 'object') ? (escapeHtml(JSON.stringify(v))) : (escapeHtml(String(v)))} </td></tr>
                                            `).join('')}
                                          </tbody></table>
                                        ` : ''}
                                      </div>
                                    ` : ''}
                                  </div>
                                </div>`;
                            }).join('')}
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn-secondary" onclick="this.closest('.tealium-results-modal').remove()">Close</button>
                    <button class="btn-primary" onclick="recorder.exportTealiumResults('${results.macro_name}', arguments[0])"
                            data-results='${JSON.stringify(results).replace(/'/g, "&#39;")}'>
                        <i class="fas fa-download"></i> Export Results
                    </button>
                </div>
            </div>
        `;
        
        // Add enhanced styles for Tealium results
        if (!document.getElementById('tealium-results-styles')) {
            const styles = document.createElement('style');
            styles.id = 'tealium-results-styles';
            styles.textContent = `
                .tealium-results {
                    max-width: 1100px;
                    max-height: 90vh;
                }
                .results-summary {
                    margin-bottom: 2rem;
                }
                .summary-cards {
                    display: flex;
                    gap: 1rem;
                    justify-content: space-around;
                }
                .summary-card {
                    background: #f8f9fa;
                    padding: 1.5rem;
                    border-radius: 8px;
                    text-align: center;
                    flex: 1;
                    border-left: 4px solid #4f79ff;
                }
                .summary-card.success {
                    border-left-color: #28a745;
                    background: #f0f8f2;
                }
                .summary-card.coverage {
                    border-left-color: #ffc107;
                    background: #fffdf0;
                }
                .card-number {
                    font-size: 2rem;
                    font-weight: 700;
                    color: #4f79ff;
                    margin-bottom: 0.5rem;
                }
                .summary-card.success .card-number {
                    color: #28a745;
                }
                .summary-card.coverage .card-number {
                    color: #ffc107;
                }
                .card-label {
                    font-size: 0.875rem;
                    color: #666;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                .results-table {
                    max-height: 400px;
                    overflow-y: auto;
                }
                .result-row {
                    display: flex;
                    align-items: flex-start;
                    gap: 1rem;
                    padding: 1rem;
                    margin-bottom: 1rem;
                    border: 1px solid #e1e5e9;
                    border-radius: 8px;
                    background: #fff;
                }
                .result-row.tealium-active {
                    border-left: 4px solid #28a745;
                    background: #f8fff9;
                }
                .result-index {
                    background: #4f79ff;
                    color: white;
                    width: 30px;
                    height: 30px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 0.875rem;
                    font-weight: 600;
                    flex-shrink: 0;
                }
                .result-content {
                    flex: 1;
                }
                .result-description {
                    font-weight: 600;
                    margin-bottom: 0.25rem;
                }
                .result-selector {
                    font-family: 'JetBrains Mono', monospace;
                    font-size: 0.8rem;
                    color: #666;
                    background: #f8f9fa;
                    padding: 0.25rem 0.5rem;
                    border-radius: 3px;
                    margin-bottom: 0.5rem;
                    word-break: break-all;
                }
                .status-success {
                    color: #28a745;
                    font-weight: 600;
                }
                .status-success.tealium {
                    background: #d4edda;
                    padding: 0.25rem 0.5rem;
                    border-radius: 4px;
                }
                .status-failed {
                    color: #dc3545;
                    font-weight: 600;
                }
                .tealium-details {
                    margin-top: 0.5rem;
                    padding: 0.5rem;
                    background: #e8f5e8;
                    border-radius: 4px;
                    font-size: 0.875rem;
                }
                .progress-bar {
                    width: 100%;
                    height: 20px;
                    background: #e9ecef;
                    border-radius: 10px;
                    overflow: hidden;
                    margin-bottom: 1rem;
                }
                .progress-fill {
                    height: 100%;
                    background: linear-gradient(90deg, #4f79ff, #28a745);
                    transition: width 0.3s ease;
                }
            `;
            document.head.appendChild(styles);
        }
        
        document.body.appendChild(modal);
        this.showNotification(`Analysis complete! ${results.tealium_active_clicks}/${results.total_selectors} clicks triggered Tealium events`, 'success', 5000);
    }
    
    showAnalysisError(errorData, progressModal) {
        if (progressModal) {
            progressModal.remove();
        }
        
        this.showNotification(`Analysis failed: ${errorData.message}`, 'error', 5000);
    }
    
    exportTealiumResults(macroName, buttonElement) {
        try {
            const resultsData = JSON.parse(buttonElement.getAttribute('data-results'));
            const jsonStr = JSON.stringify(resultsData, null, 2);
            const blob = new Blob([jsonStr], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = `tealium_analysis_${macroName.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            this.showNotification('Tealium analysis exported successfully!', 'success');
        } catch (error) {
            console.error('Error exporting Tealium results:', error);
            this.showNotification('Error exporting results: ' + error.message, 'error');
        }
    }
    
    displaySelectorAnalysis(analysis) {
        const modal = document.createElement('div');
        modal.className = 'selector-analysis-modal';
        modal.innerHTML = `
            <div class="modal-overlay" onclick="this.parentElement.remove()"></div>
            <div class="modal-content selector-modal">
                <div class="modal-header">
                    <h3><i class="fas fa-search"></i> Selector Analysis: ${analysis.macro_name}</h3>
                    <button class="modal-close" onclick="this.closest('.selector-analysis-modal').remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="analysis-summary">
                        <div class="summary-stats">
                            <div class="stat-item">
                                <span class="stat-label">Total Actions:</span>
                                <span class="stat-value">${analysis.total_actions}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Tealium Matches:</span>
                                <span class="stat-value">${analysis.tealium_matches.length}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Optimizations:</span>
                                <span class="stat-value">${analysis.optimization_suggestions.length}</span>
                            </div>
                        </div>
                    </div>
                    
                    ${analysis.tealium_matches.length > 0 ? `
                    <div class="section tealium-matches">
                        <h4><i class="fas fa-bullseye"></i> Tealium Matches Found</h4>
                        ${analysis.tealium_matches.map(match => `
                            <div class="match-item priority-${match.priority.toLowerCase()}">
                                <div class="match-header">
                                    <span class="match-priority">${match.priority}</span>
                                    <span class="match-description">${match.tealium_description}</span>
                                </div>
                                <div class="match-details">
                                    <div class="selector-comparison">
                                        <div class="selector-item">
                                            <label>Recorded:</label>
                                            <code class="recorded-selector">${match.recorded_selector}</code>
                                        </div>
                                        <div class="selector-item">
                                            <label>Tealium:</label>
                                            <code class="tealium-selector">${match.tealium_selector}</code>
                                        </div>
                                    </div>
                                    <div class="match-reason">${match.match_reason}</div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                    ` : ''}
                    
                    <div class="section selector-details">
                        <h4><i class="fas fa-list"></i> Detailed Selector Analysis</h4>
                        ${analysis.selector_analysis.map(item => `
                            <div class="selector-item-detail">
                                <div class="selector-header">
                                    <span class="action-index">#${item.action_index + 1}</span>
                                    <span class="action-description">${item.description}</span>
                                    <span class="selector-type type-${item.selector_type}">${item.selector_type}</span>
                                    <span class="specificity-score">Score: ${item.specificity_score}</span>
                                </div>
                                <div class="selector-content">
                                    <code class="current-selector">${item.original_selector}</code>
                                    ${item.improvements.length > 0 ? `
                                    <div class="improvements">
                                        <h5>Optimization Suggestions:</h5>
                                        ${item.improvements.map(imp => `
                                            <div class="improvement-item priority-${imp.priority.toLowerCase()}">
                                                <div class="improvement-type">${imp.type.replace('_', ' ')}</div>
                                                <div class="improvement-reason">${imp.reason}</div>
                                                ${imp.suggested ? `<code class="suggested-selector">${imp.suggested}</code>` : ''}
                                                ${imp.recommendation ? `<div class="recommendation">${imp.recommendation}</div>` : ''}
                                            </div>
                                        `).join('')}
                                    </div>
                                    ` : ''}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn-secondary" onclick="this.closest('.selector-analysis-modal').remove()">Close</button>
                </div>
            </div>
        `;
        
        // Add styles for selector analysis modal
        if (!document.getElementById('selector-analysis-styles')) {
            const styles = document.createElement('style');
            styles.id = 'selector-analysis-styles';
            styles.textContent = `
                .selector-modal {
                    max-width: 1000px;
                    max-height: 90vh;
                }
                .summary-stats {
                    display: flex;
                    gap: 2rem;
                    margin-bottom: 1.5rem;
                }
                .stat-item {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    padding: 1rem;
                    background: #f8f9fa;
                    border-radius: 8px;
                }
                .stat-label {
                    font-size: 0.875rem;
                    color: #666;
                    margin-bottom: 0.5rem;
                }
                .stat-value {
                    font-size: 1.5rem;
                    font-weight: 600;
                    color: #4f79ff;
                }
                .match-item {
                    margin-bottom: 1rem;
                    padding: 1rem;
                    border-radius: 8px;
                    border-left: 4px solid;
                }
                .priority-critical { border-left-color: #dc3545; background: #fdf2f2; }
                .priority-high { border-left-color: #fd7e14; background: #fef7f0; }
                .priority-medium { border-left-color: #ffc107; background: #fffdf0; }
                .priority-low { border-left-color: #28a745; background: #f0f8f2; }
                .match-header {
                    display: flex;
                    align-items: center;
                    gap: 1rem;
                    margin-bottom: 0.5rem;
                }
                .match-priority {
                    padding: 0.25rem 0.5rem;
                    border-radius: 4px;
                    font-size: 0.75rem;
                    font-weight: 600;
                    text-transform: uppercase;
                }
                .priority-critical .match-priority { background: #dc3545; color: white; }
                .priority-high .match-priority { background: #fd7e14; color: white; }
                .priority-medium .match-priority { background: #ffc107; color: black; }
                .priority-low .match-priority { background: #28a745; color: white; }
                .selector-comparison {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 1rem;
                    margin: 0.5rem 0;
                }
                .selector-item label {
                    display: block;
                    font-size: 0.75rem;
                    color: #666;
                    margin-bottom: 0.25rem;
                }
                .recorded-selector {
                    background: #e3f2fd;
                    color: #1976d2;
                }
                .tealium-selector {
                    background: #f3e5f5;
                    color: #7b1fa2;
                }
                .suggested-selector {
                    background: #e8f5e8;
                    color: #2e7d32;
                    margin-top: 0.5rem;
                    display: block;
                }
                .selector-item-detail {
                    margin-bottom: 1.5rem;
                    padding: 1rem;
                    border: 1px solid #e1e5e9;
                    border-radius: 8px;
                }
                .selector-header {
                    display: flex;
                    align-items: center;
                    gap: 1rem;
                    margin-bottom: 0.5rem;
                }
                .action-index {
                    background: #4f79ff;
                    color: white;
                    padding: 0.25rem 0.5rem;
                    border-radius: 4px;
                    font-size: 0.75rem;
                    font-weight: 600;
                }
                .selector-type {
                    padding: 0.25rem 0.5rem;
                    border-radius: 4px;
                    font-size: 0.75rem;
                    text-transform: uppercase;
                    background: #f8f9fa;
                    color: #666;
                }
                .specificity-score {
                    font-size: 0.875rem;
                    color: #666;
                }
                .current-selector {
                    display: block;
                    margin: 0.5rem 0;
                    padding: 0.5rem;
                    background: #f8f9fa;
                    border-radius: 4px;
                    font-family: 'JetBrains Mono', monospace;
                }
                .improvements {
                    margin-top: 1rem;
                    padding-top: 1rem;
                    border-top: 1px solid #e1e5e9;
                }
                .improvements h5 {
                    margin: 0 0 0.5rem 0;
                    font-size: 0.875rem;
                    color: #666;
                }
                .improvement-item {
                    margin-bottom: 0.5rem;
                    padding: 0.75rem;
                    border-radius: 6px;
                    border-left: 3px solid;
                }
                .improvement-type {
                    font-weight: 600;
                    text-transform: capitalize;
                    margin-bottom: 0.25rem;
                }
                .improvement-reason {
                    font-size: 0.875rem;
                    color: #666;
                    margin-bottom: 0.5rem;
                }
                .recommendation {
                    font-size: 0.875rem;
                    font-style: italic;
                    color: #666;
                    margin-top: 0.5rem;
                }
            `;
            document.head.appendChild(styles);
        }
        
        document.body.appendChild(modal);
    }

    // Progress Management Methods
    showMacroProgress(macroId, show, progressText = 'Starting analysis...') {
        const progressEl = document.getElementById(`progress-${macroId}`);
        const progressFill = document.getElementById(`progress-fill-${macroId}`);
        const progressTextEl = document.getElementById(`progress-text-${macroId}`);
        
        if (!progressEl) return;
        
        if (show) {
            progressEl.classList.add('active');
            if (progressTextEl) progressTextEl.textContent = progressText;
            if (progressFill) progressFill.style.width = '0%';
        } else {
            progressEl.classList.remove('active');
        }
    }
    
    updateMacroProgress(macroId, percentage, text) {
        const progressFill = document.getElementById(`progress-fill-${macroId}`);
        const progressTextEl = document.getElementById(`progress-text-${macroId}`);
        
        if (progressFill) {
            progressFill.style.width = `${Math.min(100, Math.max(0, percentage))}%`;
        }
        if (progressTextEl && text) {
            progressTextEl.textContent = text;
        }
    }

    // Utility Methods
    showNotification(message, type = 'success', duration = 3000) {
        const notification = this.notification;
        const icon = notification.querySelector('.notification-icon i');
        const content = notification.querySelector('.notification-content');
        
        // Set icon based on type
        const iconMap = {
            'success': 'fa-check-circle',
            'error': 'fa-exclamation-circle',
            'warning': 'fa-exclamation-triangle',
            'info': 'fa-info-circle'
        };
        
        icon.className = `fas ${iconMap[type] || iconMap['info']}`;
        
        // Handle multi-line messages by preserving line breaks
        if (message.includes('\n')) {
            content.innerHTML = message.replace(/\n/g, '<br>');
        } else {
            content.textContent = message;
        }
        
        // Show notification
        notification.className = `notification ${type} show`;
        
        // Hide after duration
        setTimeout(() => {
            notification.className = 'notification';
        }, duration);
    }
}

// Initialize the recorder when the page loads
let recorder;
document.addEventListener('DOMContentLoaded', () => {
    recorder = new MacroRecorder();
});