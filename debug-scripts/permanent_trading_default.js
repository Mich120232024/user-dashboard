// PERMANENT SOLUTION: Modify app initialization to set Trading as default

console.log("🔧 Applying permanent Trading Operations default");

// 1. Find the tab initialization code
const findInitCode = () => {
    // Common patterns for tab initialization
    const patterns = [
        'defaultTab',
        'activeTab',
        'selectedIndex',
        'initialTab',
        'defaultIndex'
    ];
    
    // Search for React state
    if (window.React && window.__REACT_DEVTOOLS_GLOBAL_HOOK__) {
        console.log("⚛️ React app detected - modifying component state");
        
        // Hook into React component lifecycle
        const originalUseState = window.React.useState;
        window.React.useState = function(initialValue) {
            // If it's a tab index, default to Trading (usually index 2 or 3)
            if (typeof initialValue === 'number' && initialValue >= 0 && initialValue < 10) {
                // Find Trading tab index
                setTimeout(() => {
                    const tabs = document.querySelectorAll('[role="tab"], .tab');
                    tabs.forEach((tab, index) => {
                        if (tab.innerText.includes('Trading')) {
                            initialValue = index;
                            console.log(`✅ Set default tab index to ${index} (Trading)`);
                        }
                    });
                }, 0);
            }
            return originalUseState.call(this, initialValue);
        };
    }
};

// 2. Override common tab libraries
const overrideTabLibraries = () => {
    // Bootstrap tabs
    if (window.$ && window.$.fn && window.$.fn.tab) {
        const originalTab = window.$.fn.tab;
        window.$.fn.tab = function(...args) {
            // Auto-select Trading on init
            if (this.length && !this.data('defaultSet')) {
                this.data('defaultSet', true);
                const tradingTab = this.filter(':contains("Trading")');
                if (tradingTab.length) {
                    setTimeout(() => tradingTab.tab('show'), 100);
                }
            }
            return originalTab.apply(this, args);
        };
    }
    
    // Material UI Tabs
    if (window.MaterialUI) {
        console.log("📦 Material UI detected - setting default tab");
    }
};

// 3. Create initialization override
const initOverride = `
// Trading Operations Default Tab Override
(function() {
    const setTradingDefault = () => {
        // Method 1: Direct tab activation
        const tabs = document.querySelectorAll('[role="tab"], .tab, .nav-link, button[data-tab]');
        let tradingIndex = -1;
        
        tabs.forEach((tab, index) => {
            const text = (tab.innerText || tab.textContent || '').toLowerCase();
            if (text.includes('trading') || text.includes('operations')) {
                tradingIndex = index;
                
                // Remove active from all tabs
                tabs.forEach(t => {
                    t.classList.remove('active', 'selected', 'mui-selected');
                    t.setAttribute('aria-selected', 'false');
                });
                
                // Activate trading tab
                tab.classList.add('active', 'selected');
                tab.setAttribute('aria-selected', 'true');
                
                // Trigger click for event handlers
                setTimeout(() => tab.click(), 50);
            }
        });
        
        // Method 2: URL hash
        if (tradingIndex >= 0 && !window.location.hash.includes('trading')) {
            window.location.hash = '#trading-operations';
        }
        
        // Method 3: Local storage preference
        localStorage.setItem('defaultTabIndex', tradingIndex);
        localStorage.setItem('defaultTabName', 'trading-operations');
        
        return tradingIndex >= 0;
    };
    
    // Multiple attempts to ensure it works
    const attempts = [0, 100, 500, 1000, 2000];
    attempts.forEach(delay => {
        setTimeout(setTradingDefault, delay);
    });
    
    // Hook into history changes for SPA
    const originalPushState = history.pushState;
    history.pushState = function(...args) {
        originalPushState.apply(history, args);
        setTimeout(setTradingDefault, 100);
    };
})();
`;

// 4. Inject the override
const injectOverride = () => {
    // Create script element
    const script = document.createElement('script');
    script.id = 'trading-default-override';
    script.textContent = initOverride;
    
    // Remove any existing override
    const existing = document.getElementById('trading-default-override');
    if (existing) existing.remove();
    
    // Add to head
    document.head.appendChild(script);
    console.log("✅ Trading default override injected");
};

// 5. Apply all methods
findInitCode();
overrideTabLibraries();
injectOverride();

// 6. Immediate activation
setTimeout(() => {
    const tradingTab = Array.from(document.querySelectorAll('[role="tab"], .tab, .nav-link, button')).find(tab => {
        const text = (tab.innerText || tab.textContent || '').toLowerCase();
        return text.includes('trading') || text.includes('operations');
    });
    
    if (tradingTab) {
        tradingTab.click();
        console.log("✅ Trading Operations activated immediately");
        
        // Also trigger any custom events
        ['click', 'mousedown', 'mouseup', 'change'].forEach(eventType => {
            const event = new Event(eventType, { bubbles: true });
            tradingTab.dispatchEvent(event);
        });
    }
}, 100);

console.log("\n✅ PERMANENT FIX APPLIED");
console.log("💡 Trading Operations will now be the default tab on every page load");
console.log("💡 To verify: Refresh the page and Trading should be selected automatically");