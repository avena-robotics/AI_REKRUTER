document.addEventListener('DOMContentLoaded', function() {
    // Add this near the beginning of your DOMContentLoaded handler
    const addCampaignModal = document.getElementById('addCampaignModal');
    if (addCampaignModal) {
        addCampaignModal.addEventListener('hidden.bs.modal', resetAddCampaignForm);
    }
    
    // Add this new event listener for the Add Campaign button
    const addCampaignButton = document.querySelector('[data-bs-target="#addCampaignModal"]');
    if (addCampaignButton) {
        addCampaignButton.addEventListener('click', resetAddCampaignForm);
    }
    
    // Handle form submissions
    ['addCampaignForm', 'editCampaignForm'].forEach(formId => {
        const form = document.getElementById(formId);
        if (form) {
            form.addEventListener('submit', handleCampaignFormSubmit);
            // Add change listeners for test selects
            form.querySelectorAll('[name$="_test_id"]').forEach(select => {
                select.addEventListener('change', updateWeightValidation);
            });
        }
    });

    // Handle copy link buttons
    document.querySelectorAll('.copy-link').forEach(button => {
        button.addEventListener('click', async function() {
            const link = this.dataset.link;
            try {
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
                console.error('Failed to copy text: ', err);
                showToast('Nie udało się skopiować linku. Spróbuj ponownie.', 'error');
            }
        });
    });

    // Handle generate link buttons
    document.querySelectorAll('.generate-link-list').forEach(button => {
        button.addEventListener('click', function() {
            const campaignId = this.dataset.campaignId;
            generateLink(campaignId);
        });
    });

    // Reset modal title when opening normally
    document.querySelector('[data-bs-target="#addCampaignModal"]').addEventListener('click', function() {
        document.querySelector('#addCampaignModal .modal-title').textContent = 'Dodaj nową kampanię';
    });

    // Add this to prevent double click from triggering when clicking buttons
    document.querySelectorAll('.btn-group button').forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    });

    document.querySelectorAll('.copy-link, .generate-link-list').forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    });

    // Add input event listener for weight changes
    ['addCampaignForm', 'editCampaignForm'].forEach(formId => {
        const form = document.getElementById(formId);
        if (form) {
            form.querySelectorAll('[name$="_test_weight"]').forEach(weightInput => {
                weightInput.addEventListener('input', () => updateMaxWeights(form));
            });
            
            // Set up change listeners for all test selects
            form.querySelectorAll('[name$="_test_id"]').forEach(select => {
                select.addEventListener('change', () => {
                    updateTestDependencies(form);
                    // Enable/disable corresponding weight input
                    const weightInput = form.querySelector(select.name.replace('_test_id', '_test_weight'));
                    if (weightInput) {
                        weightInput.disabled = !select.value;
                    }
                });
            });
        }
    });

    // Dla modalu dodawania/klonowania
    const addModal = document.getElementById('addCampaignModal');
    if (addModal) {
        addModal.addEventListener('hidden.bs.modal', function() {
            resetAddCampaignForm();
        });
    }
    
    // Dla modalu edycji
    const editModal = document.getElementById('editCampaignModal');
    if (editModal) {
        editModal.addEventListener('hidden.bs.modal', function() {
            const form = document.getElementById('editCampaignForm');
            resetCodeValidation(form);
        });
    }

    // Add input event listener for code fields
    ['addCampaignForm', 'editCampaignForm'].forEach(formId => {
        const form = document.getElementById(formId);
        if (form) {
            const codeInput = form.querySelector('[name="code"]');
            codeInput.addEventListener('input', function() {
                // Clear custom validity on input change
                this.setCustomValidity('');
                this.classList.remove('is-invalid');
                const feedbackDiv = this.nextElementSibling;
                if (feedbackDiv) {
                    feedbackDiv.style.display = 'none';
                }
            });
        }
    });
}); 

function editCampaign(campaignId) {
    fetch(`/campaigns/${campaignId}/data`)
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.error || 'Błąd podczas ładowania danych kampanii');
                });
            }
            return response.json();
        })
        .then(campaign => {
            const form = document.getElementById('editCampaignForm');
            
            // Reset validation state before filling form
            resetCodeValidation(form);
            
            // Populate form fields
            form.action = `/campaigns/${campaignId}/edit`;
            
            // Populate form fields
            form.querySelector('[name="code"]').value = campaign.code || '';
            form.querySelector('[name="title"]').value = campaign.title || '';
            form.querySelector('[name="workplace_location"]').value = campaign.workplace_location || '';
            form.querySelector('[name="work_start_date"]').value = campaign.work_start_date || '';
            form.querySelector('[name="contract_type"]').value = campaign.contract_type || '';
            form.querySelector('[name="employment_type"]').value = campaign.employment_type || '';
            form.querySelector('[name="salary_range_min"]').value = campaign.salary_range_min || '';
            form.querySelector('[name="salary_range_max"]').value = campaign.salary_range_max || '';
            form.querySelector('[name="duties"]').value = campaign.duties || '';
            form.querySelector('[name="requirements"]').value = campaign.requirements || '';
            form.querySelector('[name="employer_offerings"]').value = campaign.employer_offerings || '';
            form.querySelector('[name="job_description"]').value = campaign.job_description || '';
            form.querySelector('[name="is_active"]').checked = campaign.is_active;
            
            // Add these lines to populate token expiry days
            form.querySelector('[name="po2_token_expiry_days"]').value = campaign.po2_token_expiry_days || 7;
            form.querySelector('[name="po3_token_expiry_days"]').value = campaign.po3_token_expiry_days || 7;
            
            // Set group and trigger test updates
            const groupSelect = form.querySelector('[name="group_id"]');
            if (campaign.groups && campaign.groups.length > 0) {
                groupSelect.value = campaign.groups[0].id;
                updateTestOptions(groupSelect);
                
                // Store weights to set after test updates
                const weights = {
                    po1: campaign.po1_test_weight || 0,
                    po2_5: campaign.po2_5_test_weight || 0,
                    po3: campaign.po3_test_weight || 0
                };
                
                // Wait for tests to load before setting test selections
                setTimeout(() => {
                    const po1Select = form.querySelector('[name="po1_test_id"]');
                    const po2Select = form.querySelector('[name="po2_test_id"]');
                    const po2_5Select = form.querySelector('[name="po2_5_test_id"]');
                    const po3Select = form.querySelector('[name="po3_test_id"]');
                    
                    if (campaign.po1_test_id) {
                        po1Select.value = campaign.po1_test_id;
                        po2Select.disabled = false;
                    }
                    
                    if (campaign.po2_test_id) {
                        po2Select.value = campaign.po2_test_id;
                        po2_5Select.disabled = false;
                    }
                    
                    if (campaign.po2_5_test_id) {
                        po2_5Select.value = campaign.po2_5_test_id;
                        po3Select.disabled = false;
                    }
                    
                    if (campaign.po3_test_id) {
                        po3Select.value = campaign.po3_test_id;
                    }
                    
                    // Update dependencies after setting values
                    updateTestDependencies(form);
                    
                    // Set weights after dependencies are updated
                    form.querySelector('[name="po1_test_weight"]').value = weights.po1;
                    form.querySelector('[name="po2_5_test_weight"]').value = weights.po2_5;
                    form.querySelector('[name="po3_test_weight"]').value = weights.po3;
                    
                    // Update max weights after setting values
                    updateMaxWeights(form);
                }, 500);
            }
            
            new bootstrap.Modal(document.getElementById('editCampaignModal')).show();
        })
        .catch(error => {
            console.error('Error:', error);
            showToast(error.message || 'Błąd podczas ładowania danych kampanii', 'error');
        });
}

function confirmDelete(campaignId) {
    if (confirm('Czy na pewno chcesz usunąć tę kampanię?')) {
        fetch(`/campaigns/${campaignId}/delete`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.querySelector(`tr[data-campaign-id="${campaignId}"]`).remove();
                showToast('Kampania została usunięta', 'success');
            } else {
                throw new Error(data.error || 'Wystąpił błąd podczas usuwania kampanii');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast(error.message, 'error');
        });
    }
}

function generateLink(campaignId) {
    fetch(`/campaigns/${campaignId}/generate-link`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.reload();
        } else {
            throw new Error(data.error || 'Wystąpił błąd podczas generowania linku');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast(error.message, 'error');
    });
} 

function handleCampaignFormSubmit(e) {
    e.preventDefault();
    const form = e.target;
    
    // Get elements
    const formData = new FormData(form);
    const code = formData.get('code');
    const campaignId = form.action.includes('/edit') ? form.action.split('/').slice(-2)[0] : null;
    const codeInput = form.querySelector('[name="code"]');
    const feedbackDiv = codeInput.nextElementSibling;
    
    // Get submit button and show loading state
    const submitButton = form.querySelector('button[type="submit"]');
    const spinner = submitButton.querySelector('.spinner-border');
    const buttonText = submitButton.querySelector('.button-text');
    
    // Add validation class only on submit
    form.classList.add('was-validated');
    
    // Check basic form validity first
    if (!form.checkValidity()) {
        return;
    }
    
    // Show loading state
    submitButton.disabled = true;
    spinner.classList.remove('d-none');
    buttonText.textContent = 'Zapisywanie...';
    
    // First check if code exists
    fetch('/campaigns/check-code', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            code: code,
            campaign_id: campaignId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (!data.valid) {
            // Add Bootstrap validation classes for code error
            codeInput.classList.remove('is-valid');
            codeInput.classList.add('is-invalid');
            feedbackDiv.classList.remove('valid-feedback');
            feedbackDiv.classList.add('invalid-feedback');
            feedbackDiv.style.display = 'block';
            feedbackDiv.textContent = 'Kampania o takim kodzie już istnieje';
            
            // Force invalid state for code input
            codeInput.setCustomValidity('Kampania o takim kodzie już istnieje');
            
            submitButton.disabled = false;
            spinner.classList.add('d-none');
            buttonText.textContent = campaignId ? 'Zapisz zmiany' : 'Zapisz kampanię';
            
            throw new Error(data.error);
        } else {
            // Clear custom validity if code is valid
            codeInput.setCustomValidity('');
        }
        
        return fetch(form.action, {
            method: 'POST',
            body: formData
        });
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            sessionStorage.setItem('pendingToast', JSON.stringify({
                message: campaignId ? 'Kampania została zaktualizowana' : 'Kampania została dodana',
                type: 'success'
            }));
            window.location.reload();
        } else {
            throw new Error(data.error || 'Wystąpił błąd podczas zapisywania kampanii');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        if (!codeInput.classList.contains('is-invalid')) {
            showToast(error.message, 'error');
        }
        
        submitButton.disabled = false;
        spinner.classList.add('d-none');
        buttonText.textContent = campaignId ? 'Zapisz zmiany' : 'Zapisz kampanię';
    });
}

function updateTestOptions(groupSelect) {
    const form = groupSelect.closest('form');
    const groupId = groupSelect.value;
    
    // Reset all test selects
    form.querySelectorAll('[name$="_test_id"]').forEach(select => {
        select.innerHTML = '<option value="">Brak</option>';
        select.disabled = true;
    });
    
    if (!groupId) return;
    
    // Fetch tests for selected group
    fetch(`/campaigns/group/${groupId}/tests`)
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.error || 'Błąd podczas pobierania testów');
                });
            }
            return response.json();
        })
        .then(tests => {
            const po1Select = form.querySelector('[name="po1_test_id"]');
            const po2Select = form.querySelector('[name="po2_test_id"]');
            const po2_5Select = form.querySelector('[name="po2_5_test_id"]');
            const po3Select = form.querySelector('[name="po3_test_id"]');
            
            // Enable PO1 select by default
            po1Select.disabled = false;
            
            // Group tests by type
            tests.forEach(test => {
                const option = new Option(
                    `${test.title} - ${test.test_type}`, 
                    test.id
                );
                
                switch(test.test_type) {
                    case 'SURVEY':
                        po1Select.add(option.cloneNode(true));
                        break;
                    case 'EQ':
                        po2Select.add(option.cloneNode(true));
                        break;
                    case 'EQ_EVALUATION':
                        po2_5Select.add(option.cloneNode(true));
                        break;
                    case 'IQ':
                        po3Select.add(option.cloneNode(true));
                        break;
                }
            });
            
            // Update dependencies
            updateTestDependencies(form);
        })
        .catch(error => {
            console.error('Error:', error);
            showToast(error.message || 'Błąd podczas pobierania testów', 'error');
        });
}

function updateTestDependencies(form) {
    const po1Select = form.querySelector('[name="po1_test_id"]');
    const po2Select = form.querySelector('[name="po2_test_id"]');
    const po2_5Select = form.querySelector('[name="po2_5_test_id"]');
    const po3Select = form.querySelector('[name="po3_test_id"]');
    
    const po1Weight = form.querySelector('[name="po1_test_weight"]');
    const po2_5Weight = form.querySelector('[name="po2_5_test_weight"]');
    const po3Weight = form.querySelector('[name="po3_test_weight"]');
    
    // Check if elements exist before using them
    if (po1Weight && po1Select) {
        po1Weight.disabled = po1Select.disabled;
    }
    
    // Handle PO2 dependency on PO1
    if (po2Select) {
        if (!po1Select?.value) {
            po2Select.value = '';
            po2Select.disabled = true; 
        } else {
            po2Select.disabled = false; 
        }
    }
    
    // Handle PO2.5 dependency on PO2
    if (po2_5Select && po2_5Weight) {
        if (!po2Select?.value) {
            po2_5Select.value = '';
            po2_5Select.disabled = true;
            po2_5Weight.value = '0';
            po2_5Weight.disabled = true;
        } else {
            po2_5Select.disabled = false;
            po2_5Weight.disabled = !po2_5Select.value;
        }
    }
    
    // Handle PO3 dependency on PO2.5
    if (po3Select && po3Weight) {
        if (!po2_5Select?.value) {
            po3Select.value = '';
            po3Select.disabled = true;
            po3Weight.value = '0';
            po3Weight.disabled = true;
        } else {
            po3Select.disabled = false;
            po3Weight.disabled = !po3Select.value;
        }
    }
    
    // Update max weights after handling dependencies
    updateMaxWeights(form);
}

function updateMaxWeights(form) {
    const po1Select = form.querySelector('[name="po1_test_id"]');
    const po2Select = form.querySelector('[name="po2_test_id"]');
    const po2_5Select = form.querySelector('[name="po2_5_test_id"]');
    const po3Select = form.querySelector('[name="po3_test_id"]');
    
    const po1Weight = form.querySelector('[name="po1_test_weight"]');
    const po2_5Weight = form.querySelector('[name="po2_5_test_weight"]');
    const po3Weight = form.querySelector('[name="po3_test_weight"]');
    
    // Calculate total used weight excluding the current input
    function getUsedWeightExcluding(excludeInput) {
        let total = 0;
        if (po1Select.value && po1Weight !== excludeInput) {
            total += parseInt(po1Weight.value) || 0;
        }
        if (po2_5Select.value && po2_5Weight !== excludeInput) {
            total += parseInt(po2_5Weight.value) || 0;
        }
        if (po3Select.value && po3Weight !== excludeInput) {
            total += parseInt(po3Weight.value) || 0;
        }
        return total;
    }
    
    // Update max values for each enabled weight input
    if (!po1Select.disabled && po1Select.value) {
        const usedWeight = getUsedWeightExcluding(po1Weight);
        po1Weight.max = 100 - usedWeight;
    }
    

    if (!po2_5Select.disabled && po2_5Select.value) {
        const usedWeight = getUsedWeightExcluding(po2_5Weight);
        po2_5Weight.max = 100 - usedWeight;
    }
    
    if (!po3Select.disabled && po3Select.value) {
        const usedWeight = getUsedWeightExcluding(po3Weight);
        po3Weight.max = 100 - usedWeight;
    }
    
    // Ensure current values don't exceed new max
    [po1Weight, po2_5Weight, po3Weight].forEach(weight => {
        if (parseInt(weight.value) > parseInt(weight.max)) {
            weight.value = weight.max;
        }
    });
}

function cloneCampaign(campaignId) {
    fetch(`/campaigns/${campaignId}/data`)
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.error || 'Błąd podczas ładowania danych kampanii');
                });
            }
            return response.json();
        })
        .then(campaign => {
            const form = document.getElementById('addCampaignForm');
            
            // Reset validation state before filling form
            resetCodeValidation(form);
            
            // Clear code field specifically for cloning
            form.querySelector('[name="code"]').value = '';
            
            // Populate form fields except code
            form.querySelector('[name="title"]').value = campaign.title || '';
            form.querySelector('[name="workplace_location"]').value = campaign.workplace_location || '';
            form.querySelector('[name="work_start_date"]').value = campaign.work_start_date || '';
            form.querySelector('[name="contract_type"]').value = campaign.contract_type || '';
            form.querySelector('[name="employment_type"]').value = campaign.employment_type || '';
            form.querySelector('[name="salary_range_min"]').value = campaign.salary_range_min || '';
            form.querySelector('[name="salary_range_max"]').value = campaign.salary_range_max || '';
            form.querySelector('[name="duties"]').value = campaign.duties || '';
            form.querySelector('[name="requirements"]').value = campaign.requirements || '';
            form.querySelector('[name="employer_offerings"]').value = campaign.employer_offerings || '';
            form.querySelector('[name="job_description"]').value = campaign.job_description || '';
            form.querySelector('[name="is_active"]').checked = campaign.is_active;
            
            // Add these lines to populate token expiry days
            form.querySelector('[name="po2_token_expiry_days"]').value = campaign.po2_token_expiry_days || 7;
            form.querySelector('[name="po3_token_expiry_days"]').value = campaign.po3_token_expiry_days || 7;
            
            // Set group and trigger test updates
            const groupSelect = form.querySelector('[name="group_id"]');
            if (campaign.groups && campaign.groups.length > 0) {
                groupSelect.value = campaign.groups[0].id;
                updateTestOptions(groupSelect);
                
                // Store weights to set after test updates
                const weights = {
                    po1: campaign.po1_test_weight || 0,
                    po2_5: campaign.po2_5_test_weight || 0,
                    po3: campaign.po3_test_weight || 0
                };
                
                // Wait for tests to load before setting test selections
                setTimeout(() => {
                    const po1Select = form.querySelector('[name="po1_test_id"]');
                    const po2Select = form.querySelector('[name="po2_test_id"]');
                    const po2_5Select = form.querySelector('[name="po2_5_test_id"]');
                    const po3Select = form.querySelector('[name="po3_test_id"]');
                    
                    if (campaign.po1_test_id) {
                        po1Select.value = campaign.po1_test_id;
                        po2Select.disabled = false;
                    }
                    
                    if (campaign.po2_test_id) {
                        po2Select.value = campaign.po2_test_id;
                        po2_5Select.disabled = false;
                    }
                    
                    if (campaign.po2_5_test_id) {
                        po2_5Select.value = campaign.po2_5_test_id;
                        po3Select.disabled = false;
                    }
                    
                    if (campaign.po3_test_id) {
                        po3Select.value = campaign.po3_test_id;
                    }
                    
                    // Update dependencies after setting values
                    updateTestDependencies(form);
                    
                    // Set weights after dependencies are updated
                    form.querySelector('[name="po1_test_weight"]').value = weights.po1;
                    form.querySelector('[name="po2_5_test_weight"]').value = weights.po2_5;
                    form.querySelector('[name="po3_test_weight"]').value = weights.po3;
                    
                    // Update max weights after setting values
                    updateMaxWeights(form);
                }, 500);
            }
            
            // Update modal title to indicate duplication
            document.querySelector('#addCampaignModal .modal-title').textContent = 'Duplikuj kampanie';
            
            // Show the modal
            new bootstrap.Modal(document.getElementById('addCampaignModal')).show();
        })
        .catch(error => {
            console.error('Error:', error);
            showToast(error.message || 'Błąd podczas ładowania danych kampanii', 'error');
        });
} 

function updateWeightValidation() {
    const forms = ['addCampaignForm', 'editCampaignForm'];
    forms.forEach(formId => {
        const form = document.getElementById(formId);
        if (form) {
            const po1Select = form.querySelector('[name="po1_test_id"]');
            const po2_5Select = form.querySelector('[name="po2_5_test_id"]');
            const po3Select = form.querySelector('[name="po3_test_id"]');
            
            const po1Weight = form.querySelector('[name="po1_test_weight"]');
            const po2_5Weight = form.querySelector('[name="po2_5_test_weight"]');
            const po3Weight = form.querySelector('[name="po3_test_weight"]');
            
            // Calculate sum of weights for active tests (excluding PO2)
            let sum = 0;
            let activeTests = 0;
            
            if (po1Select.value !== "") {
                sum += parseInt(po1Weight.value) || 0;
                activeTests++;
            }
            if (po2_5Select.value !== "") {
                sum += parseInt(po2_5Weight.value) || 0;
                activeTests++;
            }
            if (po3Select.value !== "") {
                sum += parseInt(po3Weight.value) || 0;
                activeTests++;
            }
            
            // Show/hide validation message
            const validationAlert = form.querySelector('#weightValidationAlert');
            if (activeTests > 0 && sum !== 100) {
                validationAlert.classList.remove('d-none');
            } else {
                validationAlert.classList.add('d-none');
            }
        }
    });
} 

// Dodaj tę funkcję do resetowania stanu walidacji kodu
function resetCodeValidation(form) {
    const codeInput = form.querySelector('[name="code"]');
    const feedbackDiv = codeInput.nextElementSibling;
    
    codeInput.classList.remove('is-invalid');
    form.classList.remove('was-validated');
    if (feedbackDiv) {
        feedbackDiv.style.display = 'none';
        feedbackDiv.textContent = '';
    }
}

// Zmodyfikuj istniejącą funkcję resetAddCampaignForm
function resetAddCampaignForm() {
    const form = document.getElementById('addCampaignForm');
    
    // Reset the form
    form.reset();
    
    // Clear all validation states
    form.querySelectorAll('.is-invalid').forEach(el => {
        el.classList.remove('is-invalid');
    });
    
    // Reset code validation specifically
    resetCodeValidation(form);
    
    // Reset all select elements to default state
    form.querySelectorAll('select').forEach(select => {
        select.value = '';
        if (select.name !== 'group_id') {
            select.disabled = true;
        }
    });
    
    // Reset all weight inputs
    form.querySelectorAll('[name$="_test_weight"]').forEach((input, index) => {
        input.disabled = true;
        input.value = index === 0 ? '100' : '0'; // PO1 weight defaults to 100, others to 0
    });
    
    // Hide validation messages
    form.querySelector('#weightValidationAlert').classList.add('d-none');
    
    // Reset the modal title
    document.querySelector('#addCampaignModal .modal-title').textContent = 'Dodaj nową kampanię';
    
    // Reset the form action to the add endpoint
    form.action = '/campaigns/add';
} 