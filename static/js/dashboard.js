// Dashboard.js - For handling dashboard functionality

// Global chart instances to destroy and recreate them
let typeChart, dateChart, orgChart;

// Format date for display in Saudi Arabia time (GMT+3)
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    // Parse the date string
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return 'N/A';
    
    // Format it with explicit Saudi Arabia time zone (GMT+3)
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        timeZone: 'Asia/Riyadh'  // Saudi Arabia timezone
    }).format(date);
}

// Load dashboard data
function loadDashboardData() {
    fetch('/api/stats')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Update summary stats
            document.getElementById('total-tenders').textContent = data.total_tenders || 0;
            
            // Update last scrape info
            if (data.latest_logs && data.latest_logs.length > 0) {
                const lastLog = data.latest_logs[0];
                const statusElement = document.getElementById('last-scrape-status');
                statusElement.textContent = lastLog.status;
                
                // Apply appropriate color
                statusElement.className = 'display-6';
                if (lastLog.status === 'SUCCESS') {
                    statusElement.classList.add('text-success');
                } else if (lastLog.status === 'ERROR') {
                    statusElement.classList.add('text-danger');
                } else if (lastLog.status === 'RUNNING') {
                    statusElement.classList.add('text-warning');
                }
                
                document.getElementById('last-scrape-time').textContent = 
                    `Last run: ${formatDate(lastLog.start_time)}`;
                
                document.getElementById('new-tenders').textContent = lastLog.new_tenders || 0;
            }
            
            // Create or update charts
            createTendersByTypeChart(data.tenders_by_type);
            createTendersByDateChart(data.tenders_by_date);
            createTendersByOrgChart(data.tenders_by_organization);
            
            // Update logs table
            updateLogsTable(data.latest_logs);
        })
        .catch(error => {
            console.error('Error loading dashboard data:', error);
            // Show error message on the page
            for (const elementId of ['total-tenders', 'last-scrape-status', 'new-tenders']) {
                document.getElementById(elementId).innerHTML = '<span class="text-danger">Error loading data</span>';
            }
        });
}

// Create chart for tenders by type
function createTendersByTypeChart(data) {
    const ctx = document.getElementById('tendersByTypeChart').getContext('2d');
    
    // Destroy previous chart if it exists
    if (typeChart) {
        typeChart.destroy();
    }
    
    // Prepare data
    const labels = data.map(item => item.type);
    const values = data.map(item => item.count);
    
    // Generate colors
    const backgroundColors = generateChartColors(data.length);
    
    // Create chart
    typeChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: backgroundColors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                }
            }
        }
    });
}

// Create chart for tenders by date
function createTendersByDateChart(data) {
    const ctx = document.getElementById('tendersByDateChart').getContext('2d');
    
    // Destroy previous chart if it exists
    if (dateChart) {
        dateChart.destroy();
    }
    
    // Sort data by date
    data.sort((a, b) => new Date(a.date) - new Date(b.date));
    
    // Prepare data
    const labels = data.map(item => item.date);
    const values = data.map(item => item.count);
    
    // Create chart
    dateChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Number of Tenders',
                data: values,
                borderColor: '#0d6efd',
                backgroundColor: 'rgba(13, 110, 253, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

// Create chart for tenders by organization
function createTendersByOrgChart(data) {
    const ctx = document.getElementById('tendersByOrgChart').getContext('2d');
    
    // Destroy previous chart if it exists
    if (orgChart) {
        orgChart.destroy();
    }
    
    // Sort data by count in descending order
    data.sort((a, b) => b.count - a.count);
    
    // Prepare data
    const labels = data.map(item => item.organization);
    const values = data.map(item => item.count);
    
    // Generate colors
    const backgroundColors = generateChartColors(data.length);
    
    // Create chart
    orgChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Number of Tenders',
                data: values,
                backgroundColor: backgroundColors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

// Generate color array for charts
function generateChartColors(count) {
    const colors = [
        '#3498db', '#2ecc71', '#f1c40f', '#e74c3c', '#9b59b6', 
        '#1abc9c', '#e67e22', '#34495e', '#7f8c8d', '#d35400',
        '#c0392b', '#16a085', '#8e44ad', '#2980b9', '#f39c12'
    ];
    
    // If we need more colors than we have, repeat them
    const result = [];
    for (let i = 0; i < count; i++) {
        result.push(colors[i % colors.length]);
    }
    
    return result;
}

// Update logs table
function updateLogsTable(logs) {
    const tableBody = document.getElementById('logsTableBody');
    tableBody.innerHTML = '';
    
    if (!logs || logs.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="7" class="text-center">No logs found</td>';
        tableBody.appendChild(row);
        return;
    }
    
    logs.forEach(log => {
        const row = document.createElement('tr');
        
        // Set status class
        let statusClass = '';
        if (log.status === 'SUCCESS') {
            statusClass = 'text-success';
        } else if (log.status === 'ERROR') {
            statusClass = 'text-danger';
        } else if (log.status === 'RUNNING') {
            statusClass = 'text-warning';
        }
        
        row.innerHTML = `
            <td>${formatDate(log.start_time)}</td>
            <td>${log.end_time ? formatDate(log.end_time) : 'In progress'}</td>
            <td><span class="${statusClass}">${log.status}</span></td>
            <td>${log.tenders_scraped}</td>
            <td>${log.new_tenders}</td>
            <td>${log.updated_tenders}</td>
            <td>${log.message ? log.message.substring(0, 100) + (log.message.length > 100 ? '...' : '') : ''}</td>
        `;
        
        tableBody.appendChild(row);
    });
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
    
    // Refresh dashboard data every 60 seconds
    setInterval(loadDashboardData, 60000);
});
