function toggleCard(selectedCard) {
    // Collapse all other cards
    document.querySelectorAll('.card-meetings').forEach(card => {
        if (card !== selectedCard) {
            card.classList.remove('active');
        }
    });

    // Toggle the clicked card
    selectedCard.classList.toggle('active');
}

function toggleView() {
    document.querySelectorAll('.container_my').forEach(item => {
        item.classList.toggle('printView');
    })
    document.querySelectorAll('.listView').forEach(item => {
        item.classList.toggle('printView');
    })
}