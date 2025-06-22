        // Professional Dashboard Implementation - FastAPI Only
        const API_BASE = 'http://localhost:8001/api/v1';
        
        // State
        let currentTab = 'overview';
        let selectedContainer = null;
        
        // Simple cache for API responses
        const apiCache = new Map();
        const CACHE_TTL = 30000; // 30 seconds
        
        // Enhanced fetch with caching
        async function fetchDataCached(url, skipCache = false) {
            const cacheKey = url;
            const now = Date.now();
            
            // Check cache first
            if (!skipCache && apiCache.has(cacheKey)) {
                const cached = apiCache.get(cacheKey);
                if (now - cached.timestamp < CACHE_TTL) {
                    return cached.data;
                }
                apiCache.delete(cacheKey);
            }
            
            try {
                const response = await fetch(url);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                const data = await response.json();
                
                // Cache the response
                apiCache.set(cacheKey, {
                    data: data,
                    timestamp: now
                });
                
                return data;
            } catch (error) {
                console.error(`Failed to fetch ${url}:`, error);
                return null;
            }
        }
        
        // Initialize
        console.log('JavaScript file loaded');
        
        // Global ESC key handler
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && window.currentModal) {
                if (window.currentModal.querySelector('#compose-to')) {
                    // It's a compose modal
                    closeComposeModal();
                } else {
                    // It's a message viewer modal
                    closeMessageViewer();
                }
            }
        });
        
        document.addEventListener('DOMContentLoaded', () => {
            console.log('DOM loaded, starting initialization');
            try {
                setupNavigation();
                loadOverview();
                console.log('Initialization complete');
            } catch (error) {
                console.error('Initialization error:', error);
            }
        });
        
        // Navigation
        function setupNavigation() {
            console.log('setupNavigation called');
            const navItems = document.querySelectorAll('.nav-item');
            console.log('Found nav items:', navItems.length);
            
            navItems.forEach((item, index) => {
                console.log(`Nav item ${index}: ${item.textContent} (data-tab: ${item.dataset.tab})`);
                item.addEventListener('click', (e) => {
                    console.log('Nav item clicked:', e.target.textContent, e.target.dataset.tab);
                    const tab = e.target.dataset.tab;
                    switchTab(tab);
                });
            });
        }
        
        function switchTab(tab) {
            console.log('switchTab called with:', tab);
            
            document.querySelectorAll('.nav-item').forEach(item => {
                item.classList.toggle('active', item.dataset.tab === tab);
            });
            
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.toggle('active', content.id === tab);
            });
            
            currentTab = tab;
            console.log('currentTab set to:', currentTab);
            
            // Load tab data
            switch(tab) {
                case 'overview': 
                    console.log('Loading overview');
                    loadOverview(); 
                    break;
                case 'mailbox': 
                    console.log('Loading mailbox');
                    refreshMessages(); 
                    break;
                case 'cosmos': refreshContainers(); break;
                case 'graph': loadGraph(); break;
                case 'agents': refreshAgents(); break;
                case 'manager': loadManagerDashboard(); break;
                case 'workspace': loadWorkspace(); break;
                case 'research': loadResearch(); break;
            }
        }
        
        // API Helper
        async function fetchData(url) {
            try {
                const response = await fetch(url);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                return await response.json();
            } catch (error) {
                console.error(`Failed to fetch ${url}:`, error);
                return null;
            }
        }
        
        // Overview
        async function loadOverview() {
            // Get containers from Cosmos endpoint
            const containers = await fetchDataCached(`${API_BASE}/cosmos/containers`);
            if (containers && containers.containers) {
                document.getElementById('stat-containers').textContent = containers.containers.length;
                
                // Calculate total documents
                let totalDocs = 0;
                containers.containers.forEach(c => {
                    if (c.count > 0) totalDocs += c.count;
                });
                document.getElementById('stat-documents').textContent = totalDocs > 0 ? totalDocs.toLocaleString() : 'N/A';
            }
            
            // Get system monitoring data
            const monitoring = await fetchDataCached(`${API_BASE}/monitoring/system`);
            if (monitoring && monitoring.metrics) {
                document.getElementById('stat-health').textContent = 'Online';
                document.getElementById('stat-health').style.color = 'var(--success-green)';
                
                // Display formatted metrics
                const metrics = {
                    cpu_percent: monitoring.metrics.cpu_percent?.toFixed(1) + '%',
                    memory_percent: monitoring.metrics.memory_percent?.toFixed(1) + '%',
                    disk_percent: monitoring.metrics.disk_percent?.toFixed(1) + '%',
                    load_average: monitoring.metrics.load_average?.[0]?.toFixed(2) || 'N/A',
                    process_count: monitoring.metrics.process_count || 'N/A'
                };
                document.getElementById('system-info').textContent = JSON.stringify(metrics, null, 2);
            }
            
            // Get agents data
            let agentCount = 0;
            const agents = await fetchDataCached(`${API_BASE}/agents/`);
            if (agents && Array.isArray(agents)) {
                agentCount = agents.length;
            } else {
                // Try legacy endpoint
                const agentsLegacy = await fetchDataCached(`${API_BASE}/agents-legacy`);
                if (agentsLegacy && Array.isArray(agentsLegacy)) {
                    agentCount = agentsLegacy.length;
                }
            }
            document.getElementById('stat-agents').textContent = agentCount;
            
            // Load recent activity
            loadRecentActivity();
        }
        
        async function loadRecentActivity() {
            const activityEl = document.getElementById('recent-activity');
            
            // Get recent messages as activity using new API format
            const messages = await fetchDataCached(`${API_BASE}/messages/?limit=10`);
            if (messages && Array.isArray(messages)) {
                activityEl.innerHTML = messages.map(msg => `
                    <div class="list-item" style="padding: 12px;">
                        <div style="font-weight: 500;">${msg.subject || msg.type || 'System Message'}</div>
                        <div style="font-size: 12px; color: var(--text-secondary);">
                            From: ${msg.from || 'System'} | ${new Date(msg.timestamp).toLocaleString()}
                        </div>
                    </div>
                `).join('');
            } else {
                activityEl.innerHTML = '<div class="empty-state">No recent activity</div>';
            }
        }
        
        // Containers
        async function refreshContainers() {
            const listEl = document.getElementById('container-list');
            listEl.innerHTML = '<div class="loading">Loading...</div>';
            
            // Use FastAPI Cosmos endpoint
            const data = await fetchData(`${API_BASE}/cosmos/containers`);
            
            if (data && data.containers) {
                listEl.innerHTML = data.containers.map(container => `
                    <div class="list-item" onclick="selectContainer('${container.id}')">
                        <div style="font-weight: 500">${container.id}</div>
                        <div style="font-size: 12px; color: var(--text-secondary)">
                            Documents: ${container.count !== -1 ? container.count : 'N/A'} | Partition: ${container.partitionKey || 'N/A'}
                        </div>
                    </div>
                `).join('');
            } else {
                listEl.innerHTML = '<div class="empty-state">No containers found</div>';
            }
        }
        
        async function selectContainer(containerId) {
            selectedContainer = containerId;
            
            // Update UI
            document.querySelectorAll('#container-list .list-item').forEach(item => {
                item.classList.toggle('active', item.textContent.includes(containerId));
            });
            
            // Load documents
            const listEl = document.getElementById('document-list');
            listEl.innerHTML = '<div class="loading">Loading documents...</div>';
            
            // Use FastAPI endpoint
            const data = await fetchData(`${API_BASE}/cosmos/containers/${containerId}/documents?limit=20`);
            
            if (data && data.documents) {
                listEl.innerHTML = data.documents.map(doc => `
                    <div class="list-item">
                        <div class="code-block">${JSON.stringify(doc, null, 2)}</div>
                    </div>
                `).join('');
            } else {
                listEl.innerHTML = '<div class="empty-state">No documents found</div>';
            }
        }
        
        // Agents
        let selectedAgent = null;
        
        async function refreshAgents() {
            const listEl = document.getElementById('agent-list');
            listEl.innerHTML = '<div class="loading">Loading...</div>';
            
            // Try multiple endpoints
            let agents = await fetchData(`${API_BASE}/agents`);
            if (!agents || !Array.isArray(agents)) {
                agents = await fetchData(`${API_BASE}/agents-legacy`);
            }
            
            // If still no agents, create mock data for demonstration
            if (!agents || !Array.isArray(agents)) {
                agents = [
                    { name: 'HEAD_OF_ENGINEERING', status: 'active', role: 'Engineering Manager' },
                    { name: 'HEAD_OF_RESEARCH', status: 'active', role: 'Research Manager' },
                    { name: 'Data_Analyst', status: 'active', role: 'Data Analysis' },
                    { name: 'Full_Stack_Software_Engineer', status: 'active', role: 'Software Development' },
                    { name: 'Azure_Infrastructure_Agent', status: 'active', role: 'Infrastructure' },
                    { name: 'Research_Advanced_Analyst', status: 'active', role: 'Advanced Research' },
                    { name: 'Research_Quantitative_Analyst', status: 'idle', role: 'Quantitative Analysis' },
                    { name: 'Research_Strategy_Analyst', status: 'idle', role: 'Strategy Research' }
                ];
            }
            
            if (agents && Array.isArray(agents)) {
                listEl.innerHTML = agents.map(agent => `
                    <div class="list-item" onclick="selectAgent('${agent.name}')">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="font-weight: 500">${agent.name || 'Unknown'}</div>
                                <div style="font-size: 12px; color: var(--text-secondary)">
                                    ${agent.role || 'Agent'}
                                </div>
                            </div>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span class="status-dot" style="background: ${agent.status === 'active' ? 'var(--success-green)' : 'var(--text-muted)'}"></span>
                                <span style="font-size: 12px; color: var(--text-secondary)">${agent.status || 'unknown'}</span>
                            </div>
                        </div>
                    </div>
                `).join('');
            } else {
                listEl.innerHTML = '<div class="empty-state">No agents found</div>';
            }
        }
        
        async function selectAgent(agentName) {
            selectedAgent = agentName;
            
            // Update active state
            document.querySelectorAll('#agent-list .list-item').forEach(item => {
                item.classList.toggle('active', item.textContent.includes(agentName));
            });
            
            // Load agent details
            const detailsEl = document.getElementById('agent-details');
            detailsEl.innerHTML = '<div class="loading">Loading agent details...</div>';
            
            // Try to get agent details
            const details = await fetchData(`${API_BASE}/agents/${agentName}`);
            
            if (details) {
                displayAgentDetails(details);
            } else {
                // Show mock details
                detailsEl.innerHTML = `
                    <div style="padding: 20px;">
                        <h3>${agentName}</h3>
                        <div class="stats-grid" style="margin-top: 16px;">
                            <div class="stat-card">
                                <div class="stat-label">Status</div>
                                <div class="stat-value" style="font-size: 16px;">Active</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-label">Tasks Completed</div>
                                <div class="stat-value" style="font-size: 16px;">42</div>
                            </div>
                        </div>
                        
                        <div class="card" style="margin-top: 16px;">
                            <h4>Recent Activity</h4>
                            <div style="font-size: 13px; color: var(--text-secondary); line-height: 1.8;">
                                <div>• Completed dashboard optimization</div>
                                <div>• Updated system documentation</div>
                                <div>• Reviewed pull requests</div>
                            </div>
                        </div>
                        
                        <div class="card" style="margin-top: 16px;">
                            <h4>Agent Shell Files</h4>
                            <div style="font-family: var(--font-mono); font-size: 12px;">
                                <div>📄 memory_context.md</div>
                                <div>📄 journal.md</div>
                                <div>📄 deep_context.md</div>
                                <div>📁 agent_notes/</div>
                            </div>
                        </div>
                    </div>
                `;
            }
        }
        
        function displayAgentDetails(details) {
            const detailsEl = document.getElementById('agent-details');
            detailsEl.innerHTML = `
                <div style="padding: 20px;">
                    <h3>${details.name}</h3>
                    <pre class="code-block">${JSON.stringify(details, null, 2)}</pre>
                </div>
            `;
        }
        
        // Messages
        let allMessages = [];
        let currentFilter = 'all';
        let messagesPagination = {
            offset: 0,
            limit: 50,
            hasMore: true,
            loading: false
        };
        
        async function refreshMessages(reset = true) {
            const listEl = document.getElementById('message-list');
            
            // Prevent multiple simultaneous calls
            if (messagesPagination.loading) {
                console.log('refreshMessages already loading, skipping');
                return;
            }
            
            if (reset) {
                listEl.innerHTML = '<div class="loading">Loading messages...</div>';
                messagesPagination.offset = 0;
                messagesPagination.hasMore = true;
                allMessages = [];
            }
            
            console.log('refreshMessages called, reset:', reset);
            
            if (!messagesPagination.hasMore && !reset) {
                return;
            }
            
            messagesPagination.loading = true;
            
            // Disable refresh button while loading
            const refreshBtn = document.querySelector('button[onclick="refreshMessages()"]');
            if (refreshBtn) {
                refreshBtn.disabled = true;
                refreshBtn.textContent = 'Loading...';
            }
            
            // Get messages for HEAD_OF_ENGINEERING from system_inbox with pagination
            const data = await fetchDataCached(`${API_BASE}/messages/HEAD_OF_ENGINEERING?limit=${messagesPagination.limit}`, true);
            console.log('API response:', data);
            if (data && data.messages && Array.isArray(data.messages)) {
                if (reset) {
                    allMessages = data.messages;
                } else {
                    allMessages = [...allMessages, ...data.messages];
                }
                
                // Check if we got fewer messages than requested (end of data)
                messagesPagination.hasMore = data.messages.length === messagesPagination.limit;
                messagesPagination.offset += data.messages.length;
                
                updateMessageCounts();
                displayFilteredMessages();
                setupInfiniteScroll();
                console.log('Messages loaded successfully:', allMessages.length);
            } else {
                console.log('Primary API failed, trying fallback');
                // Try general messages endpoint as fallback
                const fallbackData = await fetchDataCached(`${API_BASE}/messages/?limit=${messagesPagination.limit}`, true);
                console.log('Fallback API response:', fallbackData);
                if (fallbackData && Array.isArray(fallbackData)) {
                    allMessages = fallbackData;
                    messagesPagination.hasMore = fallbackData.length === messagesPagination.limit;
                    updateMessageCounts();
                    displayFilteredMessages();
                    setupInfiniteScroll();
                    console.log('Fallback messages loaded:', allMessages.length);
                } else {
                    console.log('No messages found from either API');
                    listEl.innerHTML = '<div class="empty-state">No messages found</div>';
                }
            }
            
            messagesPagination.loading = false;
            
            // Re-enable refresh button
            const refreshBtnEnd = document.querySelector('button[onclick="refreshMessages()"]');
            if (refreshBtnEnd) {
                refreshBtnEnd.disabled = false;
                refreshBtnEnd.textContent = 'Refresh';
            }
        }
        
        function setupInfiniteScroll() {
            const listEl = document.getElementById('message-list');
            const listContainer = listEl.parentElement;
            
            // Remove existing scroll listener
            listContainer.removeEventListener('scroll', handleScroll);
            
            // Add scroll listener for infinite scroll
            listContainer.addEventListener('scroll', handleScroll);
        }
        
        function handleScroll(event) {
            const container = event.target;
            const scrollTop = container.scrollTop;
            const scrollHeight = container.scrollHeight;
            const clientHeight = container.clientHeight;
            
            // Load more when near bottom (within 100px)
            if (scrollTop + clientHeight >= scrollHeight - 100) {
                loadMoreMessages();
            }
        }
        
        async function loadMoreMessages() {
            if (messagesPagination.loading || !messagesPagination.hasMore) {
                return;
            }
            
            // Show loading indicator at bottom
            const listEl = document.getElementById('message-list');
            const loadingEl = document.createElement('div');
            loadingEl.className = 'loading-more';
            loadingEl.style.cssText = 'padding: 20px; text-align: center; color: var(--text-secondary); font-size: 13px;';
            loadingEl.textContent = 'Loading more messages...';
            listEl.appendChild(loadingEl);
            
            await refreshMessages(false);
            
            // Remove loading indicator
            const loadingToRemove = listEl.querySelector('.loading-more');
            if (loadingToRemove) {
                listEl.removeChild(loadingToRemove);
            }
        }
        
        function updateMessageCounts() {
            document.getElementById('count-all').textContent = allMessages.length;
            document.getElementById('count-unread').textContent = allMessages.filter(m => m.status === 'unread').length;
            document.getElementById('count-sent').textContent = allMessages.filter(m => m.status === 'sent').length;
            document.getElementById('count-archived').textContent = allMessages.filter(m => m.status === 'archived').length;
        }
        
        function filterMessagesByFolder(folder) {
            currentFilter = folder;
            
            // Update active folder
            document.querySelectorAll('#mailbox .list-item').forEach(item => {
                item.classList.remove('active');
            });
            event.currentTarget.classList.add('active');
            
            displayFilteredMessages();
        }
        
        function displayFilteredMessages() {
            const listEl = document.getElementById('message-list');
            let filtered = allMessages;
            
            switch(currentFilter) {
                case 'unread':
                    filtered = allMessages.filter(m => m.status === 'unread');
                    break;
                case 'sent':
                    filtered = allMessages.filter(m => m.status === 'sent');
                    break;
                case 'archived':
                    filtered = allMessages.filter(m => m.status === 'archived');
                    break;
                case 'all':
                default:
                    // For 'all' messages, exclude archived ones (show them only in archived folder)
                    filtered = allMessages.filter(m => m.status !== 'archived');
                    break;
            }
            
            if (filtered.length === 0) {
                listEl.innerHTML = '<div class="empty-state">No messages in this folder</div>';
                return;
            }
            
            listEl.innerHTML = filtered.map(msg => `
                <div class="list-item ${msg.status === 'unread' ? 'unread' : ''}" onclick="viewMessage('${msg.id}')">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div>
                            <div style="font-weight: ${msg.status === 'unread' ? '600' : '500'}">${msg.subject || 'No Subject'}</div>
                            <div style="font-size: 12px; color: var(--text-secondary); margin-top: 4px;">
                                From: ${msg.from || 'Unknown'} | ${formatDate(msg.timestamp)}
                            </div>
                            <div style="font-size: 13px; color: var(--text-muted); margin-top: 4px;">
                                ${String(msg.content || '').substring(0, 100)}${String(msg.content || '').length > 100 ? '...' : ''}
                            </div>
                        </div>
                        <div style="font-size: 12px; color: var(--text-muted);">
                            ${formatTime(msg.timestamp)}
                        </div>
                    </div>
                </div>
            `).join('');
        }
        
        async function viewMessage(messageId) {
            // Find the message in our current list
            const message = allMessages.find(m => m.id === messageId);
            if (!message) {
                alert('Message not found');
                return;
            }
            
            // Mark as read if it's unread
            if (message.status === 'unread') {
                await updateMessageStatus(messageId, 'read');
            }
            
            // Create message viewer modal
            const modal = document.createElement('div');
            modal.style.cssText = `
                position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                background: rgba(0,0,0,0.7); z-index: 1000; display: flex; 
                align-items: center; justify-content: center;
            `;
            
            modal.innerHTML = `
                <div style="background: var(--bg-card); border-radius: 8px; width: 700px; max-height: 80vh; 
                            border: 1px solid var(--border-color); box-shadow: var(--shadow-lg); overflow: hidden;">
                    <div style="padding: 20px; border-bottom: 1px solid var(--border-color);">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <div>
                                <h3 style="margin: 0 0 8px 0; color: var(--text-primary);">${message.subject || 'No Subject'}</h3>
                                <div style="font-size: 13px; color: var(--text-secondary);">
                                    From: <strong>${message.from}</strong> | To: <strong>${message.to}</strong>
                                </div>
                                <div style="font-size: 13px; color: var(--text-secondary); margin-top: 4px;">
                                    ${formatDate(message.timestamp)} ${formatTime(message.timestamp)} | Priority: ${message.priority} | Status: ${message.status}
                                </div>
                            </div>
                            <button onclick="closeMessageViewer()" 
                                    style="background: none; border: none; color: var(--text-secondary); 
                                           font-size: 18px; cursor: pointer; padding: 4px;">×</button>
                        </div>
                    </div>
                    <div style="padding: 20px; max-height: 400px; overflow-y: auto;">
                        <div style="white-space: pre-wrap; line-height: 1.6; color: var(--text-primary);">${message.content}</div>
                    </div>
                    <div style="padding: 20px; border-top: 1px solid var(--border-color); display: flex; gap: 12px;">
                        <button onclick="replyToMessage('${messageId}')" 
                                style="padding: 8px 16px; background: var(--accent-blue); color: white; 
                                       border: none; border-radius: 4px; cursor: pointer;">
                            Reply
                        </button>
                        <button onclick="toggleMessageStatus('${messageId}', '${message.status}')" 
                                style="padding: 8px 16px; background: transparent; color: var(--text-secondary); 
                                       border: 1px solid var(--border-color); border-radius: 4px; cursor: pointer;">
                            Mark as ${message.status === 'read' ? 'Unread' : 'Read'}
                        </button>
                        <button onclick="archiveMessage('${messageId}')" 
                                style="padding: 8px 16px; background: transparent; color: var(--text-secondary); 
                                       border: 1px solid var(--border-color); border-radius: 4px; cursor: pointer;">
                            Archive
                        </button>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            window.currentModal = modal;
            
            // Simple click outside to close
            modal.onclick = function(e) {
                if (e.target === modal) {
                    closeMessageViewer();
                }
            };
        }
        
        function closeMessageViewer() {
            if (window.currentModal) {
                document.body.removeChild(window.currentModal);
                window.currentModal = null;
            }
        }
        
        async function updateMessageStatus(messageId, newStatus) {
            try {
                const response = await fetch(`${API_BASE}/messages/${messageId}/status?status=${newStatus}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });
                
                if (response.ok) {
                    // Update local message status
                    const message = allMessages.find(m => m.id === messageId);
                    if (message) {
                        message.status = newStatus;
                        updateMessageCounts();
                        displayFilteredMessages();
                    }
                    return true;
                } else {
                    console.error('Failed to update message status');
                    return false;
                }
            } catch (error) {
                console.error('Error updating message status:', error);
                return false;
            }
        }
        
        async function toggleMessageStatus(messageId, currentStatus) {
            const newStatus = currentStatus === 'read' ? 'unread' : 'read';
            const success = await updateMessageStatus(messageId, newStatus);
            if (success) {
                closeMessageViewer();
                refreshMessages(); // Refresh to show updated status
            }
        }
        
        async function archiveMessage(messageId) {
            const success = await updateMessageStatus(messageId, 'archived');
            if (success) {
                closeMessageViewer();
                refreshMessages(); // Refresh to show updated status
            }
        }
        
        function replyToMessage(messageId) {
            const message = allMessages.find(m => m.id === messageId);
            if (!message) return;
            
            closeMessageViewer();
            // Wait a bit for modal to close then open compose
            setTimeout(() => {
                composeNewMessage().then(() => {
                    // Pre-fill reply fields
                    document.getElementById('compose-to').value = message.from;
                    document.getElementById('compose-subject').value = 'Re: ' + (message.subject || 'No Subject');
                });
            }, 100);
        }
        
        async function composeNewMessage() {
            // Get available agents
            const agents = await fetchDataCached(`${API_BASE}/agents/`);
            if (!agents || !Array.isArray(agents)) {
                alert('Could not load agents list');
                return;
            }
            
            // Create compose modal
            const modal = document.createElement('div');
            modal.style.cssText = `
                position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                background: rgba(0,0,0,0.7); z-index: 1000; display: flex; 
                align-items: center; justify-content: center;
            `;
            
            modal.innerHTML = `
                <div style="background: var(--bg-card); border-radius: 8px; width: 600px; max-height: 80vh; 
                            border: 1px solid var(--border-color); box-shadow: var(--shadow-lg);">
                    <div style="padding: 20px; border-bottom: 1px solid var(--border-color);">
                        <h3 style="margin: 0; color: var(--text-primary);">Compose Message</h3>
                    </div>
                    <div style="padding: 20px;">
                        <div style="margin-bottom: 16px;">
                            <label style="display: block; margin-bottom: 8px; color: var(--text-secondary); font-size: 13px;">To:</label>
                            <select id="compose-to" style="width: 100%; padding: 8px; background: var(--bg-dark); 
                                                          color: var(--text-primary); border: 1px solid var(--border-color); 
                                                          border-radius: 4px;">
                                <option value="">Select recipient...</option>
                                ${agents.map(agent => `<option value="${agent.name}">${agent.name} (${agent.role})</option>`).join('')}
                            </select>
                        </div>
                        <div style="margin-bottom: 16px;">
                            <label style="display: block; margin-bottom: 8px; color: var(--text-secondary); font-size: 13px;">Subject:</label>
                            <input type="text" id="compose-subject" placeholder="Message subject..." 
                                   style="width: 100%; padding: 8px; background: var(--bg-dark); color: var(--text-primary); 
                                          border: 1px solid var(--border-color); border-radius: 4px;">
                        </div>
                        <div style="margin-bottom: 16px;">
                            <label style="display: block; margin-bottom: 8px; color: var(--text-secondary); font-size: 13px;">Priority:</label>
                            <select id="compose-priority" style="width: 100%; padding: 8px; background: var(--bg-dark); 
                                                               color: var(--text-primary); border: 1px solid var(--border-color); 
                                                               border-radius: 4px;">
                                <option value="NORMAL">Normal</option>
                                <option value="HIGH">High</option>
                                <option value="LOW">Low</option>
                            </select>
                        </div>
                        <div style="margin-bottom: 20px;">
                            <label style="display: block; margin-bottom: 8px; color: var(--text-secondary); font-size: 13px;">Message:</label>
                            <textarea id="compose-content" rows="8" placeholder="Type your message..." 
                                      style="width: 100%; padding: 12px; background: var(--bg-dark); color: var(--text-primary); 
                                             border: 1px solid var(--border-color); border-radius: 4px; resize: vertical; 
                                             font-family: var(--font-main);"></textarea>
                        </div>
                        <div style="display: flex; gap: 12px; justify-content: flex-end;">
                            <button onclick="closeComposeModal()" 
                                    style="padding: 8px 16px; background: transparent; color: var(--text-secondary); 
                                           border: 1px solid var(--border-color); border-radius: 4px; cursor: pointer;">
                                Cancel
                            </button>
                            <button onclick="sendComposedMessage()" 
                                    style="padding: 8px 16px; background: var(--accent-blue); color: white; 
                                           border: none; border-radius: 4px; cursor: pointer;">
                                Send Message
                            </button>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            document.getElementById('compose-to').focus();
            
            // Store modal reference
            window.currentModal = modal;
            
            // Simple click outside to close
            modal.onclick = function(e) {
                if (e.target === modal) {
                    closeComposeModal();
                }
            };
        }
        
        function closeComposeModal() {
            if (window.currentModal) {
                document.body.removeChild(window.currentModal);
                window.currentModal = null;
            }
        }
        
        async function sendComposedMessage() {
            const to = document.getElementById('compose-to').value;
            const subject = document.getElementById('compose-subject').value;
            const priority = document.getElementById('compose-priority').value;
            const content = document.getElementById('compose-content').value;
            
            if (!to) {
                alert('Please select a recipient');
                return;
            }
            
            if (!content.trim()) {
                alert('Please enter a message');
                return;
            }
            
            try {
                const response = await fetch(`${API_BASE}/messages/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        from_agent: 'USER_DASHBOARD',
                        to: to,
                        content: content.trim(),
                        priority: priority,
                        message_type: 'MESSAGE',
                        subject: subject || undefined
                    })
                });
                
                if (response.ok) {
                    closeComposeModal();
                    // Refresh messages to show sent message
                    refreshMessages();
                    alert('Message sent successfully!');
                } else {
                    const error = await response.json();
                    alert(`Failed to send message: ${error.detail || 'Unknown error'}`);
                }
            } catch (error) {
                alert(`Error sending message: ${error.message}`);
            }
        }
        
        function formatDate(timestamp) {
            if (!timestamp) return 'Unknown';
            const date = new Date(timestamp);
            return date.toLocaleDateString();
        }
        
        function formatTime(timestamp) {
            if (!timestamp) return '';
            const date = new Date(timestamp);
            const now = new Date();
            const diff = now - date;
            
            if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
            if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
            return date.toLocaleDateString();
        }
        
        // Graph
        async function loadGraph() {
            const container = document.getElementById('graph-container');
            container.innerHTML = '<div class="loading">Loading graph data...</div>';
            
            const data = await fetchData(`${API_BASE}/graph/data`);
            if (data) {
                // Initialize Cytoscape
                // Implementation depends on actual data structure
                container.innerHTML = '<div class="empty-state">Graph visualization coming soon</div>';
            } else {
                container.innerHTML = '<div class="empty-state">No graph data available</div>';
            }
        }
        
        // Additional tab functions
        async function loadManagerDashboard() {
            const content = document.getElementById('manager-content');
            content.innerHTML = '<div class="loading">Loading manager dashboard...</div>';
            
            // For now, show placeholder
            setTimeout(() => {
                content.innerHTML = `
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-label">Team Members</div>
                            <div class="stat-value">8</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Active Tasks</div>
                            <div class="stat-value">12</div>
                        </div>
                    </div>
                `;
            }, 500);
        }
        
        async function loadWorkspace() {
            const content = document.getElementById('workspace-content');
            content.innerHTML = '<div class="loading">Loading workspace...</div>';
            
            setTimeout(() => {
                content.innerHTML = `
                    <div style="font-family: var(--font-mono); padding: 20px;">
                        <div>📁 Research & Analytics Services</div>
                        <div style="margin-left: 20px;">📁 Agent_Shells</div>
                        <div style="margin-left: 20px;">📁 Engineering Workspace</div>
                        <div style="margin-left: 20px;">📁 System Enforcement Workspace</div>
                    </div>
                `;
            }, 500);
        }
        
        async function loadResearch() {
            const content = document.getElementById('research-content');
            content.innerHTML = '<div class="loading">Loading research visualization...</div>';
            
            setTimeout(() => {
                content.innerHTML = '<div class="empty-state">Research visualization coming soon</div>';
            }, 500);
        }
        
        // Export functions for onclick
        window.loadOverview = loadOverview;
        window.refreshContainers = refreshContainers;
        window.selectContainer = selectContainer;
        window.refreshAgents = refreshAgents;
        window.selectAgent = selectAgent;
        window.refreshMessages = refreshMessages;
        window.filterMessagesByFolder = filterMessagesByFolder;
        window.viewMessage = viewMessage;
        window.composeNewMessage = composeNewMessage;
        window.loadGraph = loadGraph;
        window.closeComposeModal = closeComposeModal;
        window.sendComposedMessage = sendComposedMessage;
        window.closeMessageViewer = closeMessageViewer;
        window.updateMessageStatus = updateMessageStatus;
        window.toggleMessageStatus = toggleMessageStatus;
        window.archiveMessage = archiveMessage;
        window.replyToMessage = replyToMessage;
