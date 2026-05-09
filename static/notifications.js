function initCustomNotifications() {
    if (document.getElementById('custom-alert-container')) return;

    const container = document.createElement('div');
    container.id = 'custom-alert-container';
    container.innerHTML = `
        <div id="custom-alert" class="fixed inset-0 bg-black bg-opacity-50 hidden flex items-center justify-center z-[9999]">
            <div class="bg-white p-8 rounded-3xl shadow-2xl w-full max-w-sm mx-4 transform transition-all scale-95 opacity-0 duration-300" id="alert-card">
                <div class="text-center">
                    <div id="alert-icon-container" class="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
                        <i id="alert-icon" class="fas fa-check-circle text-blue-600 text-3xl"></i>
                    </div>
                    <h3 class="text-xl font-bold text-gray-800 mb-3" id="alert-title">Sukses!</h3>
                    <p class="text-gray-600 mb-8 leading-relaxed" id="alert-message"></p>
                    <button onclick="closeCustomAlert()" class="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-4 rounded-2xl font-bold hover:shadow-lg transition-all duration-300">
                        Mengerti
                    </button>
                </div>
            </div>
        </div>

        <div id="custom-confirm" class="fixed inset-0 bg-black bg-opacity-50 hidden flex items-center justify-center z-[9999]">
            <div class="bg-white p-8 rounded-3xl shadow-2xl w-full max-w-sm mx-4 transform transition-all scale-95 opacity-0 duration-300" id="confirm-card">
                <div class="text-center">
                    <div class="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
                        <i class="fas fa-exclamation-triangle text-red-600 text-3xl"></i>
                    </div>
                    <h3 class="text-xl font-bold text-gray-800 mb-3">Konfirmasi</h3>
                    <p class="text-gray-600 mb-8 leading-relaxed" id="confirm-message"></p>
                    <div class="flex gap-4">
                        <button id="confirm-cancel" class="flex-1 bg-gray-100 text-gray-600 py-4 rounded-2xl font-bold hover:bg-gray-200 transition-all duration-300" onclick="closeCustomConfirm()">Batal</button>
                        <button id="confirm-yes" class="flex-1 bg-gradient-to-r from-red-500 to-red-600 text-white py-4 rounded-2xl font-bold hover:shadow-lg transition-all duration-300">Ya, Hapus</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(container);
}

window.showAlert = function(message, title = 'Notifikasi', type = 'success') {
    initCustomNotifications();
    const modal = document.getElementById('custom-alert');
    const card = document.getElementById('alert-card');
    const icon = document.getElementById('alert-icon');
    const iconContainer = document.getElementById('alert-icon-container');
    
    document.getElementById('alert-title').innerText = title;
    document.getElementById('alert-message').innerText = message;
    
    if (type === 'error') {
        icon.className = 'fas fa-times-circle text-red-600 text-3xl';
        iconContainer.className = 'w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6';
    } else {
        icon.className = 'fas fa-check-circle text-blue-600 text-3xl';
        iconContainer.className = 'w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6';
    }

    modal.classList.remove('hidden');
    setTimeout(() => {
        card.classList.remove('scale-95', 'opacity-0');
        card.classList.add('scale-100', 'opacity-100');
    }, 10);
};

window.closeCustomAlert = function() {
    const modal = document.getElementById('custom-alert');
    const card = document.getElementById('alert-card');
    card.classList.remove('scale-100', 'opacity-100');
    card.classList.add('scale-95', 'opacity-0');
    setTimeout(() => modal.classList.add('hidden'), 300);
};

window.showConfirm = function(message, callback) {
    initCustomNotifications();
    const modal = document.getElementById('custom-confirm');
    const card = document.getElementById('confirm-card');
    document.getElementById('confirm-message').innerText = message;
    
    modal.classList.remove('hidden');
    setTimeout(() => {
        card.classList.remove('scale-95', 'opacity-0');
        card.classList.add('scale-100', 'opacity-100');
    }, 10);

    const btnYes = document.getElementById('confirm-yes');
    const newBtnYes = btnYes.cloneNode(true);
    btnYes.parentNode.replaceChild(newBtnYes, btnYes);

    newBtnYes.addEventListener('click', () => {
        closeCustomConfirm();
        callback();
    });
};

window.closeCustomConfirm = function() {
    const modal = document.getElementById('custom-confirm');
    const card = document.getElementById('confirm-card');
    card.classList.remove('scale-100', 'opacity-100');
    card.classList.add('scale-95', 'opacity-0');
    setTimeout(() => modal.classList.add('hidden'), 300);
};

// Override default alert
window.alert = function(msg) {
    showAlert(msg);
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', initCustomNotifications);
