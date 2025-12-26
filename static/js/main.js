// MyZenBrain - Main JavaScript

// Close alert messages
document.querySelectorAll('.alert-close').forEach(btn => {
    btn.addEventListener('click', () => {
        btn.closest('.alert').remove();
    });
});

// Auto-hide alerts after 5 seconds
setTimeout(() => {
    document.querySelectorAll('.alert').forEach(alert => {
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 300);
    });
}, 5000);
