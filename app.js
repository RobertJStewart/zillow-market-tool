console.log('✅ Zillow Market Tool frontend loaded');

// Load and display the Zillow data
async function loadData() {
    try {
        // Load the ZIP code data
        console.log('🔄 Attempting to fetch data...');
        const response = await fetch('data_demo/zip_latest.geojson?v=' + Date.now());
        console.log('📡 Response status:', response.status);
        console.log('📡 Response headers:', response.headers.get('content-type'));
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // Check if response is JSON (including GeoJSON)
        const contentType = response.headers.get('content-type');
        if (!contentType || (!contentType.includes('application/json') && !contentType.includes('application/geo+json'))) {
            throw new Error(`Expected JSON but got: ${contentType}`);
        }
        
        const text = await response.text();
        console.log('📄 Response text length:', text.length);
        console.log('📄 First 200 chars:', text.substring(0, 200));
        
        const data = JSON.parse(text);
        console.log('📊 Data loaded successfully');
        console.log(`📊 Loaded ${data.features.length} ZIP codes`);
        
        // Extract and sort data by home value
        const zipData = data.features
            .map(feature => ({
                zip: feature.properties.zcta,
                zhvi: feature.properties.zhvi || 0,
                zori: (feature.properties.zori === null || isNaN(feature.properties.zori)) ? 0 : feature.properties.zori,
                date: feature.properties.date
            }))
            .filter(item => item.zhvi > 0)
            .sort((a, b) => b.zhvi - a.zhvi);
        
        // Display stats
        displayStats(zipData);
        
        // Create chart
        createChart(zipData.slice(0, 20));
        
        // Display data table
        displayDataTable(zipData.slice(0, 50));
        
        // Update footer with Zillow data date
        updateFooter(zipData);
        
    } catch (error) {
        console.error('❌ Error loading data:', error);
        console.error('❌ Error details:', error.message);
        document.getElementById('stats').innerHTML = `<p>❌ Error loading data: ${error.message}</p>`;
    }
}

function displayStats(data) {
    const stats = document.getElementById('stats');
    const totalZips = data.length;
    const avgValue = data.reduce((sum, item) => sum + item.zhvi, 0) / totalZips;
    const maxValue = Math.max(...data.map(item => item.zhvi));
    const minValue = Math.min(...data.map(item => item.zhvi));
    
    stats.innerHTML = `
        <div class="stat-item">
            <strong>Total ZIP Codes:</strong> ${totalZips.toLocaleString()}
        </div>
        <div class="stat-item">
            <strong>Average Home Value:</strong> $${avgValue.toLocaleString()}
        </div>
        <div class="stat-item">
            <strong>Highest Value:</strong> $${maxValue.toLocaleString()}
        </div>
        <div class="stat-item">
            <strong>Lowest Value:</strong> $${minValue.toLocaleString()}
        </div>
    `;
}

function createChart(data) {
    const ctx = document.getElementById('chart').getContext('2d');
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(item => item.zip),
            datasets: [{
                label: 'Home Value (ZHVI)',
                data: data.map(item => item.zhvi),
                backgroundColor: 'rgba(54, 162, 235, 0.6)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }, {
                label: 'Rent Index (ZORI)',
                data: data.map(item => item.zori),
                backgroundColor: 'rgba(255, 99, 132, 0.6)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': $' + context.parsed.y.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

function displayDataTable(data) {
    const table = document.getElementById('data-table');
    
    let html = '<table><thead><tr><th>ZIP Code</th><th>Home Value</th><th>Rent Index</th><th>Date</th></tr></thead><tbody>';
    
    data.forEach(item => {
        html += `
            <tr>
                <td>${item.zip}</td>
                <td>$${item.zhvi.toLocaleString()}</td>
                <td>$${(item.zori || 0).toLocaleString()}</td>
                <td>${item.date}</td>
            </tr>
        `;
    });
    
    html += '</tbody></table>';
    table.innerHTML = html;
}

function updateFooter(zipData) {
    // Get the latest date from the Zillow data
    const latestDate = zipData.length > 0 ? zipData[0].date : 'Unknown';
    
    // Format the date nicely
    const formattedDate = new Date(latestDate).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
    
    // Update the footer
    const zillowDateElement = document.getElementById('zillow-date');
    if (zillowDateElement) {
        zillowDateElement.textContent = formattedDate;
    }
}

// Page switching functionality
function switchPage(pageName) {
    // Hide all pages
    document.querySelectorAll('.page-content').forEach(page => {
        page.style.display = 'none';
    });
    
    // Remove active class from all buttons
    document.querySelectorAll('.page-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected page
    document.getElementById(pageName + '-page').style.display = 'block';
    
    // Add active class to clicked button
    document.querySelector(`[data-page="${pageName}"]`).classList.add('active');
    
    console.log(`📄 Switched to ${pageName} page`);
}

// Initialize page switching
function initializePageSwitching() {
    // Add click listeners to page buttons
    document.querySelectorAll('.page-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const pageName = this.getAttribute('data-page');
            switchPage(pageName);
        });
    });
    
    console.log('✅ Page switching initialized');
}

// Map and Time Series functionality
let map = null;
let timeSeriesData = null;
let currentLayer = null;
let isPlaying = false;
let playInterval = null;
let drawnItems = null;
let isDrawing = false;
let currentZoomLevel = 4;
let dataCache = {
    states: null,
    counties: null,
    zipcodes: null
};

// Initialize map when Time Series page is shown
function initializeMap() {
    if (map) return; // Already initialized
    
    console.log('🗺️ Initializing map...');
    
    // Create map centered on US
    map = L.map('map').setView([39.8283, -98.5795], 4);
    
    // Add tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    
    // Initialize drawing layer
    drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);
    
    // Add zoom level detection
    map.on('zoomend', function() {
        const newZoom = map.getZoom();
        if (Math.abs(newZoom - currentZoomLevel) >= 1) {
            currentZoomLevel = newZoom;
            console.log(`🔍 Zoom level changed to: ${currentZoomLevel}`);
            updateMapData(); // Reload data at appropriate detail level
        }
    });
    
    console.log('✅ Map initialized');
}

// Load time series data with progressive detail
async function loadTimeSeriesData() {
    try {
        console.log('📊 Loading time series data...');
        
        // Load initial state-level data (fast)
        await loadStateLevelData();
        
        console.log(`✅ Loaded state-level data`);
        
        // Initialize time slider
        initializeTimeSlider();
        
        // Load initial map data
        updateMapData();
        
    } catch (error) {
        console.error('❌ Error loading time series data:', error);
    }
}

// Load state-level aggregated data
async function loadStateLevelData() {
    try {
        const response = await fetch('data_demo/zip_latest.geojson?v=' + Date.now());
        const data = await response.json();
        
        // Aggregate ZIP codes by state (simplified - using first 2 digits of ZIP as state proxy)
        const stateData = {};
        
        data.features.forEach(feature => {
            const zip = feature.properties.zcta;
            const stateCode = zip.substring(0, 2); // Simplified state grouping
            
            if (!stateData[stateCode]) {
                stateData[stateCode] = {
                    zips: [],
                    totalZhvi: 0,
                    totalZori: 0,
                    count: 0
                };
            }
            
            stateData[stateCode].zips.push(feature);
            stateData[stateCode].totalZhvi += feature.properties.zhvi || 0;
            stateData[stateCode].totalZori += feature.properties.zori || 0;
            stateData[stateCode].count++;
        });
        
        // Create state-level features
        const stateFeatures = Object.entries(stateData).map(([stateCode, data]) => {
            const avgZhvi = data.totalZhvi / data.count;
            const avgZori = data.totalZori / data.count;
            
            // Create a simple polygon for the state (centered on average location)
            const avgLat = data.zips.reduce((sum, zip) => sum + (zip.geometry.coordinates[1] || 0), 0) / data.count;
            const avgLon = data.zips.reduce((sum, zip) => sum + (zip.geometry.coordinates[0] || 0), 0) / data.count;
            
            return {
                type: 'Feature',
                geometry: {
                    type: 'Polygon',
                    coordinates: [[
                        [avgLon - 2, avgLat - 1],
                        [avgLon + 2, avgLat - 1],
                        [avgLon + 2, avgLat + 1],
                        [avgLon - 2, avgLat + 1],
                        [avgLon - 2, avgLat - 1]
                    ]]
                },
                properties: {
                    stateCode: stateCode,
                    avgZhvi: avgZhvi,
                    avgZori: avgZori,
                    zipCount: data.count,
                    timeValues: {
                        '2024-01': { zhvi: avgZhvi * 0.95, zori: avgZori * 0.95 },
                        '2024-02': { zhvi: avgZhvi * 0.97, zori: avgZori * 0.97 },
                        '2024-03': { zhvi: avgZhvi * 0.99, zori: avgZori * 0.99 },
                        '2024-04': { zhvi: avgZhvi * 1.01, zori: avgZori * 1.01 },
                        '2024-05': { zhvi: avgZhvi * 1.03, zori: avgZori * 1.03 },
                        '2024-06': { zhvi: avgZhvi, zori: avgZori }
                    }
                }
            };
        });
        
        // Cache state data
        dataCache.states = {
            dates: ['2024-01', '2024-02', '2024-03', '2024-04', '2024-05', '2024-06'],
            features: stateFeatures
        };
        
        timeSeriesData = dataCache.states;
        
    } catch (error) {
        console.error('❌ Error loading state data:', error);
    }
}

// Load detailed data based on zoom level
async function loadDetailedData() {
    const zoom = map.getZoom();
    
    if (zoom >= 8 && !dataCache.zipcodes) {
        console.log('🔍 Loading detailed ZIP code data...');
        try {
            const response = await fetch('data_demo/zip_latest.geojson?v=' + Date.now());
            const data = await response.json();
            
            // Limit to visible area for performance
            const bounds = map.getBounds();
            const visibleFeatures = data.features.filter(feature => {
                const coords = feature.geometry.coordinates;
                return bounds.contains([coords[1], coords[0]]);
            }).slice(0, 1000); // Limit to 1000 features max
            
            dataCache.zipcodes = {
                dates: ['2024-01', '2024-02', '2024-03', '2024-04', '2024-05', '2024-06'],
                features: visibleFeatures.map(feature => ({
                    ...feature,
                    timeValues: {
                        '2024-01': { zhvi: feature.properties.zhvi * 0.95, zori: (feature.properties.zori || 0) * 0.95 },
                        '2024-02': { zhvi: feature.properties.zhvi * 0.97, zori: (feature.properties.zori || 0) * 0.97 },
                        '2024-03': { zhvi: feature.properties.zhvi * 0.99, zori: (feature.properties.zori || 0) * 0.99 },
                        '2024-04': { zhvi: feature.properties.zhvi * 1.01, zori: (feature.properties.zori || 0) * 1.01 },
                        '2024-05': { zhvi: feature.properties.zhvi * 1.03, zori: (feature.properties.zori || 0) * 1.03 },
                        '2024-06': { zhvi: feature.properties.zhvi, zori: feature.properties.zori || 0 }
                    }
                }))
            };
            
            console.log(`✅ Loaded ${visibleFeatures.length} detailed features`);
        } catch (error) {
            console.error('❌ Error loading detailed data:', error);
        }
    }
}

// Initialize time slider
function initializeTimeSlider() {
    const slider = document.getElementById('time-slider');
    const display = document.getElementById('time-display');
    
    if (!slider || !display) return;
    
    slider.max = timeSeriesData.dates.length - 1;
    slider.value = timeSeriesData.dates.length - 1; // Start at latest
    
    slider.addEventListener('input', function() {
        const index = parseInt(this.value);
        display.textContent = timeSeriesData.dates[index];
        updateMapData();
    });
    
    // Set initial display
    display.textContent = timeSeriesData.dates[timeSeriesData.dates.length - 1];
}

// Update map data based on current time and settings
async function updateMapData() {
    if (!map || !timeSeriesData) return;
    
    const slider = document.getElementById('time-slider');
    const dataType = document.getElementById('data-type').value;
    const overlayType = document.getElementById('overlay-type').value;
    
    if (!slider) return;
    
    const timeIndex = parseInt(slider.value);
    const currentDate = timeSeriesData.dates[timeIndex];
    
    console.log(`📅 Updating map for ${currentDate}, ${dataType}, ${overlayType}, zoom: ${currentZoomLevel}`);
    
    // Load detailed data if needed
    await loadDetailedData();
    
    // Choose appropriate data source based on zoom level
    let dataSource = timeSeriesData;
    if (currentZoomLevel >= 8 && dataCache.zipcodes) {
        dataSource = dataCache.zipcodes;
        console.log('🔍 Using detailed ZIP code data');
    } else {
        console.log('🗺️ Using state-level data');
    }
    
    // Clear existing layer
    if (currentLayer) {
        map.removeLayer(currentLayer);
    }
    
    // Create new layer based on overlay type and zoom level
    if (overlayType === 'zip') {
        currentLayer = createZipLayer(currentDate, dataType, dataSource);
    } else {
        currentLayer = createH3Layer(currentDate, dataType, dataSource);
    }
    
    if (currentLayer) {
        map.addLayer(currentLayer);
    }
    
    // Update color legend
    updateColorLegend();
}

// Create ZIP code layer
function createZipLayer(date, dataType, dataSource = timeSeriesData) {
    const features = dataSource.features
        .map(feature => {
            const timeData = feature.timeValues?.[date];
            if (!timeData) return null;
            
            return {
                type: 'Feature',
                geometry: feature.geometry,
                properties: {
                    id: feature.properties.zcta || feature.properties.stateCode,
                    value: timeData[dataType] || 0,
                    date: date,
                    zipCount: feature.properties.zipCount || 1,
                    isState: !!feature.properties.stateCode
                }
            };
        })
        .filter(f => f !== null);
    
    console.log(`🎨 Rendering ${features.length} features`);
    
    return L.geoJSON(features, {
        style: function(feature) {
            const value = feature.properties.value;
            const color = getColorForValue(value, dataType);
            
            return {
                fillColor: color,
                weight: feature.properties.isState ? 2 : 1,
                opacity: 1,
                color: 'white',
                dashArray: feature.properties.isState ? '5' : '3',
                fillOpacity: 0.7
            };
        },
        onEachFeature: function(feature, layer) {
            const props = feature.properties;
            const label = props.isState ? `State Region: ${props.id}` : `ZIP: ${props.id}`;
            const countInfo = props.zipCount > 1 ? `<br>ZIP Codes: ${props.zipCount}` : '';
            
            layer.bindPopup(`
                <strong>${label}</strong><br>
                ${dataType.toUpperCase()}: $${props.value.toLocaleString()}<br>
                Date: ${props.date}${countInfo}
            `);
        }
    });
}

// Create H3 layer
function createH3Layer(date, dataType, dataSource = timeSeriesData) {
    try {
        // For now, use the same data source as ZIP codes
        // In a real implementation, you'd have separate H3 data
        const features = dataSource.features
            .map(feature => {
                const timeData = feature.timeValues?.[date];
                if (!timeData) return null;
                
                return {
                    type: 'Feature',
                    geometry: feature.geometry,
                    properties: {
                        id: feature.properties.zcta || feature.properties.stateCode || 'hex',
                        value: timeData[dataType] || 0,
                        date: date,
                        isState: !!feature.properties.stateCode
                    }
                };
            })
            .filter(f => f !== null);
        
        console.log(`🔷 Rendering ${features.length} H3 features`);
        
        return L.geoJSON(features, {
            style: function(feature) {
                const value = feature.properties.value;
                const color = getColorForValue(value, dataType);
                
                return {
                    fillColor: color,
                    weight: 2,
                    opacity: 1,
                    color: 'white',
                    fillOpacity: 0.8
                };
            },
            onEachFeature: function(feature, layer) {
                const props = feature.properties;
                const label = props.isState ? `State Region: ${props.id}` : `H3 Hex: ${props.id}`;
                
                layer.bindPopup(`
                    <strong>${label}</strong><br>
                    ${dataType.toUpperCase()}: $${props.value.toLocaleString()}<br>
                    Date: ${props.date}
                `);
            }
        });
    } catch (error) {
        console.error('Error creating H3 layer:', error);
        return null;
    }
}

// Load H3 data
async function loadH3Data() {
    try {
        const response = await fetch('data_demo/grid_latest.geojson?v=' + Date.now());
        const data = await response.json();
        
        // Simulate time series for H3 data
        window.h3GridData = {
            features: data.features.map(feature => ({
                ...feature,
                timeValues: {
                    '2024-01': { zhvi: feature.properties.avg_zhvi * 0.95, zori: (feature.properties.avg_zori || 0) * 0.95 },
                    '2024-02': { zhvi: feature.properties.avg_zhvi * 0.97, zori: (feature.properties.avg_zori || 0) * 0.97 },
                    '2024-03': { zhvi: feature.properties.avg_zhvi * 0.99, zori: (feature.properties.avg_zori || 0) * 0.99 },
                    '2024-04': { zhvi: feature.properties.avg_zhvi * 1.01, zori: (feature.properties.avg_zori || 0) * 1.01 },
                    '2024-05': { zhvi: feature.properties.avg_zhvi * 1.03, zori: (feature.properties.avg_zori || 0) * 1.03 },
                    '2024-06': { zhvi: feature.properties.avg_zhvi, zori: feature.properties.avg_zori || 0 }
                }
            }))
        };
        
        console.log('✅ H3 data loaded');
    } catch (error) {
        console.error('❌ Error loading H3 data:', error);
    }
}

// Get color for value based on data type
function getColorForValue(value, dataType) {
    // Simple color scale - in a real implementation, you'd want more sophisticated scaling
    const maxValue = dataType === 'zhvi' ? 2000000 : 5000;
    const normalized = Math.min(value / maxValue, 1);
    
    // Color scale from green (low) to red (high)
    const hue = (1 - normalized) * 120; // 120 = green, 0 = red
    return `hsl(${hue}, 70%, 50%)`;
}

// Update color legend
function updateColorLegend() {
    const legendContent = document.getElementById('legend-content');
    const dataType = document.getElementById('data-type').value;
    
    if (!legendContent) return;
    
    const maxValue = dataType === 'zhvi' ? 2000000 : 5000;
    const steps = 5;
    
    let html = '';
    for (let i = 0; i < steps; i++) {
        const value = (maxValue / steps) * (steps - i);
        const color = getColorForValue(value, dataType);
        
        html += `
            <div class="legend-item">
                <div class="legend-color" style="background-color: ${color}"></div>
                <span>$${value.toLocaleString()}</span>
            </div>
        `;
    }
    
    legendContent.innerHTML = html;
}

// Initialize Time Series page
function initializeTimeSeriesPage() {
    console.log('📈 Initializing Time Series page...');
    
    // Initialize map
    initializeMap();
    
    // Load time series data
    loadTimeSeriesData();
    
    // Add event listeners for controls
    document.getElementById('data-type').addEventListener('change', updateMapData);
    document.getElementById('overlay-type').addEventListener('change', updateMapData);
    
    // Play/pause button
    const playPauseBtn = document.getElementById('play-pause-btn');
    if (playPauseBtn) {
        playPauseBtn.addEventListener('click', function() {
            if (isPlaying) {
                pauseAnimation();
            } else {
                playAnimation();
            }
        });
    }
    
    // Export button
    const exportBtn = document.getElementById('export-btn');
    if (exportBtn) {
        exportBtn.addEventListener('click', exportMapData);
    }
    
    // Draw button
    const drawBtn = document.getElementById('draw-btn');
    if (drawBtn) {
        drawBtn.addEventListener('click', toggleDrawing);
    }
    
    // Clear button
    const clearBtn = document.getElementById('clear-btn');
    if (clearBtn) {
        clearBtn.addEventListener('click', clearDrawings);
    }
    
    console.log('✅ Time Series page initialized');
}

// Play animation
function playAnimation() {
    if (!timeSeriesData) return;
    
    isPlaying = true;
    const playPauseBtn = document.getElementById('play-pause-btn');
    if (playPauseBtn) playPauseBtn.textContent = '⏸️ Pause';
    
    const slider = document.getElementById('time-slider');
    let currentIndex = parseInt(slider.value);
    
    playInterval = setInterval(() => {
        currentIndex = (currentIndex + 1) % timeSeriesData.dates.length;
        slider.value = currentIndex;
        slider.dispatchEvent(new Event('input'));
        
        if (currentIndex === timeSeriesData.dates.length - 1) {
            pauseAnimation();
        }
    }, 1000); // 1 second per frame
}

// Pause animation
function pauseAnimation() {
    isPlaying = false;
    const playPauseBtn = document.getElementById('play-pause-btn');
    if (playPauseBtn) playPauseBtn.textContent = '▶️ Play';
    
    if (playInterval) {
        clearInterval(playInterval);
        playInterval = null;
    }
}

// Enhanced page switching to initialize Time Series
function switchPage(pageName) {
    // Hide all pages
    document.querySelectorAll('.page-content').forEach(page => {
        page.style.display = 'none';
    });
    
    // Remove active class from all buttons
    document.querySelectorAll('.page-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected page
    document.getElementById(pageName + '-page').style.display = 'block';
    
    // Add active class to clicked button
    document.querySelector(`[data-page="${pageName}"]`).classList.add('active');
    
    // Initialize Time Series page if switching to it
    if (pageName === 'timeseries') {
        setTimeout(() => {
            initializeTimeSeriesPage();
        }, 100); // Small delay to ensure DOM is ready
    }
    
    console.log(`📄 Switched to ${pageName} page`);
}

// Export map data
function exportMapData() {
    if (!timeSeriesData || !currentLayer) {
        alert('No data to export. Please load the map first.');
        return;
    }
    
    const slider = document.getElementById('time-slider');
    const dataType = document.getElementById('data-type').value;
    const overlayType = document.getElementById('overlay-type').value;
    
    const timeIndex = parseInt(slider.value);
    const currentDate = timeSeriesData.dates[timeIndex];
    
    // Get current layer data
    const layerData = currentLayer.toGeoJSON();
    
    // Create export data
    const exportData = {
        metadata: {
            date: currentDate,
            dataType: dataType,
            overlayType: overlayType,
            exportTime: new Date().toISOString(),
            totalFeatures: layerData.features.length
        },
        data: layerData
    };
    
    // Create and download JSON file
    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `zillow-export-${currentDate}-${dataType}-${overlayType}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    console.log('📊 Data exported successfully');
}

// Toggle drawing mode
function toggleDrawing() {
    const drawBtn = document.getElementById('draw-btn');
    
    if (isDrawing) {
        // Disable drawing
        isDrawing = false;
        drawBtn.textContent = '✏️ Draw';
        drawBtn.style.backgroundColor = '#007bff';
        
        // Remove drawing tools
        if (map.drawControl) {
            map.removeControl(map.drawControl);
        }
        
        console.log('✏️ Drawing mode disabled');
    } else {
        // Enable drawing
        isDrawing = true;
        drawBtn.textContent = '✏️ Drawing...';
        drawBtn.style.backgroundColor = '#28a745';
        
        // Add drawing tools
        if (!map.drawControl) {
            map.drawControl = new L.Control.Draw({
                edit: {
                    featureGroup: drawnItems,
                    remove: true
                },
                draw: {
                    polygon: true,
                    polyline: true,
                    rectangle: true,
                    circle: true,
                    marker: true,
                    circlemarker: false
                }
            });
        }
        
        map.addControl(map.drawControl);
        
        // Handle drawing events
        map.on(L.Draw.Event.CREATED, function(event) {
            const layer = event.layer;
            drawnItems.addLayer(layer);
            console.log('✏️ Drawing created:', layer);
        });
        
        console.log('✏️ Drawing mode enabled');
    }
}

// Clear all drawings
function clearDrawings() {
    if (drawnItems) {
        drawnItems.clearLayers();
        console.log('🗑️ All drawings cleared');
    }
}

// Enhanced color scaling
function getColorForValue(value, dataType) {
    // Get current data range for better scaling
    const allValues = [];
    
    if (timeSeriesData) {
        timeSeriesData.features.forEach(feature => {
            Object.values(feature.timeValues || {}).forEach(timeData => {
                if (timeData[dataType]) {
                    allValues.push(timeData[dataType]);
                }
            });
        });
    }
    
    if (allValues.length === 0) {
        return '#cccccc';
    }
    
    const minValue = Math.min(...allValues);
    const maxValue = Math.max(...allValues);
    const normalized = (value - minValue) / (maxValue - minValue);
    
    // Enhanced color scale: blue (low) -> green -> yellow -> orange -> red (high)
    if (normalized < 0.2) return `hsl(240, 70%, ${50 + normalized * 20}%)`; // Blue
    if (normalized < 0.4) return `hsl(${240 - (normalized - 0.2) * 300}, 70%, 60%)`; // Blue to Green
    if (normalized < 0.6) return `hsl(${120 - (normalized - 0.4) * 60}, 70%, 60%)`; // Green to Yellow
    if (normalized < 0.8) return `hsl(${60 - (normalized - 0.6) * 30}, 70%, 60%)`; // Yellow to Orange
    return `hsl(${30 - (normalized - 0.8) * 30}, 70%, 60%)`; // Orange to Red
}

// Load data when page loads
document.addEventListener('DOMContentLoaded', function() {
    loadData();
    initializePageSwitching();
});