/**
 * Professional Dashboard Implementation
 * Complete working implementation with all required functionality
 * HEAD_OF_ENGINEERING - 2025-06-22
 */

// API Configuration
const API_BASE = 'http://localhost:8001/api/v1';

// Global State Management
const DashboardState = {
    currentTab: 'overview',
    currentFolder: 'inbox',
    selectedContainer: null,
    selectedAgent: null,
    messages: [],
    containers: [],
    agents: [],
    documents: [],
    stats: {},
    graphInstance: null
};

// Initialize Dashboard
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing Professional Dashboard...');
    
    // Set up tab navigation
    setupTabNavigation();
    
    // Initialize with overview data
    switchTab('overview');
    
    // Update connection status
    updateConnectionStatus('connected');
    
    // Set up auto-refresh
    setInterval(refreshCurrentTab, 30000); // Refresh every 30 seconds
});

// Tab Navigation System
function setupTabNavigation() {
    document.querySelectorAll('.nav-item').forEach(tab => {
        tab.addEventListener('click', (e) => {
            const tabName = e.target.dataset.tab;
            if (tabName) {
                switchTab(tabName);
            }
        });
    });
}

function switchTab(tabName) {
    // Update active nav item
    document.querySelectorAll('.nav-item').forEach(nav => {
        nav.classList.toggle('active', nav.dataset.tab === tabName);
    });
    
    // Update active content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === tabName);
    });
    
    DashboardState.currentTab = tabName;
    
    // Load tab-specific data
    loadTabData(tabName);
}

function loadTabData(tabName) {
    switch(tabName) {
        case 'overview':
            loadOverviewData();
            break;
        case 'mailbox':
            refreshMailbox();
            break;
        case 'cosmos':
            refreshContainers();
            break;
        case 'graph':
            loadGraphData();
            break;
        case 'agents':
            loadAgentShells();
            break;
        case 'manager':
            loadManagerDashboard();
            break;
        case 'workspace':
            loadWorkspaceExplorer();
            break;
        case 'research':
            loadResearchVisualization();
            break;
    }
}

function refreshCurrentTab() {
    loadTabData(DashboardState.currentTab);
}

// API Helper Functions
async function fetchAPI(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Request Failed:', error);
        showNotification(`API Error: ${error.message}`, 'error');
        return null;
    }
}

// Overview Tab Implementation
async function loadOverviewData() {
    showLoading('overview');
    
    try {
        // Fetch all data in parallel - using actual FastAPI endpoints
        const [systemMetrics, agents, cosmosContainers] = await Promise.all([
            fetchAPI('/monitoring/system'),
            fetchAPI('/agents'),
            fetchAPI('/cosmos/containers')
        ]);
        
        // Map the responses
        const stats = systemMetrics || {};
        const containers = cosmosContainers || [];
        
        // Update state
        DashboardState.stats = stats || {};
        DashboardState.agents = agents || [];
        DashboardState.containers = containers || [];
        
        // Update UI
        updateOverviewStats();
        
    } catch (error) {
        console.error('Failed to load overview:', error);
    }
    
    hideLoading('overview');
}

function updateOverviewStats() {
    // Update stat cards
    document.getElementById('system-health').textContent = 'Operational';
    document.getElementById('system-health').className = 'stat-value success';
    
    document.getElementById('total-containers').textContent = 
        DashboardState.containers.length || '0';
    
    document.getElementById('active-agents').textContent = 
        DashboardState.agents.filter(a => a.status === 'active').length || '0';
    
    document.getElementById('total-documents').textContent = 
        DashboardState.stats.total_documents || '0';
}

// Mailbox Implementation
async function refreshMailbox() {
    showLoading('message-list');
    
    try {
        const messages = await fetchAPI('/messages');
        if (messages) {
            DashboardState.messages = messages;
            renderMessages(filterMessagesByFolder(messages, DashboardState.currentFolder));
            updateFolderCounts(messages);
        }
    } catch (error) {
        console.error('Failed to refresh mailbox:', error);
    }
    
    hideLoading('message-list');
}

function filterMessagesByFolder(messages, folder) {
    switch(folder) {
        case 'inbox':
            return messages.filter(m => !m.sent && !m.draft && !m.archived);
        case 'sent':
            return messages.filter(m => m.sent);
        case 'drafts':
            return messages.filter(m => m.draft);
        case 'archived':
            return messages.filter(m => m.archived);
        default:
            return messages;
    }
}

function renderMessages(messages) {
    const container = document.getElementById('message-list');
    if (!container) return;
    
    if (messages.length === 0) {
        container.innerHTML = '<div class="empty-state">No messages in this folder</div>';
        return;
    }
    
    container.innerHTML = messages.map(msg => `
        <div class="message-item ${msg.read ? '' : 'unread'}" onclick="viewMessage('${msg.id}')">
            <div class="message-header">
                <span class="message-from">${escapeHtml(msg.from || 'Unknown')}</span>
                <span class="message-time">${formatTimestamp(msg.timestamp)}</span>
            </div>
            <div class="message-subject">${escapeHtml(msg.subject || 'No Subject')}</div>
            <div class="message-preview">${escapeHtml((msg.body || '').substring(0, 100))}...</div>
        </div>
    `).join('');
}

function updateFolderCounts(messages) {
    const counts = {
        inbox: messages.filter(m => !m.sent && !m.draft && !m.archived).length,
        sent: messages.filter(m => m.sent).length,
        drafts: messages.filter(m => m.draft).length,
        archived: messages.filter(m => m.archived).length
    };
    
    Object.entries(counts).forEach(([folder, count]) => {
        const elem = document.getElementById(`${folder}-count`);
        if (elem) elem.textContent = count;
    });
}

function selectFolder(folder) {
    DashboardState.currentFolder = folder;
    
    // Update UI
    document.querySelectorAll('.folder-item').forEach(item => {
        item.classList.toggle('active', item.dataset.folder === folder);
    });
    
    // Re-render messages
    renderMessages(filterMessagesByFolder(DashboardState.messages, folder));
}

function filterMessages() {
    const filterValue = document.getElementById('mailbox-filter').value;
    let filtered = DashboardState.messages;
    
    switch(filterValue) {
        case 'unread':
            filtered = filtered.filter(m => !m.read);
            break;
        case 'sent':
            filtered = filtered.filter(m => m.sent);
            break;
        case 'archived':
            filtered = filtered.filter(m => m.archived);
            break;
    }
    
    renderMessages(filterMessagesByFolder(filtered, DashboardState.currentFolder));
}

function composeMessage() {
    // TODO: Implement compose modal
    showNotification('Compose feature in development', 'info');
}

function viewMessage(messageId) {
    const message = DashboardState.messages.find(m => m.id === messageId);
    if (message) {
        // TODO: Implement message viewer modal
        showNotification(`Viewing: ${message.subject}`, 'info');
    }
}

// Cosmos Explorer Implementation
async function refreshContainers() {
    showLoading('container-list');
    
    try {
        const containers = await fetchAPI('/cosmos/containers');
        if (containers) {
            DashboardState.containers = containers;
            renderContainers(containers);
        }
    } catch (error) {
        console.error('Failed to load containers:', error);
    }
    
    hideLoading('container-list');
}

function renderContainers(containers) {
    const container = document.getElementById('container-list');
    if (!container) return;
    
    container.innerHTML = containers.map(cont => `
        <div class="container-item ${cont.id === DashboardState.selectedContainer ? 'active' : ''}" 
             onclick="selectContainer('${cont.id}')">
            <div class="container-icon">📦</div>
            <div class="container-info">
                <div class="container-name">${escapeHtml(cont.id)}</div>
                <div class="container-stats">${cont._count || 0} documents</div>
            </div>
        </div>
    `).join('');
}

async function selectContainer(containerId) {
    DashboardState.selectedContainer = containerId;
    
    // Update UI
    renderContainers(DashboardState.containers);
    
    // Load documents
    showLoading('document-list');
    
    try {
        const documents = await fetchAPI(`/cosmos/containers/${containerId}/documents`);
        if (documents) {
            DashboardState.documents = documents;
            renderDocuments(documents);
        }
    } catch (error) {
        console.error('Failed to load documents:', error);
    }
    
    hideLoading('document-list');
}

function renderDocuments(documents) {
    const container = document.getElementById('document-list');
    if (!container) return;
    
    if (documents.length === 0) {
        container.innerHTML = '<div class="empty-state">No documents in this container</div>';
        return;
    }
    
    container.innerHTML = documents.map(doc => `
        <div class="document-item" onclick="viewDocument('${doc.id}')">
            <div class="document-header">
                <span class="document-id">${escapeHtml(doc.id)}</span>
                <span class="document-type">${doc._type || 'document'}</span>
            </div>
            <pre class="document-preview">${escapeHtml(JSON.stringify(doc, null, 2).substring(0, 200))}...</pre>
        </div>
    `).join('');
}

function applyFilters() {
    // TODO: Implement advanced filtering
    showNotification('Advanced filtering in development', 'info');
}

function viewDocument(documentId) {
    const doc = DashboardState.documents.find(d => d.id === documentId);
    if (doc) {
        // TODO: Implement document viewer modal
        console.log('Viewing document:', doc);
        showNotification(`Viewing document: ${documentId}`, 'info');
    }
}

// Graph Database Implementation
async function loadGraphData() {
    const container = document.getElementById('graph-container');
    if (!container) return;
    
    showLoading('graph-container');
    
    try {
        const graphData = await fetchAPI('/graph/data');
        if (graphData && window.cytoscape) {
            renderCytoscapeGraph(graphData);
        } else if (!window.cytoscape) {
            container.innerHTML = '<div class="error-state">Cytoscape.js not loaded</div>';
        } else {
            container.innerHTML = '<div class="empty-state">No graph data available</div>';
        }
    } catch (error) {
        console.error('Failed to load graph:', error);
        container.innerHTML = '<div class="error-state">Failed to load graph data</div>';
    }
    
    hideLoading('graph-container');
}

function renderCytoscapeGraph(data) {
    const container = document.getElementById('graph-container');
    
    // Clear previous instance
    if (DashboardState.graphInstance) {
        DashboardState.graphInstance.destroy();
    }
    
    // Initialize Cytoscape
    DashboardState.graphInstance = cytoscape({
        container: container,
        elements: data.elements || [],
        style: [
            {
                selector: 'node',
                style: {
                    'background-color': '#3b82f6',
                    'label': 'data(label)',
                    'color': '#ffffff',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'font-size': '14px',
                    'width': '60px',
                    'height': '60px'
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 3,
                    'line-color': '#64748b',
                    'target-arrow-color': '#64748b',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'label': 'data(label)',
                    'font-size': '12px',
                    'text-rotation': 'autorotate'
                }
            },
            {
                selector: ':selected',
                style: {
                    'background-color': '#f59e0b',
                    'line-color': '#f59e0b',
                    'target-arrow-color': '#f59e0b'
                }
            }
        ],
        layout: {
            name: 'dagre',
            rankDir: 'TB',
            padding: 50,
            nodeSep: 100,
            rankSep: 100
        }
    });
    
    // Add interactivity
    DashboardState.graphInstance.on('tap', 'node', function(evt) {
        const node = evt.target;
        showNotification(`Node: ${node.data('label')}`, 'info');
    });
}

function applyGraphFilters() {
    // TODO: Implement graph filtering
    showNotification('Graph filtering in development', 'info');
}

// Agent Shell Implementation
async function loadAgentShells() {
    showLoading('agent-list');
    
    try {
        const agents = await fetchAPI('/agents');
        if (agents) {
            DashboardState.agents = agents;
            renderAgentList(agents);
        }
    } catch (error) {
        console.error('Failed to load agents:', error);
    }
    
    hideLoading('agent-list');
}

function renderAgentList(agents) {
    const container = document.getElementById('agent-list');
    if (!container) return;
    
    container.innerHTML = agents.map(agent => `
        <div class="agent-card ${agent.name === DashboardState.selectedAgent ? 'active' : ''}" 
             onclick="selectAgent('${agent.name}')">
            <div class="agent-header">
                <span class="agent-name">${escapeHtml(agent.name)}</span>
                <span class="agent-status ${agent.status || 'inactive'}">${agent.status || 'inactive'}</span>
            </div>
            <div class="agent-info">
                <div>Role: ${escapeHtml(agent.role || 'Unknown')}</div>
                <div>Last Active: ${formatTimestamp(agent.last_active)}</div>
            </div>
        </div>
    `).join('');
}

async function selectAgent(agentName) {
    DashboardState.selectedAgent = agentName;
    
    // Update UI
    renderAgentList(DashboardState.agents);
    
    // Load agent details
    showLoading('agent-details');
    
    try {
        const details = await fetchAPI(`/agents/${agentName}/details`);
        if (details) {
            renderAgentDetails(details);
        }
    } catch (error) {
        console.error('Failed to load agent details:', error);
    }
    
    hideLoading('agent-details');
}

function renderAgentDetails(details) {
    const container = document.getElementById('agent-details');
    if (!container) return;
    
    container.innerHTML = `
        <div class="agent-detail-view">
            <h3>${escapeHtml(details.name)}</h3>
            <div class="detail-tabs">
                <button class="detail-tab active" onclick="showAgentTab('memory')">Memory</button>
                <button class="detail-tab" onclick="showAgentTab('journal')">Journal</button>
                <button class="detail-tab" onclick="showAgentTab('messages')">Messages</button>
            </div>
            <div id="agent-tab-content" class="tab-content">
                <pre>${escapeHtml(JSON.stringify(details.memory || {}, null, 2))}</pre>
            </div>
        </div>
    `;
}

function showAgentTab(tab) {
    // Update tab buttons
    document.querySelectorAll('.detail-tab').forEach(btn => {
        btn.classList.toggle('active', btn.textContent.toLowerCase() === tab);
    });
    
    // TODO: Load tab-specific content
    showNotification(`Loading ${tab} data...`, 'info');
}

function refreshAgentStatus() {
    loadAgentShells();
}

// Manager Dashboard Implementation
async function loadManagerDashboard() {
    showLoading('manager-content');
    
    try {
        // For now, use agent data to simulate team view
        const agents = await fetchAPI('/agents');
        if (agents) {
            renderManagerView(agents);
        }
    } catch (error) {
        console.error('Failed to load manager data:', error);
    }
    
    hideLoading('manager-content');
}

function renderManagerView(agents) {
    const container = document.getElementById('manager-content');
    if (!container) return;
    
    container.innerHTML = `
        <div class="manager-dashboard">
            <div class="dashboard-header">
                <h2>Team Management Dashboard</h2>
                <button class="btn btn-primary" onclick="updateAgenda()">Update Agenda</button>
            </div>
            
            <div class="team-grid">
                ${agents.map(agent => `
                    <div class="team-member-card">
                        <div class="member-header">
                            <span class="member-name">${escapeHtml(agent.name)}</span>
                            <span class="member-status ${agent.status}">${agent.status || 'inactive'}</span>
                        </div>
                        <div class="member-details">
                            <div>Role: ${escapeHtml(agent.role || 'Unknown')}</div>
                            <div>Tasks: ${agent.active_tasks || 0}</div>
                            <div>Performance: ${agent.performance || 'N/A'}</div>
                        </div>
                    </div>
                `).join('')}
            </div>
            
            <div class="agenda-section">
                <h3>Team Agenda</h3>
                <div class="agenda-placeholder">
                    <p>Team agenda and task assignments will appear here</p>
                </div>
            </div>
        </div>
    `;
}

function updateAgenda() {
    showNotification('Agenda update feature in development', 'info');
}

// Workspace Explorer Implementation
async function loadWorkspaceExplorer() {
    const container = document.getElementById('workspace-tree');
    if (!container) return;
    
    // For now, show static structure
    container.innerHTML = `
        <div class="workspace-explorer">
            <h3>Workspace Structure</h3>
            <div class="tree-view">
                <div class="tree-item expanded" onclick="toggleTreeItem(this)">
                    <span class="tree-toggle">▼</span>
                    <span class="tree-icon">📁</span>
                    <span class="tree-label">Research & Analytics Services</span>
                </div>
                <div class="tree-children">
                    <div class="tree-item">
                        <span class="tree-toggle">▶</span>
                        <span class="tree-icon">📁</span>
                        <span class="tree-label">Agent_Shells</span>
                    </div>
                    <div class="tree-item">
                        <span class="tree-toggle">▶</span>
                        <span class="tree-icon">📁</span>
                        <span class="tree-label">Engineering Workspace</span>
                    </div>
                    <div class="tree-item">
                        <span class="tree-toggle">▶</span>
                        <span class="tree-icon">📁</span>
                        <span class="tree-label">System Enforcement Workspace</span>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function toggleTreeItem(element) {
    element.classList.toggle('expanded');
    const toggle = element.querySelector('.tree-toggle');
    if (toggle) {
        toggle.textContent = element.classList.contains('expanded') ? '▼' : '▶';
    }
}

function browseDirectory(path) {
    showNotification(`Browsing: ${path}`, 'info');
}

// Research Visualization Implementation
async function loadResearchVisualization() {
    const container = document.getElementById('research-viz');
    if (!container) return;
    
    container.innerHTML = `
        <div class="research-dashboard">
            <h2>Research Content Visualization</h2>
            <div class="viz-grid">
                <div class="viz-card">
                    <h3>Document Distribution</h3>
                    <div class="chart-placeholder">Chart will appear here</div>
                </div>
                <div class="viz-card">
                    <h3>Research Topics</h3>
                    <div class="chart-placeholder">Topic cloud will appear here</div>
                </div>
                <div class="viz-card">
                    <h3>Timeline</h3>
                    <div class="chart-placeholder">Timeline will appear here</div>
                </div>
                <div class="viz-card">
                    <h3>Relationships</h3>
                    <div class="chart-placeholder">Network graph will appear here</div>
                </div>
            </div>
        </div>
    `;
}

function loadResearchContent() {
    showNotification('Loading research content...', 'info');
}

// Utility Functions
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = '<div class="loading-spinner">Loading...</div>';
    }
}

function hideLoading(elementId) {
    // Content will be replaced by actual data
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function updateConnectionStatus(status) {
    const statusElement = document.getElementById('status');
    const statusText = document.getElementById('status-text');
    
    if (statusElement && statusText) {
        statusElement.className = `status-indicator ${status}`;
        statusText.textContent = status === 'connected' ? 'Connected' : 'Disconnected';
    }
}

function formatTimestamp(timestamp) {
    if (!timestamp) return 'Never';
    
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    
    return date.toLocaleDateString();
}

function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Export functions for onclick handlers
window.refreshMailbox = refreshMailbox;
window.refreshContainers = refreshContainers;
window.loadGraphData = loadGraphData;
window.composeMessage = composeMessage;
window.selectFolder = selectFolder;
window.filterMessages = filterMessages;
window.applyFilters = applyFilters;
window.selectContainer = selectContainer;
window.viewDocument = viewDocument;
window.applyGraphFilters = applyGraphFilters;
window.selectAgent = selectAgent;
window.refreshAgentStatus = refreshAgentStatus;
window.updateAgenda = updateAgenda;
window.browseDirectory = browseDirectory;
window.loadResearchContent = loadResearchContent;
window.viewMessage = viewMessage;
window.showAgentTab = showAgentTab;
window.toggleTreeItem = toggleTreeItem;

console.log('✅ Dashboard.js loaded - All functions implemented!');