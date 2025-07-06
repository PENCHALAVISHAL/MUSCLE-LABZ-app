// Simple background image preloader
document.addEventListener('DOMContentLoaded', function() {
    // Preload critical background images
    const backgrounds = [
        '/static/images/background1.png',
        '/static/images/background2.png',
        '/static/images/background3.png',
        '/static/images/background4.png',
        '/static/images/background5.png',
        '/static/images/background6.png',
        '/static/images/background7.png'
    ];
    
    // Load images in background without blocking
    backgrounds.forEach(src => {
        const img = new Image();
        img.src = src;
    });
}); 