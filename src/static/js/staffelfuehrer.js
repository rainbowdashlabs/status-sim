function initStaffelfuehrer(sfCode) {
    const connectionsDiv = document.getElementById('connections');
    const protocol = location.protocol.replace('http', 'ws');
    const wsUrl = `${protocol}//${window.location.host}/ws/${sfCode}?name=STAFFELFUEHRER_${Math.random().toString(36).substring(2, 11)}`;
    
    ws = new WebSocketManager(wsUrl, {
        onMessage: (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'status_update') {
                updateUI(data.connections, data.notices);
            }
        }
    });

    function updateUI(connections, notices) {
        const cars = connections.filter(c => !c.name.startsWith('LEITSTELLE_VIEW') && !c.is_staffelfuehrer);

        const expandedSet = new Set(Array.from(document.querySelectorAll('#connections .car-details.active')).map(d => d.id.replace('details-','')));
        const noteDrafts = {};
        document.querySelectorAll('#connections .notes-area textarea').forEach(t => {
            const id = t.closest('.car-details')?.id?.replace('details-','');
            if (id) noteDrafts[id] = t.value;
        });
        const msgDrafts = {};
        document.querySelectorAll('#connections .private-message-form-inline input[name="message"]').forEach(i => {
            const name = i.getAttribute('data-car-name');
            if (name) msgDrafts[name] = i.value;
        });

        connectionsDiv.innerHTML = '';
        
        if (cars.length === 0) {
            connectionsDiv.innerHTML = '<p>Keine Fahrzeuge verbunden.</p>';
            return;
        }

        const sortedCars = [...cars].sort((a, b) => {
            const timeA = a.last_status_update || 0;
            const timeB = b.last_status_update || 0;
            return timeB - timeA;
        });

        sortedCars.forEach(car => {
            const div = document.createElement('div');
            div.className = 'connection';
            div.dataset.status = car.status;
            div.setAttribute('data-car-name', car.name);
            
            let noticeHtml = '';
            const notice = notices[car.name];
            if (notice) {
                const statusClass = notice.status === 'confirmed' ? 'notice-confirmed' : 'notice-pending';
                const statusText = notice.status === 'confirmed' ? 'BESTÄTIGT' : 'Ausstehend';
                noticeHtml = `
                    <div class="notice-badge ${statusClass}">
                        ${notice.text} (${statusText})
                        ${notice.status === 'confirmed' ? `<button class="ack-btn" onclick="event.stopPropagation(); acknowledgeNotice('${car.name}')">Fertig</button>` : ''}
                    </div>
                `;
            } else if (car.talking_to_sf) {
                noticeHtml = `
                    <div class="notice-badge notice-confirmed">
                        Eigen-Initialisiert (BESTÄTIGT)
                    </div>
                `;
            } else {
                noticeHtml = `
                    <button class="request-btn" onclick="sendNotice('${car.name}', 'SF Sprechwunsch')">SF Sprechwunsch</button>
                `;
            }

            const timeSinceStatus = formatTimeSince(car.last_status_update);
            const isExpanded = expandedSet.has(car.name);
            const detailsClass = isExpanded ? 'car-details active' : 'car-details';
            const msgValue = msgDrafts[car.name] || '';
            const noteValue = (noteDrafts[car.name] !== undefined) ? noteDrafts[car.name] : (car.note || '');

            div.innerHTML = `
                <div class="car-main-row" onclick="toggleDetails('${car.name}')">
                    <div class="car-info-left">
                        <strong>${car.name}</strong>
                        <span class="status-badge status-${car.status}">${car.status}</span>
                        <span class="timer" data-timestamp="${car.last_status_update}">${timeSinceStatus}</span>
                    </div>
                    <div class="car-info-right" style="display: flex; gap: 10px; align-items: center;">
                        <form class="private-message-form private-message-form-inline" onsubmit="sendPrivateMessage(event, '${car.name}')" onclick="event.stopPropagation()">
                            <input type="text" name="message" placeholder="Privatnachricht" required data-car-name="${car.name}" value="${msgValue}">
                            <button type="submit">Senden</button>
                        </form>
                        <div onclick="event.stopPropagation()">
                            ${noticeHtml}
                        </div>
                    </div>
                </div>
                <div class="${detailsClass}" id="details-${car.name}">
                    <div class="notes-area">
                        <label>Notizen:</label>
                        <textarea oninput="autoResize(this)" onchange="updateNote('${car.name}', this.value)" placeholder="Notizen für dieses Fahrzeug...">${noteValue}</textarea>
                    </div>
                </div>
            `;
            connectionsDiv.appendChild(div);
        });

        document.querySelectorAll('#connections .notes-area textarea').forEach(t => autoResize(t));
    }

    async function updateNote(targetName, note) {
        const formData = new FormData();
        formData.append('target_name', targetName);
        formData.append('note', note);

        await fetch(`/api/leitstelle/${sfCode}/update_note`, {
            method: 'POST',
            body: formData
        });
    }
    window.updateNote = updateNote;

    async function sendPrivateMessage(e, targetName) {
        e.preventDefault();
        const form = e.target;
        const message = form.message.value;
        const formData = new FormData();
        formData.append('message', message);
        formData.append('target_name', targetName);

        const response = await fetch(`/api/leitstelle/${sfCode}/message`, {
            method: 'POST',
            body: formData
        });
        const result = await response.json();
        if (result.status === 'success') {
            form.reset();
        } else {
            alert('Fehler beim Senden der privaten Nachricht.');
        }
    }
    window.sendPrivateMessage = sendPrivateMessage;

    setInterval(() => {
        document.querySelectorAll('.timer').forEach(timerSpan => {
            const timestampStr = timerSpan.getAttribute('data-timestamp');
            if (timestampStr === "null" || timestampStr === "undefined" || !timestampStr) {
                timerSpan.textContent = "";
                timerSpan.className = "timer";
                return;
            }
            const timestamp = parseFloat(timestampStr);
            const now = Date.now() / 1000;
            const diff = Math.floor(now - timestamp);
            
            timerSpan.textContent = formatTimeSince(timestamp);
            
            timerSpan.classList.remove('timer-green', 'timer-yellow', 'timer-orange', 'timer-red');
            if (diff < 120) {
                timerSpan.classList.add('timer-green');
            } else if (diff < 180) {
                timerSpan.classList.add('timer-yellow');
            } else if (diff < 240) {
                timerSpan.classList.add('timer-orange');
            } else {
                timerSpan.classList.add('timer-red');
            }
        });
    }, 1000);

    async function sendNotice(targetName, text) {
        if (!text) return;
        
        const formData = new FormData();
        formData.append('target_name', targetName);
        formData.append('text', text);
        
        await fetch(`/api/staffelfuehrer/${sfCode}/notice`, {
            method: 'POST',
            body: formData
        });
    }
    window.sendNotice = sendNotice;

    async function acknowledgeNotice(targetName) {
        const formData = new FormData();
        formData.append('target_name', targetName);
        
        await fetch(`/api/staffelfuehrer/${sfCode}/acknowledge`, {
            method: 'POST',
            body: formData
        });
    }
    window.acknowledgeNotice = acknowledgeNotice;
}
