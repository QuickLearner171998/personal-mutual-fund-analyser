// API Client for MF Portfolio Analyzer Backend
// Handles all communication with FastAPI backend

const API_BASE = 'http://localhost:8000';

class PortfolioAPI {
    constructor(baseURL = API_BASE) {
        this.baseURL = baseURL;
    }

    // Helper method for fetch with error handling
    async request(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers,
                },
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || error.message || 'Request failed');
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // Health and Status
    async health() {
        return this.request('/api/health');
    }

    async status() {
        return this.request('/api/status');
    }

    // Portfolio Endpoints
    async getPortfolioSummary() {
        return this.request('/api/portfolio/summary');
    }

    async getHoldings(filters = {}) {
        const params = new URLSearchParams(filters);
        return this.request(`/api/portfolio/holdings?${params}`);
    }

    async getHoldingByFolio(folio) {
        return this.request(`/api/portfolio/holdings/${folio}`);
    }

    // SIP Endpoints
    async getSIPs() {
        return this.request('/api/sips');
    }

    async getUpcomingSIPs(days = 30) {
        return this.request(`/api/sips/upcoming?days=${days}`);
    }

    async getSIPAnalytics() {
        return this.request('/api/sips/analytics');
    }

    // Broker Endpoints
    async getBrokers() {
        return this.request('/api/brokers');
    }

    async getBrokerHoldings(brokerName) {
        return this.request(`/api/brokers/${encodeURIComponent(brokerName)}/holdings`);
    }

    // Allocation Endpoints
    async getAllocationByType() {
        return this.request('/api/allocation/type');
    }

    async getAllocationByCategory() {
        return this.request('/api/allocation/category');
    }

    // Chat Endpoints
    async sendMessage(message) {
        return this.request('/api/chat', {
            method: 'POST',
            body: JSON.stringify({ message }),
        });
    }

    async getChatHistory(limit = 50) {
        return this.request(`/api/chat/history?limit=${limit}`);
    }

    async clearChatHistory() {
        return this.request('/api/chat/history', {
            method: 'DELETE',
        });
    }

    // Upload Endpoints
    async uploadFiles(excelFile, transactionJSON, xirrJSON) {
        const formData = new FormData();
        formData.append('excel_file', excelFile);
        formData.append('transaction_json', transactionJSON);
        formData.append('xirr_json', xirrJSON);

        try {
            const response = await fetch(`${this.baseURL}/api/upload`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Upload failed');
            }

            return await response.json();
        } catch (error) {
            console.error('Upload Error:', error);
            throw error;
        }
    }

    async deletePortfolio() {
        return this.request('/api/upload', {
            method: 'DELETE',
        });
    }
}

// Create global API instance
const api = new PortfolioAPI();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { PortfolioAPI, api };
}
