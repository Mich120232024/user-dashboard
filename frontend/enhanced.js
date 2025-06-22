// Professional Research & Analytics Dashboard - Enhanced JavaScript
// Enterprise-grade frontend with real-time updates and professional UX

// Enhanced Global State Management
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
    messagesPerPage: 20,
    realTimeUpdates: true,
    notifications: [],
    performance: {
        lastLoadTime: null,
        apiResponseTimes: {},
        cacheHitRate: 0
    }
};

// Configuration
const CONFIG = {
    API_BASE: 'http://localhost:8001/api/v1',
    REFRESH_INTERVAL: 30000, // 30 seconds
    ANIMATION_DURATION: 300,
    CACHE_TTL: 60000, // 1 minute
    MAX_RETRIES: 3,
    RETRY_DELAY: 1000
};

// Enhanced Cache System
class DataCache {
    constructor() {
        this.cache = new Map();
        this.hitCount = 0;
        this.missCount = 0;
    }

    set(key, data, ttl = CONFIG.CACHE_TTL) {
        this.cache.set(key, {
            data,
            timestamp: Date.now(),
            ttl
        });
    }

    get(key) {
        const item = this.cache.get(key);
        if (!item) {
            this.missCount++;
            return null;
        }

        if (Date.now() - item.timestamp > item.ttl) {
            this.cache.delete(key);
            this.missCount++;
            return null;
        }

        this.hitCount++;
        AppState.performance.cacheHitRate = this.hitCount / (this.hitCount + this.missCount);
        return item.data;
    }

    clear() {
        this.cache.clear();
        this.hitCount = 0;
        this.missCount = 0;
    }

    size() {
        return this.cache.size;
    }

    getStats() {
        return {
            size: this.cache.size,
            hitRate: this.hitCount / (this.hitCount + this.missCount) || 0,
            hitCount: this.hitCount,
            missCount: this.missCount
        };
    }
}

const cache = new DataCache();

// Enhanced API Client with retry logic and performance monitoring
class ApiClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
        this.requestCounter = 0;
    }

    async request(endpoint, options = {}) {
        const startTime = performance.now();
        const requestId = ++this.requestCounter;
        
        // Check cache first
        const cacheKey = `${endpoint}:${JSON.stringify(options)}`;
        const cachedData = cache.get(cacheKey);
        if (cachedData && options.method !== 'POST') {
            console.log(`[${requestId}] Cache hit for ${endpoint}`);
            return cachedData;
        }

        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-Request-ID': requestId.toString()
            },
            ...options
        };

        let lastError;
        for (let attempt = 1; attempt <= CONFIG.MAX_RETRIES; attempt++) {
            try {
                console.log(`[${requestId}] Attempt ${attempt} for ${endpoint}`);
                
                const response = await fetch(url, config);
                const responseTime = performance.now() - startTime;
                
                // Track performance
                AppState.performance.apiResponseTimes[endpoint] = responseTime;
                AppState.performance.lastLoadTime = responseTime;

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();
                
                // Cache successful GET requests
                if (config.method === 'GET') {
                    cache.set(cacheKey, data);
                }

                console.log(`[${requestId}] Success: ${endpoint} (${responseTime.toFixed(2)}ms)`);
                updatePerformanceIndicators();
                
                return data;

            } catch (error) {
                lastError = error;
                console.warn(`[${requestId}] Attempt ${attempt} failed for ${endpoint}:`, error.message);
                
                if (attempt < CONFIG.MAX_RETRIES) {
                    await this.delay(CONFIG.RETRY_DELAY * attempt);
                }
            }
        }

        console.error(`[${requestId}] All attempts failed for ${endpoint}:`, lastError);
        showNotification(`Failed to load ${endpoint}`, 'error');
        throw lastError;
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Convenience methods
    get(endpoint) {
        return this.request(endpoint);
    }

    post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE'
        });
    }
}

const api = new ApiClient(CONFIG.API_BASE);

// Enhanced Notification System
function showNotification(message, type = 'info', duration = 5000) {
    const notification = {
        id: Date.now(),
        message,
        type,
        timestamp: new Date()
    };

    AppState.notifications.push(notification);
    
    // Create notification element
    const notificationEl = document.createElement('div');
    notificationEl.className = `notification notification-${type}`;
    notificationEl.innerHTML = `
        <div class="notification-content">
            <span class="notification-icon">${getNotificationIcon(type)}</span>
            <span class="notification-message">${message}</span>
            <button class="notification-close" onclick="closeNotification(${notification.id})">×</button>
        </div>
    `;

    // Add to DOM
    let container = document.querySelector('.notifications-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'notifications-container';
        document.body.appendChild(container);
    }
    container.appendChild(notificationEl);

    // Auto-remove after duration
    setTimeout(() => {
        closeNotification(notification.id);
    }, duration);

    return notification.id;
}

function getNotificationIcon(type) {
    const icons = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
    };
    return icons[type] || icons.info;
}

function closeNotification(id) {
    const notificationEl = document.querySelector(`[data-notification-id="${id}"]`);
    if (notificationEl) {
        notificationEl.remove();
    }
    AppState.notifications = AppState.notifications.filter(n => n.id !== id);
}

// Enhanced Status Management
class StatusManager {
    constructor() {
        this.currentStatus = 'loading';
        this.statusHistory = [];
    }

    setStatus(status, message = '') {
        this.currentStatus = status;
        this.statusHistory.push({
            status,
            message,
            timestamp: new Date()
        });

        this.updateStatusIndicator(status, message);
        
        // Keep only last 10 status changes
        if (this.statusHistory.length > 10) {
            this.statusHistory.shift();
        }
    }

    updateStatusIndicator(status, message) {
        const indicator = document.getElementById('status');
        const text = document.getElementById('status-text');
        
        if (!indicator || !text) return;

        // Update indicator color
        const statusClasses = {
            healthy: 'status-success',
            warning: 'status-warning',
            error: 'status-error',
            loading: 'status-info'
        };

        indicator.className = `status-indicator ${statusClasses[status] || 'status-info'}`;
        text.textContent = message || this.getDefaultMessage(status);
    }

    getDefaultMessage(status) {
        const messages = {
            healthy: 'System Operational',
            warning: 'Minor Issues',
            error: 'System Error',
            loading: 'Loading...'
        };
        return messages[status] || 'Unknown Status';
    }

    getSystemHealth() {
        return {
            status: this.currentStatus,
            uptime: this.calculateUptime(),
            lastCheck: new Date(),
            history: this.statusHistory.slice(-5)
        };
    }

    calculateUptime() {
        const startTime = AppState.performance.startTime || Date.now();
        return Date.now() - startTime;
    }
}

const statusManager = new StatusManager();

// Enhanced Performance Monitoring
function updatePerformanceIndicators() {
    const perfData = {
        apiResponseTime: AppState.performance.lastLoadTime,
        cacheHitRate: AppState.performance.cacheHitRate,
        cacheSize: cache.size(),
        activeConnections: 1, // Simplified for demo
        memoryUsage: getMemoryUsage()
    };

    // Update performance UI if exists
    const perfContainer = document.querySelector('.performance-indicators');
    if (perfContainer) {
        perfContainer.innerHTML = `
            <div class="perf-metric">
                <span class="perf-label">Response Time</span>
                <span class="perf-value">${(perfData.apiResponseTime || 0).toFixed(0)}ms</span>
            </div>
            <div class="perf-metric">
                <span class="perf-label">Cache Hit Rate</span>
                <span class="perf-value">${(perfData.cacheHitRate * 100).toFixed(1)}%</span>
            </div>
            <div class="perf-metric">
                <span class="perf-label">Cache Size</span>
                <span class="perf-value">${perfData.cacheSize}</span>
            </div>
        `;
    }
}

function getMemoryUsage() {
    if (performance.memory) {
        return {
            used: performance.memory.usedJSHeapSize,
            total: performance.memory.totalJSHeapSize,
            limit: performance.memory.jsHeapSizeLimit
        };
    }
    return null;
}

// Enhanced Data Loading with Professional UX
async function loadDashboardData() {
    try {
        statusManager.setStatus('loading', 'Loading dashboard data...');
        
        // Show loading skeleton
        showLoadingSkeleton();

        // Load critical data in parallel
        const [systemHealth, containers, agents, messages] = await Promise.allSettled([
            api.get('/live/system-health'),
            api.get('/cosmos/containers'),
            api.get('/agents'),
            api.get('/messages?limit=5')
        ]);

        // Process results
        const results = {
            systemHealth: systemHealth.status === 'fulfilled' ? systemHealth.value : null,
            containers: containers.status === 'fulfilled' ? containers.value : null,
            agents: agents.status === 'fulfilled' ? agents.value : null,
            messages: messages.status === 'fulfilled' ? messages.value : null
        };

        // Update UI with loaded data
        updateOverviewStats(results);
        
        // Hide loading skeleton
        hideLoadingSkeleton();

        // Determine overall system status
        const healthScore = results.systemHealth?.health_score || 0;
        if (healthScore > 80) {
            statusManager.setStatus('healthy', 'All systems operational');
        } else if (healthScore > 50) {
            statusManager.setStatus('warning', `Health score: ${healthScore}%`);
        } else {
            statusManager.setStatus('error', 'System requires attention');
        }

        showNotification('Dashboard data loaded successfully', 'success', 3000);

    } catch (error) {
        console.error('Failed to load dashboard data:', error);
        statusManager.setStatus('error', 'Failed to load data');
        showNotification('Failed to load dashboard data', 'error');
        hideLoadingSkeleton();
    }
}

function showLoadingSkeleton() {
    const statCards = document.querySelectorAll('.stat-value');
    statCards.forEach(card => {
        card.classList.add('skeleton-loading');
        card.textContent = '';
    });
}

function hideLoadingSkeleton() {
    const statCards = document.querySelectorAll('.stat-value');
    statCards.forEach(card => {
        card.classList.remove('skeleton-loading');
    });
}

function updateOverviewStats(data) {
    // Update system health
    if (data.systemHealth) {
        updateStatCard('system-health', `${data.systemHealth.health_score || 'N/A'}%`);
    }

    // Update containers count
    if (data.containers) {
        updateStatCard('total-containers', data.containers.containers?.length || 0);
    }

    // Update agents count
    if (data.agents) {
        updateStatCard('active-agents', data.agents.agents?.length || 0);
    }

    // Update documents count (placeholder)
    updateStatCard('total-documents', '0');
}

function updateStatCard(id, value) {
    const element = document.getElementById(id);
    if (element) {
        // Animate value change
        element.style.transform = 'scale(0.95)';
        setTimeout(() => {
            element.textContent = value;
            element.style.transform = 'scale(1)';
        }, 150);
    }
}

// Enhanced Navigation with Animation
function switchToTab(tabName) {
    if (AppState.currentTab === tabName) return;

    console.log(`Switching to tab: ${tabName}`);
    
    // Update navigation state
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    // Hide current tab content with animation
    const currentContent = document.querySelector('.tab-content.active');
    if (currentContent) {
        currentContent.style.opacity = '0';
        currentContent.style.transform = 'translateY(10px)';
        
        setTimeout(() => {
            currentContent.classList.remove('active');
            
            // Show new tab content with animation
            const newContent = document.getElementById(tabName);
            if (newContent) {
                newContent.classList.add('active');
                newContent.style.opacity = '0';
                newContent.style.transform = 'translateY(10px)';
                
                // Trigger reflow
                newContent.offsetHeight;
                
                newContent.style.opacity = '1';
                newContent.style.transform = 'translateY(0)';
            }
        }, CONFIG.ANIMATION_DURATION / 2);
    }

    // Update app state
    AppState.currentTab = tabName;

    // Load tab-specific data
    loadTabData(tabName);
}

async function loadTabData(tabName) {
    switch (tabName) {
        case 'overview':
            await loadDashboardData();
            break;
        case 'mailbox':
            await loadMailboxData();
            break;
        case 'cosmos':
            await loadCosmosData();
            break;
        case 'agents':
            await loadAgentsData();
            break;
        case 'graph':
            await loadGraphData();
            break;
        case 'manager':
            await loadManagerData();
            break;
        case 'workspace':
            await loadWorkspaceData();
            break;
        case 'research':
            await loadResearchData();
            break;
    }
}

// Enhanced Module Loading Functions
async function loadMailboxData() {
    try {
        const messages = await api.get('/messages');
        updateMailboxUI(messages);
    } catch (error) {
        console.error('Failed to load mailbox data:', error);
    }
}

async function loadCosmosData() {
    try {
        const containers = await api.get('/cosmos/containers');
        updateCosmosUI(containers);
    } catch (error) {
        console.error('Failed to load cosmos data:', error);
    }
}

async function loadAgentsData() {
    try {
        const agents = await api.get('/agents');
        updateAgentsUI(agents);
    } catch (error) {
        console.error('Failed to load agents data:', error);
    }
}

// Real-time Updates
function startRealTimeUpdates() {
    if (!AppState.realTimeUpdates) return;

    setInterval(async () => {
        // Only update if dashboard is visible
        if (document.visibilityState === 'visible') {
            try {
                // Light refresh of current tab data
                await loadTabData(AppState.currentTab);
            } catch (error) {
                console.warn('Real-time update failed:', error);
            }
        }
    }, CONFIG.REFRESH_INTERVAL);
}

// Enhanced Error Handling
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
    showNotification('An unexpected error occurred', 'error');
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    showNotification('A network error occurred', 'error');
});

// Professional Initialization
document.addEventListener('DOMContentLoaded', async function() {
    console.log('🚀 Professional Research & Analytics Dashboard Initializing...');
    
    // Set start time for uptime calculation
    AppState.performance.startTime = Date.now();
    
    try {
        // Initialize status
        statusManager.setStatus('loading', 'Initializing dashboard...');
        
        // Test API connectivity
        await api.get('/health');
        showNotification('Connected to backend successfully', 'success', 3000);
        
        // Setup navigation
        setupNavigation();
        
        // Load initial data
        await loadDashboardData();
        
        // Start real-time updates
        startRealTimeUpdates();
        
        // Initialize performance monitoring
        updatePerformanceIndicators();
        
        console.log('✅ Dashboard initialization complete');
        statusManager.setStatus('healthy', 'Dashboard ready');
        
    } catch (error) {
        console.error('❌ Dashboard initialization failed:', error);
        statusManager.setStatus('error', 'Initialization failed');
        showNotification('Failed to initialize dashboard', 'error');
    }
});

function setupNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const tab = this.dataset.tab;
            if (tab) {
                switchToTab(tab);
            }
        });
    });
}

// Placeholder update functions (to be implemented based on specific requirements)
function updateMailboxUI(data) {
    console.log('Updating mailbox UI with:', data);
}

function updateCosmosUI(data) {
    console.log('Updating cosmos UI with:', data);
}

function updateAgentsUI(data) {
    console.log('Updating agents UI with:', data);
}

async function loadGraphData() {
    console.log('Loading graph data...');
}

async function loadManagerData() {
    console.log('Loading manager data...');
}

async function loadWorkspaceData() {
    console.log('Loading workspace data...');
}

async function loadResearchData() {
    console.log('Loading research data...');
}

// Export for debugging
window.AppState = AppState;
window.api = api;
window.cache = cache;
window.statusManager = statusManager;