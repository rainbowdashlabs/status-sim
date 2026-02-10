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

class WebSocketManager {
    constructor(url, options = {}) {
        this.url = url;
        this.onMessage = options.onMessage || (() => {});
        this.onOpen = options.onOpen || (() => {});
        this.reconnectAttempts = 0;
        this.reconnectTimeout = null;
        this.ws = null;
        this.isUnloading = false;
        this.heartbeatInterval = null;
        this.connectionTimeout = null;

        window.addEventListener('beforeunload', () => {
            this.isUnloading = true;
        });

        this.connect();
    }

    connect() {
        if (this.ws) {
            this.ws.close();
        }

        this.ws = new WebSocket(this.url);

        this.connectionTimeout = setTimeout(() => {
            if (this.ws && this.ws.readyState !== WebSocket.OPEN) {
                console.log("WebSocket connection handshake timed out. Closing and retrying...");
                this.ws.close();
            }
        }, 5000);

        this.ws.onopen = () => {
            console.log("WebSocket connected");
            clearTimeout(this.connectionTimeout);
            this.reconnectAttempts = 0;
            hideConnectionError();
            this.startHeartbeat();
            this.onOpen(this.ws);
        };

        this.ws.onmessage = (event) => {
            this.onMessage(event);
        };

        this.ws.onerror = (error) => {
            console.error("WebSocket error:", error);
            clearTimeout(this.connectionTimeout);
        };

        this.ws.onclose = () => {
            this.stopHeartbeat();
            if (this.isUnloading) return;
            showConnectionError();

            const delay = Math.min(500 * Math.pow(2, this.reconnectAttempts), 30000);
            this.reconnectAttempts++;
            console.log(`WebSocket closed. Reconnecting in ${delay}ms...`);
            clearTimeout(this.reconnectTimeout);
            this.reconnectTimeout = setTimeout(() => this.connect(), delay);
        };
    }

    startHeartbeat() {
        this.stopHeartbeat();
        this.heartbeatInterval = setInterval(() => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send("heartbeat");
            }
        }, 20000);
    }

    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(data);
        }
    }
}
