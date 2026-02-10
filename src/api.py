from fastapi import APIRouter, Request, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import json
import uuid
import time
import os
from datetime import datetime
from src.manager import manager
from src.models import (
    LeitstelleData, Connection, Notice, 
    MessageRequest, TargetRequest, NoticeRequest, 
    NoteRequest, StatusRequest, LeitstelleCreateRequest, ChatMessage
)
from src.logging_conf import get_logger
from src.scenario_models import Scenario, FunkEntry

logger = get_logger("api")

from fastapi.staticfiles import StaticFiles

router = APIRouter()

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
# Prefer built frontend inside Python source; fallback to frontend/dist for local dev
_frontend_dist_primary = os.path.join(current_dir, "frontend_dist")
_frontend_dist_legacy = os.path.join(project_root, "frontend", "dist")
frontend_dist = _frontend_dist_primary if os.path.exists(_frontend_dist_primary) else _frontend_dist_legacy

templates_dir = os.path.join(current_dir, "templates")
templates = Jinja2Templates(directory=templates_dir)
templates.env.globals['current_year'] = datetime.now().year

# Serve Vue static files if dist exists
# Handled in main.py for better reliability with absolute paths and app mounting

async def serve_vue_index(request: Request):
    index_path = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r") as f:
            return HTMLResponse(content=f.read())
    return None

@router.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    vue_resp = await serve_vue_index(request)
    if vue_resp: return vue_resp
    return templates.TemplateResponse(request, "index.html")

@router.post("/leitstelle")
async def create_leitstelle(request: LeitstelleCreateRequest):
    name = request.name
    admin_code = str(uuid.uuid4())[:8].upper()
    vehicle_code = str(uuid.uuid4())[:8].upper()
    staffelfuehrer_code = str(uuid.uuid4())[:8].upper()
    
    codes = {admin_code, vehicle_code, staffelfuehrer_code}
    while len(codes) < 3:
        vehicle_code = str(uuid.uuid4())[:8].upper()
        staffelfuehrer_code = str(uuid.uuid4())[:8].upper()
        codes = {admin_code, vehicle_code, staffelfuehrer_code}
        
    manager.leitstellen[admin_code] = LeitstelleData(
        name=name, 
        vehicle_code=vehicle_code,
        staffelfuehrer_code=staffelfuehrer_code
    )
    manager.code_to_admin[vehicle_code] = admin_code
    manager.code_to_admin[staffelfuehrer_code] = admin_code
    return {"status": "success", "admin_code": admin_code, "vehicle_code": vehicle_code, "staffelfuehrer_code": staffelfuehrer_code}

@router.get("/leitstelle/{code}", response_class=HTMLResponse)
async def get_leitstelle_view(request: Request, code: str):
    vue_resp = await serve_vue_index(request)
    if vue_resp: return vue_resp
    
    admin_code = code.upper()
    if admin_code not in manager.leitstellen:
        return RedirectResponse(url="/", status_code=307)
    ls = manager.leitstellen[admin_code]
    return templates.TemplateResponse(request, "leitstelle_view.html", {
        "admin_code": admin_code,
        "vehicle_code": ls.vehicle_code,
        "staffelfuehrer_code": ls.staffelfuehrer_code,
        "name": ls.name
    })

@router.get("/staffelfuehrer/{code}", response_class=HTMLResponse)
async def get_staffelfuehrer_view(request: Request, code: str):
    vue_resp = await serve_vue_index(request)
    if vue_resp: return vue_resp
    
    sf_code = code.upper()
    if sf_code not in manager.code_to_admin:
        return RedirectResponse(url="/", status_code=307)
    
    admin_code = manager.code_to_admin[sf_code]
    if manager.leitstellen[admin_code].staffelfuehrer_code != sf_code:
        return RedirectResponse(url="/", status_code=307)

    return templates.TemplateResponse(request, "staffelfuehrer_view.html", {
        "sf_code": sf_code,
        "name": manager.leitstellen[admin_code].name
    })

@router.get("/status", response_class=HTMLResponse)
async def get_status_page(request: Request, code: str, name: str):
    code = code.upper()
    if code not in manager.code_to_admin:
        return RedirectResponse(url="/", status_code=307)
    
    admin_code = manager.code_to_admin[code]
    if manager.leitstellen[admin_code].vehicle_code == code:
        # Check for duplicate vehicle names
        existing = next((c for c in manager.leitstellen[admin_code].connections if c.name == name), None)
        # Only treat as name taken if the connection is active AND it's not a very recent disconnect
        # (Recent disconnects might be due to a page refresh where the old WS is closing while the new GET arrives)
        if existing and existing.ws is not None:
            # Check if the connection has been updated very recently (heartbeat)
            # If it's been more than 5 seconds since the last update, it might be a stale connection 
            # that's about to be closed or taken over.
            if time.time() - existing.last_update < 5:
                return RedirectResponse(url=f"/?error=name_taken&old_name={name}&code={code}", status_code=307)
            
        return templates.TemplateResponse(request, "status.html", {
            "code": code,
            "name": name,
            "leitstelle_name": manager.leitstellen[admin_code].name
        })
    elif manager.leitstellen[admin_code].staffelfuehrer_code == code:
        return RedirectResponse(url=f"/staffelfuehrer/{code}", status_code=307)
    
    return RedirectResponse(url="/", status_code=307)

async def handle_status_change(connection: Connection, admin_code: str, new_status: str):
    if new_status in ["0", "5"]:
        if connection.special == new_status:
            connection.special = None
            if new_status == "0":
                connection.last_blitz_update = None
            else:
                connection.last_sprechwunsch_update = None
        else:
            connection.special = new_status
            if new_status == "0":
                connection.last_blitz_update = time.time()
            else:
                connection.last_sprechwunsch_update = time.time()
        await manager.broadcast_status(admin_code)
    else:
        allowed = True
        current = connection.status
        if new_status == "1":
            if current not in ["2", "3", "4", "6", "8"]:
                allowed = False
        elif new_status == "2":
            if current not in ["1", "6"]:
                allowed = False
        elif new_status == "3":
            if current not in ["1", "2"]:
                allowed = False
        elif new_status == "4":
            if current not in ["1", "3"]:
                allowed = False
        elif new_status == "7":
            if current != "4":
                allowed = False
        elif new_status == "8":
            if current != "7":
                allowed = False

        if allowed:
            connection.status = new_status
            connection.last_status_update = time.time()
            connection.last_update = time.time()

        await manager.broadcast_status(admin_code)

@router.websocket("/ws/{code}")
async def websocket_endpoint(websocket: WebSocket, code: str, name: str = None):
    if name is None:
        name = websocket.query_params.get("name")
    
    code = code.upper()
    admin_code = None
    is_staffelfuehrer = False
    is_leitstelle = False
    
    if code in manager.leitstellen:
        admin_code = code
        is_leitstelle = True
    elif code in manager.code_to_admin:
        admin_code = manager.code_to_admin[code]
        if manager.leitstellen[admin_code].staffelfuehrer_code == code:
            is_staffelfuehrer = True
    if is_leitstelle and not name:
        name = "Leitstelle"
    elif not name:
        name = "Unknown"
    
    if admin_code is None:
        await websocket.accept()
        await websocket.send_json({"type": "error", "message": "Invalid code"})
        await websocket.close(code=1008)
        return
    
    # Check for duplicate vehicle names
    existing_connection = next((c for c in manager.leitstellen[admin_code].connections if c.name == name), None)
    if not is_staffelfuehrer and not is_leitstelle and existing_connection and existing_connection.ws is not None:
        await websocket.accept()
        await websocket.send_json({"type": "error", "message": "Name already taken"})
        await websocket.close(code=1008, reason="Name already taken")
        return

    await websocket.accept()
    
    if existing_connection:
        connection = existing_connection
        connection.ws = websocket
        connection.last_update = time.time()
        connection.disconnected_at = None
        connection.is_leitstelle = is_leitstelle
    else:
        connection = Connection(
            ws=websocket,
            name=name,
            last_update=time.time(),
            last_status_update=time.time(),
            is_staffelfuehrer=is_staffelfuehrer,
            is_leitstelle=is_leitstelle
        )
        manager.leitstellen[admin_code].connections.append(connection)
    
    logger.info(f"New connection: {name} to {admin_code}")
    await manager.broadcast_status(admin_code)
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                json_data = json.loads(data)
                if isinstance(json_data, dict) and "type" in json_data:
                    msg_type = json_data["type"]
                    if msg_type == "status":
                        new_status = json_data.get("value")
                        if new_status:
                            await handle_status_change(connection, admin_code, new_status)
                    elif msg_type == "confirm_notice":
                        if name in manager.leitstellen[admin_code].notices:
                            manager.leitstellen[admin_code].notices[name].status = "confirmed"
                            manager.leitstellen[admin_code].notices[name].confirmed_at = time.time()
                            await manager.broadcast_status(admin_code)
                    elif msg_type == "kurzstatus":
                        kurztext = json_data.get("value")
                        connection.kurzstatus = kurztext if kurztext != "" else None
                        connection.last_update = time.time()
                        await manager.broadcast_status(admin_code)
                    elif msg_type == "toggle_talking_to_sf":
                        connection.talking_to_sf = not connection.talking_to_sf
                        await manager.broadcast_status(admin_code)
            except json.JSONDecodeError:
                if data.startswith("status:"):
                    new_status = data.split(":", 1)[1]
                    await handle_status_change(connection, admin_code, new_status)
                elif data.startswith("confirm_notice"):
                    if name in manager.leitstellen[admin_code].notices:
                        manager.leitstellen[admin_code].notices[name].status = "confirmed"
                        manager.leitstellen[admin_code].notices[name].confirmed_at = time.time()
                        await manager.broadcast_status(admin_code)
                elif data.startswith("kurzstatus:"):
                    kurztext = data.split(":", 1)[1]
                    connection.kurzstatus = kurztext if kurztext != "" else None
                    connection.last_update = time.time()
                    await manager.broadcast_status(admin_code)
                elif data == "toggle_talking_to_sf":
                    connection.talking_to_sf = not connection.talking_to_sf
                    await manager.broadcast_status(admin_code)
                elif data == "heartbeat":
                    connection.last_update = time.time()
                    await websocket.send_text("heartbeat")
    except WebSocketDisconnect:
        logger.debug(f"WebSocket disconnected: {name}")
    except Exception as e:
        logger.error(f"Error in websocket_endpoint for {name}: {e}")
    finally:
        if admin_code in manager.leitstellen:
            if connection.ws == websocket:
                connection.ws = None
                connection.disconnected_at = time.time()
            await manager.broadcast_status(admin_code)

@router.get("/api/leitstelle_info/{code}")
async def get_leitstelle_info(code: str):
    admin_code = code.upper()
    if admin_code not in manager.leitstellen:
        return {"status": "error", "message": "Leitstelle not found"}
    ls = manager.leitstellen[admin_code]
    return {
        "status": "success",
        "name": ls.name,
        "vehicle_code": ls.vehicle_code,
        "staffelfuehrer_code": ls.staffelfuehrer_code
    }

@router.get("/api/staffelfuehrer_info/{code}")
async def get_staffelfuehrer_info(code: str):
    sf_code = code.upper()
    if sf_code not in manager.code_to_admin:
        return {"status": "error", "message": "Invalid code"}
    admin_code = manager.code_to_admin[sf_code]
    if manager.leitstellen[admin_code].staffelfuehrer_code != sf_code:
        return {"status": "error", "message": "Unauthorized"}
    return {
        "status": "success",
        "name": manager.leitstellen[admin_code].name
    }

@router.get("/api/status_info")
async def get_status_info(code: str, name: str):
    code = code.upper()
    if code not in manager.code_to_admin:
        return {"status": "error", "message": "Invalid code"}
    admin_code = manager.code_to_admin[code]
    return {
        "status": "success",
        "leitstelle_name": manager.leitstellen[admin_code].name
    }

@router.post("/api/leitstelle/{code}/message")
async def send_message(code: str, request: MessageRequest):
    code_upper = code.upper()
    admin_code = None
    prefix = ""
    sender = ""
    
    if code_upper in manager.leitstellen:
        admin_code = code_upper
        prefix = "LS: "
        sender = "LS"
    elif code_upper in manager.code_to_admin:
        admin_code = manager.code_to_admin[code_upper]
        prefix = "SF: "
        sender = "SF"
    
    if admin_code is None:
        return {"status": "error", "message": "Invalid code"}
    
    prefixed_message = f"{prefix}{request.message}"

    if request.target_name:
        history = manager.leitstellen[admin_code].chat_history.setdefault(request.target_name, [])
        history.append(ChatMessage(sender=sender, text=request.message, timestamp=time.time()))
        if len(history) > 200:
            history[:] = history[-200:]
    else:
        for connection in manager.leitstellen[admin_code].connections:
            if connection.is_staffelfuehrer or connection.is_leitstelle:
                continue
            history = manager.leitstellen[admin_code].chat_history.setdefault(connection.name, [])
            history.append(ChatMessage(sender=sender, text=request.message, timestamp=time.time()))
            if len(history) > 200:
                history[:] = history[-200:]
    
    for connection in manager.leitstellen[admin_code].connections:
        should_send = False
        if request.target_name is None:
            should_send = True
        elif connection.name == request.target_name or connection.is_staffelfuehrer or connection.is_leitstelle:
            should_send = True

        if should_send and connection.ws:
            await connection.ws.send_text(prefixed_message)
    
    return {"status": "success"}

@router.get("/api/leitstelle/{code}/chat_history")
async def get_chat_history(code: str, target_name: str):
    code_upper = code.upper()
    admin_code = None
    if code_upper in manager.leitstellen:
        admin_code = code_upper
    elif code_upper in manager.code_to_admin:
        admin_code = manager.code_to_admin[code_upper]

    if admin_code is None:
        return {"status": "error", "message": "Invalid code"}

    history = manager.leitstellen[admin_code].chat_history.get(target_name, [])
    return {
        "status": "success",
        "messages": [msg.model_dump() for msg in history]
    }

@router.post("/api/leitstelle/{code}/clear_special")
async def clear_special(code: str, request: TargetRequest):
    admin_code = code.upper()
    if admin_code not in manager.leitstellen:
        return {"status": "error", "message": "Leitstelle not found"}
    
    for connection in manager.leitstellen[admin_code].connections:
        if connection.name == request.target_name:
            connection.special = None
            connection.last_blitz_update = None
            connection.last_sprechwunsch_update = None
            await manager.broadcast_status(admin_code)
            return {"status": "success"}
    
    return {"status": "error", "message": "Vehicle not found"}

@router.post("/api/staffelfuehrer/{code}/notice")
async def send_notice(code: str, request: NoticeRequest):
    sf_code = code.upper()
    if sf_code not in manager.code_to_admin:
        return {"status": "error", "message": "Invalid code"}
    
    admin_code = manager.code_to_admin[sf_code]
    if manager.leitstellen[admin_code].staffelfuehrer_code != sf_code:
        return {"status": "error", "message": "Unauthorized"}
    
    manager.leitstellen[admin_code].notices[request.target_name] = Notice(text=request.text, status="pending")
    await manager.broadcast_status(admin_code)
    return {"status": "success"}

@router.post("/api/staffelfuehrer/{code}/acknowledge")
async def acknowledge_notice(code: str, request: TargetRequest):
    sf_code = code.upper()
    if sf_code not in manager.code_to_admin:
        return {"status": "error", "message": "Invalid code"}
    
    admin_code = manager.code_to_admin[sf_code]
    if manager.leitstellen[admin_code].staffelfuehrer_code != sf_code:
        return {"status": "error", "message": "Unauthorized"}
    
    if request.target_name in manager.leitstellen[admin_code].notices:
        del manager.leitstellen[admin_code].notices[request.target_name]
        await manager.broadcast_status(admin_code)
        return {"status": "success"}
    
    return {"status": "error", "message": "Notice not found"}

@router.post("/api/leitstelle/{code}/clear_kurzstatus")
async def clear_kurzstatus(code: str, request: TargetRequest):
    admin_code = code.upper()
    if admin_code not in manager.leitstellen:
        return {"status": "error", "message": "Leitstelle not found"}
    
    for connection in manager.leitstellen[admin_code].connections:
        if connection.name == request.target_name:
            connection.kurzstatus = None
            connection.last_update = time.time()
            await manager.broadcast_status(admin_code)
            return {"status": "success"}
    
    return {"status": "error", "message": "Vehicle not found"}

@router.post("/api/leitstelle/{code}/update_note")
async def update_note(code: str, request: NoteRequest):
    code_upper = code.upper()
    admin_code = None
    is_staffelfuehrer = False
    if code_upper in manager.leitstellen:
        admin_code = code_upper
    elif code_upper in manager.code_to_admin:
        admin_code = manager.code_to_admin[code_upper]
        is_staffelfuehrer = True
    
    if admin_code is None:
        return {"status": "error", "message": "Invalid code"}
    
    if is_staffelfuehrer:
        manager.leitstellen[admin_code].sf_notes[request.target_name] = request.note
    else:
        manager.leitstellen[admin_code].notes[request.target_name] = request.note
    await manager.broadcast_status(admin_code)
    return {"status": "success"}

@router.post("/api/leitstelle/{code}/set_status")
async def set_status(code: str, request: StatusRequest):
    admin_code = code.upper()
    if admin_code not in manager.leitstellen:
        return {"status": "error", "message": "Leitstelle not found"}
    
    for connection in manager.leitstellen[admin_code].connections:
        if connection.name == request.target_name:
            connection.status = request.status
            connection.last_status_update = time.time()
            connection.last_update = time.time()
            await manager.broadcast_status(admin_code)
            return {"status": "success"}
    
    return {"status": "error", "message": "Vehicle not found"}


# --- Szenario-API: Generator exponieren ---
SCENARIOS_DIR = os.path.join(current_dir, "static", "scenarios")


def _ensure_scenarios_loaded(admin_code: str):
    """Lädt alle Szenario‑JSONs einmalig in den Speicher der Leitstelle."""
    ls = manager.leitstellen.get(admin_code)
    if not ls:
        return
    if ls.scenarios:
        return
    if not os.path.isdir(SCENARIOS_DIR):
        logger.warning(f"Scenarios directory not found: {SCENARIOS_DIR}")
        return
    for fname in os.listdir(SCENARIOS_DIR):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(SCENARIOS_DIR, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                raw = json.load(f)
            scen_name = raw.get("name") or os.path.splitext(fname)[0]
            ls.scenarios[scen_name] = raw
        except Exception as e:
            logger.error(f"Failed to load scenario {fname}: {e}")


@router.get("/api/leitstelle/{code}/scenarios")
async def list_scenarios(code: str):
    admin_code = code.upper()
    if admin_code not in manager.leitstellen:
        return {"status": "error", "message": "Leitstelle nicht gefunden"}
    _ensure_scenarios_loaded(admin_code)
    ls = manager.leitstellen[admin_code]
    items = []
    for name, raw in ls.scenarios.items():
        items.append({
            "name": name,
            "beschreibung": raw.get("beschreibung", "")
        })
    return {"status": "success", "scenarios": items}


@router.post("/api/leitstelle/{code}/scenario/next")
async def next_scenario(code: str, request: TargetRequest):
    """
    Liefert das nächste unbenutzte Szenario für das angegebene Fahrzeug
    und markiert es als benutzt. Erzeugt die Funksprüche über den Generator.
    """
    admin_code = code.upper()
    if admin_code not in manager.leitstellen:
        return {"status": "error", "message": "Leitstelle nicht gefunden"}
    vehicle_name = request.target_name
    if not vehicle_name:
        return {"status": "error", "message": "Fahrzeugname fehlt"}

    _ensure_scenarios_loaded(admin_code)
    ls = manager.leitstellen[admin_code]

    # Bestimme bereits verwendete Szenarien für das Fahrzeug
    used = set(ls.used_scenarios.get(vehicle_name, []))
    # Kandidaten sind alle geladenen Szenarien außer den bereits verwendeten
    candidates = [name for name in ls.scenarios.keys() if name not in used]
    if not candidates:
        return {"status": "error", "message": "Keine unbenutzten Szenarien mehr verfügbar"}

    # Deterministische Auswahl: alphabetisch erstes unbenutztes Szenario
    candidates.sort()
    chosen_name = candidates[0]
    raw = ls.scenarios[chosen_name]

    # Parse zu Scenario und generiere Funksprüche
    try:
        scenario = Scenario.model_validate(raw)
    except Exception as e:
        logger.error(f"Fehler beim Laden des Szenarios {chosen_name}: {e}")
        return {"status": "error", "message": f"Szenario fehlerhaft: {chosen_name}"}

    # Kontext: Fahrzeugkennung = angefragtes Fahrzeug, LS Name deutsch
    funke = scenario.generate_funksprueche(fk=vehicle_name, ls="Leitstelle", start_enr=1)

    # Als benutzt markieren
    ls.used_scenarios.setdefault(vehicle_name, []).append(chosen_name)

    # Rückgabe serialisieren
    entries = [entry.model_dump() if isinstance(entry, FunkEntry) else entry for entry in funke]
    return {
        "status": "success",
        "scenario": {"name": chosen_name, "beschreibung": raw.get("beschreibung", "")},
        "entries": entries
    }
