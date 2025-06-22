// Simple working dashboard
console.log('Dashboard loading...');

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded');
    
    // Test basic functionality
    testAPI();
    
    // Setup tab switching
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function(e) {
            const tab = e.target.dataset.tab;
            console.log('Switching to tab:', tab);
            
            // Update nav
            document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
            e.target.classList.add('active');
            
            // Update content
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            document.getElementById(tab).classList.add('active');
            
            if (tab === 'containers') {
                loadContainers();
            }
        });
    });
});

async function testAPI() {
    try {
        const response = await fetch('http://localhost:8001/api/v1/cosmos/containers');
        const data = await response.json();
        console.log('API working:', data.success, 'containers:', data.containers?.length);
        
        // Update status
        document.getElementById('status-text').textContent = 'Connected';
        document.getElementById('total-containers').textContent = data.containers?.length || 0;
        
    } catch (error) {
        console.error('API Error:', error);
        document.getElementById('status-text').textContent = 'Error: ' + error.message;
        document.getElementById('status').className = 'status-indicator error';
    }
}

async function loadContainers() {
    console.log('Loading containers...');
    
    const listEl = document.getElementById('container-list');
    listEl.innerHTML = '<div class="loading">Loading containers...</div>';
    
    try {
        const response = await fetch('http://localhost:8001/api/v1/cosmos/containers');
        const data = await response.json();
        
        if (data.success && data.containers) {
            console.log('Containers loaded:', data.containers.length);
            renderContainers(data.containers);
        } else {
            listEl.innerHTML = '<div class="empty-state">No containers found</div>';
        }
    } catch (error) {
        console.error('Error loading containers:', error);
        listEl.innerHTML = '<div class="empty-state">Error: ' + error.message + '</div>';
    }
}

function renderContainers(containers) {
    const listEl = document.getElementById('container-list');
    
    const html = containers.map(container => `
        <div class="container-item" onclick="selectContainer('${container.id}')">
            <div class="container-name">${container.id}</div>
            <div class="container-count">${container.count >= 0 ? container.count : 'Loading...'}</div>
        </div>
    `).join('');
    
    listEl.innerHTML = html;
    console.log('Rendered', containers.length, 'containers');
}

function selectContainer(id) {
    console.log('Selected container:', id);
    document.getElementById('selected-container').textContent = id;
    
    // Update selection
    document.querySelectorAll('.container-item').forEach(item => item.classList.remove('selected'));
    event.target.closest('.container-item').classList.add('selected');
    
    loadDocuments(id);
}

async function loadDocuments(containerId) {
    const listEl = document.getElementById('document-list');
    listEl.innerHTML = '<div class="loading">Loading documents...</div>';
    
    try {
        const response = await fetch(`http://localhost:8001/api/v1/cosmos/containers/${containerId}/documents?limit=10`);
        const data = await response.json();
        
        if (data.success && data.documents) {
            console.log('Documents loaded:', data.documents.length);
            renderDocuments(data.documents);
        } else {
            listEl.innerHTML = '<div class="empty-state">No documents found</div>';
        }
    } catch (error) {
        console.error('Error loading documents:', error);
        listEl.innerHTML = '<div class="empty-state">Error: ' + error.message + '</div>';
    }
}

function renderDocuments(documents) {
    const listEl = document.getElementById('document-list');
    
    const html = documents.map(doc => {
        const timestamp = new Date(doc._ts * 1000).toLocaleString();
        const preview = doc.content || doc.message || doc.subject || doc.action || 'No preview';
        
        return `
            <div class="document-item">
                <div class="document-header">
                    <div class="document-id">${doc.id}</div>
                    <div class="document-timestamp">${timestamp}</div>
                </div>
                <div class="document-preview">${String(preview).substring(0, 150)}...</div>
            </div>
        `;
    }).join('');
    
    listEl.innerHTML = html;
    console.log('Rendered', documents.length, 'documents');
}