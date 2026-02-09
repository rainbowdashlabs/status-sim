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
