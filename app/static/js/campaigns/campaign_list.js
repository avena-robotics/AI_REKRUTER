// Import components
import { CampaignTable } from './components/table.js';
import { CampaignForm } from './components/form.js';
import { CampaignAPI } from './components/api.js'; 

document.addEventListener('DOMContentLoaded', function() {
    // Initialize error message toast if exists
    if (document.querySelector('#error_message')) {
        showToast(document.querySelector('#error_message').textContent, 'error');
    }

    // Initialize campaign table
    const campaignTable = new CampaignTable();
    campaignTable.initialize();

    // Initialize forms
    const addForm = new CampaignForm('addCampaignForm');
    const editForm = new CampaignForm('editCampaignForm');

    // Listen for table updates
    document.addEventListener('campaignTableUpdate', (event) => {
        if (event.detail && event.detail.rows) {
            campaignTable.updateTableData(event.detail.rows);
        }
    });

    // Handle edit campaign event
    document.addEventListener('editCampaign', async (event) => {
        const campaignId = event.detail.campaignId;
        try {
            const campaign = await CampaignAPI.getCampaign(campaignId);
            editForm.populateFormFields(campaign);
            editForm.form.action = `/campaigns/${campaignId}/edit`;
            const bsModal = new bootstrap.Modal(document.getElementById('editCampaignModal'));
            bsModal.show();
        } catch (error) {
            console.error('Error:', error);
            showToast('Nie udało się załadować danych kampanii', 'error');
        }
    });

    // Add campaign button click handler
    const addCampaignButton = document.querySelector('[data-bs-target="#addCampaignModal"]');
    if (addCampaignButton) {
        addCampaignButton.addEventListener('click', () => addForm.resetForm());
    }

    // Add event listener for pending toast messages
    window.addEventListener('load', () => {
        const pendingToast = sessionStorage.getItem('pendingToast');
        if (pendingToast) {
            try {
                const toastData = JSON.parse(pendingToast);
                showToast(toastData.message, toastData.type);
            } finally {
                sessionStorage.removeItem('pendingToast');
            }
        }
    });
}); 