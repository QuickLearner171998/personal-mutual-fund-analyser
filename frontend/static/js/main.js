// Main JavaScript - Common functionality across all pages

// Show loading overlay
function showLoading(message = 'Loading...') {
    const overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.id = 'loading-overlay';
    overlay.innerHTML = `
    <div>
      <div class="spinner"></div>
      <p style="margin-top: 1rem; color: var(--text-secondary);">${message}</p>
    </div>
  `;
    document.body.appendChild(overlay);
}

// Hide loading overlay
function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.remove();
    }
}

// Show toast notification
function showToast(message, type = 'info') {
    const colors = {
        success: 'var(--success)',
        error: 'var(--danger)',
        warning: 'var(--warning)',
        info: 'var(--info)',
    };

    const toast = document.createElement('div');
    toast.className = 'toast fade-in';
    toast.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: ${colors[type] || colors.info};
    color: white;
    padding: 1rem 1.5rem;
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-lg);
    z-index: 10000;
    max-width: 400px;
  `;
    toast.textContent = message;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.transition = 'opacity var(--transition-base), transform var(--transition-base)';
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Format currency
function formatCurrency(value) {
    if (value === null || value === undefined) return '₹0';
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 0,
    }).format(value);
}

// Format percentage
function formatPercentage(value) {
    if (value === null || value === undefined) return '0.00%';
    return `${value.toFixed(2)}%`;
}

// Format number
function formatNumber(value) {
    if (value === null || value === undefined) return '0';
    return new Intl.NumberFormat('en-IN').format(value);
}

// Get color for gain/loss
function getGainLossColor(value) {
    if (value > 0) return 'var(--success)';
    if (value < 0) return 'var(--danger)';
    return 'var(--text-secondary)';
}

// Highlight active navigation
function highlightActiveNav() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');

    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (currentPath === href || currentPath.startsWith(href) && href !== '/') {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    highlightActiveNav();

    // Add smooth scrolling
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
});

// Error handler
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
});

// Handle API errors
async function handleAPIError(error, defaultMessage = 'An error occurred') {
    console.error('API Error:', error);
    const message = error.message || defaultMessage;
    showToast(message, 'error');
}

// Toggle folio details for aggregated holdings
function toggleFolioDetails(holdingId) {
    const icon = document.querySelector(`[data-holding-id="${holdingId}"] .expand-icon`);
    const detailRows = document.querySelectorAll(`[id^="detail-${holdingId}-"]`);
    
    if (!icon || detailRows.length === 0) return;
    
    const isExpanded = icon.textContent.trim() === '▼';
    
    if (isExpanded) {
        // Collapse
        icon.textContent = '▶';
        detailRows.forEach(row => {
            row.style.display = 'none';
        });
    } else {
        // Expand
        icon.textContent = '▼';
        detailRows.forEach(row => {
            row.style.display = 'table-row';
        });
    }
}
