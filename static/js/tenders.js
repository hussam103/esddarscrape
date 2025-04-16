// Tenders.js - For handling tenders listing and details

// DataTable instance
let tendersTable;
let vectorSearchResults = []; // Store vector search results

// Initialize tenders page
document.addEventListener('DOMContentLoaded', function() {
    // Initialize filter dropdowns
    loadOrganizations();
    loadTenderTypes();
    
    // Initialize DataTable
    initializeTendersTable();
    
    // Add event listeners for filter buttons
    document.getElementById('apply-filters').addEventListener('click', applyFilters);
    document.getElementById('reset-filters').addEventListener('click', resetFilters);
    
    // Initialize tender details modal
    initializeTenderDetailsModal();
    
    // Initialize vector search functionality
    initializeVectorSearch();
});

// Format date for display
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return 'N/A';
    
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}

// Load organizations for filter dropdown
function loadOrganizations() {
    fetch('/api/organizations')
        .then(response => response.json())
        .then(organizations => {
            const select = document.getElementById('organization-filter');
            
            // Clear all options except the first one
            while (select.options.length > 1) {
                select.remove(1);
            }
            
            // Add options
            organizations.forEach(org => {
                const option = document.createElement('option');
                option.value = org;
                option.textContent = org;
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error loading organizations:', error);
        });
}

// Load tender types for filter dropdown
function loadTenderTypes() {
    fetch('/api/tender-types')
        .then(response => response.json())
        .then(types => {
            const select = document.getElementById('type-filter');
            
            // Clear all options except the first one
            while (select.options.length > 1) {
                select.remove(1);
            }
            
            // Add options
            types.forEach(type => {
                const option = document.createElement('option');
                option.value = type;
                option.textContent = type;
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error loading tender types:', error);
        });
}

// Initialize tenders DataTable
function initializeTendersTable() {
    // Destroy existing table if it exists
    if (tendersTable) {
        tendersTable.destroy();
    }
    
    // Create DataTable
    tendersTable = $('#tendersTable').DataTable({
        serverSide: false,  // Handle in client-side for simpler processing
        processing: true,
        paging: true,
        ordering: false,  // Disable client-side sorting as we'll use server-side sorting
        searching: false,  // We handle search via our own filters
        deferRender: true, // Better performance with large datasets
        lengthMenu: [[25, 50, 100, 300], [25, 50, 100, "All 300"]],
        pageLength: 300,  // Default to 300 entries - show all tenders at once
        language: {
            processing: '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>',
            emptyTable: 'No tenders found'
        },
        ajax: {
            url: '/api/tenders',
            dataSrc: function(json) {
                return json.tenders || [];
            },
            data: function(d) {
                // Add our filter parameters
                d.search = document.getElementById('search-filter').value;
                d.organization = document.getElementById('organization-filter').value;
                d.tender_type = document.getElementById('type-filter').value;
                d.date_from = document.getElementById('date-from').value;
                d.date_to = document.getElementById('date-to').value;
                d.page = (d.start / d.length) + 1;
                d.per_page = d.length;
                return d;
            }
        },
        columns: [
            { 
                data: 'publication_date',
                render: function(data) {
                    return formatDate(data);
                }
            },
            { data: 'reference_number' },
            { 
                data: 'tender_title',
                render: function(data, type, row) {
                    // Truncate long titles
                    if (type === 'display' && data && data.length > 50) {
                        return `<span title="${data}">${data.substring(0, 50)}...</span>`;
                    }
                    return data;
                }
            },
            { data: 'organization' },
            { data: 'tender_type' },
            { 
                data: 'submission_deadline',
                render: function(data) {
                    return formatDate(data);
                }
            },
            { 
                data: 'similarity_score',
                render: function(data) {
                    if (!data) return '';
                    
                    // Extract the percentage value without the % sign
                    const value = parseFloat(data);
                    
                    // Determine appropriate color based on raw match score
                    // Raw similarity scores are typically between 0.65-0.95
                    let colorClass = 'bg-secondary';
                    if (value >= 90) {
                        colorClass = 'bg-success'; // Excellent match: green
                    } else if (value >= 85) {
                        colorClass = 'bg-info';    // Good match: blue
                    } else if (value >= 80) {
                        colorClass = 'bg-primary'; // Moderate match: primary blue
                    } else if (value >= 75) {
                        colorClass = 'bg-warning'; // Fair match: yellow/orange
                    } else {
                        colorClass = 'bg-danger';  // Poor match: red
                    }
                    
                    // Create a progress bar with color coding (without match label)
                    return `
                        <div class="progress" style="height: 20px;">
                            <div class="progress-bar ${colorClass}" role="progressbar" 
                                style="width: ${data};" aria-valuenow="${value}" 
                                aria-valuemin="0" aria-valuemax="100">
                                ${data}
                            </div>
                        </div>
                    `;
                }
            },
            {
                data: null,
                render: function(data, type, row) {
                    return `
                        <button class="btn btn-sm btn-info view-details" data-tender-id="${row.tender_id}">
                            <i class="fas fa-eye"></i> Details
                        </button>
                        <a href="${row.tender_url}" target="_blank" class="btn btn-sm btn-secondary">
                            <i class="fas fa-external-link-alt"></i> Etimad
                        </a>
                    `;
                }
            }
        ],
        drawCallback: function() {
            // Add event listeners to the "View Details" buttons
            document.querySelectorAll('.view-details').forEach(button => {
                button.addEventListener('click', function() {
                    const tenderId = this.getAttribute('data-tender-id');
                    showTenderDetails(tenderId);
                });
            });
        }
    });
}

// Apply filters to the table
function applyFilters() {
    tendersTable.ajax.reload();
}

// Reset all filters
function resetFilters() {
    document.getElementById('search-filter').value = '';
    document.getElementById('organization-filter').value = '';
    document.getElementById('type-filter').value = '';
    document.getElementById('date-from').value = '';
    document.getElementById('date-to').value = '';
    
    tendersTable.ajax.reload();
}

// Initialize tender details modal
function initializeTenderDetailsModal() {
    // Create modal instance
    const tenderDetailsModal = new bootstrap.Modal(document.getElementById('tenderDetailsModal'));
    
    // Listen for modal hidden event to clear content
    document.getElementById('tenderDetailsModal').addEventListener('hidden.bs.modal', function() {
        document.getElementById('tender-details-content').style.display = 'none';
        document.getElementById('modal-loader').style.display = 'flex';
        
        // Clear content
        document.getElementById('tender-title').textContent = '';
        document.getElementById('tender-reference').textContent = '';
        document.getElementById('tender-organization').textContent = '';
        document.getElementById('tender-type').textContent = '';
        document.getElementById('tender-publication-date').textContent = '';
        document.getElementById('tender-submission-deadline').textContent = '';
        document.getElementById('tender-inquiry-deadline').textContent = '';
        document.getElementById('tender-opening-date').textContent = '';
        document.getElementById('tender-duration').textContent = '';
        document.getElementById('tender-city').textContent = '';
        document.getElementById('tender-price').textContent = '';
        document.getElementById('tender-activities').textContent = '';
        document.getElementById('tender-url').href = '#';
    });
}

// Show tender details in modal
function showTenderDetails(tenderId) {
    const modal = new bootstrap.Modal(document.getElementById('tenderDetailsModal'));
    modal.show();
    
    // Show loader, hide content
    document.getElementById('tender-details-content').style.display = 'none';
    document.getElementById('modal-loader').style.display = 'flex';
    
    // Fetch tender details
    fetch(`/api/tenders/${tenderId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(tender => {
            // Hide loader, show content
            document.getElementById('modal-loader').style.display = 'none';
            document.getElementById('tender-details-content').style.display = 'block';
            
            // Populate modal with tender details
            document.getElementById('tender-title').textContent = tender.tender_title || 'N/A';
            document.getElementById('tender-reference').textContent = tender.reference_number || 'N/A';
            document.getElementById('tender-organization').textContent = tender.organization || 'N/A';
            document.getElementById('tender-type').textContent = tender.tender_type || 'N/A';
            document.getElementById('tender-publication-date').textContent = formatDate(tender.publication_date);
            document.getElementById('tender-submission-deadline').textContent = formatDate(tender.submission_deadline);
            document.getElementById('tender-inquiry-deadline').textContent = formatDate(tender.inquiry_deadline);
            document.getElementById('tender-opening-date').textContent = formatDate(tender.opening_date);
            document.getElementById('tender-duration').textContent = tender.duration || 'N/A';
            document.getElementById('tender-city').textContent = tender.city || 'N/A';
            document.getElementById('tender-price').textContent = tender.price || 'N/A';
            document.getElementById('tender-activities').textContent = tender.main_activities || 'N/A';
            document.getElementById('tender-url').href = tender.tender_url || '#';
            
            // Set modal title
            document.getElementById('tenderDetailsModalLabel').textContent = `Tender Details - ${tender.reference_number || 'N/A'}`;
        })
        .catch(error => {
            console.error('Error fetching tender details:', error);
            
            // Hide loader, show error message
            document.getElementById('modal-loader').style.display = 'none';
            document.getElementById('tender-details-content').style.display = 'block';
            document.getElementById('tender-details-content').innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Error loading tender details. Please try again later.
                </div>
            `;
        });
}

// Initialize vector search functionality
function initializeVectorSearch() {
    // Load embeddings stats
    loadEmbeddingsStats();
    
    // Add event listeners
    document.getElementById('run-vector-search').addEventListener('click', performVectorSearch);
    document.getElementById('generate-embeddings').addEventListener('click', generateEmbeddings);
    document.getElementById('regenerate-all-embeddings').addEventListener('click', regenerateAllEmbeddings);
    
    // Initialize tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    
    // Add event listener for tab switch to reload stats
    const vectorTab = document.getElementById('vector-tab');
    vectorTab.addEventListener('shown.bs.tab', function (e) {
        loadEmbeddingsStats();
    });
    
    // Allow searching with Enter key
    document.getElementById('vector-query').addEventListener('keyup', function(event) {
        if (event.key === 'Enter') {
            performVectorSearch();
        }
    });
}

// Load embeddings statistics
function loadEmbeddingsStats() {
    const statsContainer = document.getElementById('vector-embeddings-stats');
    statsContainer.innerHTML = '<div class="spinner-border spinner-border-sm text-primary" role="status"><span class="visually-hidden">Loading...</span></div> Loading stats...';
    
    fetch('/api/embeddings/stats')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(stats => {
            let html = '<div class="mt-2 small">';
            html += `<p><strong>Tenders with embeddings:</strong> ${stats.tenders_with_embeddings} / ${stats.total_tenders}</p>`;
            
            if (stats.tenders_needing_embeddings > 0) {
                html += `<p class="text-warning"><strong>Tenders needing embeddings:</strong> ${stats.tenders_needing_embeddings}</p>`;
            } else {
                html += '<p class="text-success"><strong>All eligible tenders have embeddings</strong></p>';
            }
            
            html += '</div>';
            statsContainer.innerHTML = html;
            
            // Enable/disable generate button based on needs
            const generateButton = document.getElementById('generate-embeddings');
            if (stats.tenders_needing_embeddings > 0) {
                generateButton.removeAttribute('disabled');
                generateButton.classList.remove('btn-outline-secondary');
                generateButton.classList.add('btn-secondary');
            } else {
                generateButton.setAttribute('disabled', 'disabled');
                generateButton.classList.remove('btn-secondary');
                generateButton.classList.add('btn-outline-secondary');
            }
        })
        .catch(error => {
            console.error('Error loading embeddings stats:', error);
            statsContainer.innerHTML = '<div class="alert alert-danger small">Error loading embedding statistics</div>';
        });
}

// Generate embeddings for tenders that need them
function generateEmbeddings() {
    const button = document.getElementById('generate-embeddings');
    const statusContainer = document.getElementById('vector-status');
    
    // Disable button during generation
    button.setAttribute('disabled', 'disabled');
    button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generating...';
    
    statusContainer.innerHTML = '<div class="alert alert-info">Generating embeddings, please wait...</div>';
    
    fetch('/api/embeddings/generate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ limit: 50 }) // Process up to 50 tenders at a time
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(result => {
            statusContainer.innerHTML = `<div class="alert alert-success">Successfully generated ${result.created} embeddings</div>`;
            loadEmbeddingsStats(); // Refresh stats after generation
            
            // Re-enable button
            button.removeAttribute('disabled');
            button.textContent = 'Generate Embeddings';
        })
        .catch(error => {
            console.error('Error generating embeddings:', error);
            statusContainer.innerHTML = '<div class="alert alert-danger">Error generating embeddings</div>';
            
            // Re-enable button
            button.removeAttribute('disabled');
            button.textContent = 'Generate Embeddings';
        });
}

// Perform vector search
function performVectorSearch() {
    const query = document.getElementById('vector-query').value.trim();
    const limit = document.getElementById('vector-limit').value;
    const statusContainer = document.getElementById('vector-status');
    
    if (!query) {
        statusContainer.innerHTML = '<div class="alert alert-warning">Please enter a search query</div>';
        return;
    }
    
    statusContainer.innerHTML = '<div class="alert alert-info"><div class="spinner-border spinner-border-sm text-primary me-2" role="status"></div> Searching...</div>';
    
    // Perform vector search
    fetch(`/api/vector-search?query=${encodeURIComponent(query)}&limit=${limit}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(result => {
            if (result.results && result.results.length > 0) {
                vectorSearchResults = result.results;
                updateTableWithVectorResults();
                
                // Switch to the results tab
                document.getElementById('filter-tab').classList.remove('active');
                document.getElementById('filter-tab-pane').classList.remove('show', 'active');
                
                // Show success message
                statusContainer.innerHTML = `<div class="alert alert-success">Found ${result.results.length} matching tenders</div>`;
            } else {
                statusContainer.innerHTML = '<div class="alert alert-warning">No matching tenders found. Try a different query.</div>';
            }
        })
        .catch(error => {
            console.error('Error performing vector search:', error);
            statusContainer.innerHTML = '<div class="alert alert-danger">Error performing search. Please try again later.</div>';
        });
}

// Update DataTable with vector search results
function updateTableWithVectorResults() {
    // Clear the table
    tendersTable.clear();
    
    // Extract the tender objects from the vector search results and add similarity scores
    // Vector search returns objects with {tender: {...}, similarity: 0.95} structure
    const flattenedResults = vectorSearchResults.map(item => {
        // Create a new object with tender data plus similarity score
        const tenderWithScore = {...item.tender};
        
        // Use raw similarity score directly without any buffering
        const rawScore = item.similarity;
        
        // Convert to percentage (0.0-1.0 to 0-100%)
        const exactPercentage = (rawScore * 100).toFixed(2);
        tenderWithScore.similarity_score = `${exactPercentage}%`;
        // Store the raw score for debugging/sorting
        tenderWithScore.raw_similarity = rawScore;
        
        return tenderWithScore;
    });
    
    // Add the flattened results to the table
    tendersTable.rows.add(flattenedResults);
    tendersTable.draw();
}
