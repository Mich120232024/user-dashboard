// Fix Layout: Use Saved Layout (not All Components) + Fix Rendering Below
console.log("🔧 Fixing Layout and Component Rendering");

// PART 1: Set "Saved Layout" as default (not "All Components")
const setSavedLayoutDefault = () => {
    console.log("\n📐 Setting Saved Layout as default...");
    
    // Find layout selector (usually a dropdown or radio buttons)
    const layoutSelectors = document.querySelectorAll('select, input[type="radio"], .layout-selector, .view-selector');
    
    layoutSelectors.forEach(selector => {
        if (selector.tagName === 'SELECT') {
            // Dropdown selector
            const options = selector.options;
            for (let i = 0; i < options.length; i++) {
                const optionText = options[i].text.toLowerCase();
                if (optionText.includes('saved') || optionText.includes('saved layout') || optionText.includes('my layout')) {
                    selector.selectedIndex = i;
                    selector.dispatchEvent(new Event('change', { bubbles: true }));
                    console.log(`✅ Selected "Saved Layout" option: ${options[i].text}`);
                    break;
                }
            }
        } else if (selector.type === 'radio') {
            // Radio button
            const label = selector.parentElement.textContent.toLowerCase();
            if (label.includes('saved') || label.includes('saved layout')) {
                selector.checked = true;
                selector.dispatchEvent(new Event('change', { bubbles: true }));
                console.log("✅ Selected Saved Layout radio button");
            }
        }
    });
    
    // Also check for custom layout toggles
    const layoutButtons = document.querySelectorAll('button, .btn, .layout-option');
    layoutButtons.forEach(button => {
        const text = (button.innerText || button.textContent || '').toLowerCase();
        if (text.includes('saved layout') && !text.includes('all components')) {
            button.click();
            console.log("✅ Clicked Saved Layout button");
        }
    });
    
    // Save preference
    localStorage.setItem('preferredLayout', 'saved');
    localStorage.setItem('layoutMode', 'saved-layout');
};

// PART 2: Fix Component Rendering Below
const fixComponentRendering = () => {
    console.log("\n🔨 Fixing component rendering issues...");
    
    // Common rendering issues and fixes
    
    // Fix 1: Height constraints
    const containers = document.querySelectorAll('.component-container, .dashboard-content, .tab-content, [role="tabpanel"]');
    containers.forEach(container => {
        // Remove height restrictions
        container.style.height = 'auto';
        container.style.minHeight = 'auto';
        container.style.maxHeight = 'none';
        container.style.overflow = 'visible';
        
        // Fix flex issues
        if (getComputedStyle(container).display === 'flex') {
            container.style.flexWrap = 'wrap';
        }
    });
    
    // Fix 2: Clear overflow hidden
    const overflowElements = document.querySelectorAll('[style*="overflow"]');
    overflowElements.forEach(el => {
        if (el.style.overflow === 'hidden' || el.style.overflowY === 'hidden') {
            el.style.overflow = 'visible';
            console.log("✅ Fixed overflow on:", el.className);
        }
    });
    
    // Fix 3: Grid layout issues
    const gridContainers = document.querySelectorAll('.grid, .dashboard-grid, [style*="grid"]');
    gridContainers.forEach(grid => {
        // Ensure grid can expand
        grid.style.gridAutoRows = 'auto';
        grid.style.height = 'auto';
        
        // Fix grid items
        const gridItems = grid.children;
        for (let item of gridItems) {
            item.style.gridRow = 'auto';
            item.style.height = 'auto';
        }
    });
    
    // Fix 4: Force reflow for stuck components
    const allComponents = document.querySelectorAll('.component, .widget, .chart-container, .fred-component');
    allComponents.forEach(component => {
        // Force display
        if (component.offsetHeight === 0) {
            component.style.display = 'block';
            component.style.visibility = 'visible';
            component.style.opacity = '1';
            console.log("✅ Forced display on hidden component:", component.className);
        }
        
        // Trigger reflow
        component.style.display = 'none';
        component.offsetHeight; // Force reflow
        component.style.display = '';
    });
    
    // Fix 5: Viewport and scrolling
    const mainContent = document.querySelector('.main-content, .dashboard-main, main, #root');
    if (mainContent) {
        mainContent.style.height = 'auto';
        mainContent.style.minHeight = '100vh';
        mainContent.style.overflow = 'visible';
    }
    
    // Fix 6: Z-index stacking
    let zIndex = 1;
    allComponents.forEach(component => {
        if (component.style.position === 'absolute' || component.style.position === 'fixed') {
            component.style.position = 'relative';
        }
        component.style.zIndex = zIndex++;
    });
};

// PART 3: CSS Injection for permanent fixes
const injectRenderingFixes = () => {
    const fixStyles = document.createElement('style');
    fixStyles.id = 'rendering-fixes';
    fixStyles.textContent = `
    /* Global Rendering Fixes */
    
    /* Fix container heights */
    .dashboard-content,
    .tab-content,
    .component-container,
    [role="tabpanel"] {
        height: auto !important;
        min-height: auto !important;
        max-height: none !important;
        overflow: visible !important;
    }
    
    /* Fix grid layouts */
    .dashboard-grid,
    .component-grid {
        display: grid !important;
        grid-auto-rows: auto !important;
        height: auto !important;
        gap: 20px !important;
    }
    
    /* Ensure components are visible */
    .component,
    .widget,
    .fred-component,
    .chart-container {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        position: relative !important;
        height: auto !important;
        min-height: 200px !important;
    }
    
    /* Fix main content area */
    main,
    .main-content,
    #root > div {
        height: auto !important;
        min-height: 100vh !important;
        overflow: visible !important;
    }
    
    /* Prevent absolute positioning issues */
    .component-wrapper {
        position: relative !important;
    }
    
    /* Fix flex containers */
    .flex-container {
        flex-wrap: wrap !important;
    }
    
    /* Ensure proper stacking */
    .component-stack > * {
        position: relative !important;
        z-index: auto !important;
    }
    
    /* Fix viewport constraints */
    body {
        overflow-y: auto !important;
        height: auto !important;
    }
    
    /* Saved layout specific */
    .saved-layout .component {
        display: block !important;
    }
    
    /* Prevent cutting off */
    .tab-pane,
    .tab-panel {
        overflow: visible !important;
        height: auto !important;
        padding-bottom: 50px !important;
    }
    `;
    
    // Remove existing and add new
    const existing = document.getElementById('rendering-fixes');
    if (existing) existing.remove();
    document.head.appendChild(fixStyles);
    
    console.log("✅ Injected CSS rendering fixes");
};

// PART 4: Monitor and fix dynamic content
const monitorAndFix = () => {
    const observer = new MutationObserver((mutations) => {
        let needsFix = false;
        
        mutations.forEach(mutation => {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === 1 && node.matches && 
                        node.matches('.component, .widget, .tab-content')) {
                        needsFix = true;
                    }
                });
            }
        });
        
        if (needsFix) {
            setTimeout(fixComponentRendering, 100);
        }
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['style', 'class']
    });
};

// PART 5: Execute all fixes
console.log("🚀 Applying all fixes...\n");

// Apply immediately
setSavedLayoutDefault();
fixComponentRendering();
injectRenderingFixes();
monitorAndFix();

// Reapply after delays for dynamic content
setTimeout(() => {
    setSavedLayoutDefault();
    fixComponentRendering();
}, 1000);

setTimeout(() => {
    fixComponentRendering();
}, 2000);

// Force window resize event (sometimes triggers reflow)
window.dispatchEvent(new Event('resize'));

console.log("\n✅ COMPLETE: Layout and rendering fixes applied!");
console.log("💡 Saved Layout is now default (not All Components)");
console.log("💡 Components should now render properly below");
console.log("💡 If components still don't appear, try switching tabs and back");