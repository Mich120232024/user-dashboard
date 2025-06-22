const puppeteer = require('puppeteer');

async function debugNavigation() {
    const browser = await puppeteer.launch({
        headless: false,
        devtools: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    try {
        const page = await browser.newPage();
        
        // Enable console logging
        page.on('console', msg => {
            console.log('Browser console:', msg.type(), msg.text());
        });
        
        // Log any page errors
        page.on('pageerror', error => {
            console.error('Page error:', error.message);
        });
        
        console.log('Loading dashboard...');
        await page.goto('http://localhost:8080', {
            waitUntil: 'networkidle2',
            timeout: 30000
        });
        
        console.log('Page loaded. Taking initial screenshot...');
        await page.screenshot({ 
            path: 'dashboard-initial.png',
            fullPage: true 
        });
        
        // Check if navigation items exist
        const navItems = await page.$$eval('.nav-item', items => {
            return items.map(item => ({
                text: item.textContent,
                dataTab: item.getAttribute('data-tab'),
                hasClickHandler: !!item.onclick
            }));
        });
        
        console.log('Navigation items found:', navItems);
        
        // Check for tab content sections
        const tabSections = await page.$$eval('.tab-content', sections => {
            return sections.map(section => ({
                id: section.id,
                isActive: section.classList.contains('active'),
                display: window.getComputedStyle(section).display
            }));
        });
        
        console.log('Tab sections found:', tabSections);
        
        // Try clicking on the Mailbox tab
        console.log('\nTrying to click on Mailbox tab...');
        
        // First check if there are any click handlers
        const clickHandlers = await page.evaluate(() => {
            const navItems = document.querySelectorAll('.nav-item');
            const handlers = [];
            navItems.forEach(item => {
                const tab = item.getAttribute('data-tab');
                handlers.push({
                    tab: tab,
                    hasOnclick: !!item.onclick,
                    hasEventListener: item._addEventListener !== undefined,
                    listeners: getEventListeners ? getEventListeners(item) : 'Cannot check'
                });
            });
            return handlers;
        });
        
        console.log('Click handlers status:', clickHandlers);
        
        // Try to click Mailbox
        try {
            await page.click('[data-tab="mailbox"]');
            console.log('Clicked Mailbox tab');
            await page.waitForTimeout(1000);
            
            // Check if the view changed
            const mailboxActive = await page.$eval('#mailbox', el => {
                return {
                    hasActiveClass: el.classList.contains('active'),
                    display: window.getComputedStyle(el).display,
                    isHidden: el.hasAttribute('hidden')
                };
            });
            
            console.log('Mailbox tab state after click:', mailboxActive);
            
            await page.screenshot({ 
                path: 'dashboard-after-mailbox-click.png',
                fullPage: true 
            });
        } catch (error) {
            console.error('Error clicking Mailbox tab:', error);
        }
        
        // Check for any JavaScript errors in the console
        const jsErrors = await page.evaluate(() => {
            return window.jsErrors || [];
        });
        
        if (jsErrors.length > 0) {
            console.log('JavaScript errors found:', jsErrors);
        }
        
        // Check if professional.js is loaded and initialized
        const dashboardState = await page.evaluate(() => {
            return {
                hasDashboard: typeof window.dashboard !== 'undefined',
                hasTabComponent: typeof window.TabComponent !== 'undefined',
                components: window.dashboard ? Array.from(window.dashboard.components.keys()) : []
            };
        });
        
        console.log('Dashboard state:', dashboardState);
        
        // Try to manually trigger tab switching
        console.log('\nTrying manual tab switch...');
        const manualSwitch = await page.evaluate(() => {
            const navItems = document.querySelectorAll('.nav-item');
            const tabContents = document.querySelectorAll('.tab-content');
            
            // Function to switch tabs manually
            function switchTab(tabName) {
                // Remove active from all nav items and tab contents
                navItems.forEach(item => item.classList.remove('active'));
                tabContents.forEach(content => content.classList.remove('active'));
                
                // Add active to selected tab
                const selectedNav = document.querySelector(`[data-tab="${tabName}"]`);
                const selectedContent = document.getElementById(tabName);
                
                if (selectedNav && selectedContent) {
                    selectedNav.classList.add('active');
                    selectedContent.classList.add('active');
                    return true;
                }
                return false;
            }
            
            // Try switching to cosmos tab
            const result = switchTab('cosmos');
            return {
                switchResult: result,
                activeTab: document.querySelector('.nav-item.active')?.getAttribute('data-tab'),
                activeContent: document.querySelector('.tab-content.active')?.id
            };
        });
        
        console.log('Manual switch result:', manualSwitch);
        
        await page.screenshot({ 
            path: 'dashboard-after-manual-switch.png',
            fullPage: true 
        });
        
        console.log('\nDebug complete. Check the screenshots and console output.');
        
    } catch (error) {
        console.error('Debug error:', error);
    } finally {
        // Keep browser open for manual inspection
        console.log('\nBrowser will remain open for manual inspection. Press Ctrl+C to close.');
    }
}

// Run the debug script
debugNavigation();