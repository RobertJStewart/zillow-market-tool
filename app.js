// Zillow Market Tool - Multi-Level Geographic Visualization
// Handles country, region, state, and ZIP code levels with statistical aggregation

let map, timeSeriesData, currentLayer, isPlaying = false, playInterval;
let currentZoomLevel = 5;
let currentGeographicLevel = 'region';
let currentStatisticalMethod = 'average';
let currentDataType = 'zhvi';

// Geographic level configuration
const GEOGRAPHIC_LEVELS = {
    'region': { zoom_threshold: 4, file: 'data_demo/aggregated/regions.geojson' },
    'state_region': { zoom_threshold: 6, file: 'data_demo/aggregated/state_regions.geojson' },
    'state': { zoom_threshold: 8, file: 'data_demo/aggregated/states.geojson' },
    'zipcode': { zoom_threshold: 10, file: 'data_demo/zip_latest.geojson' },
    'h3': { zoom_threshold: 10, file: 'data_demo/grid_latest.geojson' }
};

// Statistical method mapping
const STATISTICAL_METHODS = {
    'average': 'avg_',
    'median': 'median_',
    'max': 'max_',
    'min': 'min_',
    'count': 'count'
};

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initializing Zillow Market Tool...');
    
    // Set up page switching
    setupPageSwitching();
    
    // Set up map controls
    setupMapControls();
    
    // Initialize map
    initializeMap();
    
    // Load initial data
    loadTimeSeriesData();
    
    // Set up event listeners
    setupEventListeners();
    
    console.log('✅ Application initialized');
});

function setupPageSwitching() {
    const pageButtons = document.querySelectorAll('.page-btn');
    const pages = document.querySelectorAll('.page-content');
    
    pageButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetPage = button.dataset.page;
            
            // Update button states
            pageButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Show/hide pages
            pages.forEach(page => {
                page.style.display = page.id === `${targetPage}-page` ? 'block' : 'none';
            });
            
            // Initialize map if switching to time series
            if (targetPage === 'timeseries' && !map) {
                initializeMap();
            }
        });
    });
}

function setupMapControls() {
    // Geographic level selector
    const overlayTypeSelect = document.getElementById('overlay-type');
    overlayTypeSelect.addEventListener('change', (e) => {
        currentGeographicLevel = e.target.value;
        updateMapData();
    });
    
    // Statistical method selector
    const statisticalMethodSelect = document.getElementById('statistical-method');
    statisticalMethodSelect.addEventListener('change', (e) => {
        currentStatisticalMethod = e.target.value;
        updateMapData();
    });
    
    // Data type selector
    const dataTypeSelect = document.getElementById('data-type');
    dataTypeSelect.addEventListener('change', (e) => {
        currentDataType = e.target.value;
        updateMapData();
    });
    
    // Play/pause button
    const playPauseBtn = document.getElementById('play-pause-btn');
    playPauseBtn.addEventListener('click', togglePlayPause);
    
    // Export button
    const exportBtn = document.getElementById('export-btn');
    exportBtn.addEventListener('click', exportData);
    
    // Draw button
    const drawBtn = document.getElementById('draw-btn');
    drawBtn.addEventListener('click', toggleDrawing);
    
    // Clear button
    const clearBtn = document.getElementById('clear-btn');
    clearBtn.addEventListener('click', clearMap);
}

function initializeMap() {
    if (map) {
        map.remove();
    }
    
    // Initialize Leaflet map
    map = L.map('map').setView([39.8283, -98.5795], 5);
    
    // Add tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    
    // Set up zoom change listener
    map.on('zoomend', () => {
        const newZoom = map.getZoom();
        if (Math.abs(newZoom - currentZoomLevel) > 1) {
            currentZoomLevel = newZoom;
            updateGeographicLevel();
        }
    });
    
    // Initialize drawing tools
    initializeDrawingTools();
    
    console.log('🗺️ Map initialized');
}

function updateGeographicLevel() {
    // Determine appropriate geographic level based on zoom
    let newLevel = 'region';
    
    for (const [level, config] of Object.entries(GEOGRAPHIC_LEVELS)) {
        if (currentZoomLevel <= config.zoom_threshold) {
            newLevel = level;
            break;
        }
    }
    
    if (newLevel !== currentGeographicLevel) {
        currentGeographicLevel = newLevel;
        
        // Update the UI selector
        const overlaySelect = document.getElementById('overlay-type');
        overlaySelect.value = newLevel;
        
        // Update the map
        updateMapData();
        
        console.log(`🔄 Switched to ${newLevel} level (zoom: ${currentZoomLevel})`);
    }
}

async function loadTimeSeriesData() {
    try {
        console.log('📊 Loading time series data...');
        
        // Load the appropriate data file based on current level
        const dataFile = GEOGRAPHIC_LEVELS[currentGeographicLevel].file;
        const response = await fetch(dataFile + '?v=' + Date.now());
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const contentType = response.headers.get('content-type');
        if (!contentType || (!contentType.includes('application/json') && !contentType.includes('application/geo+json'))) {
            throw new Error(`Expected JSON but got: ${contentType}`);
        }
        
        timeSeriesData = await response.json();
        console.log(`✅ Loaded ${timeSeriesData.features.length} features from ${dataFile}`);
        
        // Update the map with the new data
        updateMapData();
        
    } catch (error) {
        console.error('❌ Error loading time series data:', error);
        document.getElementById('map').innerHTML = `
            <div style="padding: 20px; text-align: center; color: #666;">
                <h3>⚠️ Data Loading Error</h3>
                <p>Could not load geographic data. Please check the console for details.</p>
                <p><strong>Error:</strong> ${error.message}</p>
            </div>
        `;
    }
}

function updateMapData() {
    if (!map || !timeSeriesData) {
        console.log('⚠️ Map or data not ready');
        return;
    }
    
    console.log(`🔄 Updating map data: ${currentGeographicLevel} level, ${currentStatisticalMethod} ${currentDataType}`);
    
    // Remove existing layer
    if (currentLayer) {
        map.removeLayer(currentLayer);
    }
    
    // Create new layer based on current settings
    currentLayer = createMapLayer();
    
    if (currentLayer) {
        currentLayer.addTo(map);
        updateColorLegend();
        console.log('✅ Map updated successfully');
    } else {
        console.error('❌ Failed to create map layer');
    }
}

function createMapLayer() {
    if (!timeSeriesData || !timeSeriesData.features) {
        console.error('❌ No features to render');
        return null;
    }
    
    const currentDate = getCurrentDate();
    const features = timeSeriesData.features.map(feature => {
        const timeData = feature.properties.timeValues?.[currentDate];
        if (!timeData) {
            return null;
        }
        
        // Get the appropriate value based on statistical method
        const value = getStatisticalValue(feature.properties, currentDataType, currentStatisticalMethod);
        
        return {
            type: 'Feature',
            geometry: feature.geometry,
            properties: {
                id: feature.properties.id || feature.properties.zcta || feature.properties.stateCode,
                value: value,
                date: currentDate,
                level: currentGeographicLevel,
                method: currentStatisticalMethod,
                count: feature.properties.count || 1
            }
        };
    }).filter(f => f !== null);
    
    console.log(`🎨 Rendering ${features.length} features`);
    
    if (features.length === 0) {
        console.error('❌ No features to render!');
        return null;
    }
    
    // Create the layer
    const layer = L.geoJSON(features, {
        style: function(feature) {
            const value = feature.properties.value;
            const color = getColorForValue(value, currentDataType);
            
            return {
                fillColor: color,
                weight: currentGeographicLevel === 'region' ? 3 : currentGeographicLevel === 'state' ? 2 : 1,
                opacity: 1,
                color: 'white',
                dashArray: currentGeographicLevel === 'region' ? '8' : currentGeographicLevel === 'state' ? '5' : '3',
                fillOpacity: 0.7
            };
        },
        onEachFeature: function(feature, layer) {
            const props = feature.properties;
            const label = getFeatureLabel(props);
            
            layer.bindPopup(`
                <strong>${label}</strong><br>
                ${currentDataType.toUpperCase()}: $${props.value.toLocaleString()}<br>
                Method: ${currentStatisticalMethod}<br>
                Date: ${props.date}<br>
                Count: ${props.count}
            `);
        }
    });
    
    console.log('✅ Layer created successfully');
    return layer;
}

function getStatisticalValue(properties, dataType, method) {
    const prefix = STATISTICAL_METHODS[method];
    const propertyName = `${prefix}${dataType}`;
    
    if (properties[propertyName] !== undefined) {
        return properties[propertyName];
    }
    
    // Fallback to average if specific method not available
    const avgPropertyName = `avg_${dataType}`;
    if (properties[avgPropertyName] !== undefined) {
        return properties[avgPropertyName];
    }
    
    // Final fallback
    return properties[dataType] || 0;
}

function getFeatureLabel(properties) {
    const level = properties.level || currentGeographicLevel;
    const id = properties.id;
    
    switch (level) {
        case 'region':
            return `Region: ${id}`;
        case 'state_region':
            return `State Region: ${id}`;
        case 'state':
            return `State: ${id}`;
        case 'zipcode':
            return `ZIP: ${id}`;
        case 'h3':
            return `H3: ${id}`;
        default:
            return `${level}: ${id}`;
    }
}

function getColorForValue(value, dataType) {
    if (!timeSeriesData || !timeSeriesData.features) {
        return '#cccccc';
    }
    
    // Collect all values for scaling
    const allValues = [];
    timeSeriesData.features.forEach(feature => {
        const val = getStatisticalValue(feature.properties, dataType, currentStatisticalMethod);
        if (val && val > 0) {
            allValues.push(val);
        }
    });
    
    if (allValues.length === 0) {
        return '#cccccc';
    }
    
    const minValue = Math.min(...allValues);
    const maxValue = Math.max(...allValues);
    const normalized = (value - minValue) / (maxValue - minValue);
    
    // Enhanced color scale
    if (normalized < 0.2) return `hsl(240, 70%, ${50 + normalized * 20}%)`; // Blue
    if (normalized < 0.4) return `hsl(${240 - (normalized - 0.2) * 300}, 70%, 60%)`; // Blue to Green
    if (normalized < 0.6) return `hsl(${120 - (normalized - 0.4) * 60}, 70%, 60%)`; // Green to Yellow
    if (normalized < 0.8) return `hsl(${60 - (normalized - 0.6) * 30}, 70%, 60%)`; // Yellow to Orange
    return `hsl(${30 - (normalized - 0.8) * 30}, 70%, 60%)`; // Orange to Red
}

function updateColorLegend() {
    const legendContent = document.getElementById('legend-content');
    if (!legendContent) return;
    
    const legendItems = [
        { label: 'Low', color: 'hsl(240, 70%, 50%)' },
        { label: 'Medium-Low', color: 'hsl(180, 70%, 60%)' },
        { label: 'Medium', color: 'hsl(120, 70%, 60%)' },
        { label: 'Medium-High', color: 'hsl(60, 70%, 60%)' },
        { label: 'High', color: 'hsl(30, 70%, 60%)' }
    ];
    
    legendContent.innerHTML = legendItems.map(item => `
        <div class="legend-item">
            <div class="legend-color" style="background-color: ${item.color}"></div>
            <span>${item.label}</span>
        </div>
    `).join('');
}

function getCurrentDate() {
    const slider = document.getElementById('time-slider');
    const maxValue = parseInt(slider.max);
    const currentValue = parseInt(slider.value);
    
    // Map slider value to date (simplified)
    const dates = ['2024-01', '2024-02', '2024-03', '2024-04', '2024-05', '2024-06'];
    const index = Math.floor((currentValue / maxValue) * (dates.length - 1));
    return dates[index] || dates[dates.length - 1];
}

function setupEventListeners() {
    // Time slider
    const timeSlider = document.getElementById('time-slider');
    const timeDisplay = document.getElementById('time-display');
    
    timeSlider.addEventListener('input', (e) => {
        const date = getCurrentDate();
        timeDisplay.textContent = date;
        updateMapData();
    });
}

function togglePlayPause() {
    const btn = document.getElementById('play-pause-btn');
    
    if (isPlaying) {
        clearInterval(playInterval);
        btn.textContent = '▶️ Play';
        isPlaying = false;
    } else {
        const slider = document.getElementById('time-slider');
        let currentValue = parseInt(slider.value);
        const maxValue = parseInt(slider.max);
        
        playInterval = setInterval(() => {
            currentValue = (currentValue + 1) % (maxValue + 1);
            slider.value = currentValue;
            slider.dispatchEvent(new Event('input'));
        }, 1000);
        
        btn.textContent = '⏸️ Pause';
        isPlaying = true;
    }
}

function exportData() {
    if (!timeSeriesData) {
        alert('No data available to export');
        return;
    }
    
    const dataStr = JSON.stringify(timeSeriesData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `zillow_data_${currentGeographicLevel}_${currentStatisticalMethod}.json`;
    link.click();
    
    URL.revokeObjectURL(url);
}

function initializeDrawingTools() {
    // Initialize Leaflet.draw
    const drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);
    
    const drawControl = new L.Control.Draw({
        edit: {
            featureGroup: drawnItems
        },
        draw: {
            polygon: true,
            polyline: false,
            rectangle: true,
            circle: true,
            marker: false
        }
    });
    
    map.addControl(drawControl);
    
    // Handle drawing events
    map.on(L.Draw.Event.CREATED, function(event) {
        const layer = event.layer;
        drawnItems.addLayer(layer);
        console.log('✏️ Shape drawn:', layer);
    });
}

function toggleDrawing() {
    // This would toggle the drawing tools visibility
    console.log('✏️ Toggle drawing tools');
}

function clearMap() {
    if (currentLayer) {
        map.removeLayer(currentLayer);
        currentLayer = null;
    }
    console.log('🗑️ Map cleared');
}

// Legacy functions for Overview page compatibility
async function loadData() {
    try {
        console.log('📊 Loading data for overview...');
        const response = await fetch('./data_demo/zip_latest.geojson?v=' + Date.now());
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const contentType = response.headers.get('content-type');
        if (!contentType || (!contentType.includes('application/json') && !contentType.includes('application/geo+json'))) {
            throw new Error(`Expected JSON but got: ${contentType}`);
        }
        
        const data = await response.json();
        console.log(`✅ Loaded ${data.features.length} ZIP codes`);
        
        displayStats(data);
        createChart(data);
        displayDataTable(data);
        updateFooter();
        
    } catch (error) {
        console.error('❌ Error loading data:', error);
        document.getElementById('stats').innerHTML = `
            <div style="color: #d32f2f; padding: 20px; text-align: center;">
                <h3>⚠️ Data Loading Error</h3>
                <p>Could not load data. Please check the console for details.</p>
                <p><strong>Error:</strong> ${error.message}</p>
            </div>
        `;
    }
}

function displayStats(data) {
    const statsDiv = document.getElementById('stats');
    if (!statsDiv) return;
    
    const features = data.features;
    const totalZips = features.length;
    
    const zhviValues = features.map(f => f.properties.zhvi).filter(v => v && !isNaN(v));
    const zoriValues = features.map(f => f.properties.zori).filter(v => v && !isNaN(v));
    
    const avgZhvi = zhviValues.length > 0 ? zhviValues.reduce((a, b) => a + b, 0) / zhviValues.length : 0;
    const avgZori = zoriValues.length > 0 ? zoriValues.reduce((a, b) => a + b, 0) / zoriValues.length : 0;
    
    statsDiv.innerHTML = `
        <div class="stat-item">
            <strong>Total ZIP Codes:</strong> ${totalZips.toLocaleString()}
        </div>
        <div class="stat-item">
            <strong>Average Home Value (ZHVI):</strong> $${Math.round(avgZhvi).toLocaleString()}
        </div>
        <div class="stat-item">
            <strong>Average Rent Index (ZORI):</strong> $${Math.round(avgZori).toLocaleString()}
        </div>
        <div class="stat-item">
            <strong>Data Points:</strong> ${zhviValues.length} home values, ${zoriValues.length} rent indices
        </div>
    `;
}

function createChart(data) {
    const canvas = document.getElementById('chart');
    if (!canvas) return;
    
    const features = data.features;
    const topZips = features
        .map(f => ({
            zip: f.properties.zcta,
            zhvi: f.properties.zhvi || 0
        }))
        .filter(f => f.zhvi > 0)
        .sort((a, b) => b.zhvi - a.zhvi)
        .slice(0, 20);
    
    const ctx = canvas.getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: topZips.map(f => f.zip),
            datasets: [{
                label: 'Home Value (ZHVI)',
                data: topZips.map(f => f.zhvi),
                backgroundColor: 'rgba(54, 162, 235, 0.6)',
                borderColor: 'rgba(54, 162, 235, 1)',
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
            }
        }
    });
}

function displayDataTable(data) {
    const tableDiv = document.getElementById('data-table');
    if (!tableDiv) return;
    
    const features = data.features.slice(0, 50); // Show first 50
    
    const tableHTML = `
        <table>
            <thead>
                <tr>
                    <th>ZIP Code</th>
                    <th>Home Value (ZHVI)</th>
                    <th>Rent Index (ZORI)</th>
                    <th>Date</th>
                </tr>
            </thead>
            <tbody>
                ${features.map(f => `
                    <tr>
                        <td>${f.properties.zcta}</td>
                        <td>$${(f.properties.zhvi || 0).toLocaleString()}</td>
                        <td>$${(f.properties.zori || 0).toLocaleString()}</td>
                        <td>${f.properties.date || 'N/A'}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    
    tableDiv.innerHTML = tableHTML;
}

function updateFooter() {
    const zillowDate = document.getElementById('zillow-date');
    const serverDate = document.getElementById('server-date');
    
    if (zillowDate) {
        zillowDate.textContent = new Date().toLocaleDateString();
    }
    if (serverDate) {
        serverDate.textContent = new Date().toLocaleString();
    }
}

// Load data for overview page
loadData();