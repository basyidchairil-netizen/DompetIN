// dashboard.js - Handle form submissions, smart nudge logic, and other JS functionalities for dashboard

// Section navigation
function showSection(sectionId) {
    const sections = document.querySelectorAll('.section');
    sections.forEach(section => section.classList.add('hidden'));
    document.getElementById(sectionId).classList.remove('hidden');
}

// Modal functions
function openModal() {
    document.getElementById('transaction-modal').classList.remove('hidden');
}

function closeModal() {
    document.getElementById('transaction-modal').classList.add('hidden');
}

// Nudge functions
function showNudge(message) {
    document.getElementById('nudge-message').textContent = message;
    document.getElementById('nudge-alert').classList.remove('hidden');
}

function closeNudge() {
    document.getElementById('nudge-alert').classList.add('hidden');
}

// Form submission
document.getElementById('transaction-form').addEventListener('submit', function(e) {
    e.preventDefault();
    const formData = new FormData(this);
    const data = Object.fromEntries(formData);
    data.amount = parseFloat(data.amount);

    fetch('/add_transaction', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            closeModal();
            location.reload(); // Reload to update balance
            if (result.nudge) {
                showNudge(result.nudge);
            }
        }
    })
    .catch(error => console.error('Error:', error));
});

// Update dashboard
function updateDashboard() {
    fetch('/get_spending')
    .then(response => response.json())
    .then(spending => {
        // Update chart (placeholder)
        console.log('Spending data:', spending);
        // In a real implementation, update the chart here
    });
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    updateDashboard();
});
