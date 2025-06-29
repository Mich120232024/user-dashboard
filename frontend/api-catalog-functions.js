        // API Catalog JavaScript Functions
        let catalogData = [];
        let catalogTypes = [];

        async function loadApiCatalog() {
            try {
                console.log('Loading API catalog...');
                
                // Load metrics
                await loadCatalogMetrics();
                
                // Load catalog types for filter
                await loadCatalogTypes();
                
                // Load catalog list
                await loadCatalogList();
                
            } catch (error) {
                console.error('Error loading API catalog:', error);
                showCatalogError('Failed to load API catalog data');
            }
        }

        async function loadCatalogMetrics() {
            try {
                const response = await fetch('/api/v1/api-catalog/catalogs/metrics/summary');
                const metrics = await response.json();
                
                document.getElementById('total-catalogs').textContent = metrics.total_catalogs;
                document.getElementById('total-endpoints').textContent = metrics.total_endpoints;
                document.getElementById('avg-endpoints').textContent = metrics.avg_endpoints_per_catalog;
                document.getElementById('catalog-types-count').textContent = Object.keys(metrics.catalog_types).length;
                
                console.log('Catalog metrics loaded:', metrics);
            } catch (error) {
                console.error('Error loading catalog metrics:', error);
            }
        }

        async function loadCatalogTypes() {
            try {
                const response = await fetch('/api/v1/api-catalog/catalogs/types');
                const data = await response.json();
                catalogTypes = data.catalog_types;
                
                const select = document.getElementById('catalog-type-filter');
                select.innerHTML = '<option value="">All Types</option>';
                
                catalogTypes.forEach(type => {
                    const option = document.createElement('option');
                    option.value = type;
                    option.textContent = type.toUpperCase();
                    select.appendChild(option);
                });
                
                console.log('Catalog types loaded:', catalogTypes);
            } catch (error) {
                console.error('Error loading catalog types:', error);
            }
        }

        async function loadCatalogList(catalogType = '', limit = 100) {
            try {
                const listContainer = document.getElementById('catalog-list');
                listContainer.innerHTML = '<div class="loading-state"><div class="spinner"></div><p>Loading catalogs...</p></div>';
                
                let url = `/api/v1/api-catalog/catalogs?limit=${limit}`;
                if (catalogType) {
                    url += `&catalog_type=${catalogType}`;
                }
                
                const response = await fetch(url);
                catalogData = await response.json();
                
                renderCatalogList(catalogData);
                
                console.log('Catalog list loaded:', catalogData.length, 'items');
            } catch (error) {
                console.error('Error loading catalog list:', error);
                showCatalogError('Failed to load catalog list');
            }
        }

        function renderCatalogList(catalogs) {
            const listContainer = document.getElementById('catalog-list');
            
            if (catalogs.length === 0) {
                listContainer.innerHTML = '<div class="loading-state"><p>No catalogs found</p></div>';
                return;
            }
            
            const catalogsHtml = catalogs.map(catalog => `
                <div class="catalog-item" onclick="showCatalogDetail('${catalog.id}')">
                    <div class="catalog-header">
                        <h4 class="catalog-title">${catalog.name}</h4>
                        <span class="catalog-type">${catalog.catalog_type}</span>
                    </div>
                    <div class="catalog-description">${catalog.description}</div>
                    <div class="catalog-meta">
                        <span class="catalog-endpoints-count">
                            <span>🔌</span> ${catalog.endpoints_count} endpoints
                        </span>
                        <span class="catalog-url">
                            <span>🌐</span> ${catalog.base_url}
                        </span>
                        <span class="catalog-version">v${catalog.version}</span>
                        <span class="catalog-updated">${new Date(catalog.last_updated).toLocaleDateString()}</span>
                    </div>
                </div>
            `).join('');
            
            listContainer.innerHTML = catalogsHtml;
        }

        async function showCatalogDetail(catalogId) {
            try {
                const modal = document.getElementById('catalog-detail-modal');
                const title = document.getElementById('catalog-detail-title');
                const content = document.getElementById('catalog-detail-content');
                
                title.textContent = 'Loading...';
                content.innerHTML = '<div class="loading-state"><div class="spinner"></div><p>Loading catalog details...</p></div>';
                modal.style.display = 'flex';
                
                const response = await fetch(`/api/v1/api-catalog/catalogs/${catalogId}`);
                const catalog = await response.json();
                
                title.textContent = catalog.name;
                content.innerHTML = `
                    <div class="catalog-detail">
                        <div class="detail-section">
                            <h4>Overview</h4>
                            <p><strong>Type:</strong> ${catalog.catalog_type}</p>
                            <p><strong>Base URL:</strong> <code>${catalog.base_url}</code></p>
                            <p><strong>Version:</strong> ${catalog.version}</p>
                            <p><strong>Last Updated:</strong> ${new Date(catalog.last_updated).toLocaleString()}</p>
                            <p><strong>Description:</strong> ${catalog.description}</p>
                        </div>
                        
                        ${catalog.authentication ? `
                        <div class="detail-section">
                            <h4>Authentication</h4>
                            <p><strong>Type:</strong> ${catalog.authentication.type || 'None'}</p>
                            ${catalog.authentication.description ? `<p>${catalog.authentication.description}</p>` : ''}
                        </div>
                        ` : ''}
                        
                        <div class="detail-section">
                            <h4>Endpoints (${catalog.endpoints.length})</h4>
                            <div class="endpoint-list">
                                ${catalog.endpoints.map(endpoint => `
                                    <div class="endpoint-item">
                                        <span class="endpoint-method ${endpoint.method.toLowerCase()}">${endpoint.method}</span>
                                        <span class="endpoint-path">${endpoint.path}</span>
                                        ${endpoint.description ? `<span class="endpoint-description">${endpoint.description}</span>` : ''}
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        
                        ${catalog.documentation_url ? `
                        <div class="detail-section">
                            <h4>Documentation</h4>
                            <p><a href="${catalog.documentation_url}" target="_blank" style="color: var(--accent-blue);">${catalog.documentation_url}</a></p>
                        </div>
                        ` : ''}
                    </div>
                `;
                
                console.log('Catalog detail loaded:', catalog.name);
            } catch (error) {
                console.error('Error loading catalog detail:', error);
                document.getElementById('catalog-detail-content').innerHTML = '<p style="color: var(--danger-red);">Failed to load catalog details</p>';
            }
        }

        function closeCatalogDetail() {
            document.getElementById('catalog-detail-modal').style.display = 'none';
        }

        function refreshApiCatalog() {
            loadApiCatalog();
        }

        function filterCatalogs() {
            const catalogType = document.getElementById('catalog-type-filter').value;
            loadCatalogList(catalogType);
        }

        async function performSearch() {
            const query = document.getElementById('catalog-search').value.trim();
            const field = document.getElementById('search-field-filter').value;
            
            if (!query) {
                loadCatalogList();
                return;
            }
            
            try {
                const listContainer = document.getElementById('catalog-list');
                listContainer.innerHTML = '<div class="loading-state"><div class="spinner"></div><p>Searching...</p></div>';
                
                const response = await fetch(`/api/v1/api-catalog/catalogs/search?q=${encodeURIComponent(query)}&field=${field}`);
                const searchData = await response.json();
                
                renderCatalogList(searchData.results);
                
                console.log(`Search for "${query}" returned ${searchData.results_count} results`);
            } catch (error) {
                console.error('Error searching catalogs:', error);
                showCatalogError('Search failed');
            }
        }

        function searchCatalogs(event) {
            if (event.key === 'Enter') {
                performSearch();
            }
        }

        function showCatalogError(message) {
            document.getElementById('catalog-list').innerHTML = `
                <div class="loading-state">
                    <p style="color: var(--danger-red);">${message}</p>
                </div>
            `;
        }

        // Close modal when clicking outside
        document.addEventListener('click', function(event) {
            const modal = document.getElementById('catalog-detail-modal');
            if (event.target === modal) {
                closeCatalogDetail();
            }
        });