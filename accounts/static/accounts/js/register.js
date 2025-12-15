// File upload interaction
document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.querySelector('input[type="file"]');
    const fileName = document.getElementById('fileName');

    if (uploadArea && fileInput) {
        // Click to upload
        uploadArea.addEventListener('click', () => fileInput.click());

        // File selection
        fileInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                fileName.textContent = `Selected: ${this.files[0].name}`;
                fileName.style.display = 'block';
            }
        });

        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = '#003DA5';
            uploadArea.style.backgroundColor = '#f0f5ff';
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.style.borderColor = '#cbd5e1';
            uploadArea.style.backgroundColor = '#f8fafc';
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = '#cbd5e1';
            uploadArea.style.backgroundColor = '#f8fafc';
            
            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                fileName.textContent = `Selected: ${e.dataTransfer.files[0].name}`;
                fileName.style.display = 'block';
            }
        });
    }

    // Form validation
    function checkCapitalization(input) {
        const value = input.value;
        if (value.length > 0 && !value[0].match(/[A-Z]/)) {
            input.setCustomValidity("This field must start with a capital letter.");
        } else {
            input.setCustomValidity("");
        }
    }

    function validatePhoneNumber(input) {
        input.value = input.value.replace(/\D/g, '');
        if (input.value.length > 11) {
            input.value = input.value.slice(0, 11);
        }
    }

    // Add event listeners to name fields
    const nameFields = document.querySelectorAll('input[name$="name"], input[name="citizenship"]');
    nameFields.forEach(function(field) {
        field.addEventListener('input', function() { 
            checkCapitalization(this); 
        });
    });

    // Phone number validation
    const phoneField = document.querySelector('input[name="phone_number"]');
    if (phoneField) {
        phoneField.addEventListener('input', function() {
            validatePhoneNumber(this);
        });
        
        phoneField.addEventListener('keypress', function(e) {
            if (e.which < 48 || e.which > 57) {
                if (e.which !== 8 && e.which !== 9 && e.which !== 46 && 
                    e.which !== 37 && e.which !== 38 && e.which !== 39 && e.which !== 40 &&
                    (e.which < 127 || e.which > 127)) {
                    e.preventDefault();
                }
            }
            
            if (this.value.length >= 11 && (e.which >= 48 && e.which <= 57)) {
                e.preventDefault();
            }
        });
    }
});

// Success Modal Functions
function showSuccessModal() {
    const modal = document.getElementById('successModal');
    if (modal) {
        modal.classList.add('show');
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
    }
}

function closeSuccessModal() {
    const modal = document.getElementById('successModal');
    if (modal) {
        modal.classList.remove('show');
        document.body.style.overflow = ''; // Restore scrolling
        // Redirect to login page after closing
        window.location.href = "/login/";
    }
}

// Auto-show modal if registration was successful
document.addEventListener('DOMContentLoaded', function() {
    // Check if success parameter exists in URL
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('success') === 'true') {
        showSuccessModal();
    }
});

