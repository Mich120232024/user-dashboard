// COMPREHENSIVE DROPDOWN FIX FOR ENTIRE APPLICATION
// This fixes cursor sticking issues across ALL dropdowns/selectors

console.log("🔧 APPLYING GLOBAL DROPDOWN FIX");

// 1. IMMEDIATE CSS FIX - Inject styles to prevent cursor issues
const globalDropdownFix = document.createElement('style');
globalDropdownFix.id = 'global-dropdown-fix';
globalDropdownFix.textContent = `
/* ===== GLOBAL DROPDOWN CURSOR FIX ===== */

/* Fix all select elements */
select, 
.dropdown,
.dropdown-select,
.custom-select,
[role="combobox"],
[role="listbox"],
.MuiSelect-root,
.ant-select,
.select2-container,
.react-select__control {
    cursor: pointer !important;
    user-select: none !important;
    -webkit-user-select: none !important;
    position: relative !important;
}

/* Prevent drag behavior */
select:active,
.dropdown:active,
[role="combobox"]:active {
    cursor: pointer !important;
    user-drag: none !important;
    -webkit-user-drag: none !important;
}

/* Fix option hover states */
option,
.dropdown-item,
.dropdown-option,
[role="option"],
.MuiMenuItem-root,
.ant-select-item,
.react-select__option {
    cursor: pointer !important;
    user-select: none !important;
}

/* Prevent parent containers from interfering */
.dropdown-wrapper,
.select-wrapper,
.form-group,
.input-group,
.field-wrapper {
    pointer-events: none !important;
}

/* Re-enable pointer events only on the actual dropdown */
.dropdown-wrapper select,
.select-wrapper select,
.form-group select,
.input-group select,
.field-wrapper select,
.dropdown-wrapper .dropdown,
.select-wrapper .dropdown {
    pointer-events: auto !important;
}

/* Fix for custom dropdown implementations */
.dropdown-toggle {
    cursor: pointer !important;
    user-select: none !important;
}

.dropdown-menu {
    cursor: default !important;
}

.dropdown-menu a,
.dropdown-menu button,
.dropdown-menu li {
    cursor: pointer !important;
}

/* Prevent text selection during dropdown interaction */
body.dropdown-open {
    user-select: none !important;
    -webkit-user-select: none !important;
    -moz-user-select: none !important;
    -ms-user-select: none !important;
}

/* Fix z-index stacking issues */
.dropdown-menu,
.dropdown-content,
[role="listbox"] {
    z-index: 9999 !important;
}

/* Ensure dropdowns don't cause layout shifts */
select:focus,
.dropdown:focus,
[role="combobox"]:focus {
    outline: 2px solid #0078d4 !important;
    outline-offset: 2px !important;
}

/* Fix for React Select and similar libraries */
.react-select__control--is-focused,
.react-select__control:hover {
    cursor: pointer !important;
}

.react-select__value-container {
    cursor: pointer !important;
}

.react-select__indicators {
    cursor: pointer !important;
}
`;

// Remove any existing fix and apply new one
const existingFix = document.getElementById('global-dropdown-fix');
if (existingFix) existingFix.remove();
document.head.appendChild(globalDropdownFix);

console.log("✅ Global CSS fix applied");

// 2. FIX EVENT HANDLING - Prevent event bubbling issues
function fixDropdownEvents() {
    // Find all dropdowns
    const allDropdowns = document.querySelectorAll(`
        select, 
        .dropdown, 
        [role="combobox"], 
        [role="listbox"],
        .custom-select,
        .dropdown-toggle
    `);
    
    console.log(`📊 Found ${allDropdowns.length} dropdown elements to fix`);
    
    allDropdowns.forEach((dropdown, index) => {
        // Remove any existing problematic listeners
        const newDropdown = dropdown.cloneNode(true);
        dropdown.parentNode.replaceChild(newDropdown, dropdown);
        
        // Add fixed event handlers
        newDropdown.addEventListener('mousedown', function(e) {
            e.stopPropagation();
        });
        
        newDropdown.addEventListener('click', function(e) {
            e.stopPropagation();
        });
        
        // Prevent drag behavior
        newDropdown.addEventListener('dragstart', function(e) {
            e.preventDefault();
            return false;
        });
        
        // Fix focus behavior
        newDropdown.addEventListener('focus', function() {
            document.body.classList.add('dropdown-open');
        });
        
        newDropdown.addEventListener('blur', function() {
            document.body.classList.remove('dropdown-open');
        });
        
        console.log(`✅ Fixed dropdown ${index + 1}:`, newDropdown.tagName, newDropdown.className);
    });
}

// 3. MONITOR FOR NEW DROPDOWNS (for dynamically added content)
const dropdownObserver = new MutationObserver(function(mutations) {
    let hasNewDropdowns = false;
    
    mutations.forEach(function(mutation) {
        mutation.addedNodes.forEach(function(node) {
            if (node.nodeType === 1) { // Element node
                if (node.matches && node.matches('select, .dropdown, [role="combobox"]')) {
                    hasNewDropdowns = true;
                } else if (node.querySelectorAll) {
                    const innerDropdowns = node.querySelectorAll('select, .dropdown, [role="combobox"]');
                    if (innerDropdowns.length > 0) {
                        hasNewDropdowns = true;
                    }
                }
            }
        });
    });
    
    if (hasNewDropdowns) {
        console.log("🔄 New dropdowns detected, applying fixes...");
        setTimeout(fixDropdownEvents, 100);
    }
});

// Start observing
dropdownObserver.observe(document.body, {
    childList: true,
    subtree: true
});

// 4. FIX SPECIFIC FRAMEWORK ISSUES
// React specific fixes
if (window.React || document.querySelector('[data-reactroot]')) {
    console.log("⚛️ React detected, applying React-specific fixes");
    
    // Override synthetic event handling
    document.addEventListener('mousedown', function(e) {
        if (e.target.matches('select, .dropdown, [role="combobox"]')) {
            e.stopImmediatePropagation();
        }
    }, true);
}

// 5. APPLY FIXES
fixDropdownEvents();

// 6. UTILITY FUNCTIONS FOR DEBUGGING
window.debugDropdowns = function() {
    const dropdowns = document.querySelectorAll('select, .dropdown, [role="combobox"]');
    console.log(`\n🔍 Dropdown Debug Report:`);
    console.log(`Total dropdowns: ${dropdowns.length}`);
    
    dropdowns.forEach((dd, i) => {
        const computed = getComputedStyle(dd);
        console.log(`\nDropdown ${i + 1}:`, {
            element: dd,
            cursor: computed.cursor,
            position: computed.position,
            pointerEvents: computed.pointerEvents,
            userSelect: computed.userSelect,
            zIndex: computed.zIndex
        });
    });
};

window.resetDropdownFixes = function() {
    const fix = document.getElementById('global-dropdown-fix');
    if (fix) fix.remove();
    dropdownObserver.disconnect();
    console.log("❌ Dropdown fixes removed");
};

// 7. FINAL CHECK
setTimeout(() => {
    const totalFixed = document.querySelectorAll('select, .dropdown, [role="combobox"]').length;
    console.log(`\n✅ GLOBAL DROPDOWN FIX COMPLETE`);
    console.log(`📊 ${totalFixed} dropdowns protected from cursor issues`);
    console.log(`💡 Run 'debugDropdowns()' to check dropdown states`);
    console.log(`💡 Run 'resetDropdownFixes()' to remove fixes`);
}, 1000);

// 8. PREVENT FUTURE ISSUES
// Add to window resize to reapply if needed
window.addEventListener('resize', () => {
    if (!document.getElementById('global-dropdown-fix')) {
        document.head.appendChild(globalDropdownFix);
    }
});