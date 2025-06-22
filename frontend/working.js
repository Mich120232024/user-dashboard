// Research & Analytics Command Center - Complete Dashboard
// Comprehensive vanilla JS dashboard with all requested modules

// Global state management
const AppState = {
    currentTab: 'overview',
    selectedAgent: null,
    selectedFolder: 'inbox',
    selectedContainer: null,
    currentFilters: {},
    graphInstance: null,
    researchVizInstance: null,
    mailboxData: {},
    agentData: {},
    workspaceData: {},
    messagesPage: 0,
    messagesPerPage: 20
};

// API Base URL
const API_BASE = 'http://localhost:8001/api/v1';

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    console.log('Research & Analytics Command Center loading...');
    
    // Test connection first
    testConnection();
    
    // Load overview by default
    loadOverview();
    
    // Setup navigation
    setupNavigation();
    
    // Setup mailbox compose modal
    setupComposeModal();
    
    console.log('Dashboard initialized successfully');
});

// ================== CORE NAVIGATION ==================

function setupNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function(e) {
            const tab = e.target.dataset.tab;
            switchToTab(tab);
        });
    });
}

function switchToTab(tabName) {
    // Update nav buttons
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    
    // Update content sections
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(tabName).classList.add('active');
    
    // Update current tab
    AppState.currentTab = tabName;
    
    // Load content for the tab
    switch(tabName) {
        case 'overview':
            loadOverview();
            break;
        case 'mailbox':
            loadMailbox();
            break;
        case 'cosmos':
            loadCosmosExplorer();
            break;
        case 'graph':
            loadGraphExplorer();
            break;
        case 'agents':
            loadAgentShell();
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

async function testConnection() {
    try {
        const response = await fetch(`${API_BASE}/cosmos/containers`);
        const data = await response.json();
        
        if (data.success) {
            updateStatus('Connected - ' + data.containers.length + ' containers', 'success');
        } else {
            updateStatus('API Error', 'error');
        }
    } catch (error) {
        updateStatus('Connection Failed: ' + error.message, 'error');
    }
}

function updateStatus(text, type) {
    const statusEl = document.getElementById('status');
    const textEl = document.getElementById('status-text');
    
    if (statusEl) statusEl.className = 'status-indicator ' + type;
    if (textEl) textEl.textContent = text;
}

// ================== OVERVIEW MODULE ==================

async function loadOverview() {
    console.log('Loading overview...');
    
    try {
        // Load basic stats in parallel
        const [containersResponse, agentsResponse, messagesResponse] = await Promise.all([
            fetch(`${API_BASE}/cosmos/containers`),
            fetch(`${API_BASE}/agents/status`),
            fetch(`${API_BASE}/cosmos/user-content`)
        ]);
        
        const containersData = await containersResponse.json();
        const agentsData = await agentsResponse.json();
        const messagesData = await messagesResponse.json();
        
        // Update overview stats
        document.getElementById('total-containers').textContent = containersData.containers?.length || 0;
        document.getElementById('active-agents').textContent = agentsData.summary?.active_agents || 0;
        document.getElementById('system-health').textContent = 'Healthy';
        
        // Calculate total documents
        let totalDocs = 0;
        if (containersData.containers) {
            for (const container of containersData.containers) {
                if (container.count > 0) totalDocs += container.count;
            }
        }
        document.getElementById('total-documents').textContent = totalDocs.toLocaleString();
        
    } catch (error) {
        console.error('Overview load error:', error);
        updateStatus('Overview load failed', 'error');
    }
}

// ================== MAILBOX MODULE ==================

async function loadMailbox() {
    console.log('Loading mailbox...');
    
    try {
        // Load recipients for compose modal
        await loadRecipients();
        
        // Load folder counts
        await loadFolderCounts();
        
        // Load messages for current folder
        await loadMessages(AppState.selectedFolder);
        
    } catch (error) {
        console.error('Mailbox load error:', error);
    }
}

async function loadRecipients() {
    try {
        const response = await fetch(`${API_BASE}/agents/status`);
        const data = await response.json();
        
        const select = document.getElementById('compose-to');
        select.innerHTML = '<option value="">Select recipient...</option>';
        
        if (data.success && data.agents) {
            data.agents.forEach(agent => {
                const option = document.createElement('option');
                option.value = agent.agent_name;
                option.textContent = agent.agent_name;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading recipients:', error);
    }
}

async function loadFolderCounts() {
    try {
        const response = await fetch(`${API_BASE}/cosmos/containers/system_inbox/documents?limit=1000`);
        const data = await response.json();
        
        if (data.success && data.documents) {
            const messages = data.documents;
            
            // Count by status/folder
            const counts = {
                inbox: messages.filter(m => m.status !== 'sent' && m.status !== 'archived').length,
                sent: messages.filter(m => m.status === 'sent').length,
                archived: messages.filter(m => m.status === 'archived').length,
                drafts: 0 // Placeholder for drafts functionality
            };
            
            // Update folder counts
            document.getElementById('inbox-count').textContent = counts.inbox;
            document.getElementById('sent-count').textContent = counts.sent;
            document.getElementById('archived-count').textContent = counts.archived;
            document.getElementById('drafts-count').textContent = counts.drafts;
        }
    } catch (error) {
        console.error('Error loading folder counts:', error);
    }
}

async function loadMessages(folder = 'inbox') {
    try {
        const listEl = document.getElementById('message-list');
        listEl.innerHTML = '<div class="loading">Loading messages...</div>';
        
        let filter = '';
        switch(folder) {
            case 'sent':
                filter = '&status=sent';
                break;
            case 'archived':
                filter = '&status=archived';
                break;
            case 'inbox':
            default:
                filter = ''; // All non-sent, non-archived
                break;
        }
        
        const offset = AppState.messagesPage * AppState.messagesPerPage;
        const response = await fetch(`${API_BASE}/cosmos/containers/system_inbox/documents?limit=${AppState.messagesPerPage}&offset=${offset}${filter}`);
        const data = await response.json();
        
        if (data.success && data.documents) {
            renderMessages(data.documents);
        } else {
            listEl.innerHTML = '<div class="empty-state">No messages found</div>';
        }
    } catch (error) {
        console.error('Error loading messages:', error);
        document.getElementById('message-list').innerHTML = '<div class="empty-state">Error: ' + error.message + '</div>';
    }
}

function renderMessages(messages) {
    const listEl = document.getElementById('message-list');
    
    let html = '';
    for (const message of messages) {
        const timestamp = new Date(message.timestamp || message._ts * 1000).toLocaleString();
        const priorityClass = message.priority === 'high' ? 'priority-high' : message.priority === 'low' ? 'priority-low' : '';
        const unreadClass = message.status === 'unread' ? 'unread' : '';
        
        html += `
            <div class="message-item ${priorityClass} ${unreadClass}" data-message-id="${message.id}" onclick="selectMessage('${message.id}')">
                <div class="message-header">
                    <div class="message-from">${message.from || 'Unknown'}</div>
                    <div class="message-timestamp">${timestamp}</div>
                </div>
                <div class="message-subject">${message.subject || 'No Subject'}</div>
                <div class="message-preview">${getMessagePreview(message)}</div>
                <div class="message-meta">
                    <span class="message-type">${message.type || 'MESSAGE'}</span>
                    <span class="message-priority">${message.priority || 'medium'}</span>
                </div>
            </div>
        `;
    }
    
    listEl.innerHTML = html;
}

function getMessagePreview(message) {
    if (typeof message.content === 'string') {
        return message.content.substring(0, 150) + '...';
    } else if (typeof message.content === 'object') {
        // Handle structured content
        return JSON.stringify(message.content).substring(0, 150) + '...';
    }
    return 'No preview available';
}

function selectMessage(messageId) {
    // Remove previous selection
    document.querySelectorAll('.message-item').forEach(item => {
        item.classList.remove('selected');
    });
    
    // Add selection to clicked item
    document.querySelector(`[data-message-id="${messageId}"]`).classList.add('selected');
    
    // Load message preview
    loadMessagePreview(messageId);
}

async function loadMessagePreview(messageId) {
    try {
        const response = await fetch(`${API_BASE}/cosmos/containers/system_inbox/documents/${messageId}`);
        const data = await response.json();
        
        if (data.success && data.document) {
            renderMessagePreview(data.document);
        }
    } catch (error) {
        console.error('Error loading message preview:', error);
    }
}

function renderMessagePreview(message) {
    const previewEl = document.getElementById('message-preview');
    
    const timestamp = new Date(message.timestamp || message._ts * 1000).toLocaleString();
    const content = typeof message.content === 'string' ? 
        message.content : 
        `<pre>${JSON.stringify(message.content, null, 2)}</pre>`;
    
    previewEl.innerHTML = `
        <div class="message-preview-header">
            <h3>${message.subject || 'No Subject'}</h3>
            <div class="message-details">
                <div><strong>From:</strong> ${message.from || 'Unknown'}</div>
                <div><strong>To:</strong> ${message.to || 'Unknown'}</div>
                <div><strong>Date:</strong> ${timestamp}</div>
                <div><strong>Type:</strong> ${message.type || 'MESSAGE'}</div>
                <div><strong>Priority:</strong> ${message.priority || 'medium'}</div>
                ${message.tags ? `<div><strong>Tags:</strong> ${message.tags.join(', ')}</div>` : ''}
            </div>
        </div>
        <div class="message-preview-content">
            ${content}
        </div>
        <div class="message-preview-actions">
            <button class="btn btn-primary" onclick="replyToMessage('${message.id}')">Reply</button>
            <button class="btn btn-secondary" onclick="archiveMessage('${message.id}')">Archive</button>
            <button class="btn btn-secondary" onclick="deleteMessage('${message.id}')">Delete</button>
        </div>
    `;
}

function selectFolder(folderName) {
    // Update folder selection
    document.querySelectorAll('.folder-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-folder="${folderName}"]`).classList.add('active');
    
    AppState.selectedFolder = folderName;
    AppState.messagesPage = 0; // Reset pagination
    
    // Load messages for selected folder
    loadMessages(folderName);
}

function refreshMailbox() {
    loadMailbox();
}

// ================== COMPOSE MESSAGE MODAL ==================

function setupComposeModal() {
    const form = document.getElementById('compose-form');
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        await sendMessage();
    });
}

function composeMessage() {
    document.getElementById('compose-modal').style.display = 'flex';
}

function closeComposeModal() {
    document.getElementById('compose-modal').style.display = 'none';
    document.getElementById('compose-form').reset();
}

async function sendMessage() {
    try {
        const formData = {
            to: document.getElementById('compose-to').value,
            subject: document.getElementById('compose-subject').value,
            content: document.getElementById('compose-content').value,
            priority: document.getElementById('compose-priority').value,
            type: document.getElementById('compose-type').value,
            from_: 'USER_DASHBOARD'
        };
        
        const response = await fetch(`${API_BASE}/cosmos/message`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            closeComposeModal();
            updateStatus('Message sent successfully', 'success');
            // Refresh mailbox
            loadMessages(AppState.selectedFolder);
        } else {
            updateStatus('Failed to send message', 'error');
        }
    } catch (error) {
        console.error('Error sending message:', error);
        updateStatus('Error sending message', 'error');
    }
}

function replyToMessage(messageId) {
    // TODO: Implement reply functionality
    console.log('Reply to message:', messageId);
    composeMessage();
}

function archiveMessage(messageId) {
    // TODO: Implement archive functionality
    console.log('Archive message:', messageId);
}

function deleteMessage(messageId) {
    // TODO: Implement delete functionality
    console.log('Delete message:', messageId);
}

// ================== COSMOS EXPLORER MODULE ==================

async function loadCosmosExplorer() {
    console.log('Loading Cosmos Explorer...');
    
    try {
        await loadContainers();
    } catch (error) {
        console.error('Cosmos Explorer load error:', error);
    }
}

async function loadContainers() {
    const listEl = document.getElementById('container-list');
    listEl.innerHTML = '<div class="loading">Loading containers...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/cosmos/containers`);
        const data = await response.json();
        
        if (data.success && data.containers) {
            renderContainerList(data.containers);
        } else {
            listEl.innerHTML = '<div class="empty-state">No containers found</div>';
        }
    } catch (error) {
        console.error('Containers load error:', error);
        listEl.innerHTML = '<div class="empty-state">Error: ' + error.message + '</div>';
    }
}

function renderContainerList(containers) {
    const listEl = document.getElementById('container-list');
    
    let html = '';
    for (const container of containers) {
        html += `
            <div class="container-item" data-container-id="${container.id}" onclick="selectContainer('${container.id}')">
                <div class="container-name">${container.id}</div>
                <div class="container-count">${container.count >= 0 ? container.count.toLocaleString() : 'Loading...'}</div>
                <div class="container-partition">${container.partitionKey || '/id'}</div>
            </div>
        `;
    }
    
    listEl.innerHTML = html;
}

function selectContainer(containerId) {
    console.log('Selected container:', containerId);
    
    // Update UI
    document.querySelectorAll('.container-item').forEach(item => {
        item.classList.remove('selected');
    });
    document.querySelector(`[data-container-id="${containerId}"]`).classList.add('selected');
    
    document.getElementById('selected-container').textContent = containerId;
    AppState.selectedContainer = containerId;
    
    // Load documents
    loadDocuments(containerId);
}

async function loadDocuments(containerId) {
    const listEl = document.getElementById('document-list');
    listEl.innerHTML = '<div class="loading">Loading documents...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/cosmos/containers/${containerId}/documents?limit=20`);
        const data = await response.json();
        
        if (data.success && data.documents) {
            renderDocuments(data.documents);
        } else {
            listEl.innerHTML = '<div class="empty-state">No documents found</div>';
        }
    } catch (error) {
        console.error('Documents load error:', error);
        listEl.innerHTML = '<div class="empty-state">Error: ' + error.message + '</div>';
    }
}

function renderDocuments(documents) {
    const listEl = document.getElementById('document-list');
    
    let html = '';
    for (const doc of documents) {
        const timestamp = new Date(doc._ts * 1000).toLocaleString();
        const preview = getDocumentPreview(doc);
        
        html += `
            <div class="document-item" onclick="selectDocument('${doc.id}')">
                <div class="document-header">
                    <div class="document-id">${doc.id}</div>
                    <div class="document-timestamp">${timestamp}</div>
                </div>
                <div class="document-preview">${preview}</div>
            </div>
        `;
    }
    
    listEl.innerHTML = html;
}

function getDocumentPreview(doc) {
    const fields = ['content', 'message', 'subject', 'action', 'type', 'description'];
    
    for (const field of fields) {
        if (doc[field]) {
            const value = String(doc[field]).substring(0, 100);
            return `<strong>${field}:</strong> ${value}...`;
        }
    }
    
    return 'No preview available';
}

function selectDocument(documentId) {
    console.log('Selected document:', documentId);
    // TODO: Implement document detail view
}

function refreshContainers() {
    loadContainers();
}

// ================== GRAPH DB EXPLORER MODULE ==================

async function loadGraphExplorer() {
    console.log('Loading Graph Explorer...');
    
    // Initialize Cytoscape if not already done
    if (!AppState.graphInstance) {
        initializeGraph();
    }
}

function initializeGraph() {
    try {
        // Register dagre extension
        if (typeof cytoscape !== 'undefined' && typeof dagre !== 'undefined') {
            cytoscape.use(cytoscapeDagre);
        }
        
        AppState.graphInstance = cytoscape({
            container: document.getElementById('cy-container'),
            
            style: [
                {
                    selector: 'node',
                    style: {
                        'background-color': function(ele) {
                            const type = ele.data('type');
                            switch(type) {
                                case 'agent': return '#e74c3c';
                                case 'document': return '#3498db';
                                case 'message': return '#2ecc71';
                                case 'workspace': return '#f39c12';
                                default: return '#95a5a6';
                            }
                        },
                        'label': 'data(name)',
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'font-size': '12px',
                        'width': 40,
                        'height': 40
                    }
                },
                {
                    selector: 'edge',
                    style: {
                        'width': 2,
                        'line-color': '#bdc3c7',
                        'target-arrow-color': '#bdc3c7',
                        'target-arrow-shape': 'triangle',
                        'curve-style': 'bezier'
                    }
                }
            ],
            
            layout: {
                name: 'cose',
                idealEdgeLength: 100,
                nodeOverlap: 20,
                refresh: 20,
                fit: true,
                padding: 30,
                randomize: false,
                componentSpacing: 100
            }
        });
        
        // Add event handlers
        AppState.graphInstance.on('tap', 'node', function(evt) {
            const node = evt.target;
            showNodeDetails(node.data());
        });
        
        console.log('Graph initialized successfully');
    } catch (error) {
        console.error('Error initializing graph:', error);
    }
}

async function loadGraphData() {
    if (!AppState.graphInstance) {
        initializeGraph();
    }
    
    try {
        updateStatus('Loading graph data...', 'info');
        
        // Load data from multiple sources
        const [agentsResponse, messagesResponse, containersResponse] = await Promise.all([
            fetch(`${API_BASE}/agents/status`),
            fetch(`${API_BASE}/cosmos/user-content`),
            fetch(`${API_BASE}/cosmos/containers`)
        ]);
        
        const agentsData = await agentsResponse.json();
        const messagesData = await messagesResponse.json();
        const containersData = await containersResponse.json();
        
        // Build graph elements
        const elements = [];
        
        // Add agent nodes
        if (agentsData.success && agentsData.agents) {
            agentsData.agents.forEach(agent => {
                elements.push({
                    data: {
                        id: agent.agent_name,
                        name: agent.agent_name,
                        type: 'agent',
                        status: agent.status,
                        activity: agent.current_activity
                    }
                });
            });
        }
        
        // Add message nodes and edges
        if (messagesData.success && messagesData.messages) {
            messagesData.messages.slice(0, 20).forEach(message => { // Limit for performance
                elements.push({
                    data: {
                        id: message.id,
                        name: message.subject || 'Message',
                        type: 'message',
                        from: message.from,
                        to: message.to
                    }
                });
                
                // Add edges for message relationships
                if (message.from) {
                    elements.push({
                        data: {
                            id: `${message.from}-${message.id}`,
                            source: message.from,
                            target: message.id,
                            type: 'sent'
                        }
                    });
                }
                
                if (message.to) {
                    elements.push({
                        data: {
                            id: `${message.id}-${message.to}`,
                            source: message.id,
                            target: message.to,
                            type: 'received'
                        }
                    });
                }
            });
        }
        
        // Update graph
        AppState.graphInstance.elements().remove();
        AppState.graphInstance.add(elements);
        AppState.graphInstance.layout({ name: 'cose' }).run();
        
        // Update statistics
        const nodes = AppState.graphInstance.nodes();
        const edges = AppState.graphInstance.edges();
        document.getElementById('node-count').textContent = nodes.length;
        document.getElementById('edge-count').textContent = edges.length;
        
        updateStatus('Graph data loaded successfully', 'success');
        
    } catch (error) {
        console.error('Error loading graph data:', error);
        updateStatus('Failed to load graph data', 'error');
    }
}

function showNodeDetails(nodeData) {
    const infoEl = document.getElementById('selected-node-info');
    
    let html = `<h4>${nodeData.name}</h4>`;
    html += `<p><strong>Type:</strong> ${nodeData.type}</p>`;
    
    if (nodeData.status) {
        html += `<p><strong>Status:</strong> ${nodeData.status}</p>`;
    }
    
    if (nodeData.activity) {
        html += `<p><strong>Activity:</strong> ${nodeData.activity}</p>`;
    }
    
    if (nodeData.from) {
        html += `<p><strong>From:</strong> ${nodeData.from}</p>`;
    }
    
    if (nodeData.to) {
        html += `<p><strong>To:</strong> ${nodeData.to}</p>`;
    }
    
    infoEl.innerHTML = html;
}

function changeLayout() {
    const layout = document.getElementById('graph-layout').value;
    if (AppState.graphInstance) {
        AppState.graphInstance.layout({ name: layout }).run();
    }
}

function resetGraph() {
    if (AppState.graphInstance) {
        AppState.graphInstance.fit();
    }
}

// ================== AGENT SHELL MODULE ==================

async function loadAgentShell() {
    console.log('Loading Agent Shell...');
    
    try {
        await loadAgentList();
    } catch (error) {
        console.error('Agent Shell load error:', error);
    }
}

async function loadAgentList() {
    try {
        const response = await fetch(`${API_BASE}/agents/status`);
        const data = await response.json();
        
        const select = document.getElementById('agent-selector');
        select.innerHTML = '<option value="">Select Agent...</option>';
        
        if (data.success && data.agents) {
            data.agents.forEach(agent => {
                const option = document.createElement('option');
                option.value = agent.agent_name;
                option.textContent = agent.agent_name;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading agent list:', error);
    }
}

function selectAgent() {
    const agentName = document.getElementById('agent-selector').value;
    
    if (!agentName) {
        showAgentPlaceholder();
        return;
    }
    
    AppState.selectedAgent = agentName;
    loadAgentData(agentName);
}

function showAgentPlaceholder() {
    document.getElementById('agent-summary').innerHTML = `
        <div class="agent-placeholder">
            <h3>Select an Agent</h3>
            <p>Choose an agent to explore their journal, context memory, and workspace.</p>
        </div>
    `;
    
    // Clear all tab contents
    document.getElementById('journal-entries').innerHTML = '<div class="loading">Select an agent to load journal entries...</div>';
    document.getElementById('context-memory').innerHTML = '<div class="loading">Select an agent to load context memory...</div>';
    document.getElementById('agent-messages').innerHTML = '<div class="loading">Select an agent to load messages...</div>';
    document.getElementById('workspace-explorer').innerHTML = '<div class="loading">Select an agent to explore workspace...</div>';
}

async function loadAgentData(agentName) {
    try {
        // Load agent summary
        const response = await fetch(`${API_BASE}/agents/status`);
        const data = await response.json();
        
        if (data.success && data.agents) {
            const agent = data.agents.find(a => a.agent_name === agentName);
            if (agent) {
                renderAgentSummary(agent);
            }
        }
        
        // Load current tab content
        const activeTab = document.querySelector('.agent-tab.active').dataset.tab;
        await loadAgentTabContent(agentName, activeTab);
        
    } catch (error) {
        console.error('Error loading agent data:', error);
    }
}

function renderAgentSummary(agent) {
    document.getElementById('agent-summary').innerHTML = `
        <div class="agent-info">
            <h3>${agent.agent_name}</h3>
            <div class="agent-status ${agent.status}">${agent.status}</div>
            <div class="agent-details">
                <div><strong>Current Activity:</strong> ${agent.current_activity}</div>
                <div><strong>Todos:</strong> ${agent.todos_count}</div>
                <div><strong>Completed:</strong> ${agent.completed_tasks_count}</div>
            </div>
        </div>
    `;
}

function switchAgentTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.agent-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    
    // Update tab content
    document.querySelectorAll('.agent-tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`agent-${tabName}`).classList.add('active');
    
    // Load content for selected agent and tab
    if (AppState.selectedAgent) {
        loadAgentTabContent(AppState.selectedAgent, tabName);
    }
}

async function loadAgentTabContent(agentName, tabName) {
    try {
        switch(tabName) {
            case 'journal':
                await loadAgentJournal(agentName);
                break;
            case 'context':
                await loadAgentContext(agentName);
                break;
            case 'messages':
                await loadAgentMessages(agentName);
                break;
            case 'workspace':
                await loadAgentWorkspace(agentName);
                break;
        }
    } catch (error) {
        console.error(`Error loading ${tabName} for ${agentName}:`, error);
    }
}

async function loadAgentJournal(agentName) {
    const container = document.getElementById('journal-entries');
    container.innerHTML = '<div class="loading">Loading journal entries...</div>';
    
    try {
        // Try journal_entries container first, then agent_logs
        let response = await fetch(`${API_BASE}/cosmos/containers/journal_entries/documents?agent=${agentName}&limit=20`);
        
        if (!response.ok) {
            // Fallback to agent_logs
            response = await fetch(`${API_BASE}/cosmos/containers/agent_logs/documents?agent=${agentName}&limit=20`);
        }
        
        const data = await response.json();
        
        if (data.success && data.documents && data.documents.length > 0) {
            renderJournalEntries(data.documents);
        } else {
            container.innerHTML = '<div class="empty-state">No journal entries found for this agent</div>';
        }
    } catch (error) {
        container.innerHTML = '<div class="empty-state">Error loading journal entries: ' + error.message + '</div>';
    }
}

function renderJournalEntries(entries) {
    const container = document.getElementById('journal-entries');
    
    let html = '<div class="journal-list">';
    entries.forEach(entry => {
        const timestamp = new Date(entry.timestamp || entry._ts * 1000).toLocaleString();
        html += `
            <div class="journal-entry">
                <div class="journal-header">
                    <span class="journal-date">${timestamp}</span>
                    <span class="journal-type">${entry.type || 'Entry'}</span>
                </div>
                <div class="journal-content">${entry.content || entry.action || 'No content'}</div>
            </div>
        `;
    });
    html += '</div>';
    
    container.innerHTML = html;
}

async function loadAgentContext(agentName) {
    const container = document.getElementById('context-memory');
    container.innerHTML = '<div class="loading">Loading context memory...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/cosmos/containers/agent_context_memory/documents?agent=${agentName}&limit=20`);
        const data = await response.json();
        
        if (data.success && data.documents && data.documents.length > 0) {
            renderContextMemory(data.documents);
        } else {
            container.innerHTML = '<div class="empty-state">No context memory found for this agent</div>';
        }
    } catch (error) {
        container.innerHTML = '<div class="empty-state">Error loading context memory: ' + error.message + '</div>';
    }
}

function renderContextMemory(contexts) {
    const container = document.getElementById('context-memory');
    
    let html = '<div class="context-list">';
    contexts.forEach(context => {
        const timestamp = new Date(context.timestamp || context._ts * 1000).toLocaleString();
        html += `
            <div class="context-entry">
                <div class="context-header">
                    <span class="context-date">${timestamp}</span>
                    <span class="context-id">${context.id}</span>
                </div>
                <div class="context-content">${JSON.stringify(context, null, 2)}</div>
            </div>
        `;
    });
    html += '</div>';
    
    container.innerHTML = html;
}

async function loadAgentMessages(agentName) {
    const container = document.getElementById('agent-messages');
    container.innerHTML = '<div class="loading">Loading messages...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/cosmos/containers/system_inbox/documents?from=${agentName}&limit=20`);
        const data = await response.json();
        
        if (data.success && data.documents && data.documents.length > 0) {
            renderAgentMessages(data.documents);
        } else {
            container.innerHTML = '<div class="empty-state">No messages found for this agent</div>';
        }
    } catch (error) {
        container.innerHTML = '<div class="empty-state">Error loading messages: ' + error.message + '</div>';
    }
}

function renderAgentMessages(messages) {
    const container = document.getElementById('agent-messages');
    
    let html = '<div class="agent-message-list">';
    messages.forEach(message => {
        const timestamp = new Date(message.timestamp || message._ts * 1000).toLocaleString();
        html += `
            <div class="agent-message">
                <div class="message-header">
                    <span class="message-date">${timestamp}</span>
                    <span class="message-to">To: ${message.to}</span>
                </div>
                <div class="message-subject">${message.subject || 'No Subject'}</div>
                <div class="message-content">${getMessagePreview(message)}</div>
            </div>
        `;
    });
    html += '</div>';
    
    container.innerHTML = html;
}

async function loadAgentWorkspace(agentName) {
    const container = document.getElementById('workspace-explorer');
    container.innerHTML = '<div class="loading">Loading workspace...</div>';
    
    // TODO: Implement workspace exploration for specific agent
    container.innerHTML = `
        <div class="workspace-placeholder">
            <h4>Agent Workspace</h4>
            <p>Workspace exploration for <strong>${agentName}</strong> will be implemented here.</p>
            <button class="btn btn-primary" onclick="exploreWorkspace('${agentName}')">Explore Workspace</button>
        </div>
    `;
}

function refreshAgentData() {
    if (AppState.selectedAgent) {
        loadAgentData(AppState.selectedAgent);
    }
}

function exportAgentData() {
    if (AppState.selectedAgent) {
        console.log('Export data for agent:', AppState.selectedAgent);
        // TODO: Implement export functionality
    }
}

// ================== MANAGER DASHBOARD MODULE ==================

async function loadManagerDashboard() {
    console.log('Loading Manager Dashboard...');
    
    try {
        await loadManagerStats();
        await loadManagerTabContent('overview');
    } catch (error) {
        console.error('Manager Dashboard load error:', error);
    }
}

async function loadManagerStats() {
    try {
        // Load various stats in parallel
        const [agentsResponse, messagesResponse] = await Promise.all([
            fetch(`${API_BASE}/agents/status`),
            fetch(`${API_BASE}/cosmos/user-content`)
        ]);
        
        const agentsData = await agentsResponse.json();
        const messagesData = await messagesResponse.json();
        
        // Update stats
        document.getElementById('active-agents-count').textContent = agentsData.agents?.length || 0;
        document.getElementById('pending-tasks-count').textContent = calculatePendingTasks(agentsData.agents);
        document.getElementById('completed-today-count').textContent = calculateCompletedToday(agentsData.agents);
        document.getElementById('system-health-status').textContent = 'Good';
        
    } catch (error) {
        console.error('Error loading manager stats:', error);
    }
}

function calculatePendingTasks(agents) {
    if (!agents) return 0;
    return agents.reduce((total, agent) => total + (agent.todos_count || 0), 0);
}

function calculateCompletedToday(agents) {
    if (!agents) return 0;
    return agents.reduce((total, agent) => total + (agent.completed_tasks_count || 0), 0);
}

function switchManagerTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.manager-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    
    // Update tab content
    document.querySelectorAll('.manager-tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`manager-${tabName}`).classList.add('active');
    
    // Load content for selected tab
    loadManagerTabContent(tabName);
}

async function loadManagerTabContent(tabName) {
    try {
        switch(tabName) {
            case 'overview':
                await loadManagerOverview();
                break;
            case 'agents':
                await loadManagerAgents();
                break;
            case 'agenda':
                await loadManagerAgenda();
                break;
            case 'reports':
                await loadManagerReports();
                break;
        }
    } catch (error) {
        console.error(`Error loading manager ${tabName}:`, error);
    }
}

async function loadManagerOverview() {
    // TODO: Implement charts using a charting library
    document.getElementById('activity-chart').innerHTML = '<div class="chart-placeholder">Activity Chart (TODO: Implement with Chart.js)</div>';
    document.getElementById('completion-chart').innerHTML = '<div class="chart-placeholder">Completion Chart (TODO: Implement with Chart.js)</div>';
}

async function loadManagerAgents() {
    const container = document.getElementById('manager-agent-list');
    container.innerHTML = '<div class="loading">Loading agent management...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/agents/status`);
        const data = await response.json();
        
        if (data.success && data.agents) {
            renderManagerAgents(data.agents);
        } else {
            container.innerHTML = '<div class="empty-state">No agents found</div>';
        }
    } catch (error) {
        container.innerHTML = '<div class="empty-state">Error loading agents: ' + error.message + '</div>';
    }
}

function renderManagerAgents(agents) {
    const container = document.getElementById('manager-agent-list');
    
    let html = '<div class="manager-agents-grid">';
    agents.forEach(agent => {
        html += `
            <div class="manager-agent-card">
                <div class="agent-header">
                    <h4>${agent.agent_name}</h4>
                    <span class="agent-status ${agent.status}">${agent.status}</span>
                </div>
                <div class="agent-metrics">
                    <div class="metric">
                        <span class="metric-label">Activity:</span>
                        <span class="metric-value">${agent.current_activity}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Todos:</span>
                        <span class="metric-value">${agent.todos_count}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Completed:</span>
                        <span class="metric-value">${agent.completed_tasks_count}</span>
                    </div>
                </div>
                <div class="agent-actions">
                    <button class="btn btn-sm btn-primary" onclick="viewAgentDetail('${agent.agent_name}')">View Details</button>
                    <button class="btn btn-sm btn-secondary" onclick="messageAgent('${agent.agent_name}')">Message</button>
                </div>
            </div>
        `;
    });
    html += '</div>';
    
    container.innerHTML = html;
}

function viewAgentDetail(agentName) {
    // Switch to agent shell tab with this agent selected
    switchToTab('agents');
    document.getElementById('agent-selector').value = agentName;
    selectAgent();
}

function messageAgent(agentName) {
    composeMessage();
    document.getElementById('compose-to').value = agentName;
}

async function loadManagerAgenda() {
    const calendarContainer = document.getElementById('agenda-calendar');
    const tasksContainer = document.getElementById('today-tasks');
    
    calendarContainer.innerHTML = '<div class="calendar-placeholder">Calendar View (TODO: Implement calendar)</div>';
    tasksContainer.innerHTML = '<div class="loading">Loading today\'s tasks...</div>';
    
    // TODO: Implement agenda/calendar functionality
    tasksContainer.innerHTML = `
        <div class="task-list">
            <div class="task-item">
                <span class="task-title">Review agent performance</span>
                <span class="task-time">09:00</span>
            </div>
            <div class="task-item">
                <span class="task-title">System maintenance check</span>
                <span class="task-time">14:00</span>
            </div>
            <div class="task-item">
                <span class="task-title">Weekly team sync</span>
                <span class="task-time">16:00</span>
            </div>
        </div>
    `;
}

async function loadManagerReports() {
    const container = document.getElementById('report-content');
    container.innerHTML = '<div class="loading">Select a report type and click Generate...</div>';
}

function generateReport() {
    const reportType = document.getElementById('report-type').value;
    const container = document.getElementById('report-content');
    
    container.innerHTML = `<div class="loading">Generating ${reportType} report...</div>`;
    
    // TODO: Implement report generation
    setTimeout(() => {
        container.innerHTML = `
            <div class="report-result">
                <h4>${reportType.charAt(0).toUpperCase() + reportType.slice(1)} Report</h4>
                <p>Report generation for <strong>${reportType}</strong> will be implemented here.</p>
            </div>
        `;
    }, 1000);
}

function refreshManagerData() {
    loadManagerDashboard();
}

function exportReport() {
    console.log('Export report functionality to be implemented');
}

function changeTimeRange() {
    const timeRange = document.getElementById('time-range').value;
    console.log('Changed time range to:', timeRange);
    // TODO: Implement time range filtering
}

// ================== WORKSPACE EXPLORER MODULE ==================

async function loadWorkspaceExplorer() {
    console.log('Loading Workspace Explorer...');
    
    try {
        await loadWorkspaceTree();
    } catch (error) {
        console.error('Workspace Explorer load error:', error);
    }
}

async function loadWorkspaceTree() {
    // TODO: Implement workspace tree structure loading
    const container = document.getElementById('workspace-tree');
    container.innerHTML = `
        <div class="tree-item" data-path="/" onclick="expandPath('/')">
            <span class="tree-icon">📁</span>
            <span class="tree-name">Research & Analytics Services</span>
            <span class="tree-toggle">▼</span>
        </div>
        <div class="tree-children" style="margin-left: 20px;">
            <div class="tree-item" data-path="/Engineering Workspace" onclick="expandPath('/Engineering Workspace')">
                <span class="tree-icon">📁</span>
                <span class="tree-name">Engineering Workspace</span>
                <span class="tree-toggle">▶</span>
            </div>
            <div class="tree-item" data-path="/Research Workspace" onclick="expandPath('/Research Workspace')">
                <span class="tree-icon">📁</span>
                <span class="tree-name">Research Workspace</span>
                <span class="tree-toggle">▶</span>
            </div>
            <div class="tree-item" data-path="/Projects" onclick="expandPath('/Projects')">
                <span class="tree-icon">📁</span>
                <span class="tree-name">Projects</span>
                <span class="tree-toggle">▶</span>
            </div>
        </div>
    `;
}

function expandPath(path) {
    console.log('Expanding path:', path);
    
    // Update breadcrumb
    document.getElementById('workspace-breadcrumb').innerHTML = `<span>${path}</span>`;
    
    // TODO: Load projects for selected path
    const projectList = document.getElementById('project-list');
    projectList.innerHTML = `
        <div class="project-grid">
            <div class="project-card" onclick="selectProject('user-dashboard')">
                <div class="project-icon">📊</div>
                <div class="project-name">user-dashboard</div>
                <div class="project-type">React + FastAPI</div>
            </div>
            <div class="project-card" onclick="selectProject('data-pipeline')">
                <div class="project-icon">🔄</div>
                <div class="project-name">data-pipeline</div>
                <div class="project-type">Python ETL</div>
            </div>
            <div class="project-card" onclick="selectProject('research-tools')">
                <div class="project-icon">🔬</div>
                <div class="project-name">research-tools</div>
                <div class="project-type">Analysis Tools</div>
            </div>
        </div>
    `;
}

function selectProject(projectName) {
    console.log('Selected project:', projectName);
    
    // Update project details
    const detailsContainer = document.getElementById('project-details');
    detailsContainer.innerHTML = `
        <div class="project-detail">
            <h4>${projectName}</h4>
            <div class="project-info">
                <div><strong>Type:</strong> Web Application</div>
                <div><strong>Status:</strong> Active</div>
                <div><strong>Last Modified:</strong> ${new Date().toLocaleDateString()}</div>
            </div>
            <div class="project-actions">
                <button class="btn btn-primary" onclick="exploreProject('${projectName}')">Explore</button>
                <button class="btn btn-secondary" onclick="openProject('${projectName}')">Open</button>
            </div>
        </div>
    `;
}

function exploreProject(projectName) {
    console.log('Explore project:', projectName);
    // TODO: Implement project exploration
}

function openProject(projectName) {
    console.log('Open project:', projectName);
    // TODO: Implement project opening
}

function refreshWorkspace() {
    loadWorkspaceTree();
}

function exportWorkspaceMap() {
    console.log('Export workspace map functionality to be implemented');
}

function searchWorkspace() {
    const searchTerm = document.getElementById('workspace-search').value;
    console.log('Search workspace for:', searchTerm);
    // TODO: Implement workspace search
}

// ================== RESEARCH VISUALIZATION MODULE ==================

async function loadResearchVisualization() {
    console.log('Loading Research Visualization...');
    
    try {
        await initializeResearchViz();
    } catch (error) {
        console.error('Research Visualization load error:', error);
    }
}

async function initializeResearchViz() {
    // TODO: Initialize research visualization
    const container = document.getElementById('research-viz-container');
    container.innerHTML = `
        <div class="viz-placeholder">
            <h3>Research Content Map</h3>
            <p>Click "Load Data" to visualize research content and relationships.</p>
            <button class="btn btn-primary" onclick="loadResearchData()">Load Data</button>
        </div>
    `;
}

async function loadResearchData() {
    const container = document.getElementById('research-viz-container');
    container.innerHTML = '<div class="loading">Loading research data...</div>';
    
    try {
        // Load research content from various containers
        const response = await fetch(`${API_BASE}/cosmos/containers`);
        const data = await response.json();
        
        if (data.success && data.containers) {
            // Filter research-related containers
            const researchContainers = data.containers.filter(c => 
                c.id.includes('document') || 
                c.id.includes('research') || 
                c.id.includes('institutional')
            );
            
            // Update statistics
            document.getElementById('research-docs-count').textContent = researchContainers.length;
            document.getElementById('research-categories-count').textContent = researchContainers.length;
            document.getElementById('research-connections-count').textContent = researchContainers.length * 2;
            
            // Create visualization
            await createResearchVisualization(researchContainers);
        }
    } catch (error) {
        console.error('Error loading research data:', error);
        container.innerHTML = '<div class="empty-state">Error loading research data: ' + error.message + '</div>';
    }
}

async function createResearchVisualization(containers) {
    const container = document.getElementById('research-viz-container');
    
    // Initialize Cytoscape for research viz if not already done
    if (!AppState.researchVizInstance) {
        AppState.researchVizInstance = cytoscape({
            container: container,
            
            style: [
                {
                    selector: 'node',
                    style: {
                        'background-color': function(ele) {
                            const type = ele.data('type');
                            switch(type) {
                                case 'reports': return '#3498db';
                                case 'analysis': return '#e74c3c';
                                case 'data': return '#2ecc71';
                                case 'documentation': return '#f39c12';
                                default: return '#95a5a6';
                            }
                        },
                        'label': 'data(name)',
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'font-size': '10px',
                        'width': 50,
                        'height': 50
                    }
                },
                {
                    selector: 'edge',
                    style: {
                        'width': 1,
                        'line-color': '#bdc3c7',
                        'target-arrow-color': '#bdc3c7',
                        'target-arrow-shape': 'triangle',
                        'curve-style': 'bezier'
                    }
                }
            ],
            
            layout: {
                name: 'circle',
                fit: true,
                padding: 30
            }
        });
    }
    
    // Build elements for research visualization
    const elements = [];
    
    containers.forEach(container => {
        elements.push({
            data: {
                id: container.id,
                name: container.id.replace(/_/g, ' '),
                type: categorizeContainer(container.id),
                count: container.count
            }
        });
    });
    
    // Add some sample relationships
    for (let i = 0; i < containers.length - 1; i++) {
        elements.push({
            data: {
                id: `${containers[i].id}-${containers[i + 1].id}`,
                source: containers[i].id,
                target: containers[i + 1].id
            }
        });
    }
    
    // Update visualization
    AppState.researchVizInstance.elements().remove();
    AppState.researchVizInstance.add(elements);
    AppState.researchVizInstance.layout({ name: 'circle' }).run();
}

function categorizeContainer(containerId) {
    if (containerId.includes('document') || containerId.includes('institutional')) {
        return 'documentation';
    } else if (containerId.includes('audit') || containerId.includes('log')) {
        return 'reports';
    } else if (containerId.includes('agent') || containerId.includes('process')) {
        return 'analysis';
    } else {
        return 'data';
    }
}

function changeResearchView() {
    const view = document.getElementById('research-view').value;
    
    if (AppState.researchVizInstance) {
        let layout;
        switch(view) {
            case 'network':
                layout = { name: 'cose' };
                break;
            case 'timeline':
                layout = { name: 'breadthfirst', directed: true };
                break;
            case 'categories':
                layout = { name: 'grid' };
                break;
            case 'geographic':
                layout = { name: 'circle' };
                break;
            default:
                layout = { name: 'cose' };
        }
        
        AppState.researchVizInstance.layout(layout).run();
    }
}

function resetResearchView() {
    if (AppState.researchVizInstance) {
        AppState.researchVizInstance.fit();
    }
}

// ================== UTILITY FUNCTIONS ==================

function applyFilters() {
    const priority = document.getElementById('priority-filter').value;
    const type = document.getElementById('type-filter').value;
    const from = document.getElementById('from-filter').value;
    
    AppState.currentFilters = { priority, type, from };
    
    // Reload messages with filters
    loadMessages(AppState.selectedFolder);
}

function filterMessages() {
    const filter = document.getElementById('mailbox-filter').value;
    console.log('Filter messages by:', filter);
    // TODO: Implement message filtering
}

function previousMessages() {
    if (AppState.messagesPage > 0) {
        AppState.messagesPage--;
        loadMessages(AppState.selectedFolder);
    }
}

function nextMessages() {
    AppState.messagesPage++;
    loadMessages(AppState.selectedFolder);
}

function searchDocuments() {
    const searchTerm = document.getElementById('document-search').value;
    console.log('Search documents for:', searchTerm);
    // TODO: Implement document search
}

function previousPage() {
    console.log('Previous page');
    // TODO: Implement pagination
}

function nextPage() {
    console.log('Next page');
    // TODO: Implement pagination
}

// ================== PLACEHOLDER FUNCTIONS ==================

function exploreWorkspace(agentName) {
    console.log('Explore workspace for agent:', agentName);
    // TODO: Implement workspace exploration
}

console.log('Research & Analytics Command Center - All modules loaded');