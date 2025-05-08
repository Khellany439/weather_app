// Main JavaScript file for Weather Cloud Service

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all Bootstrap tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    
    // Initialize all Bootstrap popovers
    const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
    const popoverList = [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
    
    // Setup CSRF token for AJAX requests (if using CSRF protection)
    setupCSRF();
    
    // Setup confirmation dialogs
    setupConfirmations();
});

// Function to setup CSRF protection for AJAX requests
function setupCSRF() {
    // Get CSRF token from meta tag (if present)
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    
    if (csrfToken) {
        // Add CSRF token to all AJAX requests
        document.addEventListener('ajax:beforeSend', function(e) {
            const xhr = e.detail[0];
            xhr.setRequestHeader('X-CSRF-Token', csrfToken);
        });
    }
}

// Function to setup confirmation dialogs
function setupConfirmations() {
    document.querySelectorAll('[data-confirm]').forEach(element => {
        element.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
                e.stopPropagation();
            }
        });
    });
}

// Function to show a notification
function showNotification(message, type = 'info') {
    const alertPlaceholder = document.getElementById('alert-placeholder');
    if (!alertPlaceholder) return;
    
    const wrapper = document.createElement('div');
    wrapper.innerHTML = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    alertPlaceholder.append(wrapper);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        const alert = bootstrap.Alert.getOrCreateInstance(wrapper.querySelector('.alert'));
        alert.close();
    }, 5000);
}