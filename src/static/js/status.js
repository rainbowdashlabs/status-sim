let currentTab = 'kurzstatus';
let currentStatus = "1";
let specialStatus = null;
let currentKurzstatus = null;
let ws;

function initStatus(name, code) {
    const messagesDiv = document.getElementById('messages');
    const noticeArea = document.getElementById('notice-area');
    const noticeTextDiv = document.getElementById('notice-text');
    const confirmedNoticeArea = document.getElementById('confirmed-notice-area');
    const tabNachrichten = document.getElementById('tab-nachrichten');
    const sfToggleBtn = document.getElementById('sf-toggle-btn');
    const statusSound = new Audio('/static/assets/fns_status_1.mp3');
    statusSound.volume = 0.5;

    function openTab(tabName) {
        currentTab = tabName;
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        
        document.getElementById(`tab-${tabName}`).classList.add('active');
        document.getElementById(`${tabName}-panel`).classList.add('active');

        if (tabName === 'nachrichten') {
            tabNachrichten.classList.remove('flash');
        }
    }
    window.openTab = openTab;

    function sendKurzstatus(text) {
        if (currentKurzstatus === text) {
            currentKurzstatus = null;
            ws.send("kurzstatus:");
        } else {
            currentKurzstatus = text;
            ws.send(`kurzstatus:${text}`);
        }
        updateKurzstatusUI();
    }
    window.sendKurzstatus = sendKurzstatus;

    function updateKurzstatusUI() {
        document.querySelectorAll('.kurzstatus-item').forEach(item => {
            if (item.textContent.replace(' ✓', '').trim() === currentKurzstatus) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    }

    function confirmNotice() {
        if (typeof ws !== 'undefined' && ws && ws.readyState === WebSocket.OPEN) {
            ws.send("confirm_notice");
            noticeArea.style.display = 'none';
        }
    }
    window.confirmNotice = confirmNotice;

    function toggleTalkingToSF() {
        if (typeof ws !== 'undefined' && ws && ws.readyState === WebSocket.OPEN) {
            ws.send("toggle_talking_to_sf");
        }
    }
    window.toggleTalkingToSF = toggleTalkingToSF;

    function press(key) {
        if (isTransitionAllowed(key)) {
            updateStatus(key);
        }
    }
    window.press = press;

    function isTransitionAllowed(newStatus) {
        if (newStatus === "0" || newStatus === "5") return true;
        if (newStatus === "1") return ["2", "3", "4", "8"].includes(currentStatus);
        if (newStatus === "2") return currentStatus === "1";
        if (newStatus === "3") return ["1", "2"].includes(currentStatus);
        if (newStatus === "4") return currentStatus === "3";
        if (newStatus === "7") return currentStatus === "4";
        if (newStatus === "8") return currentStatus === "7";
        return true;
    }

    function updateStatusUI() {
        document.querySelectorAll('.key').forEach(k => {
            k.classList.remove('active');
            k.classList.remove('special-active');
        });

        const activeKey = document.getElementById(`key-${currentStatus}`);
        if (activeKey) {
            activeKey.classList.add('active');
        }

        if (specialStatus) {
            const specialKey = document.getElementById(`key-${specialStatus}`);
            if (specialKey) {
                specialKey.classList.add('special-active');
            }
        }
    }

    function updateStatus(status) {
        if (status === "0" || status === "5") {
            if (specialStatus === status) {
                specialStatus = null;
            } else {
                specialStatus = status;
            }
        } else {
            currentStatus = status;
        }
        
        updateStatusUI();
        statusSound.play().catch(e => console.log("Audio play failed:", e));

        if (typeof ws !== 'undefined' && ws && ws.readyState === WebSocket.OPEN) {
            ws.send(`status:${status}`);
        }
    }

    function sendHeartbeat() {
        if (typeof ws !== 'undefined' && ws && ws.readyState === WebSocket.OPEN) {
            ws.send("heartbeat");
        }
    }
    setInterval(sendHeartbeat, 60000);

    updateStatus("2");

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const encodedName = encodeURIComponent(name);
    const wsUrl = `${protocol}//${window.location.host}/ws/${code}?name=${encodedName}`;
    ws = new WebSocket(wsUrl);

    ws.onopen = function() {
        ws.send(`status:${currentStatus}`);
    };

    ws.onerror = function(error) {
        console.error("WebSocket error:", error);
    };

    ws.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            if (data.type === 'status_update') {
                const me = data.connections.find(c => c.name === name);
                if (me) {
                    currentStatus = me.status;
                    specialStatus = me.special;
                    currentKurzstatus = me.kurzstatus;
                    
                    updateStatusUI();
                    updateKurzstatusUI();

                    if (sfToggleBtn) {
                        if (me.talking_to_sf) {
                            sfToggleBtn.textContent = "Gespräch beenden";
                            sfToggleBtn.classList.add('active');
                        } else {
                            sfToggleBtn.textContent = "Mit SF sprechen";
                            sfToggleBtn.classList.remove('active');
                        }
                    }
                }

                if (data.notices && data.notices[name]) {
                    const notice = data.notices[name];
                    noticeTextDiv.textContent = notice.text;
                    if (notice.status === 'pending') {
                        noticeArea.style.display = 'block';
                        confirmedNoticeArea.style.display = 'none';
                        if (sfToggleBtn) sfToggleBtn.style.display = 'none';
                    } else if (notice.status === 'confirmed') {
                        noticeArea.style.display = 'none';
                        confirmedNoticeArea.style.display = 'block';
                        if (sfToggleBtn) sfToggleBtn.style.display = 'none';
                        const confirmedTextDiv = document.getElementById('confirmed-notice-text');
                        if (confirmedTextDiv) {
                            confirmedTextDiv.textContent = notice.text;
                        }
                    } else {
                        noticeArea.style.display = 'none';
                        confirmedNoticeArea.style.display = 'none';
                        if (sfToggleBtn) sfToggleBtn.style.display = 'block';
                    }
                } else {
                    noticeArea.style.display = 'none';
                    confirmedNoticeArea.style.display = 'none';
                    if (sfToggleBtn) sfToggleBtn.style.display = 'block';
                }
                return;
            }
        } catch (e) {}

        const row = document.createElement('div');
        row.className = 'message-row';
        row.dataset.timestamp = Date.now();
        
        const timeSpan = document.createElement('span');
        timeSpan.className = 'message-time';
        timeSpan.textContent = 'gerade eben';
        
        let messageContent = event.data;
        let senderBadge = null;

        if (messageContent.startsWith("LS: ")) {
            senderBadge = document.createElement('span');
            senderBadge.className = 'message-sender ls';
            senderBadge.textContent = 'LS';
            messageContent = messageContent.substring(4);
        } else if (messageContent.startsWith("SF: ")) {
            senderBadge = document.createElement('span');
            senderBadge.className = 'message-sender sf';
            senderBadge.textContent = 'SF';
            messageContent = messageContent.substring(4);
        }

        const textSpan = document.createElement('span');
        textSpan.className = 'message-text';
        textSpan.textContent = messageContent;
        
        row.appendChild(timeSpan);
        if (senderBadge) {
            row.appendChild(senderBadge);
        }
        row.appendChild(textSpan);
        messagesDiv.prepend(row);

        if (currentTab !== 'nachrichten') {
            tabNachrichten.classList.add('flash');
        }
    };

    function updateTimeAgo() {
        const rows = document.querySelectorAll('.message-row');
        const now = Date.now();
        rows.forEach(row => {
            const timestamp = parseInt(row.dataset.timestamp);
            const seconds = Math.floor((now - timestamp) / 1000);
            const timeSpan = row.querySelector('.message-time');
            
            if (seconds < 60) {
                timeSpan.textContent = 'gerade eben';
            } else if (seconds < 3600) {
                const mins = Math.floor(seconds / 60);
                timeSpan.textContent = `vor ${mins} min`;
            } else {
                const hours = Math.floor(seconds / 3600);
                timeSpan.textContent = `vor ${hours} h`;
            }
        });
    }
    setInterval(updateTimeAgo, 30000);

    let isUnloading = false;
    window.addEventListener('beforeunload', () => {
        isUnloading = true;
    });

    ws.onclose = function(event) {
        if (isUnloading) return;
        if (event.code === 1008) {
            window.location.href = `/?error=name_taken&old_name=${encodedName}`;
        } else {
            window.location.href = '/';
        }
    };
}
