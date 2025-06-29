// Tab Content Loading Debug Script
// Run this in browser console on the FRED dashboard

console.log("🔍 TAB CONTENT DEBUG STARTED");

// 1. Check for API endpoints
console.log("\n📡 Checking API Endpoints:");
const possibleEndpoints = [
    '/api/fred',
    '/api/economic',
    '/api/indicators',
    '/fred/api',
    'http://localhost:2000/api',
    'http://localhost:8000/api',
    'http://localhost:5000/api',
    'http://localhost:5001/api'
];

// 2. Check Network Activity
console.log("\n🌐 Monitoring Network Requests:");
const originalFetch = window.fetch;
window.fetch = function(...args) {
    console.log('📥 Fetch request:', args[0]);
    return originalFetch.apply(this, args)
        .then(response => {
            console.log(`✅ Response ${response.status} from:`, args[0]);
            if (!response.ok) {
                console.error(`❌ Failed request to ${args[0]}: ${response.status}`);
            }
            return response;
        })
        .catch(error => {
            console.error(`❌ Fetch error for ${args[0]}:`, error);
            throw error;
        });
};

// 3. Check for Data in Window/State
console.log("\n📊 Checking for Data in Page:");
// Check window object for data
if (window.fredData) console.log("Found window.fredData:", window.fredData);
if (window.__INITIAL_STATE__) console.log("Found initial state:", window.__INITIAL_STATE__);

// Check React DevTools
if (window.__REACT_DEVTOOLS_GLOBAL_HOOK__) {
    console.log("✅ React DevTools detected - check Components tab for state");
}

// 4. Check for Loading Indicators
console.log("\n⏳ Checking Loading States:");
const loadingElements = document.querySelectorAll('[class*="loading"], [class*="spinner"], .loader');
console.log(`Found ${loadingElements.length} loading elements:`, loadingElements);

// 5. Check Tab Content Areas
console.log("\n📑 Checking Tab Content:");
const tabs = document.querySelectorAll('[role="tab"], .tab, [class*="tab"]');
const tabPanels = document.querySelectorAll('[role="tabpanel"], .tab-content, [class*="tab-content"]');

console.log(`Found ${tabs.length} tabs and ${tabPanels.length} tab panels`);

tabs.forEach((tab, index) => {
    console.log(`Tab ${index + 1}:`, {
        text: tab.innerText,
        active: tab.classList.contains('active') || tab.getAttribute('aria-selected') === 'true',
        element: tab
    });
});

tabPanels.forEach((panel, index) => {
    console.log(`Panel ${index + 1}:`, {
        visible: panel.style.display !== 'none' && !panel.hidden,
        hasContent: panel.innerText.trim().length > 0,
        childElements: panel.children.length,
        element: panel
    });
});

// 6. Check Console for Errors
console.log("\n❌ Recent Console Errors:");
// Override console.error to capture errors
const originalError = console.error;
console.error = function(...args) {
    console.log("🚨 Error captured:", ...args);
    originalError.apply(console, args);
};

// 7. Check for CORS Issues
console.log("\n🔒 Checking for CORS Issues:");
fetch('http://localhost:2000/api/health')
    .then(res => console.log("✅ Backend API accessible"))
    .catch(err => console.error("❌ Backend API CORS issue:", err));

// 8. Monitor Tab Changes
console.log("\n👁️ Monitoring Tab Changes:");
document.addEventListener('click', (e) => {
    if (e.target.matches('[role="tab"], .tab, [class*="tab"]')) {
        console.log("🔄 Tab clicked:", e.target.innerText);
        setTimeout(() => {
            const activePanel = document.querySelector('[role="tabpanel"]:not([hidden]), .tab-content.active');
            if (activePanel) {
                console.log("📋 Active panel content:", {
                    hasContent: activePanel.innerText.trim().length > 0,
                    html: activePanel.innerHTML.substring(0, 200) + '...'
                });
            }
        }, 100);
    }
});

// 9. Try to Find Data Functions
console.log("\n🔧 Checking for Data Loading Functions:");
// Look for global functions
const globalFunctions = Object.keys(window).filter(key => 
    typeof window[key] === 'function' && 
    (key.includes('load') || key.includes('fetch') || key.includes('get'))
);
console.log("Found data functions:", globalFunctions);

// 10. Create Test Data Loader
window.debugLoadData = async function() {
    console.log("🧪 Testing data load...");
    try {
        // Try common endpoints
        const testEndpoints = [
            '/api/fred/series',
            '/api/economic/indicators',
            '/api/data',
            'http://localhost:2000/api/fred',
            'http://localhost:2000/api/economic'
        ];
        
        for (const endpoint of testEndpoints) {
            try {
                const response = await fetch(endpoint);
                if (response.ok) {
                    const data = await response.json();
                    console.log(`✅ Success from ${endpoint}:`, data);
                    return data;
                }
            } catch (e) {
                console.log(`❌ Failed ${endpoint}:`, e.message);
            }
        }
    } catch (error) {
        console.error("Test load failed:", error);
    }
};

console.log("\n✅ TAB CONTENT DEBUG READY");
console.log("💡 Try clicking tabs and watch the console");
console.log("💡 Run 'debugLoadData()' to test data loading");
console.log("💡 Check Network tab in DevTools for API calls");