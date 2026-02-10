function formatTimeSince(timestamp) {
    if (!timestamp) return "";
    const now = Date.now() / 1000;
    const diff = Math.floor(now - timestamp);
    const minutes = Math.floor(diff / 60);
    const seconds = diff % 60;
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = (el.scrollHeight) + 'px';
}

function toggleDetails(carName) {
    const details = document.getElementById(`details-${carName}`);
    if (details) {
        details.classList.toggle('active');
    }
}

function showConnectionError() {
    if (document.getElementById('ws-error-msg')) return;
    const errorDiv = document.createElement('div');
    errorDiv.id = 'ws-error-msg';
    errorDiv.style.position = 'fixed';
    errorDiv.style.top = '20px';
    errorDiv.style.left = '50%';
    errorDiv.style.transform = 'translateX(-50%)';
    errorDiv.style.backgroundColor = 'var(--danger-color)';
    errorDiv.style.color = 'white';
    errorDiv.style.padding = '15px 25px';
    errorDiv.style.borderRadius = 'var(--border-radius)';
    errorDiv.style.boxShadow = 'var(--shadow)';
    errorDiv.style.zIndex = '1000';
    errorDiv.style.fontWeight = 'bold';
    errorDiv.textContent = 'Verbindung verloren. Bitte Seite neu laden.';
    document.body.appendChild(errorDiv);
}
