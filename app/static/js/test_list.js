// Global variables and initialization
let originalRows = [];

document.addEventListener('DOMContentLoaded', function() {
    // Store original table rows
    const tbody = document.querySelector('tbody');
    originalRows = Array.from(tbody.querySelectorAll('tr'));
    
    // Initialize filters and buttons
    initializeFilters();
    initializeEventListeners();
    checkPendingToast();
    
    // Initialize Sortable after modals are shown
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('shown.bs.modal', function() {
            initializeSortable();
        });
    });
});

function initializeFilters() {
    const filterTestType = document.getElementById('filterTestType');
    const filterGroup = document.getElementById('filterGroup');
    const sortBy = document.getElementById('sortBy');
    const sortOrder = document.getElementById('sortOrder');
    const applyFilters = document.getElementById('applyFilters');
    const resetFilters = document.getElementById('resetFilters');
    
    applyFilters?.addEventListener('click', () => updateTable(true));
    resetFilters?.addEventListener('click', function() {
        filterTestType.value = '';
        filterGroup.value = '';
        sortBy.value = 'created_at';
        sortOrder.value = 'desc';
        updateTable(false);
    });
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
}

function updateTable(applyFilters) {
    const tbody = document.querySelector('tbody');
    const filterTestType = document.getElementById('filterTestType');
    const filterGroup = document.getElementById('filterGroup');
    const sortBy = document.getElementById('sortBy');
    const sortOrder = document.getElementById('sortOrder');
    
    if (!applyFilters) {
        // Reset to original state
        tbody.innerHTML = '';
        originalRows.forEach(row => {
            tbody.appendChild(row.cloneNode(true));
        });
        return;
    }
    
    // Clone original rows for filtering
    let rows = originalRows.map(row => row.cloneNode(true));
    
    // Apply filters
    if (filterTestType.value || filterGroup.value) {
        rows = rows.filter(row => {
            const testType = row.querySelector('td:nth-child(2)').textContent.trim();
            const testGroups = JSON.parse(row.dataset.groups || '[]');
            
            const testTypeMatch = !filterTestType.value || 
                (filterTestType.value === 'SURVEY' && testType === 'Ankieta') ||
                (filterTestType.value === 'EQ' && testType === 'Test EQ') ||
                (filterTestType.value === 'IQ' && testType === 'Test IQ');
                
            const groupMatch = !filterGroup.value || 
                testGroups.some(group => group.id === parseInt(filterGroup.value));
            
            return testTypeMatch && groupMatch;
        });
    }
    
    // Apply sorting
    if (sortBy.value) {
        rows.sort((a, b) => {
            const aValue = getRowValue(a, sortBy.value);
            const bValue = getRowValue(b, sortBy.value);
            
            const order = sortOrder.value === 'asc' ? 1 : -1;
            
            if (typeof aValue === 'string') {
                return aValue.localeCompare(bValue) * order;
            }
            
            if (aValue < bValue) return -1 * order;
            if (aValue > bValue) return 1 * order;
            return 0;
        });
    }
    
    // Update table
    tbody.innerHTML = '';
    rows.forEach(row => tbody.appendChild(row));
}

function getRowValue(row, sortField) {
    switch (sortField) {
        case 'time_limit':
            const timeText = row.querySelector('td:nth-child(3)').textContent;
            return parseInt(timeText.replace(' min', '')) || 0;
        case 'questions':
            return parseInt(row.querySelector('td:nth-child(4)').textContent) || 0;
        case 'created_at':
            const dateText = row.querySelector('td:nth-child(8)').textContent;
            return new Date(dateText).getTime() || 0;
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
    form.querySelector('[name="test_type"]').selectedIndex = 0;
    
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
    console.log(`Starting edit process for test ID: ${testId}`);
    fetch(`/tests/${testId}/data`)
        .then(response => response.json())
        .then(test => {
            console.log('Test data received:', test);
            const form = document.getElementById('editTestForm');
            form.action = `/tests/${testId}/edit`;
            
            // Populate basic test fields
            form.querySelector('[name="title"]').value = test.title || '';
            form.querySelector('[name="test_type"]').value = test.test_type || '';
            form.querySelector('[name="description"]').value = test.description || '';
            form.querySelector('[name="passing_threshold"]').value = test.passing_threshold || 0;
            form.querySelector('[name="time_limit_minutes"]').value = test.time_limit_minutes || '';

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
    
    switch (answerType) {
        case 'TEXT':
            const textInput = questionCard.querySelector(`[name$="[correct_answer_text]"]`);
            if (textInput) {
                textInput.value = question.correct_answer_text || '';
            }
            break;
            
        case 'BOOLEAN':
            const boolValue = question.correct_answer_boolean;
            if (boolValue !== null) {
                const radio = questionCard.querySelector(`[name$="[correct_answer_boolean]"][value="${boolValue}"]`);
                if (radio) {
                    radio.checked = true;
                }
            }
            break;
            
        case 'SCALE':
            const scaleInput = questionCard.querySelector(`[name$="[correct_answer_scale]"]`);
            if (scaleInput && question.correct_answer_scale !== null) {
                scaleInput.value = question.correct_answer_scale;
            }
            break;
            
        case 'SALARY':
            const salaryInput = questionCard.querySelector(`[name$="[correct_answer_salary]"]`);
            if (salaryInput && question.correct_answer_salary !== null) {
                salaryInput.value = question.correct_answer_salary;
            }
            break;
            
        case 'DATE':
            const dateInput = questionCard.querySelector(`[name$="[correct_answer_date]"]`);
            if (dateInput) {
                dateInput.value = question.correct_answer_date || '';
            }
            break;
            
        case 'ABCDEF':
            const abcdefSelect = questionCard.querySelector(`[name$="[correct_answer_abcdef]"]`);
            if (abcdefSelect) {
                abcdefSelect.value = question.correct_answer_abcdef || '';
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
                showToast('Test został usunięty', 'success');
                document.querySelector(`tr[data-test-id="${testId}"]`).remove();
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
        <div class="card mb-2 question-card" 
             data-question-id="${q.id || ''}" 
             data-question-index="${questionCounter}">
            <input type="hidden" name="questions[${questionCounter}][id]" value="${q.id || ''}">
            <input type="hidden" name="questions[${questionCounter}][order_number]" 
                   value="${q.order_number || questionCounter + 1}">
            
            <div class="card-header d-flex justify-content-between align-items-center">
                <div class="form-check form-switch">
                    <input type="checkbox" class="form-check-input" 
                           name="questions[${questionCounter}][is_required]"
                           ${q.is_required !== false ? 'checked' : ''}>
                    <label class="form-check-label">Pytanie obowiązkowe</label>
                </div>
                <button type="button" class="btn btn-danger btn-sm remove-question">
                    Usuń pytanie
                </button>
            </div>
            
            <div class="card-body">
                <div class="d-flex">
                    <div class="drag-handle me-3 d-flex align-items-center" 
                         title="Przeciągnij aby zmienić kolejność"
                         style="cursor: move;">☰</div>
                    
                    <div class="border-start ps-3 flex-grow-1">
                        <div class="row mb-3">
                            <div class="col-12">
                                <label class="form-label">Treść pytania*</label>
                                <input type="text" class="form-control" 
                                       name="questions[${questionCounter}][question_text]"
                                       value="${q.question_text || ''}" required>
                            </div>
                        </div>
                        
                        <div class="row mb-3">
                            <div class="col-12">
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
                        </div>
                        
                        <div class="row mb-3">
                            <div class="col-md-4">
                                <label class="form-label">Typ odpowiedzi*</label>
                                <select class="form-select answer-type-select" 
                                        name="questions[${questionCounter}][answer_type]" required>
                                    <option value="TEXT" ${q.answer_type === 'TEXT' ? 'selected' : ''}>Tekst</option>
                                    <option value="BOOLEAN" ${q.answer_type === 'BOOLEAN' ? 'selected' : ''}>Tak/Nie</option>
                                    <option value="SCALE" ${q.answer_type === 'SCALE' ? 'selected' : ''}>Skala (0-5)</option>
                                    <option value="SALARY" ${q.answer_type === 'SALARY' ? 'selected' : ''}>Wynagrodzenie (Netto PLN)</option>
                                    <option value="DATE" ${q.answer_type === 'DATE' ? 'selected' : ''}>Data</option>
                                    <option value="ABCDEF" ${q.answer_type === 'ABCDEF' ? 'selected' : ''}>ABCDEF</option>
                                    <option value="AH_POINTS" ${q.answer_type === 'AH_POINTS' ? 'selected' : ''}>Test EQ (A-H)</option>
                                </select>
                            </div>
                            <div class="col-md-8">
                                <div class="answer-fields">
                                    ${createAnswerFieldsHtml(questionCounter, q)}
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-4">
                                <label class="form-label">Punkty za pytanie*</label>
                                <input type="number" class="form-control" 
                                       name="questions[${questionCounter}][points]"
                                       value="${q.points || '0'}" 
                                       min="0"
                                       required>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function handleAnswerTypeChange(e) {
    const questionCard = e.target.closest('.question-card');
    const answerFieldsContainer = questionCard.querySelector('.answer-fields');
    const questionCounter = questionCard.dataset.questionIndex;
    
    // Remove all existing answer-related hidden inputs
    const hiddenInputs = questionCard.querySelectorAll('input[type="hidden"]');
    hiddenInputs.forEach(input => {
        if (input.name.includes('correct_answer')) {
            input.remove();
        }
    });
    
    // Clear the answer fields container and create new fields
    answerFieldsContainer.innerHTML = createAnswerFieldsHtml(questionCounter, {
        answer_type: e.target.value
    });
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
        };
        reader.readAsDataURL(file);
    }
}

function handleTestFormSubmit(e) {
    e.preventDefault();
    const form = this;
    const formData = new FormData(form);
    const isEdit = form.id === 'editTestForm';
    
    // Get button elements
    const submitButton = form.querySelector('button[type="submit"]');
    const spinner = submitButton.querySelector('.spinner-border');
    const buttonText = submitButton.querySelector('.button-text');
    
    // Show loading state
    submitButton.disabled = true;
    spinner.classList.remove('d-none');
    buttonText.textContent = 'Zapisywanie...';
    
    // Get questions data
    const questions = [];
    form.querySelectorAll('.question-card').forEach((card, index) => {
        const questionData = {
            id: card.dataset.questionId || '',
            question_text: card.querySelector('[name$="[question_text]"]').value,
            answer_type: card.querySelector('[name$="[answer_type]"]').value,
            points: parseInt(card.querySelector('[name$="[points]"]').value || '0'),
            order_number: index + 1,
            is_required: card.querySelector('[name$="[is_required]"]').checked,
            image: card.querySelector('input[name$="[image]"]')?.value || null
        };

        // Handle answer type specific fields
        const answerType = questionData.answer_type;
        switch (answerType) {
            case 'BOOLEAN':
                const selectedRadio = card.querySelector('input[name$="[correct_answer_boolean]"]:checked');
                questionData.correct_answer_boolean = selectedRadio ? selectedRadio.value === 'true' : null;
                break;
            case 'ABCDEF':
                const abcdefSelect = card.querySelector('[name$="[correct_answer_abcdef]"]');
                questionData.correct_answer_abcdef = abcdefSelect ? abcdefSelect.value : null;
                break;
            case 'SALARY':
                const salaryValue = card.querySelector('[name$="[correct_answer_salary]"]')?.value;
                questionData.correct_answer_salary = salaryValue ? Number(salaryValue) : null;
                break;
            case 'AH_POINTS':
                const options = {};
                card.querySelectorAll('[name*="[options]"]').forEach(input => {
                    const letterMatch = input.name.match(/\[options\]\[([a-h])\]/);
                    if (letterMatch) {
                        options[letterMatch[1]] = input.value.trim();
                    }
                });
                questionData.options = options;
                break;
            default:
                const answerField = `correct_answer_${answerType.toLowerCase()}`;
                const answerInput = card.querySelector(`[name$="[${answerField}]"]`);
                if (answerInput) {
                    questionData[answerField] = answerInput.value;
                }
        }

        questions.push(questionData);
    });

    formData.append('questions', JSON.stringify(questions));
    
    fetch(form.action, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            sessionStorage.setItem('pendingToast', JSON.stringify({
                message: data.message || (isEdit ? 'Test został zaktualizowany' : 'Test został dodany'),
                type: 'success'
            }));

            const modal = bootstrap.Modal.getInstance(form.closest('.modal'));
            modal.hide();
            
            modal._element.addEventListener('hidden.bs.modal', function () {
                window.location.reload();
            }, { once: true });
        } else {
            throw new Error(data.error || 'Wystąpił błąd');
        }
    })
    .catch(error => {
        console.error('Error submitting form:', error);
        showToast(error.message, 'error');
        
        // Reset button state
        submitButton.disabled = false;
        spinner.classList.add('d-none');
        buttonText.textContent = isEdit ? 'Zapisz zmiany' : 'Zapisz test';
    });
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
            onEnd: function(evt) {
                updateQuestionOrders(container);
            }
        });
    });
}

function updateQuestionOrders(container) {
    container.querySelectorAll('.question-card').forEach((card, index) => {
        card.dataset.order = index + 1;
        card.querySelector('input[name$="[order_number]"]').value = index + 1;
    });
}

function duplicateTest(testId) {
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

function createAnswerFieldsHtml(questionCounter, question) {
    const q = question || {};
    const answerType = q.answer_type || 'TEXT';
    
    switch (answerType) {
        case 'TEXT':
            return `
                <div class="row">
                    <div class="col-md-12">
                        <label class="form-label">Poprawna odpowiedź tekstowa</label>
                        <input type="text" class="form-control" 
                               name="questions[${questionCounter}][correct_answer_text]"
                               value="${q.correct_answer_text || ''}">
                    </div>
                </div>
            `;
            
        case 'BOOLEAN':
            return `
                <div>
                    <label class="form-label">Poprawna odpowiedź</label>
                    <div class="form-check">
                        <input type="radio" class="form-check-input" 
                               name="questions[${questionCounter}][correct_answer_boolean]" 
                               value="true" ${q.correct_answer_boolean === true ? 'checked' : ''}>
                        <label class="form-check-label">Prawda</label>
                    </div>
                    <div class="form-check">
                        <input type="radio" class="form-check-input" 
                               name="questions[${questionCounter}][correct_answer_boolean]" 
                               value="false" ${q.correct_answer_boolean === false ? 'checked' : ''}>
                        <label class="form-check-label">Fałsz</label>
                    </div>
                </div>
            `;
            
        case 'SCALE':
            return `
                <div class="row">
                    <div class="col-md-6">
                        <label class="form-label">Poprawna odpowiedź (0-5)</label>
                        <input type="number" class="form-control" 
                               name="questions[${questionCounter}][correct_answer_scale]"
                               min="0" max="5" 
                               value="${q.correct_answer_scale || ''}">
                    </div>
                </div>
            `;
            
        case 'SALARY':
            return `
                <div class="row">
                    <div class="col-md-6">
                        <label class="form-label">Poprawna odpowiedź (Netto PLN)</label>
                        <input type="number" class="form-control" 
                               name="questions[${questionCounter}][correct_answer_salary]"
                               min="0" step="1" 
                               value="${q.correct_answer_salary !== null ? q.correct_answer_salary : ''}">
                    </div>
                </div>
            `;
            
        case 'DATE':
            return `
                <div class="row">
                    <div class="col-md-6">
                        <label class="form-label">Poprawna data</label>
                        <input type="date" class="form-control" 
                               name="questions[${questionCounter}][correct_answer_date]"
                               value="${q.correct_answer_date || ''}">
                    </div>
                </div>
            `;
            
        case 'ABCDEF':
            return `
                <div class="row">
                    <div class="col-md-6">
                        <label class="form-label">Poprawna odpowiedź</label>
                        <select class="form-select" 
                                name="questions[${questionCounter}][correct_answer_abcdef]">
                            <option value="" ${!q.correct_answer_abcdef ? 'selected' : ''}>Wybierz odpowiedź</option>
                            <option value="A" ${q.correct_answer_abcdef === 'A' ? 'selected' : ''}>A</option>
                            <option value="B" ${q.correct_answer_abcdef === 'B' ? 'selected' : ''}>B</option>
                            <option value="C" ${q.correct_answer_abcdef === 'C' ? 'selected' : ''}>C</option>
                            <option value="D" ${q.correct_answer_abcdef === 'D' ? 'selected' : ''}>D</option>
                            <option value="E" ${q.correct_answer_abcdef === 'E' ? 'selected' : ''}>E</option>
                            <option value="F" ${q.correct_answer_abcdef === 'F' ? 'selected' : ''}>F</option>
                        </select>
                    </div>
                </div>
            `;
            
        case 'AH_POINTS':
            const options = q.options || {};
            return `
                <div class="row">
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
                </div>
            `;
            
        default:
            return '';
    }
} 