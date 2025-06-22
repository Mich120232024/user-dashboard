/**
 * Navigation Fix for Dashboard
 * This script adds the missing navigation functionality
 */

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Navigation fix script loaded');
    
    // Get all navigation items and tab content sections
    const navItems = document.querySelectorAll('.nav-item');
    const tabContents = document.querySelectorAll('.tab-content');
    
    // Function to switch tabs
    function switchTab(tabName) {
        console.log('Switching to tab:', tabName);
        
        // Remove active class from all nav items and tab contents
        navItems.forEach(item => item.classList.remove('active'));
        tabContents.forEach(content => content.classList.remove('active'));
        
        // Find and activate the selected tab
        const selectedNav = document.querySelector(`[data-tab="${tabName}"]`);
        const selectedContent = document.getElementById(tabName);
        
        if (selectedNav && selectedContent) {
            selectedNav.classList.add('active');
            selectedContent.classList.add('active');
            
            // Store current tab in localStorage
            localStorage.setItem('currentTab', tabName);
            
            // Dispatch custom event
            document.dispatchEvent(new CustomEvent('tabChanged', {
                detail: { tabName: tabName }
            }));
            
            console.log('Tab switched successfully to:', tabName);
        } else {
            console.error('Tab not found:', tabName);
        }
    }
    
    // Add click handlers to all nav items
    navItems.forEach(navItem => {
        navItem.addEventListener('click', function(e) {
            e.preventDefault();
            const tabName = this.getAttribute('data-tab');
            if (tabName) {
                switchTab(tabName);
            }
        });
    });
    
    // Restore last active tab from localStorage
    const lastTab = localStorage.getItem('currentTab');
    if (lastTab && document.getElementById(lastTab)) {
        switchTab(lastTab);
    }
    
    // Make switchTab function globally available
    window.switchTab = switchTab;
    
    console.log('Navigation fix applied. Found', navItems.length, 'nav items and', tabContents.length, 'tab contents');
});