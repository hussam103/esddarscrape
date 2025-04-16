// Tenders.js - For handling tenders listing and details

// DataTable instance
let tendersTable;

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
        serverSide: false,  // We'll handle pagination on the server side manually
        processing: true,
        paging: true,
        ordering: false,  // Disable client-side sorting as we'll use server-side sorting
        searching: false,  // We handle search via our own filters
        lengthMenu: [[25, 50, 100, 300], [25, 50, 100, 300]],
        pageLength: 100,
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
