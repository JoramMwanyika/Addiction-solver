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
        const dots = document.querySelectorAll('.testimonial-dot');
        let currentIndex = 0;
        let autoScrollInterval;
        
        function updateDots() {
            dots.forEach((dot, index) => {
                dot.classList.toggle('active', index === currentIndex);
            });
        }
        
        function scrollToTestimonial(index) {
            currentIndex = index;
            testimonials[currentIndex].scrollIntoView({
                behavior: 'smooth',
                block: 'nearest',
                inline: 'start'
            });
            updateDots();
        }
        
        function scrollToNextTestimonial() {
            currentIndex = (currentIndex + 1) % testimonials.length;
            scrollToTestimonial(currentIndex);
        }
        
        // Add click handlers to dots
        dots.forEach((dot, index) => {
            dot.addEventListener('click', () => {
                scrollToTestimonial(index);
            });
        });
        
        // Pause auto-scroll on hover
        testimonialSlider.addEventListener('mouseenter', () => {
            clearInterval(autoScrollInterval);
        });
        
        testimonialSlider.addEventListener('mouseleave', () => {
            autoScrollInterval = setInterval(scrollToNextTestimonial, 5000);
        });
        
        // Start auto-scroll
        autoScrollInterval = setInterval(scrollToNextTestimonial, 5000);
        
        // Handle touch events for mobile
        let touchStartX = 0;
        let touchEndX = 0;
        
        testimonialSlider.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
        });
        
        testimonialSlider.addEventListener('touchend', (e) => {
            touchEndX = e.changedTouches[0].screenX;
            handleSwipe();
        });
        
        function handleSwipe() {
            const swipeThreshold = 50;
            const diff = touchStartX - touchEndX;
            
            if (Math.abs(diff) > swipeThreshold) {
                if (diff > 0) {
                    // Swipe left
                    scrollToNextTestimonial();
                } else {
                    // Swipe right
                    currentIndex = (currentIndex - 1 + testimonials.length) % testimonials.length;
                    scrollToTestimonial(currentIndex);
                }
            }
        }
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