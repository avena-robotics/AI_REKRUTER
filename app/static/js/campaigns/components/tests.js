import { CampaignAPI } from './api.js';

export class CampaignTests {
    constructor(formId) {
        this.form = document.getElementById(formId);
        if (!this.form) {
            console.warn(`Form with id ${formId} not found`);
            return;
        }

        this.groupSelect = this.form.querySelector('[name="group_id"]');
        this.testSelects = {
            po1: this.form.querySelector('[name="po1_test_id"]'),
            po2: this.form.querySelector('[name="po2_test_id"]'),
            po25: this.form.querySelector('[name="po2_5_test_id"]'),
            po3: this.form.querySelector('[name="po3_test_id"]')
        };
        this.weightInputs = {
            po1: this.form.querySelector('[name="po1_test_weight"]'),
            po2: this.form.querySelector('[name="po2_test_weight"]'),
            po25: this.form.querySelector('[name="po2_5_test_weight"]'),
            po3: this.form.querySelector('[name="po3_test_weight"]')
        };
        this.validationAlert = this.form.querySelector('#weightValidationAlert');
    }

    initialize() {
        if (!this.form) return;

        // Add group change handler
        if (this.groupSelect) {
            this.groupSelect.addEventListener('change', () => this.handleGroupChange());
        }
        
        // Add test select handlers
        Object.entries(this.testSelects).forEach(([type, select]) => {
            if (select) {
                select.addEventListener('change', () => {
                    this.handleTestSelect(type);
                    this.updateDependencies();
                });
            }
        });
        
        // Add weight input handlers
        Object.values(this.weightInputs).forEach(input => {
            if (input) {
                input.addEventListener('input', () => this.validateWeights());
                input.addEventListener('blur', () => this.handleWeightBlur());
            }
        });
    }

    async handleGroupChange() {
        if (!this.groupSelect) return;
        const groupId = this.groupSelect.value;
        
        // Reset all test selects and weights
        Object.entries(this.testSelects).forEach(([key, select]) => {
            if (select) {
                select.innerHTML = '<option value="">Wybierz test</option>';
                select.disabled = !groupId;
            }
        });
        
        Object.entries(this.weightInputs).forEach(([key, input], index) => {
            if (input) {
                input.disabled = !groupId;
                input.value = index === 0 ? '100' : '0';
            }
        });
        
        if (groupId) {
            try {
                const tests = await CampaignAPI.getTestsByGroup(groupId);
                
                // Update test selects with fetched options
                Object.entries(this.testSelects).forEach(([type, select]) => {
                    if (!select) return;
                    
                    // Map test types to match backend values
                    const testTypeMap = {
                        'po1': 'SURVEY',
                        'po2': 'EQ',
                        'po25': 'EQ_EVALUATION',
                        'po3': 'IQ'
                    };
                    
                    const expectedType = testTypeMap[type];
                    const typeTests = tests.filter(test => 
                        test && test.test_type && test.test_type === expectedType
                    );
                    
                    typeTests.forEach(test => {
                        const option = document.createElement('option');
                        option.value = test.id;
                        option.textContent = test.title;
                        select.appendChild(option);
                    });
                });
            } catch (error) {
                console.error('Error fetching tests:', error);
                showToast('Wystąpił błąd podczas pobierania testów', 'error');
            }
        }
        
        this.updateDependencies();
        this.validateWeights();
    }

    handleTestSelect(type) {
        const select = this.testSelects[type];
        const weightInput = this.weightInputs[type];
        
        if (!select || !weightInput) {
            console.warn(`Test select or weight input not found for type: ${type}`);
            return;
        }
        
        // Enable/disable weight input based on test selection
        weightInput.disabled = !select.value;
        
        if (!select.value) {
            weightInput.value = '0';
        }
        
        this.validateWeights();
    }

    updateDependencies() {        
        // Handle PO2 dependency on PO1
        if (this.testSelects.po2 && this.testSelects.po1) {
            const isEnabled = this.testSelects.po1.value !== '';
            this.testSelects.po2.disabled = !isEnabled;
            if (!isEnabled) {
                this.testSelects.po2.value = '';
                if (this.weightInputs.po2) {
                    this.weightInputs.po2.value = '0';
                }
            }
        }
        
        // Handle PO2.5 dependency on PO2
        if (this.testSelects.po25 && this.testSelects.po2) {
            const po2HasValue = this.testSelects.po2.value !== '';
            const po2IsEnabled = !this.testSelects.po2.disabled;
            const isEnabled = po2HasValue && po2IsEnabled;

            this.testSelects.po25.disabled = !isEnabled;
            if (this.weightInputs.po25) {
                this.weightInputs.po25.disabled = !isEnabled || !this.testSelects.po25.value;
            }
            
            if (!isEnabled) {
                this.testSelects.po25.value = '';
                if (this.weightInputs.po25) {
                    this.weightInputs.po25.value = '0';
                }
            }
        }
        
        // Handle PO3 dependency on PO2.5
        if (this.testSelects.po3 && this.testSelects.po25) {
            const po25HasValue = this.testSelects.po25.value !== '';
            const po25IsEnabled = !this.testSelects.po25.disabled;
            const isEnabled = po25HasValue && po25IsEnabled;
            
            this.testSelects.po3.disabled = !isEnabled;
            if (this.weightInputs.po3) {
                this.weightInputs.po3.disabled = !isEnabled || !this.testSelects.po3.value;
            }
            
            if (!isEnabled) {
                this.testSelects.po3.value = '';
                if (this.weightInputs.po3) {
                    this.weightInputs.po3.value = '0';
                }
            }
        }
        
        this.updateMaxWeights();
    }

    updateMaxWeights() {
        // Calculate total used weight excluding the current input
        const getUsedWeightExcluding = (excludeInput) => {
            return Object.entries(this.weightInputs)
                .filter(([type, input]) => input && !input.disabled && input !== excludeInput)
                .reduce((sum, [type, input]) => sum + (parseInt(input.value) || 0), 0);
        };
        
        // Update max values for each enabled weight input
        Object.entries(this.weightInputs).forEach(([type, input]) => {
            if (input && !input.disabled) {
                const usedWeight = getUsedWeightExcluding(input);
                input.max = 100 - usedWeight;
                
                // Ensure current value doesn't exceed new max
                const currentValue = parseInt(input.value) || 0;
                if (currentValue > input.max) {
                    input.value = input.max;
                }
            }
        });
        
        this.validateWeights();
    }

    validateWeights() {
        if (!this.validationAlert) return false;

        const weights = Object.entries(this.weightInputs)
            .filter(([type, input]) => input && !input.disabled)
            .map(([type, input]) => ({
                type,
                value: parseInt(input.value) || 0
            }));
        
        const totalWeight = weights.reduce((sum, w) => sum + w.value, 0);
        const isValid = totalWeight === 100;
        
        // Update validation states
        weights.forEach(w => {
            const input = this.weightInputs[w.type];
            if (input) {
                input.classList.toggle('is-invalid', !isValid);
            }
        });
        
        // Show/hide validation alert
        this.validationAlert.classList.toggle('d-none', isValid);
        this.validationAlert.textContent = `Suma wag musi wynosić 100%. Aktualna suma: ${totalWeight}%`;
        
        return isValid;
    }

    handleWeightBlur() {
        // Ensure all enabled weights are valid numbers
        Object.entries(this.weightInputs).forEach(([type, input]) => {
            if (input && !input.disabled) {
                const value = parseInt(input.value) || 0;
                input.value = value.toString();
            }
        });
        
        this.validateWeights();
    }

    getSelectedTests() {
        return Object.entries(this.testSelects)
            .filter(([type, select]) => select.value)
            .map(([type, select]) => ({
                type,
                id: select.value,
                weight: parseInt(this.weightInputs[type].value) || 0
            }));
    }
} 