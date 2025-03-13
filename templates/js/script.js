document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu toggle
    const menuToggle = document.querySelector('.menu-toggle');
    const navLinks = document.querySelector('.nav-links');
    
    if (menuToggle) {
        menuToggle.addEventListener('click', function() {
            navLinks.classList.toggle('active');
        });
    }
    
    // Close flash messages
    const closeButtons = document.querySelectorAll('.close-btn');
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            this.parentElement.style.display = 'none';
        });
    });
    
    // Testimonial slider auto-scroll
    const testimonialSlider = document.querySelector('.testimonial-slider');
    if (testimonialSlider) {
        const testimonials = testimonialSlider.querySelectorAll('.testimonial');
        let currentIndex = 0;
        
        function scrollToNextTestimonial() {
            currentIndex = (currentIndex + 1) % testimonials.length;
            testimonials[currentIndex].scrollIntoView({
                behavior: 'smooth',
                block: 'nearest',
                inline: 'start'
            });
        }
        
        // Auto-scroll every 5 seconds
        setInterval(scrollToNextTestimonial, 5000);
    }
    
    // Dropdown functionality
    const dropdownToggles = document.querySelectorAll('.dropdown-toggle');
    dropdownToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const dropdownMenu = this.nextElementSibling;
            dropdownMenu.classList.toggle('show');
            
            // Close when clicking outside
            document.addEventListener('click', function closeDropdown(e) {
                if (!toggle.contains(e.target) && !dropdownMenu.contains(e.target)) {
                    dropdownMenu.classList.remove('show');
                    document.removeEventListener('click', closeDropdown);
                }
            });
        });
    });
    
    // Add 'show' class to make dropdown visible
    document.head.insertAdjacentHTML('beforeend', `
        <style>
            .dropdown-menu {
                display: none;
                position: absolute;
                z-index: 1000;
                min-width: 10rem;
                margin-top: 0.5rem;
            }
            .dropdown-menu.show {
                display: block;
            }
        </style>
    `);
});