import { CampaignAPI } from './api.js';

export class CampaignTable {
    constructor() {
        this.currentSorts = [];
        this.originalRows = [];
        this.tbody = document.querySelector('tbody');
    }

    initialize() {
        // Store original rows
        this.originalRows = Array.from(this.tbody.querySelectorAll('tr'));
        
        // Initialize row numbers
        this.updateRowNumbers();
        
        // Initialize sortable headers
        this.initializeSortableHeaders();
        
        // Initialize button handlers
        this.initializeButtonHandlers();
        
        // Initialize row click handlers
        this.initializeRowHandlers();
    }

    updateRowNumbers() {
        this.originalRows.forEach((row, index) => {
            row.querySelector('.row-number').textContent = index + 1;
        });
    }

    initializeSortableHeaders() {
        const headers = document.querySelectorAll('th.sortable');
        headers.forEach(header => {
            header.addEventListener('click', () => this.handleHeaderClick(header));
        });
    }

    handleHeaderClick(header) {
        const sortField = header.dataset.sort;
        const currentDirection = header.classList.contains('asc') ? 'asc' : 
                               header.classList.contains('desc') ? 'desc' : null;
        
        let newDirection;
        if (!currentDirection) {
            newDirection = 'asc';
        } else if (currentDirection === 'asc') {
            newDirection = 'desc';
        } else {
            // Remove sorting for this column
            header.classList.remove('desc');
            const orderIndicator = header.querySelector('.sort-order');
            if (orderIndicator) {
                orderIndicator.remove();
            }
            this.currentSorts = this.currentSorts.filter(sort => sort.field !== sortField);
            this.updateSortOrderIndicators();
            this.updateTable();
            return;
        }

        // Remove existing sort for this field
        this.currentSorts = this.currentSorts.filter(sort => sort.field !== sortField);
        
        // Add new sort
        this.currentSorts.push({
            field: sortField,
            direction: newDirection,
            order: this.currentSorts.length + 1
        });

        // Update header classes
        header.classList.remove('asc', 'desc');
        header.classList.add(newDirection);

        // Update sort order indicator
        this.updateSortOrderIndicator(header, this.currentSorts.length);

        this.updateTable();
    }

    updateSortOrderIndicators() {
        this.currentSorts.forEach((sort, index) => {
            const header = document.querySelector(`th[data-sort="${sort.field}"]`);
            const indicator = header.querySelector('.sort-order');
            if (indicator) {
                indicator.textContent = index + 1;
            }
        });
    }

    updateSortOrderIndicator(header, order) {
        let orderIndicator = header.querySelector('.sort-order');
        if (!orderIndicator) {
            orderIndicator = document.createElement('span');
            orderIndicator.className = 'sort-order';
            header.appendChild(orderIndicator);
        }
        orderIndicator.textContent = order;
    }

    updateTable() {
        // Clone original rows for sorting
        let rows = this.originalRows.map(row => row.cloneNode(true));
        
        // Apply multiple sorts
        if (this.currentSorts.length > 0) {
            rows.sort((a, b) => {
                for (const sort of this.currentSorts) {
                    const aValue = this.getRowValue(a, sort.field);
                    const bValue = this.getRowValue(b, sort.field);
                    
                    const order = sort.direction === 'asc' ? 1 : -1;
                    
                    if (aValue < bValue) return -1 * order;
                    if (aValue > bValue) return 1 * order;
                }
                return 0;
            });
        }
        
        // Update table
        this.tbody.innerHTML = '';
        rows.forEach((row, index) => {
            row.querySelector('.row-number').textContent = index + 1;
            this.tbody.appendChild(row);
        });

        // Reattach all event handlers
        this.initializeButtonHandlers();
        this.initializeRowHandlers();
    }

    getRowValue(row, sortField) {
        switch (sortField) {
            case 'code':
                return row.querySelector('td:nth-child(2)').textContent.toLowerCase();
            case 'title':
                return row.querySelector('td:nth-child(3)').textContent.toLowerCase();
            case 'location':
                return row.querySelector('td:nth-child(4)').textContent.toLowerCase();
            case 'status':
                return row.querySelector('td:nth-child(5) .badge').textContent.toLowerCase();
            case 'created_at':
                const dateText = row.querySelector('td:nth-child(7)').textContent;
                const [datePart, timePart] = dateText.split(' ');
                const [day, month, year] = datePart.split('.');
                const [hours, minutes] = timePart.split(':');
                return new Date(year, month - 1, day, hours, minutes).getTime();
            default:
                return 0;
        }
    }

    initializeButtonHandlers() {
        // Handle copy link buttons
        this.tbody.querySelectorAll('.copy-link').forEach(button => {
            button.addEventListener('click', async (e) => {
                e.stopPropagation();
                const campaignId = button.dataset.campaignId;
                const link = button.dataset.link;
                
                try {
                    if (!link) {
                        throw new Error('Brak linku do skopiowania. Najpierw wygeneruj link.');
                    }

                    // Try using the modern Clipboard API
                    if (navigator.clipboard && window.isSecureContext) {
                        await navigator.clipboard.writeText(link);
                        showToast('Link został skopiowany do schowka', 'success');
                    } else {
                        // Fallback for older browsers or non-HTTPS
                        const textArea = document.createElement('textarea');
                        textArea.value = link;
                        textArea.style.position = 'fixed';
                        textArea.style.left = '-999999px';
                        textArea.style.top = '-999999px';
                        document.body.appendChild(textArea);
                        textArea.focus();
                        textArea.select();
                        
                        try {
                            document.execCommand('copy');
                            textArea.remove();
                            showToast('Link został skopiowany do schowka', 'success');
                        } catch (err) {
                            console.error('Failed to copy text: ', err);
                            showToast('Nie udało się skopiować linku. Spróbuj ponownie.', 'error');
                            textArea.remove();
                        }
                    }
                } catch (err) {
                    console.error('Failed to copy link:', err);
                    showToast(err.message || 'Nie udało się skopiować linku. Spróbuj ponownie.', 'error');
                }
            });
        });

        // Handle generate link buttons
        this.tbody.querySelectorAll('.generate-link-list').forEach(button => {
            button.addEventListener('click', async (e) => {
                e.stopPropagation();
                const campaignId = button.dataset.campaignId;
                await this.generateLink(campaignId);
            });
        });

        // Handle edit buttons
        this.tbody.querySelectorAll('.btn-warning').forEach(button => {
            button.addEventListener('click', (e) => {
                e.stopPropagation();
                const campaignId = button.dataset.campaignId;
                // Emit event before showing modal
                document.dispatchEvent(new CustomEvent('editCampaign', {
                    detail: { campaignId }
                }));
            });
        });

        // Handle clone buttons
        this.tbody.querySelectorAll('.btn-info').forEach(button => {
            button.addEventListener('click', async (e) => {
                e.stopPropagation();
                const campaignId = button.dataset.campaignId;
                try {
                    const campaign = await CampaignAPI.getCampaign(campaignId);
                    document.dispatchEvent(new CustomEvent('cloneCampaign', {
                        detail: { campaign }
                    }));
                } catch (error) {
                    console.error('Error:', error);
                    showToast('Nie udało się sklonować kampanii', 'error');
                }
            });
        });

        // Handle delete buttons
        this.tbody.querySelectorAll('.btn-danger').forEach(button => {
            button.addEventListener('click', async (e) => {
                e.stopPropagation();
                const campaignId = button.dataset.campaignId;
                await this.deleteCampaign(campaignId);
            });
        });
    }

    async generateLink(campaignId) {
        const button = this.tbody.querySelector(`[data-campaign-id="${campaignId}"].generate-link-list`);
        const originalText = button.textContent;
        
        try {
            button.disabled = true;
            button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generowanie...';

            await CampaignAPI.generateLink(campaignId);
            const html = await fetch('/campaigns/').then(r => r.text());
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = html;
            
            const newTbody = tempDiv.querySelector('tbody');
            if (newTbody) {
                this.originalRows = Array.from(newTbody.querySelectorAll('tr'));
                this.updateTable();
                showToast('Link został wygenerowany', 'success');
            }
        } catch (error) {
            console.error('Error:', error);
            showToast(error.message, 'error');
            button.disabled = false;
            button.textContent = originalText;
        }
    }

    async deleteCampaign(campaignId) {
        if (confirm('Czy na pewno chcesz usunąć tę kampanię?')) {
            const button = this.tbody.querySelector(`tr[data-campaign-id="${campaignId}"] .btn-danger`);
            const originalText = button.textContent;
            
            try {
                button.disabled = true;
                button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Usuwanie...';

                await CampaignAPI.deleteCampaign(campaignId);
                const html = await fetch('/campaigns/').then(r => r.text());
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = html;
                
                const newTbody = tempDiv.querySelector('tbody');
                if (newTbody) {
                    this.originalRows = Array.from(newTbody.querySelectorAll('tr'));
                    this.updateTable();
                    showToast('Kampania została usunięta', 'success');
                }
            } catch (error) {
                console.error('Error:', error);
                showToast(error.message, 'error');
                button.disabled = false;
                button.textContent = originalText;
            }
        }
    }

    updateTableData(newRows) {
        this.originalRows = newRows;
        this.updateTable();
    }

    initializeRowHandlers() {
        if (!this.tbody) return;
        
        this.tbody.querySelectorAll('tr').forEach(row => {
            row.addEventListener('dblclick', (e) => {
                e.stopPropagation();
                const campaignId = row.dataset.campaignId;
                if (campaignId) {
                    document.dispatchEvent(new CustomEvent('editCampaign', {
                        detail: { campaignId }
                    }));
                }
            });
        });
    }
} 