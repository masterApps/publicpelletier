const hamburger = document.querySelector('.hamburger');
const navMenu = document.querySelector('.nav-menu');

// Function to handle clicking outside the menu to close it
function handleOutsideClick(event) {
    // If menu is active and click is outside the menu
    if (navMenu.classList.contains('active') &&
        !navMenu.contains(event.target) &&
        event.target !== hamburger) {
        navMenu.classList.remove('active');
        hamburger.textContent = '☰';
    }
}

// Hamburger menu toggle
hamburger.addEventListener('click', () => {
    navMenu.classList.toggle('active');

    // Change hamburger icon between ☰ and ✕
    if (hamburger.textContent === '☰') {
        hamburger.textContent = '✕';
        // Add click event listener to document when menu is open
        setTimeout(() => {
            document.addEventListener('click', handleOutsideClick);
        }, 10);
    } else {
        hamburger.textContent = '☰';
        document.removeEventListener('click', handleOutsideClick);
    }
});

// Close menu when clicking a nav link (non-dropdown links)
document.querySelectorAll('.nav-link:not(.dropdown-toggle)').forEach(link => {
    link.addEventListener('click', () => {
        navMenu.classList.remove('active');
        hamburger.textContent = '☰';
        document.removeEventListener('click', handleOutsideClick);
    });
});

// Dropdown menu functionality
const dropdownToggles = document.querySelectorAll('.dropdown-toggle');

dropdownToggles.forEach(toggle => {
    toggle.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();

        const parentItem = toggle.closest('.nav-item');
        const dropdownMenu = parentItem.querySelector('.dropdown-menu');

        // Check if we're in mobile view
        const isMobile = window.innerWidth <= 768;

        if (isMobile) {
            // Mobile: Toggle the dropdown within the drawer
            parentItem.classList.toggle('active');
            dropdownMenu.classList.toggle('show');
        } else {
            // Desktop: Close other dropdowns and toggle current
            document.querySelectorAll('.nav-item.has-dropdown').forEach(item => {
                if (item !== parentItem) {
                    item.classList.remove('active');
                    item.querySelector('.dropdown-menu').classList.remove('show');
                }
            });

            parentItem.classList.toggle('active');
            dropdownMenu.classList.toggle('show');
        }
    });
});

// Close dropdown when clicking outside (desktop only)
document.addEventListener('click', (e) => {
    const isMobile = window.innerWidth <= 768;

    if (!isMobile) {
        if (!e.target.closest('.has-dropdown')) {
            document.querySelectorAll('.nav-item.has-dropdown').forEach(item => {
                item.classList.remove('active');
                item.querySelector('.dropdown-menu').classList.remove('show');
            });
        }
    }
});

// Close dropdown on window resize if switching from mobile to desktop
let previousWidth = window.innerWidth;
window.addEventListener('resize', () => {
    const currentWidth = window.innerWidth;

    // If switching from mobile to desktop or vice versa
    if ((previousWidth <= 768 && currentWidth > 768) ||
        (previousWidth > 768 && currentWidth <= 768)) {

        // Close all dropdowns
        document.querySelectorAll('.nav-item.has-dropdown').forEach(item => {
            item.classList.remove('active');
            item.querySelector('.dropdown-menu').classList.remove('show');
        });
    }

    previousWidth = currentWidth;
});

// Close dropdown menu items in mobile when clicked
document.querySelectorAll('.dropdown-item').forEach(item => {
    item.addEventListener('click', () => {
        const isMobile = window.innerWidth <= 768;

        if (isMobile) {
            navMenu.classList.remove('active');
            hamburger.textContent = '☰';
            document.removeEventListener('click', handleOutsideClick);
        }
    });
});