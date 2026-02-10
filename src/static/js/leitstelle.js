function initLeitstelle(adminCode) {
    const messageForm = document.getElementById('messageForm');
    const statusDiv = document.getElementById('status');
    const connectionsDiv = document.getElementById('connections');
    const sectionBlitz = document.getElementById('section-blitz');
    const sectionSprechwunsch = document.getElementById('section-sprechwunsch');
    const sectionStaffelfuehrer = document.getElementById('section-staffelfuehrer');
    const statusSound = new Audio('/static/assets/fns_status_1.mp3');
    statusSound.volume = 0.5;

    messageForm.onsubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData(messageForm);
        const response = await fetch(`/api/leitstelle/${adminCode}/message`, {
            method: 'POST',
            body: formData
        });
        const result = await response.json();
        if (result.status === 'success') {
            statusDiv.innerHTML = '<p style="color: green;">Nachricht gesendet!</p>';
            messageForm.reset();
        } else {
            statusDiv.innerHTML = '<p style="color: red;">Fehler beim Senden der Nachricht.</p>';
        }
    };

    document.querySelectorAll('.code-copyable').forEach(el => {
        el.onclick = async () => {
            if (el.classList.contains('visible')) {
                el.classList.remove('visible');
            } else {
                const code = el.textContent;
                try {
                    await navigator.clipboard.writeText(code);
                    el.classList.add('visible');
                    el.classList.add('copied');
                    setTimeout(() => el.classList.remove('copied'), 1000);
                } catch (err) {
                    console.error('Copy failed', err);
                    el.classList.add('visible'); // Show anyway if copy fails
                }
            }
        };
    });

    const protocol = location.protocol.replace('http', 'ws');
    const wsUrl = `${protocol}//${window.location.host}/ws/${adminCode}?name=LEITSTELLE_VIEW_${Math.random().toString(36).substring(2, 11)}`;
    
    ws = new WebSocketManager(wsUrl, {
        onMessage: (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'status_update') {
                    updateConnections(data.connections, data.notices);
                }
            } catch (e) {
                console.log("Error processing WS message:", e);
            }
        }
    });

    function updateConnections(connections, notices) {
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

        const cars = connections.filter(c => !c.name.startsWith('LEITSTELLE_VIEW') && !c.is_staffelfuehrer);
        
        const blitzCars = cars.filter(c => c.special === '0');
        const sprechwunschCars = cars.filter(c => c.special === '5');
        const talkingToSFCars = cars.filter(c => (notices && notices[c.name] && notices[c.name].status === 'confirmed') || c.talking_to_sf);
        
        updateSection(sectionBlitz, blitzCars, notices, expandedSet, noteDrafts, msgDrafts);
        updateSection(sectionSprechwunsch, sprechwunschCars, notices, expandedSet, noteDrafts, msgDrafts);
        updateSection(sectionStaffelfuehrer, talkingToSFCars, notices, expandedSet, noteDrafts, msgDrafts);
        
        if (cars.length === 0) {
            connectionsDiv.innerHTML = '<p>Keine Fahrzeuge verbunden.</p>';
        } else {
            connectionsDiv.innerHTML = '';
            const sortedCars = [...cars].sort((a, b) => {
                const timeA = Math.max(a.last_status_update || 0, a.last_update || 0);
                const timeB = Math.max(b.last_status_update || 0, b.last_update || 0);
                return timeB - timeA;
            });
            sortedCars.forEach(car => {
                connectionsDiv.appendChild(createCarElement(car, false, notices, expandedSet, noteDrafts, msgDrafts));
            });
        }

        document.querySelectorAll('#connections .notes-area textarea').forEach(t => autoResize(t));
    }

    function updateSection(sectionElement, cars, notices, expandedSet, noteDrafts, msgDrafts) {
        const listDiv = sectionElement.querySelector('.connections-list');
        if (cars.length === 0) {
            sectionElement.style.display = 'none';
            listDiv.innerHTML = '';
        } else {
            sectionElement.style.display = 'block';
            listDiv.innerHTML = '';
            const sortedCars = [...cars].sort((a, b) => {
                const timeA = Math.max(a.last_status_update || 0, a.last_update || 0);
                const timeB = Math.max(b.last_status_update || 0, b.last_update || 0);
                return timeB - timeA;
            });
            sortedCars.forEach(car => {
                listDiv.appendChild(createCarElement(car, true, notices, expandedSet, noteDrafts, msgDrafts, false));
            });
        }
    }

    function createCarElement(car, isSpecialSection = false, notices = {}, expandedSet = new Set(), noteDrafts = {}, msgDrafts = {}, isExpandable = true) {
        const div = document.createElement('div');
        div.className = 'connection';
        div.dataset.status = car.status;
        
        let specialBadge = '';
        let clearButton = '';

        if (car.special === '5') {
            const timeSince = formatTimeSince(car.last_sprechwunsch_update);
            specialBadge = `<span class="status-badge special">5 Sprechwunsch</span> <span onclick="event.stopPropagation()"><span class="timer" data-timestamp="${car.last_sprechwunsch_update}">${timeSince}</span></span>`;
            clearButton = `<button class="clear-special-btn" onclick="event.stopPropagation(); clearSpecial('${car.name}')">Erledigt</button>`;
        } else if (car.special === '0') {
            const timeSince = formatTimeSince(car.last_blitz_update);
            specialBadge = `<span class="status-badge special">0 Blitz</span> <span onclick="event.stopPropagation()"><span class="timer" data-timestamp="${car.last_blitz_update}">${timeSince}</span></span>`;
            clearButton = `<button class="clear-special-btn" onclick="event.stopPropagation(); clearSpecial('${car.name}')">Erledigt</button>`;
        }

        const isTalkingToSF = (notices && notices[car.name] && notices[car.name].status === 'confirmed') || car.talking_to_sf;
        let sfNoticeBadge = '';
        if (isTalkingToSF) {
            const confirmedAt = notices[car.name] ? notices[car.name].confirmed_at : car.last_update; // Fallback to last_update if no notice
            const label = car.talking_to_sf ? "Spricht mit Staffelführer (Eigen-Initialisiert)" : "Spricht mit Staffelführer";
            const timeSince = formatTimeSince(confirmedAt);
            sfNoticeBadge = `
                <span class="staffelfuehrer-notice">
                    ${label}
                    <span class="timer" data-timestamp="${confirmedAt}">${timeSince}</span>
                </span>`;
        }

        const kurzstatusHtml = car.kurzstatus ? `
            <div class="kurzstatus-badge" onclick="event.stopPropagation()">
                ${car.kurzstatus}
                <button class="ack-kurzstatus-btn" onclick="acknowledgeKurzstatus('${car.name}')">Bestätigen</button>
            </div>
        ` : '';

        const timeSinceStatus = formatTimeSince(car.last_status_update);
        const isExpanded = isExpandable && expandedSet.has(car.name);
        const detailsClass = isExpanded ? 'car-details active' : 'car-details';

        const msgValue = msgDrafts[car.name] || '';
        const noteValue = (noteDrafts[car.name] !== undefined) ? noteDrafts[car.name] : (car.note || '');

        const onclickAttr = isExpandable ? `onclick="toggleDetails('${car.name}')"` : '';
        const rowStyle = isExpandable ? '' : 'style="cursor: default;"';

        div.setAttribute('data-car-name', car.name);
        div.innerHTML = `
            <div class="car-main-row" ${onclickAttr} ${rowStyle}>
                <div class="car-info-left">
                    <span class="car-name">${car.name}</span>
                    <span class="status-badge status-${car.status}">${car.status}</span>
                    <span class="timer" data-timestamp="${car.last_status_update}">${timeSinceStatus}</span>
                    ${specialBadge}
                    ${kurzstatusHtml}
                </div>
                <div class="car-info-right" style="display: flex; gap: 10px; align-items: center;">
                    <form class="private-message-form private-message-form-inline" onsubmit="sendPrivateMessage(event, '${car.name}')" onclick="event.stopPropagation()">
                        <input type="text" name="message" placeholder="Privatnachricht" required data-car-name="${car.name}" value="${msgValue}">
                        <button type="submit">Senden</button>
                    </form>
                    ${sfNoticeBadge}
                    ${isSpecialSection ? clearButton : ''}
                </div>
            </div>
            ${isExpandable ? `
            <div class="${detailsClass}" id="details-${car.name}">
                <div class="notes-area">
                    <label>Notizen:</label>
                    <textarea oninput="autoResize(this)" onchange="updateNote('${car.name}', this.value)" placeholder="Notizen für dieses Fahrzeug...">${noteValue}</textarea>
                </div>
                <div class="status-control-area">
                    <label>Status setzen:</label>
                    <div class="status-buttons">
                        <button class="status-btn status-1" onclick="setStatus('${car.name}', '1')">1</button>
                        <button class="status-btn status-2" onclick="setStatus('${car.name}', '2')">2</button>
                        <button class="status-btn status-3" onclick="setStatus('${car.name}', '3')">3</button>
                        <button class="status-btn status-4" onclick="setStatus('${car.name}', '4')">4</button>
                        <button class="status-btn status-7" onclick="setStatus('${car.name}', '7')">7</button>
                        <button class="status-btn status-8" onclick="setStatus('${car.name}', '8')">8</button>
                    </div>
                </div>
            </div>` : ''}
        `;
        return div;
    }

    async function updateNote(targetName, note) {
        const formData = new FormData();
        formData.append('target_name', targetName);
        formData.append('note', note);

        await fetch(`/api/leitstelle/${adminCode}/update_note`, {
            method: 'POST',
            body: formData
        });
    }
    window.updateNote = updateNote;

    async function setStatus(targetName, status) {
        statusSound.play().catch(e => console.log("Audio play failed:", e));
        const formData = new FormData();
        formData.append('target_name', targetName);
        formData.append('status', status);

        await fetch(`/api/leitstelle/${adminCode}/set_status`, {
            method: 'POST',
            body: formData
        });
    }
    window.setStatus = setStatus;

    async function clearSpecial(targetName) {
        const formData = new FormData();
        formData.append('target_name', targetName);

        const response = await fetch(`/api/leitstelle/${adminCode}/clear_special`, {
            method: 'POST',
            body: formData
        });
    }
    window.clearSpecial = clearSpecial;

    async function acknowledgeKurzstatus(targetName) {
        const formData = new FormData();
        formData.append('target_name', targetName);

        await fetch(`/api/leitstelle/${adminCode}/clear_kurzstatus`, {
            method: 'POST',
            body: formData
        });
    }
    window.acknowledgeKurzstatus = acknowledgeKurzstatus;

    setInterval(() => {
        document.querySelectorAll('.timer').forEach(timerSpan => {
            const timestampStr = timerSpan.getAttribute('data-timestamp');
            if (!timestampStr || timestampStr === "null" || timestampStr === "undefined") {
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

    async function sendPrivateMessage(e, targetName) {
        e.preventDefault();
        const form = e.target;
        const message = form.message.value;
        const formData = new FormData();
        formData.append('message', message);
        formData.append('target_name', targetName);

        const response = await fetch(`/api/leitstelle/${adminCode}/message`, {
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
}
