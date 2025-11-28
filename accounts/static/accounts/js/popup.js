document.addEventListener('DOMContentLoaded', function() {
    const popupMenu = document.querySelector('.popup-menu');
    const popupButton = document.querySelector('.user-name');

    popupButton.addEventListener('click', function(e) {
        e.stopPropagation();

        if (popupMenu.style.display === 'block') {
            popupMenu.style.display = 'none';
        } else {
            popupMenu.style.display = 'block';

            // prevent overflow
            const rect = popupMenu.getBoundingClientRect();
            const viewportWidth = window.innerWidth;

            if (rect.right > viewportWidth) {
                popupMenu.style.left = `-${rect.right - viewportWidth + 10}px`; 
            } else {
                popupMenu.style.left = '0';
            }
        }
    });


    document.addEventListener('click', function(e) {
        if (!e.target.closest('.profile-popup')) {
            popupMenu.style.display = 'none';
        }
    });
});
