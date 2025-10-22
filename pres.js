// Presentation Controller
class PresentationController {
    constructor() {
        this.currentSlide = 1;
        this.totalSlides = 17;
        this.slides = document.querySelectorAll('.slide');
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupDemoButtons();
        this.updateNavigation();
        this.updateSlideCounter();
    }

    setupEventListeners() {
        // Navigation buttons
        document.getElementById('prevBtn').addEventListener('click', () => this.previousSlide());
        document.getElementById('nextBtn').addEventListener('click', () => this.nextSlide());
        document.getElementById('fullscreenBtn').addEventListener('click', () => this.toggleFullscreen());

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            switch(e.key) {
                case 'ArrowLeft':
                case 'ArrowUp':
                    e.preventDefault();
                    this.previousSlide();
                    break;
                case 'ArrowRight':
                case 'ArrowDown':
                case ' ': // Space bar
                    e.preventDefault();
                    this.nextSlide();
                    break;
                case 'Home':
                    e.preventDefault();
                    this.goToSlide(1);
                    break;
                case 'End':
                    e.preventDefault();
                    this.goToSlide(this.totalSlides);
                    break;
                case 'F11':
                    e.preventDefault();
                    this.toggleFullscreen();
                    break;
            }
        });

        // Touch/swipe support for mobile
        let startX = 0;
        let startY = 0;
        
        document.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        });
        
        document.addEventListener('touchend', (e) => {
            if (!startX || !startY) return;
            
            let endX = e.changedTouches[0].clientX;
            let endY = e.changedTouches[0].clientY;
            
            let diffX = startX - endX;
            let diffY = startY - endY;
            
            // Only process horizontal swipes
            if (Math.abs(diffX) > Math.abs(diffY)) {
                if (Math.abs(diffX) > 50) { // Minimum swipe distance
                    if (diffX > 0) {
                        this.nextSlide();
                    } else {
                        this.previousSlide();
                    }
                }
            }
            
            startX = 0;
            startY = 0;
        });

        // Prevent context menu on right click
        document.addEventListener('contextmenu', (e) => {
            e.preventDefault();
        });
    }

    setupDemoButtons() {
        const demoButtons = document.querySelectorAll('.demo-button');
        
        demoButtons.forEach(button => {
            // Убедимся, что кнопки кликабельны
            button.style.pointerEvents = 'auto';
            button.style.cursor = 'pointer';
            
            // Более надежный обработчик клика
            button.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                const href = button.getAttribute('href');
                console.log('Button clicked:', href);
                
                if (href === '#download') {
                    this.showDownloadMessage();
                } else if (href && href !== '#') {
                    // Открываем внешние ссылки в новой вкладке
                    window.open(href, '_blank', 'noopener,noreferrer');
                }
                
                // Добавляем визуальную обратную связь
                this.createRippleEffect(e, button);
            });
            
            // Остальные обработчики остаются без изменений...
            button.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    button.click();
                }
            });
            
            // Hover effects...
            button.addEventListener('mouseenter', () => {
                button.style.transform = this.getButtonHoverTransform(button);
            });
            
            button.addEventListener('mouseleave', () => {
                button.style.transform = 'translateY(0) scale(1)';
            });
            
            button.addEventListener('mousedown', () => {
                button.style.transform = 'translateY(2px) scale(0.98)';
            });
            
            button.addEventListener('mouseup', () => {
                button.style.transform = this.getButtonHoverTransform(button);
            });
        });
    }

    handleDemoButtonClick(e, button) {
        const href = button.getAttribute('href');
        
        // Handle download button separately
        if (href === '#download') {
            e.preventDefault();
            this.showDownloadMessage();
            return;
        }
        
        // Add ripple effect for external links
        this.createRippleEffect(e, button);
        
        // External links will open in new tab automatically
        console.log('Opening:', href);
    }

    getButtonHoverTransform(button) {
        if (button.classList.contains('demo-button-green')) {
            return 'translateY(-8px) scale(1.05)';
        } else {
            return 'translateY(-5px) scale(1.02)';
        }
    }

    createRippleEffect(e, button) {
        const ripple = document.createElement('span');
        const rect = button.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;
        
        ripple.style.cssText = `
            position: absolute;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.6);
            transform: scale(0);
            animation: ripple 0.6s linear;
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            pointer-events: none;
            z-index: 1;
        `;
        
        button.style.position = 'relative';
        button.style.overflow = 'hidden';
        button.appendChild(ripple);
        
        setTimeout(() => {
            if (ripple.parentNode) {
                ripple.parentNode.removeChild(ripple);
            }
        }, 600);
    }

    showDownloadMessage() {
        // Create a custom notification
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: linear-gradient(135deg, #FF8C00 0%, #D2691E 100%);
            color: #12121B;
            padding: 2rem;
            border-radius: 15px;
            font-weight: 600;
            font-size: 1.2rem;
            text-align: center;
            z-index: 10000;
            box-shadow: 0 10px 30px rgba(255, 140, 0, 0.4);
            border: 2px solid #FF8C00;
            animation: popIn 0.3s ease-out;
        `;
        
        notification.innerHTML = `
            <div style="margin-bottom: 1rem;">📥</div>
            <div>Функция скачивания .exe будет доступна в материалах конференции</div>
            <button onclick="this.parentElement.remove()" 
                    style="margin-top: 1rem; padding: 0.5rem 1rem; background: #12121B; color: white; border: none; border-radius: 8px; cursor: pointer;">
                Закрыть
            </button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }

    nextSlide() {
        if (this.currentSlide < this.totalSlides) {
            this.goToSlide(this.currentSlide + 1);
        }
    }

    previousSlide() {
        if (this.currentSlide > 1) {
            this.goToSlide(this.currentSlide - 1);
        }
    }

    goToSlide(slideNumber) {
        if (slideNumber < 1 || slideNumber > this.totalSlides) return;

        // Remove active class from current slide
        this.slides[this.currentSlide - 1].classList.remove('active');
        
        // Update current slide
        this.currentSlide = slideNumber;
        
        // Add active class to new slide
        this.slides[this.currentSlide - 1].classList.add('active');
        
        // Update navigation
        this.updateNavigation();
        this.updateSlideCounter();
        
        // Trigger slide animation
        this.animateSlideContent();
        
        // Update progress indicator
        if (this.progressIndicator) {
            this.progressIndicator.updateProgress(this.currentSlide, this.totalSlides);
        }
    }

    updateNavigation() {
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');
        
        prevBtn.disabled = this.currentSlide === 1;
        nextBtn.disabled = this.currentSlide === this.totalSlides;
    }

    updateSlideCounter() {
        document.getElementById('currentSlide').textContent = this.currentSlide;
        document.getElementById('totalSlides').textContent = this.totalSlides;
    }

    animateSlideContent() {
        const currentSlideElement = this.slides[this.currentSlide - 1];
        const content = currentSlideElement.querySelector('.slide-content');
        
        // Reset animation
        content.style.animation = 'none';
        content.offsetHeight; // Trigger reflow
        content.style.animation = 'fadeInUp 0.8s ease-out';
        
        // Animate individual elements based on slide type
        this.animateSlideElements(currentSlideElement);
    }

    animateSlideElements(slideElement) {
        const animatableElements = slideElement.querySelectorAll(
            '.item-card, .method-card, .arch-card, .result-block, .demo-button, .feature-item, .significance-item, .future-item, .conclusion-item'
        );
        
        animatableElements.forEach((element, index) => {
            element.style.opacity = '0';
            element.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                element.style.transition = 'all 0.6s ease-out';
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
            }, 200 + (index * 100));
        });
    }

    toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen().catch(err => {
                console.log(`Error attempting to enable fullscreen: ${err.message}`);
            });
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            }
        }
    }
}

// Progress indicator
class ProgressIndicator {
    constructor(presentation) {
        this.presentation = presentation;
        this.createProgressBar();
    }
    
    createProgressBar() {
        const progressBar = document.createElement('div');
        progressBar.className = 'progress-bar';
        progressBar.innerHTML = '<div class="progress-fill"></div>';
        
        document.body.appendChild(progressBar);
        
        this.progressFill = progressBar.querySelector('.progress-fill');
        this.updateProgress(this.presentation.currentSlide, this.presentation.totalSlides);
    }
    
    updateProgress(currentSlide, totalSlides) {
        const percentage = (currentSlide / totalSlides) * 100;
        if (this.progressFill) {
            this.progressFill.style.width = `${percentage}%`;
        }
    }
}

// Enhanced slide transitions
class SlideTransitions {
    constructor(presentation) {
        this.presentation = presentation;
        this.setupTransitions();
    }
    
    setupTransitions() {
        this.createParticles();
        this.addTypingEffects();
        this.addRippleStyles();
    }
    
    createParticles() {
        const particleContainer = document.createElement('div');
        particleContainer.className = 'particles';
        document.body.appendChild(particleContainer);
        
        // Create particles periodically
        setInterval(() => {
            if (this.presentation.currentSlide === 1) {
                this.createParticle(particleContainer);
            }
        }, 200);
    }
    
    createParticle(container) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.animationDuration = (Math.random() * 3 + 3) + 's';
        particle.style.animationDelay = Math.random() * 2 + 's';
        
        container.appendChild(particle);
        
        // Remove particle after animation
        setTimeout(() => {
            if (particle.parentNode) {
                particle.parentNode.removeChild(particle);
            }
        }, 8000);
    }
    
    addTypingEffects() {
        // Apply glow to title elements
        document.querySelectorAll('.title-main, .final-title').forEach(element => {
            element.classList.add('glow-text');
        });
    }
    
    addRippleStyles() {
        const style = document.createElement('style');
        style.textContent = `
            @keyframes ripple {
                to {
                    transform: scale(4);
                    opacity: 0;
                }
            }
            @keyframes popIn {
                from {
                    opacity: 0;
                    transform: translate(-50%, -50%) scale(0.8);
                }
                to {
                    opacity: 1;
                    transform: translate(-50%, -50%) scale(1);
                }
            }
            .glow-text {
                animation: textGlow 2s ease-in-out infinite alternate;
            }
            @keyframes textGlow {
                from {
                    text-shadow: 0 0 10px rgba(0, 255, 159, 0.3);
                }
                to {
                    text-shadow: 0 0 20px rgba(0, 255, 159, 0.6), 0 0 30px rgba(0, 255, 159, 0.4);
                }
            }
            .progress-bar {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 3px;
                background: rgba(0, 0, 0, 0.3);
                z-index: 2000;
            }
            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #00FF9F 0%, #8A2BE2 100%);
                transition: width 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94);
                width: 0%;
            }
            .particles {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                pointer-events: none;
                z-index: -1;
            }
            .particle {
                position: absolute;
                width: 2px;
                height: 2px;
                background: #00FF9F;
                animation: float 6s infinite linear;
                opacity: 0.7;
            }
            @keyframes float {
                0% {
                    transform: translateY(100vh) rotate(0deg);
                    opacity: 0;
                }
                10% {
                    opacity: 0.7;
                }
                90% {
                    opacity: 0.7;
                }
                100% {
                    transform: translateY(-10px) rotate(360deg);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
}

// Initialize presentation
let presentation;

document.addEventListener('DOMContentLoaded', () => {
    presentation = new PresentationController();
    const progressIndicator = new ProgressIndicator(presentation);
    const slideTransitions = new SlideTransitions(presentation);
    
    // Store progress indicator in presentation for easy access
    presentation.progressIndicator = progressIndicator;
    
    // Add loading animation
    document.body.classList.add('loaded');
    
    console.log('ØccultoNG Presentation loaded successfully! 🚀');
    console.log('Navigation: Arrow keys, Space bar, or click buttons');
    console.log('Fullscreen: F11 or click fullscreen button');
    console.log('Demo buttons are now fully functional!');
});

// Add smooth loading transition
const loadingStyle = document.createElement('style');
loadingStyle.textContent = `
    body {
        opacity: 0;
        transition: opacity 0.5s ease-in;
    }
    body.loaded {
        opacity: 1;
    }
    
    /* Ensure demo buttons are clickable */
    .demo-button {
        cursor: pointer !important;
        position: relative;
        z-index: 10;
    }
    
    .demo-button:focus {
        outline: 2px solid #00FF9F;
        outline-offset: 2px;
    }
    
    .demo-buttons-grid {
        position: relative;
        z-index: 100;
    }
`;
document.head.appendChild(loadingStyle);