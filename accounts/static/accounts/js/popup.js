document.addEventListener('DOMContentLoaded', function() {
    
    const popupMenu = document.querySelector('.popup-menu');
    const popupButton = document.querySelector('.user-name');

    popupButton.addEventListener('click', function() {
        popupMenu.style.display = popupMenu.style.display === 'block' ? 'none' : 'block';
        console.log("Popup menu toggled");
    });
});