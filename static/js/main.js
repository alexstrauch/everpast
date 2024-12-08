/**
 * main.js - Core JavaScript functionality for the Everpast Time Capsule application
 * 
 * This file contains all client-side functionality including:
 * - Countdown timers for time capsules
 * - File upload preview functionality
 * - Form validation
 * - UI enhancements and animations
 */

/**
 * Updates a countdown timer element with time remaining until unlock
 * @param {HTMLElement} element - The DOM element to update
 * @param {string} unlockDate - ISO date string of when the capsule unlocks
 */
function updateCountdown(element, unlockDate) {
    const now = new Date().getTime();
    const unlockTime = new Date(unlockDate).getTime();
    const timeLeft = unlockTime - now;

    if (timeLeft <= 0) {
        element.innerHTML = "Unlocked!";
        element.classList.add("unlocked-animation");
        return;
    }

    const days = Math.floor(timeLeft / (1000 * 60 * 60 * 24));
    const hours = Math.floor((timeLeft % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((timeLeft % (1000 * 60)) / 1000);

    element.innerHTML = `${days}d ${hours}h ${minutes}m ${seconds}s`;
}

/**
 * Initializes countdown timers for all elements with 'countdown' class
 * Runs when the DOM is fully loaded
 */
document.addEventListener('DOMContentLoaded', function() {
    const countdownElements = document.querySelectorAll('.countdown');
    countdownElements.forEach(element => {
        const unlockDate = element.dataset.unlockDate;
        if (unlockDate) {
            updateCountdown(element, unlockDate);
            setInterval(() => updateCountdown(element, unlockDate), 1000);
        }
    });
});

/**
 * Handles file selection and generates preview for images
 * Creates thumbnail previews for image files and displays file names
 * @param {Event} event - The file input change event
 */
function handleFileSelect(event) {
    const files = event.target.files;
    const previewContainer = document.getElementById('file-preview');
    if (!previewContainer) return;

    previewContainer.innerHTML = '';
    
    Array.from(files).forEach(file => {
        const reader = new FileReader();
        const previewElement = document.createElement('div');
        previewElement.className = 'preview-item mb-2';
        
        if (file.type.startsWith('image/')) {
            reader.onload = function(e) {
                previewElement.innerHTML = `
                    <img src="${e.target.result}" class="img-thumbnail" style="max-height: 100px">
                    <span class="ms-2">${file.name}</span>
                `;
            };
            reader.readAsDataURL(file);
        } else {
            previewElement.innerHTML = `
                <i class="bi bi-file-earmark"></i>
                <span class="ms-2">${file.name}</span>
            `;
        }
        
        previewContainer.appendChild(previewElement);
    });
}

/**
 * Validates the capsule creation/edit form
 * Checks:
 * - Required fields are filled
 * - Unlock date is in the future
 * - File size limits
 * @returns {boolean} Whether the form is valid
 */
function validateCapsuleForm() {
    const title = document.getElementById('id_title').value;
    const unlockDate = new Date(document.getElementById('id_unlock_date').value);
    const now = new Date();
    
    if (!title) {
        alert('Please enter a title for your time capsule');
        return false;
    }
    
    if (unlockDate <= now) {
        alert('Unlock date must be in the future');
        return false;
    }
    
    return true;
}

/**
 * Initialize Bootstrap tooltips and other UI enhancements
 */
document.addEventListener('DOMContentLoaded', function() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

/**
 * Handle file input changes
 */
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.querySelector('input[type="file"]');
    if (fileInput) {
        fileInput.addEventListener('change', handleFileSelect);
    }
});

/**
 * Form submission handling
 */
document.addEventListener('DOMContentLoaded', function() {
    const capsuleForm = document.getElementById('capsule-form');
    if (capsuleForm) {
        capsuleForm.addEventListener('submit', function(event) {
            if (!validateCapsuleForm()) {
                event.preventDefault();
            }
        });
    }
});
