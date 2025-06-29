// Verify FRED API Endpoints
// This checks the FastAPI backend on port 2000

console.log("🔍 FRED API VERIFICATION");

// Known endpoints from the FastAPI backend
const API_BASE = 'http://localhost:2000';
const endpoints = [
    '/health',
    '/api/fred/categories',
    '/api/fred/series',
    '/api/fred/search',
    '/api/economic/indicators',
    '/api/economic/unemployment',
    '/api/economic/payrolls',
    '/api/economic/earnings',
    '/api/quantitative/yield-curve',
    '/api/quantitative/correlation-matrix',
    '/api/quantitative/volatility',
    '/api/portfolio/optimization',
    '/api/portfolio/risk-metrics',
    '/api/portfolio/performance'
];

// Test each endpoint
async function testEndpoints() {
    console.log(`\n📡 Testing ${endpoints.length} endpoints on ${API_BASE}:`);
    
    for (const endpoint of endpoints) {
        const url = `${API_BASE}${endpoint}`;
        try {
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
                mode: 'cors'
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log(`✅ ${endpoint} - Status: ${response.status}`, {
                    dataReceived: !!data,
                    sampleData: JSON.stringify(data).substring(0, 100) + '...'
                });
            } else {
                console.error(`❌ ${endpoint} - Status: ${response.status}`);
            }
        } catch (error) {
            console.error(`❌ ${endpoint} - Error:`, error.message);
        }
    }
}

// Check if backend is running
async function checkBackendHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        if (response.ok) {
            console.log("✅ Backend is running on port 2000");
            return true;
        }
    } catch (error) {
        console.error("❌ Backend not accessible:", error);
        console.log("💡 Make sure backend is running: cd backend && poetry run uvicorn app.main:app --reload --port 2000");
        return false;
    }
}

// Function to manually trigger data load in UI
window.loadFREDData = async function(category = 'unemployment') {
    console.log(`📊 Loading FRED data for: ${category}`);
    
    try {
        const response = await fetch(`${API_BASE}/api/economic/${category}`);
        const data = await response.json();
        
        console.log("✅ Data received:", data);
        
        // Try to update UI if possible
        const contentArea = document.querySelector('.tab-content.active, [role="tabpanel"]:not([hidden])');
        if (contentArea && data) {
            console.log("💉 Injecting data into active tab...");
            // This is a temporary visualization
            contentArea.innerHTML = `
                <div style="padding: 20px;">
                    <h3>FRED Data Loaded</h3>
                    <pre>${JSON.stringify(data, null, 2)}</pre>
                </div>
            `;
        }
        
        return data;
    } catch (error) {
        console.error("Failed to load data:", error);
    }
};

// Start tests
(async function() {
    const isBackendRunning = await checkBackendHealth();
    if (isBackendRunning) {
        await testEndpoints();
        console.log("\n💡 Run 'loadFREDData()' to manually load data into the active tab");
    } else {
        console.log("\n⚠️ Backend not detected. The UI won't load data without the backend.");
    }
})();

// Monitor for component updates
console.log("\n👁️ Monitoring for React component updates...");
if (window.React && window.React.version) {
    console.log("React version:", window.React.version);
}