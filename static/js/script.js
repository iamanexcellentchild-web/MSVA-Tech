document.addEventListener('DOMContentLoaded', () => {

    // 1. Mobile Menu Control
    const menuToggle = document.getElementById('menuToggle');
    const navMenu = document.getElementById('navMenu');

    if (menuToggle && navMenu) {
        menuToggle.addEventListener('click', () => {
            navMenu.classList.toggle('open');
            const icon = menuToggle.querySelector('i');
            if (navMenu.classList.contains('open')) {
                icon.className = 'fa-solid fa-xmark';
            } else {
                icon.className = 'fa-solid fa-bars';
            }
        });

        const closeMenu = () => {
            navMenu.classList.remove('open');
            menuToggle.querySelector('i').className = 'fa-solid fa-bars';
            menuToggle.setAttribute('aria-expanded', 'false');
        };
        menuToggle.setAttribute('aria-expanded', 'false');
        menuToggle.addEventListener('click', () => {
            menuToggle.setAttribute('aria-expanded', String(navMenu.classList.contains('open')));
        });
        // Close the menu when tapping outside it, pressing Esc, or widening past the breakpoint.
        document.addEventListener('click', (e) => {
            if (navMenu.classList.contains('open') && !navMenu.contains(e.target) && !menuToggle.contains(e.target)) closeMenu();
        });
        document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeMenu(); });
        window.matchMedia('(min-width: 1101px)').addEventListener('change', (e) => { if (e.matches) closeMenu(); });

        const navLinks = navMenu.querySelectorAll('a');
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                navMenu.classList.remove('open');
                menuToggle.querySelector('i').className = 'fa-solid fa-bars';
            });
        });
    }

    // 2. Accordion Expansion System
    const accordionHeaders = document.querySelectorAll('.accordion-header');
    accordionHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const currentItem = this.parentElement;
            const content = this.nextElementSibling;
            const isCurrentlyActive = currentItem.classList.contains('active');

            document.querySelectorAll('.accordion-item').forEach(item => {
                item.classList.remove('active');
                item.querySelector('.accordion-content').style.maxHeight = null;
            });

            if (!isCurrentlyActive) {
                currentItem.classList.add('active');
                content.style.maxHeight = content.scrollHeight + "px";
            }
        });
    });

    // Items rendered as active by the server (e.g. Week 1) start expanded.
    document.querySelectorAll('.accordion-item.active .accordion-content').forEach(content => {
        content.style.maxHeight = content.scrollHeight + "px";
    });

    // Dismissible flash messages
    document.querySelectorAll('.flash-close').forEach(btn => {
        btn.addEventListener('click', () => btn.closest('.flash').remove());
    });

    // 3. Auto-Typing Engine
    const typingElement = document.getElementById('typing-text');
    const defaultWords = ["Cybersecurity Experts.", "Data Analysts.", "Digital Marketers.", "Tech Professionals."];
    const words = (typingElement && typingElement.dataset.words)
        ? typingElement.dataset.words.split('|').filter(Boolean)
        : defaultWords;
    let wordIndex = 0;
    let charIndex = 0;
    let isDeleting = false;

    function typeEffect() {
        if (!typingElement) return;
        const currentWord = words[wordIndex];
        if (isDeleting) {
            typingElement.textContent = currentWord.substring(0, charIndex - 1);
            charIndex--;
        } else {
            typingElement.textContent = currentWord.substring(0, charIndex + 1);
            charIndex++;
        }

        let typingSpeed = isDeleting ? 40 : 100;

        if (!isDeleting && charIndex === currentWord.length) {
            typingSpeed = 2000;
            isDeleting = true;
        } else if (isDeleting && charIndex === 0) {
            isDeleting = false;
            wordIndex = (wordIndex + 1) % words.length;
            typingSpeed = 400;
        }
        setTimeout(typeEffect, typingSpeed);
    }
    typeEffect();

    // 4. Scroll Reveal Engine
    const revealElements = document.querySelectorAll('.reveal, .scroll-reveal');
    function checkRevealScroll() {
        const triggerBottom = (window.innerHeight / 5) * 4.2;
        revealElements.forEach(element => {
            const elementTop = element.getBoundingClientRect().top;
            if (elementTop < triggerBottom) {
                element.classList.add('active');
                element.classList.add('visible');
            }
        });
    }
    window.addEventListener('scroll', checkRevealScroll);
    checkRevealScroll();

    // 5. Scroll-Triggered Animated Counter Engine
    const statNumbers = document.querySelectorAll('.stat-number');
    let hasCounted = false;

    function startCounters() {
        const statsSection = document.getElementById('stats');
        if (!statsSection || hasCounted) return;

        const sectionTop = statsSection.getBoundingClientRect().top;
        const triggerPoint = window.innerHeight * 0.85;

        if (sectionTop < triggerPoint) {
            hasCounted = true;
            statNumbers.forEach(counter => {
                const target = +counter.getAttribute('data-target');
                const suffix = counter.getAttribute('data-suffix') || '';
                const duration = 2000; // Animation duration in ms
                const increment = target / (duration / 16); // ~60fps

                let current = 0;
                const updateCounter = () => {
                    current += increment;
                    if (current < target) {
                        counter.textContent = Math.ceil(current).toLocaleString() + suffix;
                        requestAnimationFrame(updateCounter);
                    } else {
                        counter.textContent = target.toLocaleString() + suffix;
                    }
                };
                updateCounter();
            });
        }
    }

    window.addEventListener('scroll', startCounters);
    startCounters();
});