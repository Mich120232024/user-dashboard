/**
 * Enterprise Professional Dashboard
 * Implementing modern JavaScript patterns and enterprise UI design principles
 * Following WCAG 2.2 accessibility standards and professional UX patterns
 */

// ===============================
// ENTERPRISE DESIGN SYSTEM CORE
// ===============================

/**
 * Design System Constants
 * Following enterprise design principles: Simplicity, Consistency, Accessibility, Scalability
 */
const DESIGN_SYSTEM = {
    // Animation timing for professional feel
    TIMING: {
        FAST: 150,
        NORMAL: 300,
        SLOW: 500,
        EXTRA_SLOW: 700
    },
    
    // Loading states for better UX
    LOADING_STATES: {
        IDLE: 'idle',
        LOADING: 'loading',
        SUCCESS: 'success',
        ERROR: 'error'
    },
    
    // Z-index layers for proper stacking
    Z_INDEX: {
        BASE: 1,
        DROPDOWN: 100,
        STICKY: 200,
        MODAL_BACKDROP: 1000,
        MODAL: 1001,
        TOOLTIP: 1002,
        NOTIFICATION: 1003
    },
    
    // WCAG 2.2 compliant focus management
    FOCUS: {
        VISIBLE_OUTLINE: '2px solid #3b82f6',
        VISIBLE_OFFSET: '2px'
    }
};

/**
 * Professional State Management
 * Implementing Observer pattern for reactive state
 */
class StateManager {
    constructor() {
        this.state = new Proxy({}, {
            set: (target, property, value) => {
                const oldValue = target[property];
                target[property] = value;
                this.notify(property, value, oldValue);
                return true;
            }
        });
        this.observers = new Map();
    }
    
    subscribe(property, callback) {
        if (!this.observers.has(property)) {
            this.observers.set(property, new Set());
        }
        this.observers.get(property).add(callback);
        
        // Return unsubscribe function
        return () => {
            const callbacks = this.observers.get(property);
            if (callbacks) {
                callbacks.delete(callback);
            }
        };
    }
    
    notify(property, newValue, oldValue) {
        const callbacks = this.observers.get(property);
        if (callbacks) {
            callbacks.forEach(callback => {
                try {
                    callback(newValue, oldValue);
                } catch (error) {
                    console.error(`Error in state observer for ${property}:`, error);
                }
            });
        }
    }
    
    setState(updates) {
        Object.entries(updates).forEach(([key, value]) => {
            this.state[key] = value;
        });
    }
    
    getState(property) {
        return property ? this.state[property] : this.state;
    }
}

/**
 * Professional Component Base Class
 * Implementing modern component architecture patterns
 */
class BaseComponent {
    constructor(element, options = {}) {
        this.element = element;
        this.options = { ...this.getDefaultOptions(), ...options };
        this.state = new StateManager();
        this.subscriptions = [];
        this.isDestroyed = false;
        
        this.init();
    }
    
    getDefaultOptions() {
        return {
            autoInit: true,
            accessible: true,
            animations: true
        };
    }
    
    init() {
        if (this.options.autoInit) {
            this.render();
            this.bindEvents();
            if (this.options.accessible) {
                this.setupAccessibility();
            }
        }
    }
    
    render() {
        // Override in subclasses
    }
    
    bindEvents() {
        // Override in subclasses
    }
    
    setupAccessibility() {
        // WCAG 2.2 compliance
        if (!this.element.hasAttribute('role')) {
            this.element.setAttribute('role', this.getDefaultRole());
        }
        
        // Focus management
        if (this.isFocusable()) {
            this.element.setAttribute('tabindex', '0');
            this.setupFocusHandling();
        }
    }
    
    getDefaultRole() {
        return 'generic';
    }
    
    isFocusable() {
        return false;
    }
    
    setupFocusHandling() {
        this.element.addEventListener('focus', (e) => {
            this.element.style.outline = DESIGN_SYSTEM.FOCUS.VISIBLE_OUTLINE;
            this.element.style.outlineOffset = DESIGN_SYSTEM.FOCUS.VISIBLE_OFFSET;
        });
        
        this.element.addEventListener('blur', (e) => {
            this.element.style.outline = '';
            this.element.style.outlineOffset = '';
        });
    }
    
    setState(updates) {
        this.state.setState(updates);
    }
    
    getState(property) {
        return this.state.getState(property);
    }
    
    subscribe(property, callback) {
        const unsubscribe = this.state.subscribe(property, callback);
        this.subscriptions.push(unsubscribe);
        return unsubscribe;
    }
    
    destroy() {
        this.subscriptions.forEach(unsubscribe => unsubscribe());
        this.subscriptions = [];
        this.isDestroyed = true;
    }
}

/**
 * Professional Loading Component
 * Implements proper loading states and skeleton screens
 */
class LoadingComponent extends BaseComponent {
    getDefaultOptions() {
        return {
            ...super.getDefaultOptions(),
            type: 'spinner', // spinner, skeleton, progress
            size: 'medium', // small, medium, large
            text: 'Loading...'
        };
    }
    
    render() {
        this.element.className = `loading loading--${this.options.type} loading--${this.options.size}`;
        this.element.setAttribute('aria-live', 'polite');
        this.element.setAttribute('aria-label', this.options.text);
        
        if (this.options.type === 'spinner') {
            this.renderSpinner();
        } else if (this.options.type === 'skeleton') {
            this.renderSkeleton();
        } else if (this.options.type === 'progress') {
            this.renderProgress();
        }
    }
    
    renderSpinner() {
        this.element.innerHTML = `
            <div class="spinner" aria-hidden="true">
                <div class="spinner__circle"></div>
            </div>
            <span class="loading__text">${this.options.text}</span>
        `;
    }
    
    renderSkeleton() {
        this.element.innerHTML = `
            <div class="skeleton" aria-hidden="true">
                <div class="skeleton__line skeleton__line--title"></div>
                <div class="skeleton__line skeleton__line--text"></div>
                <div class="skeleton__line skeleton__line--text skeleton__line--short"></div>
            </div>
        `;
    }
    
    renderProgress() {
        this.element.innerHTML = `
            <div class="progress" role="progressbar" aria-valuemin="0" aria-valuemax="100">
                <div class="progress__bar"></div>
            </div>
            <span class="loading__text">${this.options.text}</span>
        `;
    }
    
    updateProgress(value) {
        if (this.options.type === 'progress') {
            const progressBar = this.element.querySelector('.progress__bar');
            const progressContainer = this.element.querySelector('.progress');
            if (progressBar && progressContainer) {
                progressBar.style.width = `${Math.min(100, Math.max(0, value))}%`;
                progressContainer.setAttribute('aria-valuenow', value);
            }
        }
    }
}

/**
 * Professional Card Component
 * Implements enterprise card patterns with proper interaction states
 */
class CardComponent extends BaseComponent {
    getDefaultOptions() {
        return {
            ...super.getDefaultOptions(),
            interactive: false,
            elevation: 'medium', // low, medium, high
            padding: 'medium' // small, medium, large
        };
    }
    
    getDefaultRole() {
        return this.options.interactive ? 'button' : 'article';
    }
    
    isFocusable() {
        return this.options.interactive;
    }
    
    render() {
        this.element.className = `card card--${this.options.elevation} card--padding-${this.options.padding}`;
        
        if (this.options.interactive) {
            this.element.classList.add('card--interactive');
        }
    }
    
    bindEvents() {
        if (this.options.interactive) {
            // Professional hover and focus states
            this.element.addEventListener('mouseenter', () => {
                this.element.classList.add('card--hover');
            });
            
            this.element.addEventListener('mouseleave', () => {
                this.element.classList.remove('card--hover');
            });
            
            // Keyboard interaction
            this.element.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.element.click();
                }
            });
        }
    }
}

/**
 * Professional Tab Component
 * Implements WCAG compliant tab navigation
 */
class TabComponent extends BaseComponent {
    getDefaultOptions() {
        return {
            ...super.getDefaultOptions(),
            defaultTab: 0,
            orientation: 'horizontal' // horizontal, vertical
        };
    }
    
    init() {
        this.tabButtons = this.element.querySelectorAll('[role="tab"]');
        this.tabPanels = this.element.querySelectorAll('[role="tabpanel"]');
        this.currentTab = this.options.defaultTab;
        
        super.init();
    }
    
    render() {
        this.setupTabList();
        this.activateTab(this.currentTab);
    }
    
    setupTabList() {
        const tabList = this.element.querySelector('[role="tablist"]');
        if (tabList) {
            tabList.setAttribute('aria-orientation', this.options.orientation);
        }
        
        this.tabButtons.forEach((tab, index) => {
            tab.setAttribute('tabindex', index === this.currentTab ? '0' : '-1');
            tab.setAttribute('aria-selected', index === this.currentTab ? 'true' : 'false');
        });
        
        this.tabPanels.forEach((panel, index) => {
            panel.setAttribute('hidden', index !== this.currentTab);
        });
    }
    
    bindEvents() {
        this.tabButtons.forEach((tab, index) => {
            tab.addEventListener('click', () => {
                this.activateTab(index);
            });
            
            tab.addEventListener('keydown', (e) => {
                this.handleTabKeydown(e, index);
            });
        });
    }
    
    handleTabKeydown(e, currentIndex) {
        let newIndex = currentIndex;
        
        if (this.options.orientation === 'horizontal') {
            if (e.key === 'ArrowLeft') {
                newIndex = currentIndex > 0 ? currentIndex - 1 : this.tabButtons.length - 1;
            } else if (e.key === 'ArrowRight') {
                newIndex = currentIndex < this.tabButtons.length - 1 ? currentIndex + 1 : 0;
            }
        } else {
            if (e.key === 'ArrowUp') {
                newIndex = currentIndex > 0 ? currentIndex - 1 : this.tabButtons.length - 1;
            } else if (e.key === 'ArrowDown') {
                newIndex = currentIndex < this.tabButtons.length - 1 ? currentIndex + 1 : 0;
            }
        }
        
        if (e.key === 'Home') {
            newIndex = 0;
        } else if (e.key === 'End') {
            newIndex = this.tabButtons.length - 1;
        }
        
        if (newIndex !== currentIndex) {
            e.preventDefault();
            this.activateTab(newIndex);
            this.tabButtons[newIndex].focus();
        }
    }
    
    activateTab(index) {
        // Deactivate all tabs
        this.tabButtons.forEach((tab, i) => {
            tab.setAttribute('tabindex', '-1');
            tab.setAttribute('aria-selected', 'false');
            tab.classList.remove('tab--active');
        });
        
        this.tabPanels.forEach((panel, i) => {
            panel.setAttribute('hidden', '');
            panel.classList.remove('tab-panel--active');
        });
        
        // Activate selected tab
        if (this.tabButtons[index] && this.tabPanels[index]) {
            this.tabButtons[index].setAttribute('tabindex', '0');
            this.tabButtons[index].setAttribute('aria-selected', 'true');
            this.tabButtons[index].classList.add('tab--active');
            
            this.tabPanels[index].removeAttribute('hidden');
            this.tabPanels[index].classList.add('tab-panel--active');
            
            this.currentTab = index;
            
            // Trigger custom event
            this.element.dispatchEvent(new CustomEvent('tabchange', {
                detail: { activeTab: index, activePanel: this.tabPanels[index] }
            }));
        }
    }
    
    getDefaultRole() {
        return 'tablist';
    }
}

/**
 * Professional Data Table Component
 * Implements enterprise data table patterns with sorting, filtering, pagination
 */
class DataTableComponent extends BaseComponent {
    getDefaultOptions() {
        return {
            ...super.getDefaultOptions(),
            sortable: true,
            filterable: true,
            pageable: true,
            pageSize: 10,
            data: [],
            columns: []
        };
    }
    
    init() {
        this.filteredData = [...this.options.data];
        this.currentPage = 0;
        this.sortColumn = null;
        this.sortDirection = 'asc';
        
        super.init();
    }
    
    render() {
        this.element.className = 'data-table';
        this.element.innerHTML = `
            ${this.options.filterable ? this.renderFilters() : ''}
            <div class="data-table__container">
                <table class="data-table__table" role="table">
                    ${this.renderHeader()}
                    ${this.renderBody()}
                </table>
            </div>
            ${this.options.pageable ? this.renderPagination() : ''}
        `;
    }
    
    renderFilters() {
        return `
            <div class="data-table__filters">
                <div class="search-container">
                    <label for="table-search" class="sr-only">Search table</label>
                    <input type="search" id="table-search" class="search-input" 
                           placeholder="Search..." aria-label="Search table data">
                    <span class="search-icon" aria-hidden="true">🔍</span>
                </div>
            </div>
        `;
    }
    
    renderHeader() {
        return `
            <thead class="data-table__header">
                <tr role="row">
                    ${this.options.columns.map(col => `
                        <th role="columnheader" 
                            ${this.options.sortable ? 'tabindex="0"' : ''}
                            ${this.options.sortable ? `aria-sort="${this.getSortState(col.key)}"` : ''}
                            data-column="${col.key}">
                            <div class="data-table__header-content">
                                <span>${col.label}</span>
                                ${this.options.sortable ? '<span class="sort-indicator" aria-hidden="true"></span>' : ''}
                            </div>
                        </th>
                    `).join('')}
                </tr>
            </thead>
        `;
    }
    
    renderBody() {
        const startIndex = this.currentPage * this.options.pageSize;
        const endIndex = startIndex + this.options.pageSize;
        const pageData = this.filteredData.slice(startIndex, endIndex);
        
        return `
            <tbody class="data-table__body">
                ${pageData.map((row, index) => `
                    <tr role="row" ${index % 2 === 0 ? 'aria-rowindex="even"' : 'aria-rowindex="odd"'}>
                        ${this.options.columns.map(col => `
                            <td role="gridcell">${this.formatCellValue(row[col.key], col)}</td>
                        `).join('')}
                    </tr>
                `).join('')}
            </tbody>
        `;
    }
    
    renderPagination() {
        const totalPages = Math.ceil(this.filteredData.length / this.options.pageSize);
        
        return `
            <div class="data-table__pagination" role="navigation" aria-label="Table pagination">
                <div class="pagination-info">
                    Showing ${this.currentPage * this.options.pageSize + 1} to 
                    ${Math.min((this.currentPage + 1) * this.options.pageSize, this.filteredData.length)} 
                    of ${this.filteredData.length} entries
                </div>
                <div class="pagination-controls">
                    <button class="btn btn--pagination" 
                            ${this.currentPage === 0 ? 'disabled' : ''} 
                            data-page="prev" aria-label="Previous page">
                        Previous
                    </button>
                    <span class="pagination-numbers">
                        Page ${this.currentPage + 1} of ${totalPages}
                    </span>
                    <button class="btn btn--pagination" 
                            ${this.currentPage >= totalPages - 1 ? 'disabled' : ''} 
                            data-page="next" aria-label="Next page">
                        Next
                    </button>
                </div>
            </div>
        `;
    }
    
    bindEvents() {
        // Search functionality
        const searchInput = this.element.querySelector('#table-search');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce((e) => {
                this.filterData(e.target.value);
            }, 300));
        }
        
        // Sorting functionality
        if (this.options.sortable) {
            this.element.addEventListener('click', (e) => {
                const header = e.target.closest('[role="columnheader"]');
                if (header && header.dataset.column) {
                    this.sortData(header.dataset.column);
                }
            });
            
            // Keyboard sorting
            this.element.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    const header = e.target.closest('[role="columnheader"]');
                    if (header && header.dataset.column) {
                        e.preventDefault();
                        this.sortData(header.dataset.column);
                    }
                }
            });
        }
        
        // Pagination
        if (this.options.pageable) {
            this.element.addEventListener('click', (e) => {
                const pageBtn = e.target.closest('[data-page]');
                if (pageBtn && !pageBtn.disabled) {
                    const page = pageBtn.dataset.page;
                    if (page === 'prev') {
                        this.goToPage(this.currentPage - 1);
                    } else if (page === 'next') {
                        this.goToPage(this.currentPage + 1);
                    }
                }
            });
        }
    }
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    filterData(searchTerm) {
        if (!searchTerm.trim()) {
            this.filteredData = [...this.options.data];
        } else {
            this.filteredData = this.options.data.filter(row => {
                return this.options.columns.some(col => {
                    const value = row[col.key];
                    return value && value.toString().toLowerCase().includes(searchTerm.toLowerCase());
                });
            });
        }
        
        this.currentPage = 0;
        this.updateTable();
    }
    
    sortData(columnKey) {
        if (this.sortColumn === columnKey) {
            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortColumn = columnKey;
            this.sortDirection = 'asc';
        }
        
        this.filteredData.sort((a, b) => {
            const aVal = a[columnKey];
            const bVal = b[columnKey];
            
            if (aVal < bVal) return this.sortDirection === 'asc' ? -1 : 1;
            if (aVal > bVal) return this.sortDirection === 'asc' ? 1 : -1;
            return 0;
        });
        
        this.updateTable();
    }
    
    goToPage(page) {
        const totalPages = Math.ceil(this.filteredData.length / this.options.pageSize);
        if (page >= 0 && page < totalPages) {
            this.currentPage = page;
            this.updateTable();
        }
    }
    
    updateTable() {
        const tableContainer = this.element.querySelector('.data-table__container');
        const paginationContainer = this.element.querySelector('.data-table__pagination');
        
        if (tableContainer) {
            tableContainer.innerHTML = `
                <table class="data-table__table" role="table">
                    ${this.renderHeader()}
                    ${this.renderBody()}
                </table>
            `;
        }
        
        if (paginationContainer) {
            paginationContainer.outerHTML = this.renderPagination();
        }
    }
    
    getSortState(columnKey) {
        if (this.sortColumn === columnKey) {
            return this.sortDirection === 'asc' ? 'ascending' : 'descending';
        }
        return 'none';
    }
    
    formatCellValue(value, column) {
        if (column.formatter && typeof column.formatter === 'function') {
            return column.formatter(value);
        }
        return value || '';
    }
    
    getDefaultRole() {
        return 'grid';
    }
}

/**
 * Professional Notification System
 * Implements enterprise notification patterns with accessibility
 */
class NotificationManager {
    constructor() {
        this.notifications = [];
        this.container = null;
        this.maxNotifications = 5;
        this.defaultDuration = 5000;
        
        this.init();
    }
    
    init() {
        this.createContainer();
    }
    
    createContainer() {
        this.container = document.createElement('div');
        this.container.className = 'notifications-container';
        this.container.setAttribute('aria-live', 'polite');
        this.container.setAttribute('aria-label', 'Notifications');
        this.container.style.cssText = `
            position: fixed;
            top: 1rem;
            right: 1rem;
            z-index: ${DESIGN_SYSTEM.Z_INDEX.NOTIFICATION};
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            max-width: 400px;
            pointer-events: none;
        `;
        document.body.appendChild(this.container);
    }
    
    show(message, type = 'info', options = {}) {
        const notification = {
            id: Date.now() + Math.random(),
            message,
            type,
            duration: options.duration || this.defaultDuration,
            persistent: options.persistent || false,
            actions: options.actions || []
        };
        
        this.notifications.push(notification);
        
        // Limit max notifications
        if (this.notifications.length > this.maxNotifications) {
            const oldest = this.notifications.shift();
            this.removeNotificationElement(oldest.id);
        }
        
        this.renderNotification(notification);
        
        // Auto-remove non-persistent notifications
        if (!notification.persistent && notification.duration > 0) {
            setTimeout(() => {
                this.remove(notification.id);
            }, notification.duration);
        }
        
        return notification.id;
    }
    
    renderNotification(notification) {
        const element = document.createElement('div');
        element.className = `notification notification--${notification.type}`;
        element.setAttribute('role', 'alert');
        element.setAttribute('data-notification-id', notification.id);
        element.style.cssText = `
            pointer-events: auto;
            transform: translateX(100%);
            opacity: 0;
            transition: all ${DESIGN_SYSTEM.TIMING.NORMAL}ms ease-out;
        `;
        
        element.innerHTML = `
            <div class="notification__content">
                <div class="notification__icon" aria-hidden="true">
                    ${this.getNotificationIcon(notification.type)}
                </div>
                <div class="notification__message">${notification.message}</div>
                ${notification.actions.length > 0 ? this.renderActions(notification.actions) : ''}
                <button class="notification__close" aria-label="Close notification" type="button">
                    ×
                </button>
            </div>
        `;
        
        // Bind close event
        const closeBtn = element.querySelector('.notification__close');
        closeBtn.addEventListener('click', () => {
            this.remove(notification.id);
        });
        
        // Bind action events
        notification.actions.forEach((action, index) => {
            const actionBtn = element.querySelector(`[data-action="${index}"]`);
            if (actionBtn) {
                actionBtn.addEventListener('click', () => {
                    if (action.handler) {
                        action.handler();
                    }
                    if (action.dismissOnClick !== false) {
                        this.remove(notification.id);
                    }
                });
            }
        });
        
        this.container.appendChild(element);
        
        // Trigger animation
        requestAnimationFrame(() => {
            element.style.transform = 'translateX(0)';
            element.style.opacity = '1';
        });
    }
    
    renderActions(actions) {
        return `
            <div class="notification__actions">
                ${actions.map((action, index) => `
                    <button class="btn btn--small btn--${action.type || 'secondary'}" 
                            data-action="${index}" type="button">
                        ${action.label}
                    </button>
                `).join('')}
            </div>
        `;
    }
    
    getNotificationIcon(type) {
        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };
        return icons[type] || icons.info;
    }
    
    remove(id) {
        const notification = this.notifications.find(n => n.id === id);
        if (notification) {
            this.notifications = this.notifications.filter(n => n.id !== id);
            this.removeNotificationElement(id);
        }
    }
    
    removeNotificationElement(id) {
        const element = this.container.querySelector(`[data-notification-id="${id}"]`);
        if (element) {
            element.style.transform = 'translateX(100%)';
            element.style.opacity = '0';
            
            setTimeout(() => {
                if (element.parentNode) {
                    element.parentNode.removeChild(element);
                }
            }, DESIGN_SYSTEM.TIMING.NORMAL);
        }
    }
    
    clear() {
        this.notifications = [];
        this.container.innerHTML = '';
    }
}

// ===============================
// DASHBOARD APPLICATION CORE
// ===============================

/**
 * Professional Dashboard Application
 * Implements enterprise architecture patterns
 */
class DashboardApplication {
    constructor() {
        this.state = new StateManager();
        this.components = new Map();
        this.api = new APIClient();
        this.notifications = new NotificationManager();
        
        this.init();
    }
    
    async init() {
        try {
            // Initialize application state
            this.state.setState({
                currentTab: 'overview',
                loading: false,
                error: null,
                data: {},
                user: null
            });
            
            // Setup global event listeners
            this.setupGlobalEvents();
            
            // Initialize components
            await this.initializeComponents();
            
            // Load initial data
            await this.loadInitialData();
            
            this.notifications.show('Dashboard loaded successfully', 'success');
            
        } catch (error) {
            console.error('Failed to initialize dashboard:', error);
            this.notifications.show('Failed to initialize dashboard', 'error');
        }
    }
    
    setupGlobalEvents() {
        // Global error handling
        window.addEventListener('error', (e) => {
            console.error('Global error:', e.error);
            this.notifications.show('An unexpected error occurred', 'error');
        });
        
        // Handle unhandled promise rejections
        window.addEventListener('unhandledrejection', (e) => {
            console.error('Unhandled promise rejection:', e.reason);
            this.notifications.show('A network error occurred', 'error');
        });
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            this.handleGlobalKeydown(e);
        });
    }
    
    handleGlobalKeydown(e) {
        // Escape key handling
        if (e.key === 'Escape') {
            this.closeModals();
        }
        
        // Tab navigation improvements
        if (e.key === 'Tab') {
            this.handleTabNavigation(e);
        }
    }
    
    closeModals() {
        const modals = document.querySelectorAll('.modal:not([hidden])');
        modals.forEach(modal => {
            modal.style.display = 'none';
        });
    }
    
    handleTabNavigation(e) {
        // Enhanced tab navigation for better accessibility
        const focusableElements = document.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        
        if (e.shiftKey) {
            if (document.activeElement === firstElement) {
                lastElement.focus();
                e.preventDefault();
            }
        } else {
            if (document.activeElement === lastElement) {
                firstElement.focus();
                e.preventDefault();
            }
        }
    }
    
    async initializeComponents() {
        // Initialize tab navigation
        const tabContainer = document.querySelector('.nav');
        if (tabContainer) {
            this.components.set('tabs', new TabComponent(tabContainer, {
                defaultTab: 0
            }));
        }
        
        // Initialize cards
        document.querySelectorAll('.stat-card').forEach((card, index) => {
            this.components.set(`card-${index}`, new CardComponent(card, {
                interactive: true,
                elevation: 'medium'
            }));
        });
        
        // Initialize data tables
        document.querySelectorAll('.data-table').forEach((table, index) => {
            this.components.set(`table-${index}`, new DataTableComponent(table, {
                sortable: true,
                filterable: true,
                pageable: true,
                data: [],
                columns: []
            }));
        });
    }
    
    async loadInitialData() {
        this.state.setState({ loading: true });
        
        try {
            // Load dashboard data
            const [systemHealth, containers, agents] = await Promise.allSettled([
                this.api.get('/live/system-health'),
                this.api.get('/cosmos/containers'),
                this.api.get('/agents')
            ]);
            
            // Update state with loaded data
            this.state.setState({
                loading: false,
                data: {
                    systemHealth: systemHealth.status === 'fulfilled' ? systemHealth.value : null,
                    containers: containers.status === 'fulfilled' ? containers.value : null,
                    agents: agents.status === 'fulfilled' ? agents.value : null
                }
            });
            
            // Update UI
            this.updateDashboardStats();
            
        } catch (error) {
            this.state.setState({ loading: false, error: error.message });
            throw error;
        }
    }
    
    updateDashboardStats() {
        const data = this.state.getState('data');
        
        if (data.systemHealth?.health) {
            this.updateStatCard('system-health', `${data.systemHealth.health.overall_status || 'Unknown'}`);
        }
        
        if (data.containers?.containers) {
            this.updateStatCard('total-containers', data.containers.containers.length);
        }
        
        if (data.agents?.agents) {
            this.updateStatCard('active-agents', data.agents.agents.length);
        }
        
        // Update documents count (placeholder)
        this.updateStatCard('total-documents', '0');
    }
    
    updateStatCard(id, value) {
        const element = document.getElementById(id);
        if (element) {
            // Professional animation for value updates
            element.style.transform = 'scale(0.95)';
            element.style.opacity = '0.7';
            
            setTimeout(() => {
                element.textContent = value;
                element.style.transform = 'scale(1)';
                element.style.opacity = '1';
            }, DESIGN_SYSTEM.TIMING.FAST);
        }
    }
}

/**
 * Professional API Client
 * Implements modern fetch patterns with error handling
 */
class APIClient {
    constructor(baseURL = 'http://localhost:8001/api/v1') {
        this.baseURL = baseURL;
        this.defaultHeaders = {
            'Content-Type': 'application/json'
        };
    }
    
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: { ...this.defaultHeaders, ...options.headers },
            ...options
        };
        
        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
            
        } catch (error) {
            console.error(`API request failed: ${endpoint}`, error);
            throw error;
        }
    }
    
    get(endpoint, headers = {}) {
        return this.request(endpoint, { method: 'GET', headers });
    }
    
    post(endpoint, data, headers = {}) {
        return this.request(endpoint, {
            method: 'POST',
            headers,
            body: JSON.stringify(data)
        });
    }
    
    put(endpoint, data, headers = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            headers,
            body: JSON.stringify(data)
        });
    }
    
    delete(endpoint, headers = {}) {
        return this.request(endpoint, { method: 'DELETE', headers });
    }
}

// ===============================
// APPLICATION INITIALIZATION
// ===============================

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Initializing Professional Enterprise Dashboard...');
    window.dashboard = new DashboardApplication();
    
    // Initialize tab navigation
    initializeTabNavigation();
});

// Tab Navigation System
function initializeTabNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const tabContents = document.querySelectorAll('.tab-content');
    
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const targetTab = item.getAttribute('data-tab');
            
            // Update nav items
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
            
            // Update tab content
            tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === targetTab) {
                    content.classList.add('active');
                }
            });
            
            // Update state
            if (window.dashboard) {
                window.dashboard.state.setState({ currentTab: targetTab });
            }
        });
    });
}

// Export for debugging
window.DESIGN_SYSTEM = DESIGN_SYSTEM;
window.BaseComponent = BaseComponent;
window.StateManager = StateManager;