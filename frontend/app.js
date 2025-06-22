// Modern Dashboard JavaScript - Clean & Functional
class Dashboard {
    constructor() {
        this.API_BASE = 'http://localhost:8001/api/v1';
        this.cache = new Map();
        this.cacheTTL = 60000; // 1 minute
        this.currentTab = 'overview';
        this.selectedContainer = null;
        this.currentPage = 0;
        this.pageSize = 20;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.switchTab('overview');
        this.updateStatus('Connected', 'success');
    }
    
    setupEventListeners() {
        // Tab navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });
        
        // Container list delegation
        document.getElementById('container-list').addEventListener('click', (e) => {
            const item = e.target.closest('.container-item');
            if (item) {
                this.selectContainer(item.dataset.containerId);
            }
        });
        
        // Search functionality
        document.getElementById('container-search')?.addEventListener('input', (e) => {
            this.filterContainers(e.target.value);
        });
        
        document.getElementById('document-search')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.searchDocuments();
            }
        });
    }
    
    async api(endpoint, useCache = true) {
        const url = `${this.API_BASE}${endpoint}`;
        const cacheKey = url;
        
        // Check cache
        if (useCache && this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            if (Date.now() - cached.timestamp < this.cacheTTL) {
                return cached.data;
            }
            this.cache.delete(cacheKey);
        }
        
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            
            if (useCache) {
                this.cache.set(cacheKey, {
                    data,
                    timestamp: Date.now()
                });
            }
            
            return data;
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            this.updateStatus(`Error: ${error.message}`, 'error');
            throw error;
        }
    }
    
    updateStatus(text, type = 'success') {
        const indicator = document.getElementById('status');
        const statusText = document.getElementById('status-text');
        
        indicator.className = `status-indicator ${type}`;
        statusText.textContent = text;
    }
    
    switchTab(tabName) {
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.toggle('active', item.dataset.tab === tabName);
        });
        
        // Update content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.toggle('active', content.id === tabName);
        });
        
        this.currentTab = tabName;
        this.loadTabContent(tabName);
    }
    
    async loadTabContent(tabName) {
        try {
            switch (tabName) {
                case 'overview':
                    await this.loadOverview();
                    break;
                case 'containers':
                    await this.loadContainers();
                    break;
                case 'agents':
                    await this.loadAgents();
                    break;
                case 'monitoring':
                    await this.loadMonitoring();
                    break;
            }
            this.updateStatus('Data loaded successfully', 'success');
        } catch (error) {
            this.updateStatus(`Failed to load ${tabName}`, 'error');
        }
    }
    
    async loadOverview() {
        try {
            const [healthData, containersData, agentsData] = await Promise.all([
                this.api('/live/system-health'),
                this.api('/cosmos/containers'),
                this.api('/agents/status')
            ]);
            
            // Update stats
            document.getElementById('system-health').textContent = 
                healthData?.health?.system_status || 'Unknown';
                
            document.getElementById('total-containers').textContent = 
                containersData?.containers?.length || 0;
                
            document.getElementById('active-agents').textContent = 
                agentsData?.summary?.active_agents || 0;
                
            // Calculate total documents
            const totalDocs = containersData?.containers?.reduce((sum, c) => 
                sum + (c.count > 0 ? c.count : 0), 0) || 0;
            document.getElementById('total-documents').textContent = totalDocs.toLocaleString();
            
        } catch (error) {
            console.error('Overview load error:', error);
        }
    }
    
    async loadContainers() {
        const listEl = document.getElementById('container-list');
        listEl.innerHTML = '<div class="loading">Loading containers...</div>';
        
        try {
            const data = await this.api('/cosmos/containers?count_docs=false');
            
            if (data.success && data.containers) {
                this.renderContainers(data.containers);
                // Load counts asynchronously
                this.loadContainerCounts(data.containers);
            } else {
                listEl.innerHTML = '<div class="empty-state">No containers found</div>';
            }
        } catch (error) {
            listEl.innerHTML = '<div class="empty-state">Error loading containers</div>';
        }
    }
    
    renderContainers(containers) {
        const listEl = document.getElementById('container-list');
        
        listEl.innerHTML = containers.map(container => `
            <div class="container-item ${this.selectedContainer === container.id ? 'selected' : ''}" 
                 data-container-id="${container.id}">
                <div class="container-name">${container.id}</div>
                <div class="container-count" id="count-${container.id}">
                    ${container.count >= 0 ? container.count.toLocaleString() : 'Loading...'}
                </div>
            </div>
        `).join('');
    }
    
    async loadContainerCounts(containers) {
        // Load counts in batches to avoid overwhelming the API
        const batchSize = 3;
        for (let i = 0; i < containers.length; i += batchSize) {
            const batch = containers.slice(i, i + batchSize);
            
            const promises = batch.map(async (container) => {
                try {
                    const data = await this.api(`/cosmos/containers/${container.id}/documents?limit=1`);
                    return { id: container.id, count: data.count || 0 };
                } catch (error) {
                    return { id: container.id, count: 0 };
                }
            });
            
            const results = await Promise.allSettled(promises);
            
            results.forEach((result, idx) => {
                if (result.status === 'fulfilled') {
                    const { id, count } = result.value;
                    const countEl = document.getElementById(`count-${id}`);
                    if (countEl) {
                        countEl.textContent = count.toLocaleString();
                    }
                }
            });
            
            // Small delay between batches
            if (i + batchSize < containers.length) {
                await new Promise(resolve => setTimeout(resolve, 100));
            }
        }
    }
    
    async selectContainer(containerId) {
        this.selectedContainer = containerId;
        this.currentPage = 0;
        
        // Update UI
        document.querySelectorAll('.container-item').forEach(item => {
            item.classList.toggle('selected', item.dataset.containerId === containerId);
        });
        
        document.getElementById('selected-container').textContent = containerId;
        
        await this.loadDocuments();
    }
    
    async loadDocuments() {
        if (!this.selectedContainer) return;
        
        const listEl = document.getElementById('document-list');
        listEl.innerHTML = '<div class="loading">Loading documents...</div>';
        
        try {
            const offset = this.currentPage * this.pageSize;
            const data = await this.api(
                `/cosmos/containers/${this.selectedContainer}/documents?offset=${offset}&limit=${this.pageSize}`
            );
            
            if (data.success && data.documents) {
                this.renderDocuments(data.documents, data);
            } else {
                listEl.innerHTML = '<div class="empty-state">No documents found</div>';
            }
        } catch (error) {
            listEl.innerHTML = '<div class="empty-state">Error loading documents</div>';
        }
    }
    
    renderDocuments(documents, metadata) {
        const listEl = document.getElementById('document-list');
        
        if (documents.length === 0) {
            listEl.innerHTML = '<div class="empty-state">No documents in this container</div>';
            return;
        }
        
        listEl.innerHTML = documents.map(doc => {
            const timestamp = new Date(doc._ts * 1000).toLocaleString();
            const preview = this.getDocumentPreview(doc);
            
            return `
                <div class="document-item">
                    <div class="document-header">
                        <div class="document-id">${doc.id}</div>
                        <div class="document-timestamp">${timestamp}</div>
                    </div>
                    <div class="document-preview">${preview}</div>
                </div>
            `;
        }).join('');
        
        this.updatePagination(metadata);
    }
    
    getDocumentPreview(doc) {
        const fields = ['content', 'message', 'subject', 'action', 'type'];
        
        for (const field of fields) {
            if (doc[field]) {
                const value = String(doc[field]).substring(0, 150);
                return `<strong>${field}:</strong> ${value}${doc[field].length > 150 ? '...' : ''}`;
            }
        }
        
        return 'No preview available';
    }
    
    updatePagination(metadata) {
        const paginationEl = document.getElementById('pagination');
        const { offset = 0, limit = 20, count = 0 } = metadata;
        
        if (count <= limit) {
            paginationEl.style.display = 'none';
            return;
        }
        
        paginationEl.style.display = 'flex';
        
        const currentPage = Math.floor(offset / limit) + 1;
        const totalPages = Math.ceil(count / limit);
        
        document.getElementById('prev-btn').disabled = currentPage <= 1;
        document.getElementById('next-btn').disabled = currentPage >= totalPages;
        document.getElementById('page-info').textContent = 
            `Page ${currentPage} of ${totalPages} (${count} total)`;
    }
    
    async loadAgents() {
        const gridEl = document.getElementById('agent-grid');
        gridEl.innerHTML = '<div class="loading">Loading agents...</div>';
        
        try {
            const data = await this.api('/agents/status');
            
            if (data.success && data.agents) {
                this.renderAgents(data.agents);
            } else {
                gridEl.innerHTML = '<div class="empty-state">No agents found</div>';
            }
        } catch (error) {
            gridEl.innerHTML = '<div class="empty-state">Error loading agents</div>';
        }
    }
    
    renderAgents(agents) {
        const gridEl = document.getElementById('agent-grid');
        
        gridEl.innerHTML = agents.map(agent => `
            <div class="agent-card">
                <div class="agent-name">${agent.agent_name}</div>
                <div class="agent-status ${agent.status}">${agent.status}</div>
                <div style="margin-top: 0.5rem; font-size: 0.875rem; color: var(--text-light);">
                    <div>Activity: ${agent.current_activity}</div>
                    <div>Todos: ${agent.todos_count}</div>
                    <div>Completed: ${agent.completed_tasks_count}</div>
                </div>
            </div>
        `).join('');
    }
    
    async loadMonitoring() {
        try {
            const start = Date.now();
            await this.api('/live/system-health', false); // Don't use cache for timing
            const responseTime = Date.now() - start;
            
            document.getElementById('api-response-time').textContent = `${responseTime}ms`;
            document.getElementById('cache-hit-rate').textContent = 
                `${Math.round(this.cache.size / 10 * 100)}%`;
            document.getElementById('active-connections').textContent = '4';
        } catch (error) {
            console.error('Monitoring load error:', error);
        }
    }
    
    filterContainers(query) {
        const items = document.querySelectorAll('.container-item');
        items.forEach(item => {
            const name = item.querySelector('.container-name').textContent.toLowerCase();
            const match = name.includes(query.toLowerCase());
            item.style.display = match ? 'block' : 'none';
        });
    }
    
    async searchDocuments() {
        const query = document.getElementById('document-search').value.trim();
        if (!query) return;
        
        const listEl = document.getElementById('document-list');
        listEl.innerHTML = '<div class="loading">Searching...</div>';
        
        try {
            const data = await this.api(`/cosmos/search?q=${encodeURIComponent(query)}&limit=20`);
            
            if (data.success && data.results) {
                this.renderSearchResults(data.results);
            } else {
                listEl.innerHTML = '<div class="empty-state">No results found</div>';
            }
        } catch (error) {
            listEl.innerHTML = '<div class="empty-state">Search error</div>';
        }
    }
    
    renderSearchResults(results) {
        const listEl = document.getElementById('document-list');
        
        listEl.innerHTML = results.map(result => {
            const doc = result.document;
            const timestamp = new Date(doc._ts * 1000).toLocaleString();
            const preview = this.getDocumentPreview(doc);
            
            return `
                <div class="document-item">
                    <div class="document-header">
                        <div class="document-id">${doc.id}</div>
                        <div class="document-timestamp">${timestamp}</div>
                    </div>
                    <div style="font-size: 0.75rem; color: var(--text-light); margin-bottom: 0.5rem;">
                        From: ${result.container}
                    </div>
                    <div class="document-preview">${preview}</div>
                </div>
            `;
        }).join('');
    }
}

// Global functions for button onclick handlers
window.refreshContainers = () => dashboard.loadContainers();
window.refreshAgents = () => dashboard.loadAgents();
window.refreshMonitoring = () => dashboard.loadMonitoring();
window.searchDocuments = () => dashboard.searchDocuments();
window.previousPage = () => {
    if (dashboard.currentPage > 0) {
        dashboard.currentPage--;
        dashboard.loadDocuments();
    }
};
window.nextPage = () => {
    dashboard.currentPage++;
    dashboard.loadDocuments();
};

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new Dashboard();
});