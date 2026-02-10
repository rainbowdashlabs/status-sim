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
    errorDiv.style.backgroundColor = 'var(--warning-color, #ffc107)';
    errorDiv.style.color = 'black';
    errorDiv.style.padding = '10px 20px';
    errorDiv.style.borderRadius = 'var(--border-radius)';
    errorDiv.style.boxShadow = 'var(--shadow)';
    errorDiv.style.zIndex = '1000';
    errorDiv.style.fontWeight = 'bold';
    errorDiv.textContent = 'Verbindung unterbrochen. Verbinde neu...';
    document.body.appendChild(errorDiv);
}

function hideConnectionError() {
    const errorMsg = document.getElementById('ws-error-msg');
    if (errorMsg) errorMsg.remove();
}
