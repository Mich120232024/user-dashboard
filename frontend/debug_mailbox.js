const puppeteer = require('puppeteer');

async function debugMailboxIssue() {
    console.log('🔍 Starting mailbox debugging session...');
    
    const browser = await puppeteer.launch({
        headless: false,
        devtools: true,
        defaultViewport: { width: 1920, height: 1080 },
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    const page = await browser.newPage();
    
    // Enable console logging from the browser
    page.on('console', msg => {
        const type = msg.type();
        const args = msg.args().map(arg => arg.toString()).join(' ');
        console.log(`[BROWSER ${type.toUpperCase()}]`, args);
    });
    
    // Enable request/response logging
    page.on('request', request => {
        if (request.url().includes('/api/')) {
            console.log(`[REQUEST] ${request.method()} ${request.url()}`);
        }
    });
    
    page.on('response', response => {
        if (response.url().includes('/api/')) {
            console.log(`[RESPONSE] ${response.status()} ${response.url()}`);
        }
    });
    
    try {
        console.log('\n📝 Step 1: Testing the debug page...');
        await page.goto('http://localhost:8080/debug-mailbox.html', { waitUntil: 'networkidle0' });
        
        // Wait for the test to complete
        await page.waitForTimeout(3000);
        
        // Get the output content
        const debugOutput = await page.$eval('#output', el => el.innerHTML);
        console.log('Debug page output:', debugOutput);
        
        console.log('\n📝 Step 2: Opening the main dashboard...');
        await page.goto('http://localhost:8080/professional-dashboard.html', { waitUntil: 'networkidle0' });
        
        // Wait for initial load
        await page.waitForTimeout(2000);
        
        console.log('\n📝 Step 3: Navigating to Mailbox tab...');
        // Click on the Mailbox tab
        await page.click('[data-tab="mailbox"]');
        
        // Wait for mailbox to load
        await page.waitForTimeout(3000);
        
        console.log('\n📝 Step 4: Checking for JavaScript errors...');
        // Get any JavaScript errors that occurred
        const errorMessages = await page.evaluate(() => {
            return window.console_errors || [];
        });
        
        if (errorMessages.length > 0) {
            console.log('JavaScript errors found:', errorMessages);
        } else {
            console.log('No JavaScript errors found');
        }
        
        console.log('\n📝 Step 5: Examining the mailbox content...');
        // Check if messages are loaded
        const messageListContent = await page.$eval('#message-list', el => el.innerHTML);
        console.log('Message list HTML:', messageListContent);
        
        // Check message count displays
        const countAll = await page.$eval('#count-all', el => el.textContent);
        const countUnread = await page.$eval('#count-unread', el => el.textContent);
        console.log(`Message counts - All: ${countAll}, Unread: ${countUnread}`);
        
        console.log('\n📝 Step 6: Manually testing API endpoint...');
        // Test API endpoint directly from the browser context
        const apiTestResult = await page.evaluate(async () => {
            try {
                const response = await fetch('http://localhost:8001/api/v1/messages/HEAD_OF_ENGINEERING?limit=5');
                const data = await response.json();
                return {
                    status: response.status,
                    ok: response.ok,
                    data: data,
                    messageCount: data.messages ? data.messages.length : 0
                };
            } catch (error) {
                return { error: error.message };
            }
        });
        
        console.log('API test result:', JSON.stringify(apiTestResult, null, 2));
        
        console.log('\n📝 Step 7: Checking network requests...');
        // Trigger a manual refresh of messages
        await page.click('button[onclick="refreshMessages()"]');
        await page.waitForTimeout(2000);
        
        // Check the updated content
        const updatedMessageList = await page.$eval('#message-list', el => el.innerHTML);
        console.log('Updated message list HTML:', updatedMessageList);
        
        console.log('\n📝 Step 8: Examining global window state...');
        const windowState = await page.evaluate(() => {
            return {
                allMessages: window.allMessages || 'undefined',
                currentFilter: window.currentFilter || 'undefined',
                messagesPagination: window.messagesPagination || 'undefined',
                API_BASE: window.API_BASE || 'undefined'
            };
        });
        
        console.log('Window state:', JSON.stringify(windowState, null, 2));
        
        console.log('\n✅ Debug session complete. Check the browser for visual inspection.');
        console.log('The browser will remain open for manual inspection...');
        
        // Keep the browser open for manual inspection
        await page.waitForTimeout(60000); // Wait 1 minute before closing
        
    } catch (error) {
        console.error('❌ Error during debugging:', error);
    } finally {
        await browser.close();
    }
}

// Run the debug session
debugMailboxIssue().catch(console.error);