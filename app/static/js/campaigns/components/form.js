import { CampaignAPI } from './api.js';
import { CampaignTests } from './tests.js';

export class CampaignForm {
    constructor(formId) {
        this.form = document.getElementById(formId);
        this.formId = formId;
        this.tests = new CampaignTests(formId);
        this.isEditForm = formId === 'editCampaignForm';
        this.modal = document.getElementById(this.isEditForm ? 'editCampaignModal' : 'addCampaignModal');
        this.submitButton = this.form.querySelector('button[type="submit"]');
        this.spinner = this.submitButton.querySelector('.spinner-border');
        this.buttonText = this.submitButton.querySelector('.button-text');
        
        this.initialize();
    }

    initialize() {
        this.form.addEventListener('submit', this.handleSubmit.bind(this));
        this.tests.initialize();
        
        // Initialize Quill editor
        const editorId = this.isEditForm ? '#editEmailContent' : '#addEmailContent';
        this.quillEditor = new Quill(document.querySelector(editorId), {
            theme: 'snow',
            modules: {
                toolbar: [
                    ['bold', 'italic', 'underline'],
                    [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                    ['clean']
                ]
            },
            placeholder: 'Wprowadź treść wiadomości...'
        });

        this.quillEditor.on('text-change', () => {
            const textarea = this.form.querySelector('textarea[name="interview_email_content"]');
            textarea.value = this.quillEditor.root.innerHTML;
        });

        // Add modal cleanup on any hide
        this.modal.addEventListener('hidden.bs.modal', () => {
            this.cleanupModal();
        });

        // Listen for cloneCampaign event if this is the add form
        if (!this.isEditForm) {
            document.addEventListener('cloneCampaign', this.handleClone.bind(this));
        }
    }

    cleanupModal() {
        // Clean up any existing modal backdrops
        document.querySelectorAll('.modal-backdrop').forEach(backdrop => backdrop.remove());
        document.body.classList.remove('modal-open');
        document.body.style.removeProperty('padding-right');
    }

    async handleClone(event) {
        const campaign = event.detail.campaign;
        if (!campaign) return;

        // Reset form and validation state
        this.resetForm();
        
        // Populate form fields
        this.populateFormFields(campaign);
        
        // Update modal title to indicate cloning
        const modalTitle = this.modal.querySelector('.modal-title');
        if (modalTitle) {
            modalTitle.textContent = 'Duplikuj kampanię';
        }
        
        // Ensure we're using the add endpoint for cloning
        this.form.action = '/campaigns/add';
        
        // Show the modal
        const bsModal = new bootstrap.Modal(this.modal);
        bsModal.show();
    }

    populateFormFields(campaign) {
        // Basic fields
        const fields = [
            'title', 'workplace_location', 'work_start_date', 'contract_type',
            'employment_type', 'salary_range_min', 'salary_range_max', 'duties',
            'requirements', 'employer_offerings', 'job_description',
            'interview_email_subject'
        ];

        // Handle code field separately based on form type
        const codeInput = this.form.querySelector('[name="code"]');
        if (codeInput) {
            if (this.isEditForm) {
                codeInput.value = campaign.code || '';
            } else {
                // For cloning, append "- kopia" to the code
                codeInput.value = campaign.code ? `${campaign.code} - kopia` : '';
            }
        }

        fields.forEach(field => {
            const input = this.form.querySelector(`[name="${field}"]`);
            if (input) {
                input.value = campaign[field] || '';
            }
        });

        // Status checkbox
        const statusCheckbox = this.form.querySelector('[name="is_active"]');
        if (statusCheckbox) {
            statusCheckbox.checked = campaign.is_active;
        }

        // Email content
        if (this.quillEditor) {
            this.quillEditor.root.innerHTML = campaign.interview_email_content || '';
            const textarea = this.form.querySelector('textarea[name="interview_email_content"]');
            if (textarea) {
                textarea.value = campaign.interview_email_content || '';
            }
        }

        // Token expiry days
        const po2ExpiryInput = this.form.querySelector('[name="po2_token_expiry_days"]');
        const po3ExpiryInput = this.form.querySelector('[name="po3_token_expiry_days"]');
        if (po2ExpiryInput) po2ExpiryInput.value = campaign.po2_token_expiry_days || 7;
        if (po3ExpiryInput) po3ExpiryInput.value = campaign.po3_token_expiry_days || 7;

        // Group and tests
        if (campaign.groups && campaign.groups.length > 0) {
            const groupSelect = this.form.querySelector('[name="group_id"]');
            if (groupSelect) {
                groupSelect.value = campaign.groups[0].id;
                this.tests.handleGroupChange().then(() => {
                    // Set test selections and weights after tests are loaded
                    setTimeout(() => {
                        this.setTestSelections(campaign);
                    }, 500);
                });
            }
        }
    }

    setTestSelections(campaign) {
        const testTypes = ['po1', 'po2', 'po2_5', 'po3'];
        testTypes.forEach(type => {
            const testIdField = `${type}_test_id`;
            const weightField = `${type}_test_weight`;
            
            const select = this.form.querySelector(`[name="${testIdField}"]`);
            const weightInput = this.form.querySelector(`[name="${weightField}"]`);
            
            if (select && campaign[testIdField]) {
                select.value = campaign[testIdField];
                select.disabled = false;
            }
            
            if (weightInput && campaign[weightField]) {
                weightInput.value = campaign[weightField];
                weightInput.disabled = false;
            }
        });
        
        // Update dependencies and validate weights
        this.tests.updateDependencies();
        this.tests.validateWeights();
    }

    async handleSubmit(e) {
        e.preventDefault();
        
        // Show loading state
        this.submitButton.disabled = true;
        this.spinner.classList.remove('d-none');
        this.buttonText.textContent = 'Zapisywanie...';
        
        try {
            const formData = new FormData(this.form);
            
            // For cloning, always use the add endpoint
            if (!this.isEditForm) {
                this.form.action = '/campaigns/add';
            }
            
            const response = await fetch(this.form.action, {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                if (data.error === 'CODE_EXISTS') {
                    const codeInput = this.form.querySelector('[name="code"]');
                    codeInput.classList.add('is-invalid');
                    const feedbackDiv = codeInput.nextElementSibling;
                    if (feedbackDiv) {
                        feedbackDiv.style.display = 'block';
                        feedbackDiv.textContent = 'Kampania o takim kodzie już istnieje';
                    }
                    throw new Error('Kampania o takim kodzie już istnieje');
                }
                throw new Error(data.error || 'Wystąpił błąd podczas zapisywania kampanii');
            }
            
            if (data.success) {
                // Store success message
                const message = this.isEditForm ? 'Kampania została zaktualizowana' : 'Kampania została dodana';
                sessionStorage.setItem('pendingToast', JSON.stringify({
                    message,
                    type: 'success'
                }));

                // Hide modal
                const bsModal = bootstrap.Modal.getInstance(this.modal);
                bsModal.hide();

                // Refresh table
                const html = await fetch('/campaigns/').then(r => r.text());
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = html;
                
                const newTbody = tempDiv.querySelector('tbody');
                if (newTbody) {
                    document.dispatchEvent(new CustomEvent('campaignTableUpdate', {
                        detail: { 
                            rows: Array.from(newTbody.querySelectorAll('tr')),
                            shouldReattachListeners: true
                        }
                    }));
                }

                // Show success message
                const pendingToast = sessionStorage.getItem('pendingToast');
                if (pendingToast) {
                    try {
                        const toastData = JSON.parse(pendingToast);
                        showToast(toastData.message, toastData.type);
                    } finally {
                        sessionStorage.removeItem('pendingToast');
                    }
                }
            }
        } catch (error) {
            console.error('Error:', error);
            if (!this.form.querySelector('[name="code"]').classList.contains('is-invalid')) {
                showToast(error.message, 'error');
            }
        } finally {
            // Reset button state
            this.submitButton.disabled = false;
            this.spinner.classList.add('d-none');
            this.buttonText.textContent = this.isEditForm ? 'Zapisz zmiany' : 'Zapisz kampanię';
        }
    }

    resetForm() {
        this.form.reset();
        
        // Clear validation states
        this.form.querySelectorAll('.is-invalid').forEach(el => {
            el.classList.remove('is-invalid');
        });
        
        // Reset code validation
        const codeInput = this.form.querySelector('[name="code"]');
        const feedbackDiv = codeInput.nextElementSibling;
        codeInput.classList.remove('is-invalid');
        if (feedbackDiv) {
            feedbackDiv.style.display = 'none';
            feedbackDiv.textContent = '';
        }
        
        // Reset select elements
        this.form.querySelectorAll('select').forEach(select => {
            select.value = '';
            if (select.name !== 'group_id') {
                select.disabled = true;
            }
        });
        
        // Reset weight inputs
        this.form.querySelectorAll('[name$="_test_weight"]').forEach((input, index) => {
            input.disabled = true;
            input.value = index === 0 ? '100' : '0';
        });
        
        // Reset Quill editor
        if (this.quillEditor) {
            this.quillEditor.root.innerHTML = '';
            const textarea = this.form.querySelector('textarea[name="interview_email_content"]');
            if (textarea) {
                textarea.value = '';
            }
        }
        
        // Hide validation messages
        const validationAlert = this.form.querySelector('#weightValidationAlert');
        if (validationAlert) {
            validationAlert.classList.add('d-none');
        }
        
        // Reset form action if this is the add form
        if (!this.isEditForm) {
            this.form.action = '/campaigns/add';
        }
    }
} 