// QUICK FIX: Set PMS NextGen as default in dropdown
console.log("🚀 Quick NextGen Default Fix");

// Find and click NextGen immediately
const quickFix = () => {
    // Method 1: Find select dropdowns
    const selects = document.querySelectorAll('select');
    selects.forEach(select => {
        const options = select.options;
        for (let i = 0; i < options.length; i++) {
            if (options[i].text.includes('NextGen') || options[i].text === 'PMS NextGen') {
                select.selectedIndex = i;
                select.value = options[i].value;
                
                // Trigger change event
                select.dispatchEvent(new Event('change', { bubbles: true }));
                console.log(`✅ Set NextGen in dropdown: ${options[i].text}`);
                break;
            }
        }
    });
    
    // Method 2: Custom dropdowns (divs/buttons)
    const customDropdowns = document.querySelectorAll('.dropdown-item, .dropdown-option, [role="option"]');
    customDropdowns.forEach(item => {
        const text = item.innerText || item.textContent || '';
        if (text.includes('NextGen') || text === 'PMS NextGen') {
            item.click();
            console.log(`✅ Clicked NextGen option: ${text}`);
        }
    });
    
    // Method 3: Look for specific dropdown by current value
    const dropdownToggles = document.querySelectorAll('.dropdown-toggle, .select-toggle, button[data-toggle="dropdown"]');
    dropdownToggles.forEach(toggle => {
        const currentText = toggle.innerText || toggle.textContent || '';
        // If it doesn't already show NextGen
        if (!currentText.includes('NextGen')) {
            // Find the dropdown menu
            const menu = toggle.nextElementSibling || toggle.parentElement.querySelector('.dropdown-menu');
            if (menu) {
                const nextGenItem = Array.from(menu.children).find(child => {
                    const text = child.innerText || child.textContent || '';
                    return text.includes('NextGen');
                });
                
                if (nextGenItem) {
                    // Open dropdown first
                    toggle.click();
                    setTimeout(() => {
                        nextGenItem.click();
                        console.log("✅ Selected NextGen from dropdown menu");
                    }, 100);
                }
            }
        }
    });
};

// Run immediately
quickFix();

// Run again after a short delay
setTimeout(quickFix, 500);
setTimeout(quickFix, 1000);

// Save preference
localStorage.setItem('preferredSoftware', 'PMS NextGen');

console.log("\n✅ NextGen should now be selected!");
console.log("💡 If not visible yet, the page may still be loading - will retry automatically");