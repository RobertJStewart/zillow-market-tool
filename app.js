console.log('✅ Zillow Market Tool frontend loaded');

// Load and display the Zillow data
async function loadData() {
    try {
        // Load the ZIP code data
        const response = await fetch('data_demo/zip_latest.geojson');
        const data = await response.json();
        
        console.log(`📊 Loaded ${data.features.length} ZIP codes`);
        
        // Extract and sort data by home value
        const zipData = data.features
            .map(feature => ({
                zip: feature.properties.zcta,
                zhvi: feature.properties.zhvi || 0,
                zori: isNaN(feature.properties.zori) ? 0 : feature.properties.zori,
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
                <td>$${item.zori.toLocaleString()}</td>
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

// Load data when page loads
document.addEventListener('DOMContentLoaded', loadData);