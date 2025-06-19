document.addEventListener('DOMContentLoaded', function() {
    // Dark mode toggle
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', function() {
            const csrftoken = getCookie('csrftoken');
            const currentTheme = document.documentElement.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

            // Update theme immediately for better UX
            document.documentElement.setAttribute('data-bs-theme', newTheme);
            localStorage.setItem('theme', newTheme);

            // Update icon and text immediately
            const icon = darkModeToggle.querySelector('i');
            const text = darkModeToggle.childNodes[1];
            if (newTheme === 'dark') {
                icon.className = 'bi bi-sun';
                text.textContent = ' Light Mode';
            } else {
                icon.className = 'bi bi-moon';
                text.textContent = ' Dark Mode';
            }

            // Send request to server
            fetch('/users/toggle-dark-mode/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                console.log('Dark mode preference saved to server');
            })
            .catch(error => {
                console.error('Error:', error);
                // Don't revert the UI change, just show an error message
                const errorMessage = document.createElement('div');
                errorMessage.className = 'alert alert-warning alert-dismissible fade show fixed-top m-3';
                errorMessage.innerHTML = `
                    Warning: Could not save theme preference to server. 
                    Your preference will be restored when you reload the page.
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                `;
                document.body.appendChild(errorMessage);
            });
        });
    }

    // Star rating functionality
    const ratingInputs = document.querySelectorAll('.rating input');
    ratingInputs.forEach(input => {
        input.addEventListener('change', function() {
            this.form.submit();
        });
    });

    // Date picker minimum date
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        const today = new Date().toISOString().split('T')[0];
        input.min = today;
    });

    // Initialize tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(el => new bootstrap.Tooltip(el));

    // File input preview
    const profilePictureInput = document.getElementById('id_profile_picture');
    const profilePicturePreview = document.getElementById('profile_picture_preview');
    if (profilePictureInput && profilePicturePreview) {
        profilePictureInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    profilePicturePreview.src = e.target.result;
                };
                reader.readAsDataURL(file);
            }
        });
    }
});

// CSRF token helper function
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
} 