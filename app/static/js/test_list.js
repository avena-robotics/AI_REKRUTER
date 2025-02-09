let currentSorts = [];

document.addEventListener('DOMContentLoaded', function() {
    // Store original table rows
    const tbody = document.querySelector('tbody');
    originalRows = Array.from(tbody.querySelectorAll('tr'));
    
    // Initialize row numbers
    updateRowNumbers(tbody);
    
    // Initialize filters and buttons
    initializeFilters();
    initializeEventListeners();
    checkPendingToast();
    
    // Initialize Sortable and modal styles after modals are shown
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('shown.bs.modal', function() {
            initializeSortable();
            
            // Set modal styles for fixed footer
            const modalDialog = this.querySelector('.modal-dialog');
            const modalContent = this.querySelector('.modal-content');
            const modalBody = this.querySelector('.modal-body');
            const modalFooter = this.querySelector('.modal-footer');
            const modalHeader = this.querySelector('.modal-header');
            
            // Reset any previously set styles
            modalDialog.style = '';
            modalContent.style = '';
            modalBody.style = '';
            modalFooter.style = '';
            modalHeader.style = '';
            
            // Set new styles
            modalDialog.style.height = '90vh';
            modalDialog.style.maxHeight = '90vh';
            modalDialog.style.margin = '20px auto';
            
            modalContent.style.height = '100%';
            modalContent.style.display = 'flex';
            modalContent.style.flexDirection = 'column';
            
            modalHeader.style.flex = '0 0 auto';
            
            modalBody.style.flex = '1 1 auto';
            modalBody.style.overflowY = 'auto';
            modalBody.style.overflowX = 'hidden';
            modalBody.style.position = 'relative';
            
            modalFooter.style.flex = '0 0 auto';
            modalFooter.style.padding = '1rem';
            modalFooter.style.borderTop = '1px solid #dee2e6';
            modalFooter.style.backgroundColor = '#fff';
        });
    });

    // Add event delegation for dynamically added elements
    document.addEventListener('click', function(e) {
        if (e.target.matches('.add-question')) {
            const container = e.target.closest('.questions-section').querySelector('.questions-container');
            const questionHtml = createQuestionHtml();
            container.insertAdjacentHTML('beforeend', questionHtml);
            
            // Initialize any new answer type selects
            const newQuestion = container.lastElementChild;
            const answerTypeSelect = newQuestion.querySelector('[name$="[answer_type]"]');
            if (answerTypeSelect) {
                answerTypeSelect.addEventListener('change', handleAnswerTypeChange);
            }
        }
        if (e.target.matches('.remove-question')) {
            handleRemoveQuestion(e);
        }
    });

    // Initialize image previews for existing images
    initializeImagePreviews();
    
    // Initialize image previews after modals are shown
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('shown.bs.modal', function() {
            initializeImagePreviews();
        });
    });

    initializeSortableHeaders();
});

function initializeFilters() {
    const resetFilters = document.getElementById('resetFilters');
    
    // Usuń przycisk "Zastosuj" z HTML
    const applyFilters = document.getElementById('applyFilters');
    if (applyFilters) {
        applyFilters.remove();
    }

    // Zaznacz wszystkie checkboxy na starcie
    document.querySelectorAll('.filter-test-type, .filter-group').forEach(checkbox => {
        checkbox.checked = true;
    });
    
    // Zaznacz checkboxy "Zaznacz wszystkie" na starcie
    document.querySelectorAll('.select-all-test-types, .select-all-groups').forEach(checkbox => {
        checkbox.checked = true;
    });
    
    // Zaktualizuj tekst w dropdownach na starcie
    document.querySelectorAll('.dropdown').forEach(dropdown => {
        const selectedSpan = dropdown.querySelector('.selected-options');
        const checkboxes = dropdown.querySelectorAll('input[type="checkbox"]');
        updateSelectedOptionsText(checkboxes[0]); // Przekaż dowolny checkbox z grupy
    });
    
    // Obsługa zmiany checkboxów - natychmiastowe filtrowanie
    document.querySelectorAll('.filter-test-type, .filter-group').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            // Aktualizuj stan checkboxa "Zaznacz wszystkie"
            const isTestType = checkbox.classList.contains('filter-test-type');
            const selectAllCheckbox = isTestType ? 
                document.querySelector('.select-all-test-types') : 
                document.querySelector('.select-all-groups');
            const relatedCheckboxes = isTestType ? 
                document.querySelectorAll('.filter-test-type') : 
                document.querySelectorAll('.filter-group');
            
            const allChecked = Array.from(relatedCheckboxes).every(cb => cb.checked);
            selectAllCheckbox.checked = allChecked;
            
            updateSelectedOptionsText(this);
            updateTable(true);
        });
    });

    // Obsługa checkboxów "Zaznacz wszystkie"
    document.querySelector('.select-all-test-types').addEventListener('change', function() {
        const testTypeCheckboxes = document.querySelectorAll('.filter-test-type');
        testTypeCheckboxes.forEach(cb => {
            cb.checked = this.checked;
        });
        updateSelectedOptionsText(testTypeCheckboxes[0]);
        updateTable(true);
    });

    document.querySelector('.select-all-groups').addEventListener('change', function() {
        const groupCheckboxes = document.querySelectorAll('.filter-group');
        groupCheckboxes.forEach(cb => {
            cb.checked = this.checked;
        });
        updateSelectedOptionsText(groupCheckboxes[0]);
        updateTable(true);
    });

    // Zatrzymaj zamykanie dropdownu przy kliknięciu wewnątrz
    document.querySelectorAll('.dropdown-menu').forEach(menu => {
        menu.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    });
    
    resetFilters?.addEventListener('click', function() {
        // Zaznacz wszystkie checkboxy
        document.querySelectorAll('.filter-test-type, .filter-group, .select-all-test-types, .select-all-groups').forEach(checkbox => {
            checkbox.checked = true;
        });
        // Zaktualizuj tekst w dropdownach
        document.querySelectorAll('.dropdown').forEach(dropdown => {
            const selectedSpan = dropdown.querySelector('.selected-options');
            const checkboxes = dropdown.querySelectorAll('input[type="checkbox"]');
            updateSelectedOptionsText(checkboxes[0]); // Przekaż dowolny checkbox z grupy
        });
        // Usuń wszystkie sortowania
        document.querySelectorAll('th.sortable').forEach(header => {
            header.classList.remove('asc', 'desc');
            const orderIndicator = header.querySelector('.sort-order');
            if (orderIndicator) {
                orderIndicator.remove();
            }
        });
        currentSorts = [];
        updateTable(true);
    });
}

function updateSelectedOptionsText(checkbox) {
    const dropdownButton = checkbox.closest('.dropdown').querySelector('button');
    const selectedSpan = dropdownButton.querySelector('.selected-options');
    const checkboxes = checkbox.closest('.dropdown-menu').querySelectorAll('input[type="checkbox"]');
    const selectedOptions = Array.from(checkboxes)
        .filter(cb => cb.checked)
        .map(cb => cb.nextElementSibling.textContent);
    
    if (selectedOptions.length === 0) {
        selectedSpan.textContent = '-';
    } else if (selectedOptions.length === checkboxes.length) {
        selectedSpan.textContent = 'Wszystkie';
    } else {
        selectedSpan.textContent = selectedOptions.join(', ');
    }
}

function initializeEventListeners() {
    // Form validation for groups
    ['addTestForm', 'editTestForm'].forEach(formId => {
        const form = document.getElementById(formId);
        if (form) {
            form.addEventListener('submit', validateForm);
        }
    });

    // Add test button handler
    const addTestBtn = document.querySelector('[data-bs-target="#addTestModal"]');
    if (addTestBtn) {
        addTestBtn.addEventListener('click', () => {
            // Reset submit button state
            const submitButton = document.querySelector('#addTestSubmit');
            const spinner = submitButton.querySelector('.spinner-border');
            const buttonText = submitButton.querySelector('.button-text');
            
            submitButton.disabled = false;
            spinner.classList.add('d-none');
            buttonText.textContent = 'Zapisz test';

            document.querySelector('#addTestModal .modal-title').textContent = 'Dodaj nowy szablon testu';
            resetAddTestForm();
        });
    }

    // Table row actions using event delegation
    document.querySelector('tbody').addEventListener('click', function(e) {
        const target = e.target;
        const row = target.closest('tr');
        
        if (!row) return;
        
        const testId = row.dataset.testId;
        
        if (target.classList.contains('btn-warning')) {
            editTest(testId);
        } else if (target.classList.contains('btn-info')) {
            duplicateTest(testId);
        } else if (target.classList.contains('btn-danger')) {
            confirmDeleteTest(testId);
        }
    });

    // Double click handler for editing
    document.querySelector('tbody').addEventListener('dblclick', function(e) {
        const row = e.target.closest('tr');
        if (row) {
            editTest(row.dataset.testId);
        }
    });

    // Dodaj obsługę zmiany typu testu dla obu formularzy
    ['addTestForm', 'editTestForm'].forEach(formId => {
        const form = document.getElementById(formId);
        if (form) {
            const testTypeSelect = form.querySelector('[name="test_type"]');
            if (testTypeSelect) {
                testTypeSelect.addEventListener('change', function() {
                    handleTestTypeChange(this);
                });
                // Inicjalizuj stan przy załadowaniu formularza
                handleTestTypeChange(testTypeSelect);
            }
        }
    });
}

function updateTable(applyFilters) {
    const tbody = document.querySelector('tbody');
    
    if (!applyFilters) {
        // Reset to original state
        tbody.innerHTML = '';
        originalRows.forEach(row => {
            tbody.appendChild(row.cloneNode(true));
        });
        updateRowNumbers(tbody);
        return;
    }
    
    // Clone original rows for filtering
    let rows = originalRows.map(row => row.cloneNode(true));
    
    // Get selected test types and groups
    const selectedTestTypes = Array.from(document.querySelectorAll('.filter-test-type:checked'))
        .map(cb => cb.value);
    const selectedGroups = Array.from(document.querySelectorAll('.filter-group:checked'))
        .map(cb => cb.value);
    
    // Apply filters
    rows = rows.filter(row => {
        const testType = row.querySelector('td:nth-child(3)').textContent.trim();
        const testGroups = JSON.parse(row.dataset.groups || '[]');
        
        const testTypeMatch = selectedTestTypes.length === 0 ? 
            testType === '' : 
            selectedTestTypes.some(type => {
                if (type === 'SURVEY') return testType === 'Ankieta';
                if (type === 'EQ') return testType === 'Test EQ';
                if (type === 'IQ') return testType === 'Test IQ';
                if (type === 'EQ_EVALUATION') return testType === 'Ocena EQ';
                return false;
            });
            
        const groupMatch = selectedGroups.length === 0 ? 
            testGroups.length === 0 : 
            testGroups.some(group => selectedGroups.includes(group.id.toString()));
        
        return testTypeMatch && groupMatch;
    });
    
    // Apply multiple sorts
    if (currentSorts.length > 0) {
        rows.sort((a, b) => {
            for (const sort of currentSorts) {
                const aValue = getRowValue(a, sort.field);
                const bValue = getRowValue(b, sort.field);
                
                const order = sort.direction === 'asc' ? 1 : -1;
                
                if (aValue < bValue) return -1 * order;
                if (aValue > bValue) return 1 * order;
            }
            return 0;
        });
    }
    
    // Update table
    tbody.innerHTML = '';
    rows.forEach(row => tbody.appendChild(row));
    
    // Update row numbers
    updateRowNumbers(tbody);
}

// Add new function for row numbering
function updateRowNumbers(tbody) {
    const rows = tbody.querySelectorAll('tr');
    rows.forEach((row, index) => {
        const numberCell = row.querySelector('.row-number');
        if (numberCell) {
            numberCell.textContent = (index + 1).toString();
        }
    });
}

function getRowValue(row, sortField) {
    switch (sortField) {
        case 'title':
            return row.querySelector('td:nth-child(2)').textContent.toLowerCase();
        case 'test_type':
            return row.querySelector('td:nth-child(3)').textContent;
        case 'time_limit':
            const timeText = row.querySelector('td:nth-child(4)').textContent;
            return parseInt(timeText.replace(' min', '')) || 0;
        case 'questions':
            return parseInt(row.querySelector('td:nth-child(5)').textContent) || 0;
        case 'points':
            return parseInt(row.querySelector('td:nth-child(6)').textContent) || 0;
        case 'threshold':
            return parseInt(row.querySelector('td:nth-child(7)').textContent) || 0;
        case 'created_at':
            const dateText = row.querySelector('td:nth-child(9)').textContent;
            const [datePart, timePart] = dateText.split(' ');
            const [day, month, year] = datePart.split('.');
            const [hours, minutes] = timePart.split(':');
            return new Date(year, month - 1, day, hours, minutes).getTime();
        default:
            return 0;
    }
}

function validateForm(e) {
    e.preventDefault();
    e.stopPropagation();
    
    const form = this;
    let isValid = true;
    let errorMessage = '';

    // Reset validation states
    form.querySelectorAll('.is-invalid').forEach(el => {
        el.classList.remove('is-invalid');
    });
    form.querySelectorAll('.border-danger').forEach(el => {
        el.classList.remove('border-danger');
    });

    // Validate required fields
    form.querySelectorAll('[required]').forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
            errorMessage = 'Uzupełnij wszystkie wymagane pola';
        }
    });

    // Validate passing threshold
    const threshold = form.querySelector('[name="passing_threshold"]');
    if (threshold && (!threshold.value.trim() || isNaN(threshold.value))) {
        threshold.classList.add('is-invalid');
        isValid = false;
        errorMessage = 'Wprowadź poprawny próg zaliczenia';
    }

    // Validate groups
    const checkedGroups = form.querySelectorAll('input[name="groups[]"]:checked');
    const groupsContainer = form.querySelector('#groupsContainer');
    if (!checkedGroups.length && groupsContainer) {
        groupsContainer.classList.add('border-danger');
        isValid = false;
        errorMessage = errorMessage || 'Aby zapisać test, musisz wybrać przynajmniej jedną grupę';
    }

    if (!isValid) {
        showToast(errorMessage, 'error');
        return;
    }

    // If validation passes, submit the form
    handleTestFormSubmit.call(this, e);
}

function resetAddTestForm() {
    const form = document.getElementById('addTestForm');
    
    // Reset all form fields
    form.reset();
    
    // Clear title field explicitly
    form.querySelector('[name="title"]').value = '';
    
    // Clear description field
    form.querySelector('[name="description"]').value = '';
    
    // Reset numeric fields
    form.querySelector('[name="passing_threshold"]').value = '';
    form.querySelector('[name="time_limit_minutes"]').value = '';
    
    // Reset test type to first option
    const testTypeSelect = form.querySelector('[name="test_type"]');
    testTypeSelect.selectedIndex = 0;
    handleTestTypeChange(testTypeSelect);
    
    // Clear questions container
    const questionsContainer = form.querySelector('.questions-container');
    if (questionsContainer) {
        questionsContainer.innerHTML = '';
    }
    
    // Uncheck all group checkboxes
    form.querySelectorAll('input[name="groups[]"]').forEach(checkbox => {
        checkbox.checked = false;
    });
    
    // Reset validation states
    form.querySelectorAll('.is-invalid').forEach(el => {
        el.classList.remove('is-invalid');
    });
    form.querySelectorAll('.border-danger').forEach(el => {
        el.classList.remove('border-danger');
    });
    form.querySelectorAll('.invalid-feedback').forEach(el => {
        el.style.display = 'none';
    });
}

function editTest(testId) {
    // Reset button state before fetching data
    const submitButton = document.querySelector('#editTestSubmit');
    const spinner = submitButton.querySelector('.spinner-border');
    const buttonText = submitButton.querySelector('.button-text');
    
    submitButton.disabled = false;
    spinner.classList.add('d-none');
    buttonText.textContent = 'Zapisz zmiany';
    
    fetch(`/tests/${testId}/data`)
        .then(response => response.json())
        .then(test => {
            const form = document.getElementById('editTestForm');
            form.action = `/tests/${testId}/edit`;
            
            // Populate basic test fields
            form.querySelector('[name="title"]').value = test.title || '';
            form.querySelector('[name="test_type"]').value = test.test_type || '';
            form.querySelector('[name="description"]').value = test.description || '';
            form.querySelector('[name="passing_threshold"]').value = test.passing_threshold || 0;
            form.querySelector('[name="time_limit_minutes"]').value = test.time_limit_minutes !== null ? test.time_limit_minutes : '0';

            // Inicjalizuj stan typu testu
            const testTypeSelect = form.querySelector('[name="test_type"]');
            handleTestTypeChange(testTypeSelect);

            // Update group checkboxes
            const testGroups = test.groups || [];
            form.querySelectorAll('input[name="groups[]"]').forEach(checkbox => {
                checkbox.checked = testGroups.some(group => group.id === parseInt(checkbox.value));
            });

            // Reset validation state
            const groupsContainer = form.querySelector('#editGroupsContainer');
            if (groupsContainer) {
                groupsContainer.classList.remove('border-danger');
            }

            // Clear and populate questions
            const questionsContainer = form.querySelector('.questions-container');
            questionsContainer.innerHTML = '';
            
            if (test.questions?.length > 0) {
                test.questions
                    .sort((a, b) => a.order_number - b.order_number)
                    .forEach(question => {
                        const questionHtml = createQuestionHtml(question);
                        questionsContainer.insertAdjacentHTML('beforeend', questionHtml);
                        
                        // Get the newly added question card
                        const questionCard = questionsContainer.lastElementChild;
                        
                        // Attach event listener to answer type select
                        const answerTypeSelect = questionCard.querySelector('[name$="[answer_type]"]');
                        if (answerTypeSelect) {
                            answerTypeSelect.addEventListener('change', handleAnswerTypeChange);
                        }
                        
                        // Set answer type specific fields
                        setAnswerFields(questionCard, question);
                    });
            }

            new bootstrap.Modal(document.getElementById('editTestModal')).show();
        })
        .catch(error => {
            console.error('Error loading test data:', error);
            showToast('Błąd podczas ładowania danych testu', 'error');
        });
}

function setAnswerFields(questionCard, question) {
    const answerType = question.answer_type;
    const algorithmType = question.algorithm_type || 'NO_ALGORITHM';
    
    // Add handling for EVALUATION_BY_AI
    if (algorithmType === 'EVALUATION_BY_AI') {
        const aiParamsContainer = questionCard.querySelector('.ai-params-container');
        if (!aiParamsContainer) {
            const container = document.createElement('div');
            container.className = 'ai-params-container col-12 mt-3';
            container.innerHTML = createAIParamsHtml(questionCard);
            const algorithmParams = questionCard.querySelector('.algorithm-params');
            if (algorithmParams) {
                algorithmParams.appendChild(container);
            }
        }
        
        // Set values if they exist
        if (question.algorithm_params) {
            const evaluationFocus = questionCard.querySelector('[name$="[algorithm_params][evaluation_focus]"]');
            const scoringCriteria = questionCard.querySelector('[name$="[algorithm_params][scoring_criteria]"]');
            
            if (evaluationFocus) {
                evaluationFocus.value = question.algorithm_params.evaluation_focus || '';
            }
            if (scoringCriteria) {
                scoringCriteria.value = question.algorithm_params.scoring_criteria || '';
            }
        }
        return; // Skip other algorithm type handling for AI evaluation
    }
    
    // Skip setting answer fields for NO_ALGORITHM
    if (algorithmType === 'NO_ALGORITHM') {
        // Set algorithm type only
        const algorithmSelect = questionCard.querySelector('[name$="[algorithm_type]"]');
        if (algorithmSelect) {
            algorithmSelect.value = algorithmType;
            handleAlgorithmTypeChange(algorithmSelect);
        }
        return;
    }
    
    switch (answerType) {
        case 'TEXT':
            const textInput = questionCard.querySelector(`[name$="[algorithm_params][correct_answer]"]`);
            if (textInput && question.algorithm_params?.correct_answer) {
                textInput.value = question.algorithm_params.correct_answer;
            }
            break;
            
        case 'BOOLEAN':
            const boolValue = question.algorithm_params?.correct_answer;
            if (boolValue !== null && boolValue !== undefined) {
                const radio = questionCard.querySelector(`[name$="[algorithm_params][correct_answer]"][value="${boolValue}"]`);
                if (radio) {
                    radio.checked = true;
                }
            }
            break;
            
        case 'SCALE':
            const scaleInput = questionCard.querySelector(`[name$="[algorithm_params][correct_answer]"]`);
            if (scaleInput && question.algorithm_params?.correct_answer !== null) {
                scaleInput.value = question.algorithm_params.correct_answer;
            }
            break;
            
        case 'SALARY':
            const salaryInput = questionCard.querySelector(`[name$="[algorithm_params][correct_answer]"]`);
            if (salaryInput && question.algorithm_params?.correct_answer !== null) {
                salaryInput.value = question.algorithm_params.correct_answer;
            }
            break;

        case 'NUMERIC':
            const numericInput = questionCard.querySelector(`[name$="[algorithm_params][correct_answer]"]`);
            if (numericInput && question.algorithm_params?.correct_answer !== null) {
                numericInput.value = question.algorithm_params.correct_answer;
            }
            break;
            
        case 'DATE':
            const dateInput = questionCard.querySelector(`[name$="[algorithm_params][correct_answer]"]`);
            if (dateInput && question.algorithm_params?.correct_answer) {
                dateInput.value = question.algorithm_params.correct_answer;
            }
            break;
            
        case 'ABCDEF':
            const abcdefSelect = questionCard.querySelector(`[name$="[algorithm_params][correct_answer]"]`);
            if (abcdefSelect && question.algorithm_params?.correct_answer) {
                abcdefSelect.value = question.algorithm_params.correct_answer.toUpperCase();
            }
            break;
            
        case 'AH_POINTS':
            if (question.options) {
                Object.entries(question.options).forEach(([letter, value]) => {
                    const input = questionCard.querySelector(`[name$="[options][${letter}]"]`);
                    if (input) {
                        input.value = value;
                    }
                });
            }
            break;
    }

    // Set image if exists
    if (question.image) {
        const imagePreview = questionCard.querySelector('.image-preview');
        if (imagePreview) {
            imagePreview.innerHTML = `
                <img src="${question.image}" class="img-thumbnail" style="max-height: 100px">
                <input type="hidden" 
                       name="questions[${questionCard.dataset.questionIndex}][image]"
                       value="${question.image}">
            `;
        }
    }

    // Set algorithm type and params for all answer types
    const algorithmSelect = questionCard.querySelector('[name$="[algorithm_type]"]');
    if (algorithmSelect) {
        algorithmSelect.value = algorithmType;
        handleAlgorithmTypeChange(algorithmSelect);
        
        // Set algorithm params if they exist and it's not NO_ALGORITHM
        if (question.algorithm_params) {
            const minInput = questionCard.querySelector('[name$="[algorithm_params][min_value]"]');
            const maxInput = questionCard.querySelector('[name$="[algorithm_params][max_value]"]');
            
            if (minInput && question.algorithm_params.min_value !== undefined) {
                minInput.value = question.algorithm_params.min_value;
            }
            if (maxInput && question.algorithm_params.max_value !== undefined) {
                maxInput.value = question.algorithm_params.max_value;
            }
        }
    }
}

function confirmDeleteTest(testId) {
    if (confirm('Czy na pewno chcesz usunąć ten test?')) {
        const deleteButton = document.querySelector(`tr[data-test-id="${testId}"] .btn-danger`);
        const originalText = deleteButton.textContent;
        
        // Show loading state
        deleteButton.disabled = true;
        deleteButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Usuwanie...';
        
        fetch(`/tests/${testId}/delete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Fetch updated test data and refresh table
                fetch('/tests/')
                    .then(response => response.text())
                    .then(html => {
                        const tempDiv = document.createElement('div');
                        tempDiv.innerHTML = html;
                        
                        const newTbody = tempDiv.querySelector('tbody');
                        if (newTbody) {
                            originalRows = Array.from(newTbody.querySelectorAll('tr'));
                            updateTable(true);
                            showToast('Test został usunięty', 'success');
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching updated test data:', error);
                        showToast('Wystąpił błąd podczas odświeżania listy testów', 'error');
                    });
            } else {
                throw new Error(data.error || 'Wystąpił błąd podczas usuwania testu');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast(error.message, 'error');
            
            // Reset button state
            deleteButton.disabled = false;
            deleteButton.textContent = originalText;
        });
    }
}

function duplicateTest(testId) {
    // Reset submit button state
    const submitButton = document.querySelector('#addTestSubmit');
    const spinner = submitButton.querySelector('.spinner-border');
    const buttonText = submitButton.querySelector('.button-text');
    
    submitButton.disabled = false;
    spinner.classList.add('d-none');
    buttonText.textContent = 'Zapisz test';

    fetch(`/tests/${testId}/data`)
        .then(response => response.json())
        .then(test => {
            const form = document.getElementById('addTestForm');
            
            // Populate form fields except unique identifiers
            form.querySelector('[name="title"]').value = test.title ? `${test.title} - kopia` : '';
            form.querySelector('[name="test_type"]').value = test.test_type || '';
            form.querySelector('[name="description"]').value = test.description || '';
            form.querySelector('[name="passing_threshold"]').value = test.passing_threshold || 0;
            form.querySelector('[name="time_limit_minutes"]').value = test.time_limit_minutes || '';
            
            // Set groups
            if (test.groups) {
                test.groups.forEach(group => {
                    const checkbox = form.querySelector(`input[name="groups[]"][value="${group.id}"]`);
                    if (checkbox) checkbox.checked = true;
                });
            }
            
            // Clear existing questions container
            const questionsContainer = form.querySelector('.questions-container');
            questionsContainer.innerHTML = '';
            
            // Add questions
            if (test.questions && test.questions.length > 0) {
                test.questions
                    .sort((a, b) => a.order_number - b.order_number)
                    .forEach(question => {
                        // Remove ID from question to create new one
                        delete question.id;
                        const questionHtml = createQuestionHtml(question);
                        questionsContainer.insertAdjacentHTML('beforeend', questionHtml);

                        // Set answer type specific fields
                        const questionCard = questionsContainer.lastElementChild;
                        setAnswerFields(questionCard, question);
                    });
            }
            
            // Update modal title to indicate duplication
            document.querySelector('#addTestModal .modal-title').textContent = 'Duplikuj szablon testu';
            
            // Show the modal
            new bootstrap.Modal(document.getElementById('addTestModal')).show();
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Błąd podczas ładowania danych testu', 'error');
        });
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('notificationToast');
    const toastMessage = document.getElementById('toastMessage');
    
    // Reset classes
    toast.className = 'toast border-0';
    
    // Add styling based on type
    if (type === 'success') {
        toast.style.backgroundColor = '#198754';  // Bootstrap success color
        toast.style.borderLeft = '4px solid #146c43';  // Darker shade
    } else {
        toast.style.backgroundColor = '#dc3545';  // Bootstrap danger color
        toast.style.borderLeft = '4px solid #b02a37';  // Darker shade
    }
    
    // Add common styles
    toast.classList.add('text-white');
    
    // Set message
    toastMessage.textContent = message;
    
    // Show toast
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}

function checkPendingToast() {
    const pendingToast = sessionStorage.getItem('pendingToast');
    if (pendingToast) {
        try {
            const toastData = JSON.parse(pendingToast);
            showToast(toastData.message, toastData.type);
        } catch (error) {
            console.error('Error showing pending toast:', error);
        } finally {
            sessionStorage.removeItem('pendingToast');
        }
    }
}

function createQuestionHtml(question = null) {
    const q = question || {};
    const questionCounter = document.querySelectorAll('.question-card').length;
    
    return `
        <div class="question-card card mb-3" data-order="${questionCounter + 1}">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <div class="d-flex align-items-center gap-3">
                        <div class="drag-handle" style="cursor: grab;">
                            <i class="bi bi-grip-vertical" style="font-size: 1.2rem;"></i>
                        </div>
                        <div class="switch-container">
                            <div class="switch-group">
                                <div class="form-check form-switch">
                                    <input type="checkbox" class="form-check-input" 
                                           name="questions[${questionCounter}][is_required]" 
                                           id="required_${questionCounter}"
                                           ${q.is_required !== false ? 'checked' : ''}>
                                    <label class="form-check-label switch-label" for="required_${questionCounter}">Wymagane</label>
                                </div>
                            </div>
                            <div class="switch-group">
                                <div class="form-check form-switch">
                                    <input type="checkbox" class="form-check-input" 
                                           name="questions[${questionCounter}][is_critical]" 
                                           id="critical_${questionCounter}"
                                           ${q.is_critical === true ? 'checked' : ''}>
                                    <label class="form-check-label switch-label" for="critical_${questionCounter}">Krytyczne</label>
                                </div>
                            </div>
                        </div>
                    </div>
                    <button type="button" class="btn btn-danger btn-sm remove-question">
                        Usuń pytanie
                    </button>
                </div>
                
                <div class="row mb-3">
                    <div class="col-12">
                        <label class="form-label">Treść pytania*</label>
                        <textarea class="form-control" 
                                name="questions[${questionCounter}][question_text]" 
                                required>${q.question_text || ''}</textarea>
                    </div>
                </div>

                <div class="answer-fields">
                    ${createAnswerFieldsHtml(questionCounter, q)}
                </div>

                <input type="hidden" name="questions[${questionCounter}][order_number]" 
                       value="${questionCounter + 1}">
                ${q.id ? `<input type="hidden" name="questions[${questionCounter}][id]" value="${q.id}">` : ''}
            </div>
        </div>
    `;
}

function handleAnswerTypeChange(event) {
    const select = event.target;
    const questionCard = select.closest('.question-card');
    if (!questionCard) {
        console.error('Could not find parent question card');
        return;
    }
    const answerFieldsContainer = questionCard.querySelector('.answer-fields');
    
    // Get current algorithm type and check if it's available for new answer type
    const algorithmTypeSelect = questionCard.querySelector('.algorithm-type-select');
    let currentAlgorithmType = algorithmTypeSelect ? algorithmTypeSelect.value : 'NO_ALGORITHM';
    
    // Reset to NO_ALGORITHM if current algorithm is not available for new answer type
    const availableAlgorithms = getAvailableAlgorithms(select.value);
    if (!availableAlgorithms.includes(currentAlgorithmType)) {
        currentAlgorithmType = 'NO_ALGORITHM';
    }
    
    // Get current algorithm params
    const minValueInput = questionCard.querySelector('input[name$="[algorithm_params][min_value]"]');
    const maxValueInput = questionCard.querySelector('input[name$="[algorithm_params][max_value]"]');
    const correctAnswerInput = questionCard.querySelector('[name$="[algorithm_params][correct_answer]"]');
    
    // Get current image
    const imageInput = questionCard.querySelector('input[name$="[image]"]');
    const currentImage = imageInput ? imageInput.value : null;
    
    const currentParams = {
        min_value: minValueInput ? minValueInput.value : '',
        max_value: maxValueInput ? maxValueInput.value : '',
        correct_answer: correctAnswerInput ? correctAnswerInput.value : ''
    };

    // Get question index
    const questionCounter = parseInt(select.name.match(/\[(\d+)\]/)[1]);

    // Create new answer fields HTML with current values
    const answerFieldsHtml = createAnswerFieldsHtml(questionCounter, {
        answer_type: select.value,
        algorithm_type: currentAlgorithmType,
        algorithm_params: currentParams,
        image: currentImage,
        points: questionCard.querySelector('input[name$="[points]"]')?.value || 0
    });
    
    // Update the container
    answerFieldsContainer.innerHTML = answerFieldsHtml;
    
    // Re-initialize algorithm type handler
    const newAlgorithmSelect = answerFieldsContainer.querySelector('.algorithm-type-select');
    if (newAlgorithmSelect) {
        handleAlgorithmTypeChange(newAlgorithmSelect);
    }

    // Re-initialize any new answer type selects
    const answerTypeSelect = answerFieldsContainer.querySelector('[name$="[answer_type]"]');
    if (answerTypeSelect) {
        answerTypeSelect.value = select.value;
    }

    initializeImagePreviews();
}

function handleImageUpload(input) {
    const file = input.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const base64String = e.target.result;
            const questionCard = input.closest('.question-card');
            
            // Create or update hidden input for image data
            const hiddenInput = questionCard.querySelector('input[name$="[image]"]') || 
                              document.createElement('input');
            hiddenInput.type = 'hidden';
            hiddenInput.name = input.name.replace('_file', '');
            hiddenInput.value = base64String;
            
            // Create or update preview container
            let previewContainer = questionCard.querySelector('.image-preview');
            if (!previewContainer) {
                previewContainer = document.createElement('div');
                previewContainer.className = 'mt-2 image-preview';
                input.parentNode.insertBefore(previewContainer, input.nextSibling);
            }
            
            // Update preview
            previewContainer.innerHTML = `
                <img src="${base64String}" class="img-thumbnail" style="max-height: 100px">
            `;
            
            // Ensure hidden input is in the form
            if (!questionCard.querySelector(`input[name$="[image]"]`)) {
                questionCard.appendChild(hiddenInput);
            }

            initializeImagePreviews();
        };
        reader.readAsDataURL(file);
    }
}

async function handleTestFormSubmit(e) {
    e.preventDefault();
    const form = this;
    
    // Update question orders before collecting data
    const questionsContainer = form.querySelector('.questions-container');
    if (questionsContainer) {
        updateQuestionOrders(questionsContainer);
    }
    
    const isEdit = form.id === 'editTestForm';
    
    // Get button elements
    const submitButton = form.querySelector('button[type="submit"]');
    const spinner = submitButton.querySelector('.spinner-border');
    const buttonText = submitButton.querySelector('.button-text');
    
    try {
        // Show loading state
        submitButton.disabled = true;
        spinner.classList.remove('d-none');
        buttonText.textContent = 'Zapisywanie...';

        // Collect form data
        const formData = new FormData();
        const basicFields = ['title', 'test_type', 'description', 'passing_threshold', 'time_limit_minutes'];
        
        // Get original data for edit mode
        let originalData = null;
        let hasBasicChanges = false;
        
        if (isEdit) {
            originalData = await fetch(form.action.replace('/edit', '/data')).then(r => r.json());
            
            // Check basic fields changes
            for (const field of basicFields) {
                const newValue = form.querySelector(`[name="${field}"]`).value;
                const oldValue = originalData[field]?.toString() || '';
                if (newValue !== oldValue) {
                    hasBasicChanges = true;
                    formData.append(field, newValue);
                }
            }
            
            // Check groups changes
            const originalGroups = new Set(originalData.groups.map(g => g.id.toString()));
            const newGroups = new Set(Array.from(form.querySelectorAll('input[name="groups[]"]:checked')).map(cb => cb.value));
            const groupsChanged = originalGroups.size !== newGroups.size || 
                                [...newGroups].some(g => !originalGroups.has(g));
            
            if (groupsChanged) {
                hasBasicChanges = true;
                form.querySelectorAll('input[name="groups[]"]:checked').forEach(checkbox => {
                    formData.append('groups[]', checkbox.value);
                });
            }
        } else {
            // For new test, add all fields
            basicFields.forEach(field => {
                formData.append(field, form.querySelector(`[name="${field}"]`).value);
            });
            form.querySelectorAll('input[name="groups[]"]:checked').forEach(checkbox => {
                formData.append('groups[]', checkbox.value);
            });
        }

        // Collect questions data
        const questions = [];
        form.querySelectorAll('.question-card').forEach((card, index) => {
            const questionData = collectQuestionData(card, index);
            questions.push(questionData);
        });

        // For edit mode, compare questions with original
        if (isEdit && originalData) {
            const {added, modified, deleted} = compareQuestions(originalData.questions || [], questions);
            
            // Handle deleted questions first
            if (deleted.length > 0) {
                formData.append('questions', JSON.stringify({
                    deleted: deleted
                }));
            }
            
            // Save basic changes and deletions
            if (hasBasicChanges || deleted.length > 0) {
                const response = await fetch(form.action, {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                if (!result.success) {
                    throw new Error(result.error || 'Wystąpił błąd podczas zapisywania podstawowych danych testu');
                }
            }
            
            // Handle added and modified questions
            if (added.length > 0 || modified.length > 0) {
                // Handle added questions
                for (const question of added) {
                    const questionFormData = new FormData();
                    questionFormData.append('test_id', originalData.id);
                    questionFormData.append('question', JSON.stringify(question));
                    
                    const response = await fetch('/tests/add/question', {
                        method: 'POST',
                        body: questionFormData
                    });
                    
                    const result = await response.json();
                    if (!result.success) {
                        throw new Error(`Błąd podczas dodawania pytania: ${result.error}`);
                    }
                }
                
                // Handle modified questions
                for (const mod of modified) {
                    const questionFormData = new FormData();
                    // Add all changes as separate fields
                    for (const [key, value] of Object.entries(mod.changes)) {
                        if (key === 'algorithm_params' || key === 'options') {
                            questionFormData.append(key, JSON.stringify(value));
                        } else {
                            questionFormData.append(key, value);
                        }
                    }
                    
                    const response = await fetch(`/tests/${originalData.id}/questions/${mod.id}/edit`, {
                        method: 'POST',
                        body: questionFormData
                    });
                    
                    const result = await response.json();
                    if (!result.success) {
                        throw new Error(`Błąd podczas aktualizacji pytania: ${result.error}`);
                    }
                }
            }
            
        } else if (!isEdit) {
            // For new test, first save basic info
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            if (!result.success) {
                throw new Error(result.error || 'Wystąpił błąd podczas zapisywania podstawowych danych testu');
            }
            
            const testId = result.test_id;
            
            // Then save questions
            if (questions.length > 0) {
                for (const question of questions) {
                    const questionFormData = new FormData();
                    questionFormData.append('test_id', testId);
                    questionFormData.append('question', JSON.stringify(question));
                    
                    const response = await fetch('/tests/add/question', {
                        method: 'POST',
                        body: questionFormData
                    });
                    
                    const result = await response.json();
                    if (!result.success) {
                        throw new Error(`Błąd podczas dodawania pytania: ${result.error}`);
                    }
                }
            }
        }

        // Show success message and reload
        sessionStorage.setItem('pendingToast', JSON.stringify({
            message: isEdit ? 'Test został zaktualizowany' : 'Test został dodany',
            type: 'success'
        }));

        const modal = bootstrap.Modal.getInstance(form.closest('.modal'));
        modal.hide();
        
        modal._element.addEventListener('hidden.bs.modal', function () {
            // Fetch updated test data and refresh table
            fetch('/tests/')
                .then(response => response.text())
                .then(html => {
                    // Create a temporary div to parse the HTML
                    const tempDiv = document.createElement('div');
                    tempDiv.innerHTML = html;
                    
                    // Get the new tbody content
                    const newTbody = tempDiv.querySelector('tbody');
                    if (newTbody) {
                        // Update originalRows with new data
                        originalRows = Array.from(newTbody.querySelectorAll('tr'));
                        
                        // Apply current filters and sorting
                        updateTable(true);
                        
                        // Show the toast
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
                })
                .catch(error => {
                    console.error('Error fetching updated test data:', error);
                    showToast('Wystąpił błąd podczas odświeżania listy testów', 'error');
                });
        }, { once: true });

    } catch (error) {
        console.error('Error submitting form:', error);
        showToast(error.message, 'error');
        
        // Reset button state
        submitButton.disabled = false;
        spinner.classList.add('d-none');
        buttonText.textContent = isEdit ? 'Zapisz zmiany' : 'Zapisz test';
    }
}

// Helper function to collect question data
function collectQuestionData(card, index) {
    // First verify the card has required elements
    const questionTextElement = card.querySelector('[name$="[question_text]"]');
    const answerTypeElement = card.querySelector('[name$="[answer_type]"]');
    const pointsElement = card.querySelector('[name$="[points]"]');
    
    if (!questionTextElement || !answerTypeElement) {
        throw new Error('Brakuje wymaganych pól w pytaniu ' + (index + 1));
    }

    const questionData = {
        id: card.querySelector('input[name$="[id]"]')?.value,
        question_text: questionTextElement.value,
        answer_type: answerTypeElement.value,
        points: parseInt(pointsElement?.value || '0'),
        order_number: index + 1,
        is_required: card.querySelector('[name$="[is_required]"]')?.checked ?? true,
        is_critical: card.querySelector('[name$="[is_critical]"]')?.checked ?? false,
        algorithm_type: card.querySelector('[name$="[algorithm_type]"]')?.value || 'NO_ALGORITHM',
        image: card.querySelector('input[name$="[image]"]')?.value
    };

    // Collect algorithm params based on type
    if (questionData.algorithm_type === 'EVALUATION_BY_AI') {
        questionData.algorithm_params = {
            evaluation_focus: card.querySelector('[name$="[algorithm_params][evaluation_focus]"]')?.value || '',
            scoring_criteria: card.querySelector('[name$="[algorithm_params][scoring_criteria]"]')?.value || ''
        };
    } else {
        // Existing algorithm params collection
        const algorithmParams = {};
        ['min_value', 'max_value', 'correct_answer'].forEach(param => {
            const input = card.querySelector(`[name$="[algorithm_params][${param}]"]`);
            if (input) {
                algorithmParams[param] = input.value;
            }
        });
        questionData.algorithm_params = algorithmParams;
    }

    // Collect options for AH_POINTS type
    if (questionData.answer_type === 'AH_POINTS') {
        const options = {};
        card.querySelectorAll('[name*="[options]"]').forEach(input => {
            const letterMatch = input.name.match(/\[options\]\[([a-h])\]/);
            if (letterMatch) {
                options[letterMatch[1]] = input.value.trim();
            }
        });
        questionData.options = options;
    }

    return questionData;
}

// Helper function to compare questions
function compareQuestions(originalQuestions, newQuestions) {
    const added = [];
    const modified = [];
    const deleted = [];
    
    // Create maps for easier comparison
    const originalMap = new Map(originalQuestions.map(q => [q.id.toString(), q]));
    const newMap = new Map(newQuestions.filter(q => q.id).map(q => [q.id.toString(), q]));
    
    // Find added questions (those without ID)
    added.push(...newQuestions.filter(q => !q.id));
    
    // Find modified questions
    for (const [id, newQuestion] of newMap) {
        const originalQuestion = originalMap.get(id);
        if (originalQuestion) {
            const changes = getQuestionChanges(originalQuestion, newQuestion);
            if (Object.keys(changes).length > 0) {
                modified.push({
                    id: parseInt(id),
                    changes: changes
                });
            }
        }
    }
    
    // Find deleted questions
    for (const id of originalMap.keys()) {
        if (!newMap.has(id)) {
            deleted.push(parseInt(id));
        }
    }
    
    return { added, modified, deleted };
}

// Helper function to get changes between questions
function getQuestionChanges(original, updated) {
    const changes = {};
    const fieldsToCompare = [
        'question_text',
        'answer_type',
        'points',
        'order_number',
        'is_required',
        'is_critical',
        'algorithm_type',
        'image'
    ];

    for (const field of fieldsToCompare) {
        if (original[field]?.toString() !== updated[field]?.toString()) {
            changes[field] = updated[field];
        }
    }

    // Compare algorithm params
    const originalParams = original.algorithm_params || {};
    const updatedParams = updated.algorithm_params || {};
    if (JSON.stringify(originalParams) !== JSON.stringify(updatedParams)) {
        changes.algorithm_params = updatedParams;
    }

    // Compare options for AH_POINTS
    if (original.answer_type === 'AH_POINTS' && updated.answer_type === 'AH_POINTS') {
        const originalOptions = original.options || {};
        const updatedOptions = updated.options || {};
        if (JSON.stringify(originalOptions) !== JSON.stringify(updatedOptions)) {
            changes.options = updatedOptions;
        }
    }

    return changes;
}

function initializeSortable() {
    const questionsContainers = document.querySelectorAll('.questions-container');
    questionsContainers.forEach(container => {
        if (container.sortableInstance) {
            container.sortableInstance.destroy();
        }
        
        container.sortableInstance = new Sortable(container, {
            animation: 150,
            handle: '.drag-handle',
            ghostClass: 'sortable-ghost',
            dragClass: 'sortable-drag',
            onEnd: function(evt) {
                updateQuestionOrders(container);
            }
        });
    });
}

function updateQuestionOrders(container) {
    // Update question numbers and order inputs
    container.querySelectorAll('.question-card').forEach((card, index) => {
        // Update order number input
        const orderInput = card.querySelector('input[name$="[order_number]"]');
        if (orderInput) {
            orderInput.value = index + 1;
        }
        
        // Update data-order attribute
        card.dataset.order = index + 1;
        
        // Update all field names to match new order
        card.querySelectorAll('[name*="questions["]').forEach(field => {
            field.name = field.name.replace(/questions\[\d+\]/, `questions[${index}]`);
        });
    });
}

function createAnswerFieldsHtml(questionCounter, question) {
    const q = question || {};
    const answerType = q.answer_type || 'TEXT';
    const algorithmType = q.algorithm_type || 'NO_ALGORITHM';
    const algorithmParams = q.algorithm_params || {};
    
    // Image upload HTML
    const imageUploadHtml = `
        <div class="col-12 mb-3">
            <label class="form-label">Obrazek</label>
            <input type="file" class="form-control" 
                   name="questions[${questionCounter}][image_file]"
                   accept="image/*"
                   onchange="handleImageUpload(this)">
            ${q.image ? `
                <div class="mt-2 image-preview">
                    <img src="${q.image}" class="img-thumbnail" style="max-height: 100px">
                    <input type="hidden" 
                           name="questions[${questionCounter}][image]"
                           value="${q.image}">
                </div>` : ''}
        </div>
    `;

    // Points HTML - hide for AH_POINTS
    const pointsHtml = answerType !== 'AH_POINTS' ? `
        <div class="row mb-3">
            <div class="col-md-6">
                <label class="form-label">Maksymalna liczba punktów za</label>
                <input type="number" class="form-control" 
                    name="questions[${questionCounter}][points]" 
                    value="${q.points || 0}" min="0">
            </div>
        </div>
    ` : '';

    // Common answer type selection HTML
    const answerTypeHtml = `
        <div class="col-md-6">
            <label class="form-label">Typ odpowiedzi</label>
            <select class="form-select" name="questions[${questionCounter}][answer_type]" onchange="handleAnswerTypeChange(event)">
                <option value="TEXT" ${answerType === 'TEXT' ? 'selected' : ''}>Tekst</option>
                <option value="BOOLEAN" ${answerType === 'BOOLEAN' ? 'selected' : ''}>Tak/Nie</option>
                <option value="SCALE" ${answerType === 'SCALE' ? 'selected' : ''}>Skala (0-5)</option>
                <option value="SALARY" ${answerType === 'SALARY' ? 'selected' : ''}>Wynagrodzenie</option>
                <option value="DATE" ${answerType === 'DATE' ? 'selected' : ''}>Data</option>
                <option value="ABCDEF" ${answerType === 'ABCDEF' ? 'selected' : ''}>ABCDEF</option>
                <option value="NUMERIC" ${answerType === 'NUMERIC' ? 'selected' : ''}>Liczba</option>
                <option value="AH_POINTS" ${answerType === 'AH_POINTS' ? 'selected' : ''}>Punkty A-H</option>
            </select>
        </div>
    `;

    // Algorithm selection HTML - hide for AH_POINTS and show only available algorithms
    const algorithmSelectionHtml = answerType !== 'AH_POINTS' ? `
        <div class="col-md-6">
            <label class="form-label">Algorytm punktacji</label>
            <select class="form-select algorithm-type-select" 
                    name="questions[${questionCounter}][algorithm_type]"
                    onchange="handleAlgorithmTypeChange(this)">
                ${getAvailableAlgorithms(answerType).map(alg => `
                    <option value="${alg}" ${algorithmType === alg ? 'selected' : ''}>
                        ${alg === 'NO_ALGORITHM' ? 'Brak algorytmu' :
                          alg === 'EXACT_MATCH' ? 'Dokładne dopasowanie' :
                          alg === 'RANGE' ? 'Przedział' :
                          alg === 'LEFT_SIDED' ? 'Lewostronny' :
                          alg === 'RIGHT_SIDED' ? 'Prawostronny' :
                          alg === 'CENTER' ? 'Środkowy' :
                          alg === 'EVALUATION_BY_AI' ? 'Ocena przez AI' : alg}
                    </option>
                `).join('')}
            </select>
            <small class="text-muted">${getAlgorithmDescription(algorithmType)}</small>
        </div>
    ` : '';

    // Algorithm parameters HTML - hide for AH_POINTS
    const algorithmParamsHtml = answerType !== 'AH_POINTS' ? `
        <div class="col-12 mt-2 algorithm-params" style="display: ${algorithmType === 'NO_ALGORITHM' ? 'none' : 'block'}">
            <div class="row">
                <div class="col-md-4 min-value-container" style="display: ${['RANGE', 'LEFT_SIDED', 'CENTER'].includes(algorithmType) ? 'block' : 'none'}">
                    <label class="form-label">Wartość minimalna</label>
                    ${getMinMaxValueInput(answerType, questionCounter, 'min_value', algorithmParams?.min_value)}
                </div>
                <div class="col-md-4 correct-answer-container" style="display: ${algorithmType !== 'NO_ALGORITHM' && algorithmType !== 'EVALUATION_BY_AI' ? 'block' : 'none'}">
                    <label class="form-label">Poprawna odpowiedź</label>
                    ${getCorrectAnswerInput(answerType, questionCounter, algorithmParams?.correct_answer)}
                </div>
                <div class="col-md-4 max-value-container" style="display: ${['RANGE', 'RIGHT_SIDED', 'CENTER'].includes(algorithmType) ? 'block' : 'none'}">
                    <label class="form-label">Wartość maksymalna</label>
                    ${getMinMaxValueInput(answerType, questionCounter, 'max_value', algorithmParams?.max_value)}
                </div>
            </div>
        </div>
    ` : '';

    // Add answer type specific HTML
    let answerTypeSpecificHtml = '';
    if (answerType === 'AH_POINTS') {
        const options = q.options || {};
        answerTypeSpecificHtml = `
            <div class="col-12">
                <label class="form-label">Opcje odpowiedzi (A-H)*</label>
                <div class="options-container">
                    ${['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'].map(letter => {
                        const letterLower = letter.toLowerCase();
                        const value = options[letterLower] || '';
                        return `
                            <div class="option-row mb-2">
                                <div class="input-group">
                                    <span class="input-group-text">${letter}.</span>
                                    <input type="text" 
                                           class="form-control"
                                           name="questions[${questionCounter}][options][${letterLower}]"
                                           value="${value}"
                                           placeholder="Treść opcji ${letter}"
                                           data-letter="${letterLower}"
                                           required>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
    }

    return `
        <div class="row">
            ${imageUploadHtml}
            ${pointsHtml}
            ${answerTypeHtml}
            ${algorithmSelectionHtml}
            ${algorithmParamsHtml}
            ${answerTypeSpecificHtml}
        </div>
    `;
}

function getCorrectAnswerInput(answerType, questionCounter, value) {
    switch (answerType) {
        case 'TEXT':
            return `<input type="text" class="form-control" 
                           name="questions[${questionCounter}][algorithm_params][correct_answer]"
                           value="${value || ''}">`;
        
        case 'BOOLEAN':
            return `
                <div class="form-check">
                    <input type="radio" class="form-check-input" 
                           name="questions[${questionCounter}][algorithm_params][correct_answer]" 
                           value="true" ${value === 'true' ? 'checked' : ''}>
                    <label class="form-check-label">Prawda</label>
                </div>
                <div class="form-check">
                    <input type="radio" class="form-check-input" 
                           name="questions[${questionCounter}][algorithm_params][correct_answer]" 
                           value="false" ${value === 'false' ? 'checked' : ''}>
                    <label class="form-check-label">Fałsz</label>
                </div>`;
        
        case 'SCALE':
            return `
                <div class="scale-input-container">
                    <div class="scale-value-display" id="scaleValue_${questionCounter}">
                        Wybrana wartość: <span>${value || '0'}</span>
                    </div>
                    <input type="range" 
                           class="form-range" 
                           name="questions[${questionCounter}][algorithm_params][correct_answer]"
                           min="0" 
                           max="5" 
                           step="1"
                           value="${value || '0'}"
                           oninput="updateScaleValue(this, ${questionCounter})">
                    <div class="scale-labels">
                        <span class="scale-min">0 (Min)</span>
                        <span class="scale-max">5 (Max)</span>
                    </div>
                </div>`;
        
        case 'SALARY':
            return `<input type="number" class="form-control" 
                           name="questions[${questionCounter}][algorithm_params][correct_answer]"
                           min="0" step="1" 
                           value="${value || ''}">`;

        case 'NUMERIC':
            return `<input type="number" class="form-control" 
                           name="questions[${questionCounter}][algorithm_params][correct_answer]"
                           step="1" 
                           value="${value || ''}">`;
        
        case 'DATE':
            return `<input type="date" class="form-control" 
                           name="questions[${questionCounter}][algorithm_params][correct_answer]"
                           value="${value || ''}"
                           onclick="showDatePicker(this)">`;
        
        case 'ABCDEF':
            return `<select class="form-select" 
                            name="questions[${questionCounter}][algorithm_params][correct_answer]">
                        <option value="" ${!value ? 'selected' : ''}>Wybierz odpowiedź</option>
                        <option value="A" ${value === 'A' ? 'selected' : ''}>A</option>
                        <option value="B" ${value === 'B' ? 'selected' : ''}>B</option>
                        <option value="C" ${value === 'C' ? 'selected' : ''}>C</option>
                        <option value="D" ${value === 'D' ? 'selected' : ''}>D</option>
                        <option value="E" ${value === 'E' ? 'selected' : ''}>E</option>
                        <option value="F" ${value === 'F' ? 'selected' : ''}>F</option>
                    </select>`;
        
        default:
            return '';
    }
}

function handleAlgorithmTypeChange(select) {
    const questionCard = select.closest('.question-card');
    const algorithmParams = questionCard.querySelector('.algorithm-params');
    const minValueContainer = questionCard.querySelector('.min-value-container');
    const correctAnswerContainer = questionCard.querySelector('.correct-answer-container');
    const maxValueContainer = questionCard.querySelector('.max-value-container');
    const aiParamsContainer = questionCard.querySelector('.ai-params-container');
    
    // Update algorithm description
    const algorithmDescription = select.closest('div').querySelector('.text-muted');
    if (algorithmDescription) {
        algorithmDescription.textContent = getAlgorithmDescription(select.value);
    }
    
    // Hide all params initially
    algorithmParams.style.display = 'none';
    minValueContainer.style.display = 'none';
    correctAnswerContainer.style.display = 'none';
    maxValueContainer.style.display = 'none';
    if (aiParamsContainer) aiParamsContainer.style.display = 'none';
    
    // Show relevant params based on algorithm type
    switch (select.value) {
        case 'EVALUATION_BY_AI':
            algorithmParams.style.display = 'block';
            // Przenieśmy wszystkie kontenery poza AI na display: none
            minValueContainer.style.display = 'none';
            correctAnswerContainer.style.display = 'none';
            maxValueContainer.style.display = 'none';
            
            if (aiParamsContainer) {
                aiParamsContainer.style.display = 'block';
            } else {
                // Create AI params container if it doesn't exist
                const container = document.createElement('div');
                container.className = 'ai-params-container col-12 mt-3';
                container.innerHTML = createAIParamsHtml(questionCard);
                algorithmParams.appendChild(container);
            }
            break;
            
        case 'NO_ALGORITHM':
            break;
            
        case 'EXACT_MATCH':
            algorithmParams.style.display = 'block';
            correctAnswerContainer.style.display = 'block';
            break;
            
        case 'RANGE':
            algorithmParams.style.display = 'block';
            minValueContainer.style.display = 'block';
            maxValueContainer.style.display = 'block';
            break;
            
        case 'LEFT_SIDED':
            algorithmParams.style.display = 'block';
            minValueContainer.style.display = 'block';
            correctAnswerContainer.style.display = 'block';
            break;
            
        case 'RIGHT_SIDED':
            algorithmParams.style.display = 'block';
            correctAnswerContainer.style.display = 'block';
            maxValueContainer.style.display = 'block';
            break;
            
        case 'CENTER':
            algorithmParams.style.display = 'block';
            minValueContainer.style.display = 'block';
            correctAnswerContainer.style.display = 'block';
            maxValueContainer.style.display = 'block';
            break;
    }
}

function handleRemoveQuestion(e) {
    const questionCard = e.target.closest('.question-card');
    if (confirm('Czy na pewno chcesz usunąć to pytanie?')) {
        // Remove the question card
        questionCard.remove();
        
        // Update order numbers for remaining questions
        const container = document.querySelector('.questions-container');
        container.querySelectorAll('.question-card').forEach((card, index) => {
            // Update order number input
            const orderInput = card.querySelector('input[name$="[order_number]"]');
            if (orderInput) {
                orderInput.value = index + 1;
            }
            
            // Update question index in all field names
            card.querySelectorAll('[name*="questions["]').forEach(field => {
                field.name = field.name.replace(/questions\[\d+\]/, `questions[${index}]`);
            });
        });
    }
}

// Add this function after handleImageUpload function
function initializeImagePreviews() {
    document.querySelectorAll('.image-preview img').forEach(img => {
        // Add preview container if not already wrapped
        if (!img.parentElement.classList.contains('preview-image-container')) {
            const container = document.createElement('div');
            container.className = 'preview-image-container';
            img.parentNode.insertBefore(container, img);
            container.appendChild(img);
        }

        // Add click handler
        img.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const previewModal = new bootstrap.Modal(document.getElementById('imagePreviewModal'));
            const previewImage = document.getElementById('previewImage');
            
            previewImage.src = this.src;
            previewModal.show();
        };
    });
}

function getAlgorithmParamsValue(input, answerType) {
    if (!input) return null;
    
    const value = input.value;
    if (!value) return null;
    
    switch (answerType) {
        case 'BOOLEAN':
            return value === 'true';
        case 'SCALE':
        case 'SALARY':
        case 'NUMERIC':
            return parseFloat(value) || null;
        default:
            return value;
    }
}

// Add new function for min/max value inputs
function getMinMaxValueInput(answerType, questionCounter, fieldName, value) {
    switch (answerType) {
        case 'DATE':
            return `<input type="date" class="form-control date-picker-input" 
                           name="questions[${questionCounter}][algorithm_params][${fieldName}]"
                           value="${value || ''}"
                           onclick="showDatePicker(this)">`;
        
        case 'SCALE':
            return `<input type="number" class="form-control" 
                           name="questions[${questionCounter}][algorithm_params][${fieldName}]"
                           min="0" max="5" 
                           value="${value || ''}">`;
        
        case 'SALARY':
            return `<input type="number" class="form-control" 
                           name="questions[${questionCounter}][algorithm_params][${fieldName}]"
                           min="0" step="1" 
                           value="${value !== null ? value : ''}">`;

        case 'NUMERIC':
            return `<input type="number" class="form-control" 
                           name="questions[${questionCounter}][algorithm_params][${fieldName}]"
                           step="1" 
                           value="${value !== null ? value : ''}">`;
        
        default:
            return '';
    }
}

// Add new function to handle date picker clicks
function showDatePicker(input) {
    try {
        input.showPicker();
    } catch (e) {
        // Fallback for browsers that don't support showPicker()
        console.log('showPicker not supported in this browser');
    }
}

function createAIParamsHtml(questionCard) {
    const questionIndex = questionCard.querySelector('[name$="[order_number]"]').value - 1;
    
    // Get algorithm_params from the question data
    let params = {};
    try {
        const algorithmType = questionCard.querySelector('[name$="[algorithm_type]"]').value;
        if (algorithmType === 'EVALUATION_BY_AI') {
            const evaluationFocus = questionCard.querySelector('[name$="[algorithm_params][evaluation_focus]"]')?.value;
            const scoringCriteria = questionCard.querySelector('[name$="[algorithm_params][scoring_criteria]"]')?.value;
            params = {
                evaluation_focus: evaluationFocus || '',
                scoring_criteria: scoringCriteria || ''
            };
        }
    } catch (error) {
        console.error('Error getting AI params:', error);
    }
    
    return `
        <div class="row">
            <div class="col-12 mb-3">
                <label class="form-label">Na co zwrócić uwagę w odpowiedzi</label>
                <textarea class="form-control" 
                         name="questions[${questionIndex}][algorithm_params][evaluation_focus]"
                         rows="3">${params.evaluation_focus || ''}</textarea>
                <small class="text-muted">Opisz algorytm oceny odpowiedzi</small>
            </div>
            <div class="col-12 mb-3">
                <label class="form-label">Kryteria przyznawania punktów</label>
                <textarea class="form-control" 
                         name="questions[${questionIndex}][algorithm_params][scoring_criteria]"
                         rows="3">${params.scoring_criteria || ''}</textarea>
                <small class="text-muted">Opisz, jak powinny być przyznawane punkty za poszczególne elementy odpowiedzi</small>
            </div>
        </div>
    `;
}

function getAlgorithmDescription(algorithmType) {
    const descriptions = {
        'NO_ALGORITHM': 'Odpowiedź nie jest oceniana.',
        'EXACT_MATCH': 'Punkty przyznawane tylko za dokładnie poprawną odpowiedź.',
        'RANGE': 'Punkty przyznawane, jeśli odpowiedź mieści się w określonym przedziale.',
        'LEFT_SIDED': 'Im bliżej minimalnej wartości, tym mniej punktów. Wartości większe lub równe poprawnej odpowiedzi to maksymalna liczba punktów.',
        'RIGHT_SIDED': 'Im bliżej maksymalnej wartości, tym mniej punktów. Wartości mniejsze lub równe poprawnej odpowiedzi to maksymalna liczba punktów.',
        'CENTER': 'Maksymalna liczba punktów za dokładne dopasowanie odpowiedzi, punkty maleją proporcjonalnie wraz oddaleniem od poprawnej odpowiedzi.',
        'EVALUATION_BY_AI': 'Ocena przez sztuczną inteligencję na podstawie zdefiniowanych kryteriów.'
    };
    return descriptions[algorithmType] || '';
}

// Dodaj nową funkcję do określania dostępnych algorytmów
function getAvailableAlgorithms(answerType) {
    const commonAlgorithms = ['NO_ALGORITHM'];
    
    switch (answerType) {
        case 'TEXT':
            return [...commonAlgorithms, 'EXACT_MATCH', 'EVALUATION_BY_AI'];
        case 'BOOLEAN':
            return [...commonAlgorithms, 'EXACT_MATCH'];
        case 'SCALE':
        case 'NUMERIC':
        case 'SALARY':
            return [...commonAlgorithms, 'RANGE', 'LEFT_SIDED', 'RIGHT_SIDED', 'CENTER'];
        case 'DATE':
            return [...commonAlgorithms, 'EXACT_MATCH', 'RANGE', 'LEFT_SIDED', 'RIGHT_SIDED'];
        case 'ABCDEF':
            return [...commonAlgorithms, 'EXACT_MATCH'];
        default:
            return commonAlgorithms;
    }
}

// Dodaj tę funkcję na początku pliku
function handleTestTypeChange(select) {
    const form = select.closest('form');
    const thresholdContainer = form.querySelector('[name="passing_threshold"]').closest('.col-md-12');
    
    if (select.value === 'EQ') {
        thresholdContainer.style.display = 'none';
        // Ustaw wartość na 0 gdy ukrywamy
        thresholdContainer.querySelector('input').value = '0';
    } else {
        thresholdContainer.style.display = 'block';
    }
}

function initializeSortableHeaders() {
    const headers = document.querySelectorAll('th.sortable');
    headers.forEach(header => {
        header.addEventListener('click', function() {
            const sortField = this.dataset.sort;
            const currentDirection = this.classList.contains('asc') ? 'asc' : 
                                   this.classList.contains('desc') ? 'desc' : null;
            
            // Aktualizuj kierunek sortowania
            let newDirection;
            if (!currentDirection) {
                newDirection = 'asc';
            } else if (currentDirection === 'asc') {
                newDirection = 'desc';
            } else {
                // Usuń sortowanie dla tej kolumny
                this.classList.remove('desc');
                // Usuń wskaźnik kolejności
                const orderIndicator = this.querySelector('.sort-order');
                if (orderIndicator) {
                    orderIndicator.remove();
                }
                currentSorts = currentSorts.filter(sort => sort.field !== sortField);
                // Zaktualizuj numerację pozostałych sortowań
                currentSorts.forEach((sort, index) => {
                    const header = document.querySelector(`th[data-sort="${sort.field}"]`);
                    const indicator = header.querySelector('.sort-order');
                    if (indicator) {
                        indicator.textContent = index + 1;
                    }
                });
                updateTable(true);
                return;
            }

            // Usuń istniejące sortowanie dla tego pola
            currentSorts = currentSorts.filter(sort => sort.field !== sortField);
            
            // Dodaj nowe sortowanie
            currentSorts.push({
                field: sortField,
                direction: newDirection,
                order: currentSorts.length + 1
            });

            // Aktualizuj klasy i wskaźniki
            this.classList.remove('asc', 'desc');
            this.classList.add(newDirection);

            // Aktualizuj lub dodaj wskaźnik kolejności
            let orderIndicator = this.querySelector('.sort-order');
            if (!orderIndicator) {
                orderIndicator = document.createElement('span');
                orderIndicator.className = 'sort-order';
                this.appendChild(orderIndicator);
            }
            orderIndicator.textContent = currentSorts.length;

            updateTable(true);
        });
    });
}
 