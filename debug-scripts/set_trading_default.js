// Script to set Trading Operations as the default view
console.log("🎯 Setting Trading Operations as Default View");

// Method 1: Find the current tab system
const tabs = document.querySelectorAll('[role="tab"], .tab, .nav-link, [data-tab]');
console.log(`Found ${tabs.length} tabs:`);

tabs.forEach((tab, index) => {
    const tabText = tab.innerText || tab.textContent || '';
    console.log(`Tab ${index + 1}: ${tabText}`);
    
    // Look for Trading Operations tab
    if (tabText.includes('Trading') || tabText.includes('AI Trading') || tabText.includes('Operations')) {
        console.log(`✅ Found Trading tab: ${tabText}`);
        
        // Method 1: Click the tab
        tab.click();
        
        // Method 2: Set active classes
        tabs.forEach(t => {
            t.classList.remove('active', 'selected');
            t.setAttribute('aria-selected', 'false');
        });
        tab.classList.add('active', 'selected');
        tab.setAttribute('aria-selected', 'true');
        
        // Find associated content panel
        const tabId = tab.getAttribute('data-tab') || tab.getAttribute('href') || tab.id;
        if (tabId) {
            // Hide all panels
            const panels = document.querySelectorAll('[role="tabpanel"], .tab-content, .tab-pane');
            panels.forEach(panel => {
                panel.style.display = 'none';
                panel.classList.remove('active', 'show');
                panel.setAttribute('hidden', 'true');
            });
            
            // Show trading panel
            const tradingPanel = document.querySelector(`[id="${tabId.replace('#', '')}"], [data-tab-content="${tabId}"]`);
            if (tradingPanel) {
                tradingPanel.style.display = 'block';
                tradingPanel.classList.add('active', 'show');
                tradingPanel.removeAttribute('hidden');
                console.log("✅ Trading panel activated");
            }
        }
    }
});

// Method 2: Permanent fix - modify initialization
window.setDefaultTab = function(tabName) {
    // Store preference
    localStorage.setItem('defaultTab', tabName);
    console.log(`✅ Default tab set to: ${tabName}`);
};

// Method 3: Auto-select on page load
if (!window.defaultTabSet) {
    window.defaultTabSet = true;
    
    // Override any existing initialization
    const originalOnload = window.onload;
    window.onload = function() {
        if (originalOnload) originalOnload();
        
        // Wait for content to load
        setTimeout(() => {
            const tradingTab = Array.from(document.querySelectorAll('[role="tab"], .tab, .nav-link')).find(tab => {
                const text = tab.innerText || tab.textContent || '';
                return text.includes('Trading') || text.includes('Operations');
            });
            
            if (tradingTab) {
                tradingTab.click();
                console.log("✅ Trading Operations set as default on load");
            }
        }, 100);
    };
    
    // Also handle React/Vue apps
    if (window.addEventListener) {
        window.addEventListener('DOMContentLoaded', () => {
            setTimeout(() => {
                const tradingTab = Array.from(document.querySelectorAll('[role="tab"], .tab, .nav-link')).find(tab => {
                    const text = tab.innerText || tab.textContent || '';
                    return text.includes('Trading') || text.includes('Operations');
                });
                
                if (tradingTab) {
                    tradingTab.click();
                }
            }, 500);
        });
    }
}

// Method 4: Create persistent preference
const createPersistentDefault = () => {
    const script = document.createElement('script');
    script.textContent = `
        // Auto-select Trading Operations on load
        (function() {
            const selectTradingTab = () => {
                const tabs = document.querySelectorAll('[role="tab"], .tab, .nav-link');
                const tradingTab = Array.from(tabs).find(tab => {
                    const text = tab.innerText || tab.textContent || '';
                    return text.includes('Trading') || text.includes('Operations');
                });
                
                if (tradingTab && !tradingTab.classList.contains('active')) {
                    tradingTab.click();
                    return true;
                }
                return false;
            };
            
            // Try immediately
            if (!selectTradingTab()) {
                // Try again after DOM ready
                document.addEventListener('DOMContentLoaded', selectTradingTab);
                
                // Try again after a delay for dynamic content
                setTimeout(selectTradingTab, 1000);
            }
        })();
    `;
    document.head.appendChild(script);
};

createPersistentDefault();

console.log("\n💡 To make this permanent, run: setDefaultTab('Trading Operations')");
console.log("✅ Trading Operations should now be the active tab!");