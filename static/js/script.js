// Function to remove artwork from the UI
function removeArtwork(artworkId) {
    const artworkCard = document.querySelector(`.artwork-card[data-id="${artworkId}"]`);
    if (artworkCard) {
        artworkCard.remove();
    }
}

// Function to save edited artwork data to the database
function saveToDatabase() {
    const saveButton = document.getElementById('save-button');
    saveButton.disabled = true;
    saveButton.textContent = 'Saving...';
    
    // Collect all artwork data
    const artworkCards = document.querySelectorAll('.artwork-card');
    const artworks = [];
    
    artworkCards.forEach(card => {
        const id = card.getAttribute('data-id');
        const artwork = {
            id: id,
            title: document.getElementById(`title-${id}`).value,
            artist: document.getElementById(`artist-${id}`).value,
            dimensions: document.getElementById(`dimensions-${id}`).value,
            material: document.getElementById(`material-${id}`).value,
            year: document.getElementById(`year-${id}`).value,
            description: document.getElementById(`description-${id}`).value,
            page_number: parseInt(card.querySelector('.page-info').textContent.replace('Page ', ''))
        };
        artworks.push(artwork);
    });
    
    // Send to server
    fetch('/save', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ artworks })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Data saved successfully!');
            window.location.href = '/';
        } else {
            alert('Error saving data: ' + data.message);
            saveButton.disabled = false;
            saveButton.textContent = 'Save to Database';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while saving. Please try again.');
        saveButton.disabled = false;
        saveButton.textContent = 'Save to Database';
    });
}