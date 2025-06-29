// Set BOTH Trading Operations AND NextGen as defaults
console.log("🎯 Setting Trading Operations + NextGen as Defaults");

// PART 1: Set NextGen as default in dropdown/selector
const setNextGenDefault = () => {
    console.log("\n📱 Setting NextGen as default software...");
    
    // Find all dropdowns/selectors
    const selectors = document.querySelectorAll('select, .dropdown, [role="combobox"], .custom-select');
    
    selectors.forEach((selector, index) => {
        // Check if this is the software/app selector
        const options = selector.querySelectorAll('option, .dropdown-item, [role="option"]');
        let foundNextGen = false;
        
        options.forEach(option => {
            const text = (option.innerText || option.textContent || option.value || '').toLowerCase();
            
            // Look for NextGen, Next Gen, or similar
            if (text.includes('nextgen') || text.includes('next gen') || text === 'pms nextgen') {
                console.log(`✅ Found NextGen option: "${option.innerText}"`);
                
                // Set as selected
                if (selector.tagName === 'SELECT') {
                    selector.value = option.value;
                    option.selected = true;
                } else {
                    // Custom dropdown
                    option.click();
                }
                
                // Trigger change event
                const changeEvent = new Event('change', { bubbles: true });
                selector.dispatchEvent(changeEvent);
                
                foundNextGen = true;
            }
        });
        
        if (foundNextGen) {
            console.log(`✅ NextGen set as default in selector ${index + 1}`);
            
            // Save preference
            localStorage.setItem('defaultSoftware', 'nextgen');
            localStorage.setItem('defaultApp', 'PMS NextGen');
        }
    });
    
    // Also check for custom dropdowns with divs
    const customDropdowns = document.querySelectorAll('.dropdown-toggle, .select-value, .selected-option');
    customDropdowns.forEach(dropdown => {
        const text = dropdown.innerText || dropdown.textContent || '';
        if (!text.toLowerCase().includes('nextgen')) {
            // Find NextGen option in siblings or children
            const parent = dropdown.closest('.dropdown, .select-wrapper');
            if (parent) {
                const nextGenOption = Array.from(parent.querySelectorAll('*')).find(el => {
                    const elText = (el.innerText || el.textContent || '').toLowerCase();
                    return elText.includes('nextgen') && el !== dropdown;
                });
                
                if (nextGenOption) {
                    nextGenOption.click();
                    console.log("✅ Clicked NextGen in custom dropdown");
                }
            }
        }
    });
};

// PART 2: Set Trading Operations as default tab
const setTradingDefault = () => {
    console.log("\n📊 Setting Trading Operations as default tab...");
    
    const tabs = document.querySelectorAll('[role="tab"], .tab, .nav-link, [data-tab]');
    let tradingFound = false;
    
    tabs.forEach((tab, index) => {
        const tabText = (tab.innerText || tab.textContent || '').toLowerCase();
        
        if (tabText.includes('trading') || tabText.includes('operations') || tabText.includes('ai trading')) {
            console.log(`✅ Found Trading tab: "${tab.innerText}"`);
            
            // Click the tab
            tab.click();
            
            // Set active classes
            tabs.forEach(t => {
                t.classList.remove('active', 'selected');
                t.setAttribute('aria-selected', 'false');
            });
            tab.classList.add('active', 'selected');
            tab.setAttribute('aria-selected', 'true');
            
            tradingFound = true;
            
            // Save preference
            localStorage.setItem('defaultTab', 'trading-operations');
            localStorage.setItem('defaultTabIndex', index.toString());
        }
    });
    
    return tradingFound;
};

// PART 3: Create permanent override
const createPermanentDefaults = () => {
    const permanentScript = document.createElement('script');
    permanentScript.id = 'nextgen-trading-defaults';
    permanentScript.textContent = `
    // Permanent NextGen + Trading Defaults
    (function() {
        const applyDefaults = () => {
            // Set NextGen in dropdowns
            const selectors = document.querySelectorAll('select, .dropdown');
            selectors.forEach(selector => {
                const options = selector.querySelectorAll('option, .dropdown-item');
                options.forEach(option => {
                    if (option.innerText.toLowerCase().includes('nextgen')) {
                        if (selector.tagName === 'SELECT') {
                            selector.value = option.value;
                        }
                        option.click();
                    }
                });
            });
            
            // Set Trading tab
            const tabs = document.querySelectorAll('[role="tab"], .tab, .nav-link');
            tabs.forEach(tab => {
                if (tab.innerText.toLowerCase().includes('trading')) {
                    setTimeout(() => tab.click(), 100);
                }
            });
        };
        
        // Apply on load and with delays
        applyDefaults();
        setTimeout(applyDefaults, 500);
        setTimeout(applyDefaults, 1500);
        
        // Monitor for dynamic content
        const observer = new MutationObserver(() => {
            applyDefaults();
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        // Store preferences
        localStorage.setItem('defaultSoftware', 'nextgen');
        localStorage.setItem('defaultTab', 'trading-operations');
    })();
    `;
    
    // Remove existing and add new
    const existing = document.getElementById('nextgen-trading-defaults');
    if (existing) existing.remove();
    document.head.appendChild(permanentScript);
};

// PART 4: Execute all functions
console.log("🚀 Applying all defaults...\n");

// Apply immediately
setNextGenDefault();
setTradingDefault();
createPermanentDefaults();

// Apply with delays for dynamic content
setTimeout(() => {
    setNextGenDefault();
    setTradingDefault();
}, 500);

setTimeout(() => {
    setNextGenDefault();
    setTradingDefault();
}, 1500);

// Monitor for new content
let observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
        if (mutation.addedNodes.length) {
            // Check if new dropdowns or tabs were added
            const hasNewElements = Array.from(mutation.addedNodes).some(node => {
                if (node.nodeType === 1) {
                    return node.matches && (
                        node.matches('select, .dropdown, [role="tab"]') ||
                        node.querySelector && node.querySelector('select, .dropdown, [role="tab"]')
                    );
                }
                return false;
            });
            
            if (hasNewElements) {
                console.log("🔄 New elements detected, reapplying defaults...");
                setTimeout(() => {
                    setNextGenDefault();
                    setTradingDefault();
                }, 100);
            }
        }
    });
});

observer.observe(document.body, {
    childList: true,
    subtree: true
});

console.log("\n✅ COMPLETE: NextGen + Trading Operations set as defaults!");
console.log("💡 These will now be selected automatically on page load");
console.log("💡 Preferences saved to localStorage for persistence");