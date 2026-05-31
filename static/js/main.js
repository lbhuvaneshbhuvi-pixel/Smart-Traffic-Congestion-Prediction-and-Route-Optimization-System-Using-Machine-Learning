// State Management
let map;
let junctionMarkers = {};
let routePolylines = [];
let shapChart = null;

// Analytics Charts
let volumeHourChart = null;
let weatherSpeedsChart = null;
let congestionDistributionChart = null;
let modelMetricsChart = null;

// Initialize when DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    initClock();
    initDateTimeDefault();
    initMap();
    loadJunctions();
    initCharts();
    
    // Wire up events
    document.getElementById('predictionForm').addEventListener('submit', handlePredictSubmit);
    document.getElementById('weatherTemp').addEventListener('input', e => updateSliderVal('tempVal', e.target.value + '°C'));
    document.getElementById('weatherRain').addEventListener('input', e => {
        updateSliderVal('rainVal', e.target.value + ' mm');
        // Auto-adjust humidity and visibility depending on rainfall
        const rain = parseFloat(e.target.value);
        if (rain > 0) {
            document.getElementById('weatherHumidity').value = Math.min(85 + Math.floor(rain * 0.5), 100);
            if (rain > 15) {
                document.getElementById('weatherVisibility').value = 2;
                updateSliderVal('visibilityVal', '2.0 km');
            } else if (rain > 5) {
                document.getElementById('weatherVisibility').value = 5;
                updateSliderVal('visibilityVal', '5.0 km');
            } else {
                document.getElementById('weatherVisibility').value = 7.5;
                updateSliderVal('visibilityVal', '7.5 km');
            }
        }
    });
    
    document.getElementById('weatherVisibility').addEventListener('input', e => updateSliderVal('visibilityVal', e.target.value + ' km'));
    document.getElementById('resetParamsBtn').addEventListener('click', resetParams);
    
    // Tab changed listener to reload analytics
    const tabEl = document.getElementById('analytics-tab');
    tabEl.addEventListener('shown.bs.tab', () => {
        loadAnalyticsData();
        loadModelComparisonData();
    });
});

// Clock Logic
function initClock() {
    setInterval(() => {
        const now = new Date();
        document.getElementById('liveClock').innerHTML = `<i class="fa-regular fa-clock me-2"></i>${now.toLocaleTimeString()}`;
    }, 1000);
}

// Default Prediction Time to current local time
function initDateTimeDefault() {
    const now = new Date();
    // Offset local timezone
    const tzoffset = now.getTimezoneOffset() * 60000; 
    const localISOTime = (new Date(now - tzoffset)).toISOString().slice(0, 16);
    document.getElementById('predictTime').value = localISOTime;
}

function updateSliderVal(id, val) {
    document.getElementById(id).textContent = val;
}

function resetParams() {
    initDateTimeDefault();
    document.getElementById('forecastHorizon').value = "15";
    document.getElementById('weatherTemp').value = "30";
    document.getElementById('weatherRain').value = "0";
    document.getElementById('weatherVisibility').value = "10";
    document.getElementById('weatherHumidity').value = "70";
    document.getElementById('eventType').value = "None";
    document.getElementById('isHoliday').checked = false;
    
    updateSliderVal('tempVal', '30°C');
    updateSliderVal('rainVal', '0.0 mm');
    updateSliderVal('visibilityVal', '10.0 km');
}

// Leaflet Map Initialization
function initMap() {
    // Tamil Nadu Geographic Center Coordinates
    const tnCoords = [11.0, 78.6];
    map = L.map('map', {
        zoomControl: true,
        scrollWheelZoom: true
    }).setView(tnCoords, 7.5);
    
    // Gorgeous CartoDB Dark Matter tile layer for premium dark aesthetics
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(map);
}

// Load Junction Markers from API
function loadJunctions() {
    fetch('/api/junctions')
        .then(res => res.json())
        .then(junctions => {
            junctions.forEach(j => {
                // Design specialized glowing pulsing markers for traffic nodes
                const marker = L.circleMarker([j.latitude, j.longitude], {
                    radius: 9,
                    fillColor: '#00e676', // Base green (Low)
                    color: '#ffffff',
                    weight: 1.5,
                    opacity: 0.9,
                    fillOpacity: 0.8
                }).addTo(map);
                
                // Add tooltip and popup details
                const popupContent = `
                    <div style="font-family: 'Outfit', sans-serif; padding: 5px;">
                        <h6 style="margin-bottom: 5px; font-weight: 700; color: #fff;">${j.name}</h6>
                        <span style="font-size: 0.75rem; color: #00e5ff; background: rgba(0,229,255,0.1); padding: 2px 6px; border-radius: 4px; display: inline-block; margin-bottom: 8px;">Road Class: ${j.road_type}</span>
                        <p style="margin: 0; font-size: 0.8rem; color: #d1d5db;">Free-flow speed limit: <strong>${j.free_speed} km/h</strong></p>
                    </div>
                `;
                marker.bindPopup(popupContent);
                marker.bindTooltip(j.name, { permanent: false, direction: 'top' });
                
                junctionMarkers[j.id] = marker;
            });
        })
        .catch(err => console.error("Error loading junctions: ", err));
}

// Handle Form Submission for predictions & routing
function handlePredictSubmit(e) {
    e.preventDefault();
    
    const sourceId = parseInt(document.getElementById('sourceJunction').value);
    const destId = parseInt(document.getElementById('destJunction').value);
    
    if (sourceId === destId) {
        alert("Source and Destination junctions cannot be the same!");
        return;
    }
    
    const predictionTime = document.getElementById('predictTime').value;
    const horizon = parseInt(document.getElementById('forecastHorizon').value);
    const temperature = parseFloat(document.getElementById('weatherTemp').value);
    const rainfall = parseFloat(document.getElementById('weatherRain').value);
    const humidity = parseInt(document.getElementById('weatherHumidity').value);
    const visibility = parseFloat(document.getElementById('weatherVisibility').value);
    const eventType = document.getElementById('eventType').value;
    const isHoliday = document.getElementById('isHoliday').checked ? 1 : 0;
    
    const requestData = {
        junction_id: sourceId,
        source_id: sourceId,
        dest_id: destId,
        prediction_time: predictionTime,
        horizon: horizon,
        temperature: temperature,
        rainfall: rainfall,
        humidity: humidity,
        visibility: visibility,
        event_type: eventType,
        holiday_indicator: isHoliday
    };
    
    // Add loading states
    const btn = document.getElementById('analyzeBtn');
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Calculating...`;
    
    // 1. Run standard Traffic prediction
    fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData)
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            updatePredictionUI(data);
        }
    })
    .catch(err => console.error("Prediction error: ", err));
    
    // 2. Fetch routing path suggestions
    fetch('/api/route', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData)
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            updateRoutingUI(data);
        }
    })
    .catch(err => console.error("Routing error: ", err))
    .finally(() => {
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-brain me-2"></i> Predict & Optimize`;
    });
}

// Update UI upon receiving predictions
function updatePredictionUI(data) {
    const levelEl = document.getElementById('resCongestionLevel');
    const badgeEl = document.getElementById('resCongestionBadge');
    
    levelEl.textContent = data.predicted_congestion;
    
    // Clear class list
    levelEl.className = 'mb-0 fw-bold';
    badgeEl.className = 'result-badge d-flex align-items-center justify-content-center';
    
    let colorClass = '';
    let badgeColor = '';
    
    switch (data.predicted_congestion) {
        case "Low Traffic":
            colorClass = 'traffic-low';
            badgeColor = 'badge-low';
            break;
        case "Moderate Traffic":
            colorClass = 'traffic-moderate';
            badgeColor = 'badge-moderate';
            break;
        case "Heavy Traffic":
            colorClass = 'traffic-heavy';
            badgeColor = 'badge-heavy';
            break;
        case "Severe Traffic":
            colorClass = 'traffic-severe';
            badgeColor = 'badge-severe';
            break;
    }
    
    levelEl.classList.add(colorClass);
    badgeEl.classList.add(badgeColor);
    
    document.getElementById('resSpeed').innerHTML = `${data.predicted_speed} <small class="fs-6">km/h</small>`;
    document.getElementById('resFreeSpeed').textContent = `Free-flow: ${data.free_speed} km/h`;
    document.getElementById('resVolume').textContent = data.predicted_volume;
    
    document.getElementById('friendlyExplanation').innerHTML = `<i class="fa-solid fa-circle-info text-info me-2"></i>${data.friendly_explanation}`;
    
    // Draw SHAP chart
    drawShapChart(data.attributions);
}

// Draw/Update SHAP explainable bar chart
function drawShapChart(attributions) {
    const ctx = document.getElementById('shapChart').getContext('2d');
    
    const labels = Object.keys(attributions);
    const values = Object.values(attributions);
    
    // Create color bands (Emerald/Green for negative attribution which helps traffic flow, Red/Orange for positive which increases congestion)
    const backgroundColors = values.map(v => v >= 0 ? 'rgba(255, 61, 0, 0.7)' : 'rgba(0, 230, 118, 0.7)');
    const borderColors = values.map(v => v >= 0 ? '#ff3d00' : '#00e676');
    
    if (shapChart) {
        shapChart.data.labels = labels;
        shapChart.data.datasets[0].data = values;
        shapChart.data.datasets[0].backgroundColor = backgroundColors;
        shapChart.data.datasets[0].borderColor = borderColors;
        shapChart.update();
    } else {
        shapChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Feature Influence Score',
                    data: values,
                    backgroundColor: backgroundColors,
                    borderColor: borderColors,
                    borderWidth: 1.5,
                    borderRadius: 5
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#1f293d',
                        titleColor: '#fff',
                        bodyColor: '#e5e7eb',
                        borderWidth: 1,
                        borderColor: 'rgba(255,255,255,0.1)'
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#9ca3af', font: { family: 'Outfit' } },
                        title: { display: true, text: 'Attribution Impact (SHAP)', color: '#9ca3af', font: { family: 'Outfit', size: 10 } }
                    },
                    y: {
                        grid: { display: false },
                        ticks: { color: '#f3f4f6', font: { family: 'Outfit', size: 10 } }
                    }
                }
            }
        });
    }
}

// Update routing options in UI and draw lines on Leaflet Map
function updateRoutingUI(data) {
    // 1. Clear previous map lines
    routePolylines.forEach(p => map.removeLayer(p));
    routePolylines = [];
    
    const container = document.getElementById('routesList');
    container.innerHTML = '';
    
    const alertEl = document.getElementById('routeSavingsAlert');
    if (data.time_saved_percent > 0) {
        alertEl.classList.remove('d-none');
        document.getElementById('savingsPercent').textContent = `${data.time_saved_percent}%`;
    } else {
        alertEl.classList.add('d-none');
    }
    
    data.routes.forEach((route, idx) => {
        // Draw polyline representing route option
        // Highlight recommended option with glowing color
        const color = route.recommended ? '#00e5ff' : '#9ca3af';
        const weight = route.recommended ? 5 : 3.5;
        const opacity = route.recommended ? 0.9 : 0.65;
        
        const polyline = L.polyline(route.coordinates, {
            color: color,
            weight: weight,
            opacity: opacity,
            dashArray: route.recommended ? null : '6, 6'
        }).addTo(map);
        
        // Add animated flow line if optimal
        if (route.recommended) {
            polyline.bindPopup(`<strong>Optimal Route Recommender</strong><br>Distance: ${route.distance} km<br>Est. Time: ${route.estimated_travel_time} mins`);
        } else {
            polyline.bindPopup(`<strong>Alternative path</strong><br>Distance: ${route.distance} km<br>Est. Time: ${route.estimated_travel_time} mins`);
        }
        
        routePolylines.push(polyline);
        
        // Compile UI segments list inside card
        const recText = route.recommended ? `<span class="badge bg-success-subtle border border-success text-success ms-auto"><i class="fa-solid fa-star me-1"></i> Recommended</span>` : '';
        const delayText = route.delay > 0 ? `<small class="text-danger ms-2"><i class="fa-solid fa-hourglass-half"></i> +${route.delay}m delay</small>` : '<small class="text-success ms-2"><i class="fa-solid fa-bolt"></i> No Delay</small>';
        
        let cBadge = '';
        switch (route.max_congestion) {
            case "Low Traffic": cBadge = 'bg-success'; break;
            case "Moderate Traffic": cBadge = 'bg-warning text-dark'; break;
            case "Heavy Traffic": cBadge = 'bg-danger'; break;
            case "Severe Traffic": cBadge = 'bg-purple'; break;
        }
        
        const routeItem = document.createElement('div');
        routeItem.className = `route-item ${route.recommended ? 'recommended active' : ''}`;
        routeItem.innerHTML = `
            <div class="d-flex align-items-center mb-2">
                <h6 class="mb-0 fw-bold text-white">${route.route_name}</h6>
                ${recText}
            </div>
            <div class="d-flex justify-content-between align-items-center text-white-50 fs-7">
                <span>Distance: <strong>${route.distance} km</strong></span>
                <span>Time: <strong class="text-white fs-5">${route.estimated_travel_time} min</strong> ${delayText}</span>
                <span class="badge ${cBadge} text-uppercase fs-8">${route.max_congestion.split(' ')[0]}</span>
            </div>
        `;
        
        // Clicking a route selects and zooms to its path
        routeItem.addEventListener('click', () => {
            // Mark active
            document.querySelectorAll('.route-item').forEach(el => el.classList.remove('active'));
            routeItem.classList.add('active');
            
            // Adjust polyline opacity
            routePolylines.forEach(p => p.setStyle({ opacity: 0.4, weight: 3 }));
            polyline.setStyle({ opacity: 0.95, weight: 6.5 });
            
            // Zoom bounds
            map.fitBounds(polyline.getBounds(), { padding: [40, 40] });
        });
        
        container.appendChild(routeItem);
    });
    
    // Zoom map out to envelope optimal route path
    if (routePolylines.length > 0) {
        map.fitBounds(routePolylines[0].getBounds(), { padding: [50, 50] });
    }
}

// Initialize placeholder charts for tab 2
function initCharts() {
    // Line Chart: Volume by Hour
    const volCtx = document.getElementById('volumeHourChart').getContext('2d');
    volumeHourChart = new Chart(volCtx, {
        type: 'line',
        data: {
            labels: Array.from({length: 24}, (_, i) => `${i}:00`),
            datasets: [{
                label: 'Traffic Volume (Vehicles/Hour)',
                data: Array(24).fill(0),
                borderColor: '#ffd600',
                backgroundColor: 'rgba(255, 214, 0, 0.1)',
                tension: 0.4,
                fill: true,
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255, 255, 255, 0.05)' } },
                y: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255, 255, 255, 0.05)' } }
            }
        }
    });

    // Bar Chart: Weather Speeds
    const weatherCtx = document.getElementById('weatherSpeedsChart').getContext('2d');
    weatherSpeedsChart = new Chart(weatherCtx, {
        type: 'bar',
        data: {
            labels: ['Clear Weather', 'Rainy'],
            datasets: [{
                data: [0, 0],
                backgroundColor: ['#00e676', '#ff3d00'],
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks: { color: '#9ca3af' }, grid: { display: false } },
                y: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255, 255, 255, 0.05)' }, title: { display: true, text: 'Avg Speed (km/h)', color: '#9ca3af' } }
            }
        }
    });

    // Doughnut: Congestion Levels distribution
    const congCtx = document.getElementById('congestionDistributionChart').getContext('2d');
    congestionDistributionChart = new Chart(congCtx, {
        type: 'doughnut',
        data: {
            labels: ['Low', 'Moderate', 'Heavy', 'Severe'],
            datasets: [{
                data: [0, 0, 0, 0],
                backgroundColor: ['#00e676', '#ff9100', '#ff3d00', '#d500f9'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: { color: '#9ca3af', font: { family: 'Outfit' } }
                }
            }
        }
    });
}

// Load dynamic aggregate trends from DB
function loadAnalyticsData() {
    fetch('/api/trends')
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                // Update Volume Chart
                const volData = Object.values(data.volume_by_hour);
                volumeHourChart.data.datasets[0].data = volData;
                volumeHourChart.update();
                
                // Update Weather Speeds
                const speedsData = [data.speed_by_weather["Clear Weather"], data.speed_by_weather["Rainy"]];
                weatherSpeedsChart.data.datasets[0].data = speedsData;
                weatherSpeedsChart.update();
                
                // Update Distribution Chart
                const distData = [
                    data.congestion_counts["Low Traffic"] || 0,
                    data.congestion_counts["Moderate Traffic"] || 0,
                    data.congestion_counts["Heavy Traffic"] || 0,
                    data.congestion_counts["Severe Traffic"] || 0
                ];
                congestionDistributionChart.data.datasets[0].data = distData;
                congestionDistributionChart.update();
            }
        })
        .catch(err => console.error("Error loading trends: ", err));
}

// Load dynamic ML Model Benchmark scorecard and comparison charts
function loadModelComparisonData() {
    fetch('/api/model_comparison')
        .then(res => res.json())
        .then(data => {
            // Populate comparison table
            const tbody = document.querySelector('#comparisonTable tbody');
            tbody.innerHTML = '';
            
            const models = Object.keys(data);
            const accuracyList = [];
            const f1List = [];
            
            models.forEach(modelName => {
                const metrics = data[modelName];
                accuracyList.push(metrics.Accuracy);
                f1List.push(metrics["F1-Score"]);
                
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td class="fw-bold text-white">${modelName}</td>
                    <td>${(metrics.Accuracy * 100).toFixed(1)}%</td>
                    <td>${(metrics.Precision * 100).toFixed(1)}%</td>
                    <td>${(metrics.Recall * 100).toFixed(1)}%</td>
                    <td><span class="badge bg-success-subtle border border-success text-success">${(metrics["F1-Score"] * 100).toFixed(1)}%</span></td>
                    <td>${(metrics["ROC-AUC"] * 100).toFixed(1)}%</td>
                    <td class="text-white-50">${metrics.TrainingTime}s</td>
                `;
                tbody.appendChild(tr);
            });
            
            // Draw comparative bar charts
            const ctx = document.getElementById('modelMetricsChart').getContext('2d');
            
            if (modelMetricsChart) {
                modelMetricsChart.data.labels = models;
                modelMetricsChart.data.datasets[0].data = f1List;
                modelMetricsChart.data.datasets[1].data = accuracyList;
                modelMetricsChart.update();
            } else {
                modelMetricsChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: models,
                        datasets: [
                            {
                                label: 'F1-Score',
                                data: f1List,
                                backgroundColor: 'rgba(0, 229, 255, 0.75)',
                                borderColor: '#00e5ff',
                                borderWidth: 1,
                                borderRadius: 5
                            },
                            {
                                label: 'Accuracy',
                                data: accuracyList,
                                backgroundColor: 'rgba(213, 0, 249, 0.5)',
                                borderColor: '#d500f9',
                                borderWidth: 1,
                                borderRadius: 5
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                labels: { color: '#e5e7eb', font: { family: 'Outfit' } }
                            }
                        },
                        scales: {
                            x: { ticks: { color: '#9ca3af' }, grid: { display: false } },
                            y: {
                                ticks: { color: '#9ca3af' },
                                grid: { color: 'rgba(255, 255, 255, 0.05)' },
                                min: 0.7,
                                max: 1.0,
                                title: { display: true, text: 'Performance Rate', color: '#9ca3af' }
                            }
                        }
                    }
                });
            }
        })
        .catch(err => console.error("Error loading model comparison scorecard: ", err));
}
