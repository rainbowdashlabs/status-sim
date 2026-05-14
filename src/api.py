from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
import json
import uuid
import time
import os
import random

from manager import manager  # type: ignore
from models import (
    LeitstelleData, Connection, Notice, ChatMessage,
    MessageRequest, TargetRequest, NoticeRequest,
    NoteRequest, StatusRequest, LeitstelleCreateRequest,
    ScenarioStartRequest, ChecklistUpdateRequest, ChecklistState,
    ClaimRequest, VehicleActionRequest, SfChannelRequest,
)  # type: ignore
from logging_conf import get_logger  # type: ignore
from scenario_models import Scenario, FunkEntry  # type: ignore

logger = get_logger("api")

router = APIRouter()

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
_frontend_dist_primary = os.path.join(current_dir, "frontend_dist")
_frontend_dist_legacy = os.path.join(project_root, "frontend", "dist")
frontend_dist = _frontend_dist_primary if os.path.exists(_frontend_dist_primary) else _frontend_dist_legacy

SCENARIOS_DIR = os.path.join(current_dir, "static", "scenarios")


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@router.get("/api/health")
async def health():
    redis_ok = False
    if manager._redis:
        try:
            await manager._redis.ping()
            redis_ok = True
        except Exception:
            pass

    return {
        "status": "ok",
        "redis": "connected" if redis_ok else ("disabled" if manager._redis is None else "unreachable"),
        "leitstellen": len(manager.leitstellen),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _error(message: str):
    return {"status": "error", "message": message}


def _require_leitstelle(code: str):
    result = manager.get_leitstelle(code)
    if not result:
        return None, None
    return result


def _require_sf(code: str):
    sf_code = code.upper()
    admin_code = manager.code_to_admin.get(sf_code)
    if not admin_code or admin_code not in manager.leitstellen:
        return None, None
    ls = manager.leitstellen[admin_code]
    if ls.staffelfuehrer_code != sf_code:
        return None, None
    return admin_code, ls


def _handle_status_change(connection: Connection, new_status: str):
    if new_status in ("0", "5"):
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
        return

    allowed_from = {
        "1": {"2", "3", "4", "6", "8"},
        "2": {"1", "6"},
        "3": {"1", "2"},
        "4": {"1", "3"},
        "7": {"4"},
        "8": {"7"},
    }

    if connection.status in allowed_from.get(new_status, set()):
        connection.status = new_status
        now = time.time()
        connection.last_status_update = now
        connection.last_update = now


def _ensure_scenarios_loaded(admin_code: str):
    ls = manager.leitstellen.get(admin_code)
    if not ls or ls.scenarios:
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
            ls.scenarios[raw.get("name") or os.path.splitext(fname)[0]] = raw
        except Exception as e:
            logger.error(f"Failed to load scenario {fname}: {e}")


def _append_chat(ls: LeitstelleData, vehicle_name: str, sender: str, text: str):
    history = ls.chat_history.setdefault(vehicle_name, [])
    history.append(ChatMessage(sender=sender, text=text, timestamp=time.time()))
    if len(history) > 200:
        history[:] = history[-200:]


# ---------------------------------------------------------------------------
# HTML serving
# ---------------------------------------------------------------------------

async def serve_vue_index(request: Request):
    index_path = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse(content="Frontend not found", status_code=404)


@router.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    return await serve_vue_index(request)


@router.get("/hilfe", response_class=HTMLResponse)
async def get_help(request: Request):
    return await serve_vue_index(request)


@router.get("/leitstelle/{code}", response_class=HTMLResponse)
async def get_leitstelle_view(request: Request, code: str):
    if code.upper() not in manager.leitstellen:
        return RedirectResponse(url="/", status_code=307)
    return await serve_vue_index(request)


@router.get("/staffelfuehrer/{code}", response_class=HTMLResponse)
async def get_staffelfuehrer_view(request: Request, code: str):
    admin_code, _ = _require_sf(code)
    if not admin_code:
        return RedirectResponse(url="/", status_code=307)
    return await serve_vue_index(request)


@router.get("/status", response_class=HTMLResponse)
async def get_status_page(request: Request, code: str, name: str):
    code_upper = code.upper()
    admin_code = manager.code_to_admin.get(code_upper)
    if not admin_code or admin_code not in manager.leitstellen:
        return RedirectResponse(url="/", status_code=307)

    ls = manager.leitstellen[admin_code]
    if ls.vehicle_code == code_upper:
        existing = manager.find_connection(ls, name)
        if existing and manager.is_online(existing):
            return RedirectResponse(
                url=f"/?error=name_taken&old_name={name}&code={code_upper}",
                status_code=307,
            )
        return await serve_vue_index(request)
    elif ls.staffelfuehrer_code == code_upper:
        return RedirectResponse(url=f"/staffelfuehrer/{code_upper}", status_code=307)

    return RedirectResponse(url="/", status_code=307)


# ---------------------------------------------------------------------------
# Leitstelle management
# ---------------------------------------------------------------------------

@router.post("/leitstelle")
async def create_leitstelle(request: LeitstelleCreateRequest):
    admin_code = str(uuid.uuid4())[:8].upper()
    vehicle_code = str(uuid.uuid4())[:8].upper()
    staffelfuehrer_code = str(uuid.uuid4())[:8].upper()

    codes = {admin_code, vehicle_code, staffelfuehrer_code}
    while len(codes) < 3:
        vehicle_code = str(uuid.uuid4())[:8].upper()
        staffelfuehrer_code = str(uuid.uuid4())[:8].upper()
        codes = {admin_code, vehicle_code, staffelfuehrer_code}

    manager.leitstellen[admin_code] = LeitstelleData(
        name=request.name,
        vehicle_code=vehicle_code,
        staffelfuehrer_code=staffelfuehrer_code,
    )
    manager.code_to_admin[vehicle_code] = admin_code
    manager.code_to_admin[staffelfuehrer_code] = admin_code
    await manager.persist(admin_code)
    return {
        "status": "success",
        "admin_code": admin_code,
        "vehicle_code": vehicle_code,
        "staffelfuehrer_code": staffelfuehrer_code,
    }


@router.get("/api/leitstelle_info/{code}")
async def get_leitstelle_info(code: str):
    admin_code = code.upper()
    if admin_code not in manager.leitstellen:
        return _error("Leitstelle not found")
    ls = manager.leitstellen[admin_code]
    return {
        "status": "success",
        "name": ls.name,
        "vehicle_code": ls.vehicle_code,
        "staffelfuehrer_code": ls.staffelfuehrer_code,
    }


@router.get("/api/staffelfuehrer_info/{code}")
async def get_staffelfuehrer_info(code: str):
    admin_code, ls = _require_sf(code)
    if not admin_code:
        return _error("Invalid code")
    return {"status": "success", "name": ls.name}


@router.get("/api/status_info")
async def get_status_info(code: str, name: str):
    admin_code, ls = _require_leitstelle(code)
    if not admin_code:
        return _error("Invalid code")
    return {"status": "success", "leitstelle_name": ls.name}


# ---------------------------------------------------------------------------
# Polling
# ---------------------------------------------------------------------------

@router.get("/api/poll/{code}")
async def poll(code: str, name: str | None = None):
    code_upper = code.upper()
    admin_code = manager.resolve_admin_code(code_upper)
    if not admin_code:
        return _error("Invalid code")

    ls = manager.leitstellen[admin_code]
    now = time.time()

    if ls.vehicle_code == code_upper and name:
        conn = manager.find_connection(ls, name)
        if conn:
            conn.last_update = now
        else:
            conn = Connection(
                name=name, last_update=now,
                last_status_update=now, last_activity=now,
            )
            ls.connections.append(conn)

    elif ls.staffelfuehrer_code == code_upper and name:
        sf_conn = next((c for c in ls.connections if c.is_staffelfuehrer), None)
        if sf_conn:
            sf_conn.name = name
            sf_conn.last_update = now
        else:
            ls.connections.append(Connection(
                name=name, last_update=now,
                last_status_update=now, last_activity=now,
                is_staffelfuehrer=True,
            ))

    elif code_upper == admin_code:
        ls_name = name or "Leitstelle"
        ls_conn = next((c for c in ls.connections if c.is_leitstelle and c.name == ls_name), None)
        if ls_conn:
            ls_conn.last_update = now
        else:
            ls.connections.append(Connection(
                name=ls_name, last_update=now,
                last_status_update=now, last_activity=now,
                is_leitstelle=True,
            ))

    update = manager.build_status_update(admin_code)
    if not update:
        return _error("Failed to build status")

    response = update.model_dump()

    if ls.vehicle_code == code_upper and name:
        response["messages"] = [m.model_dump() for m in ls.chat_history.get(name, [])]

    return response


# ---------------------------------------------------------------------------
# Vehicle actions
# ---------------------------------------------------------------------------

@router.post("/api/vehicle/{code}/action")
async def vehicle_action(code: str, request: VehicleActionRequest):
    admin_code, ls = _require_leitstelle(code)
    if not admin_code:
        return _error("Invalid code")

    conn = manager.find_connection(ls, request.name)
    if not conn:
        return _error("Vehicle not found")

    match request.action:
        case "status":
            if request.value:
                _handle_status_change(conn, request.value)
        case "kurzstatus":
            conn.kurzstatus = request.value or None
            conn.last_update = time.time()
        case "confirm_notice":
            if request.name in ls.notices:
                ls.notices[request.name].status = "confirmed"
                ls.notices[request.name].confirmed_at = time.time()
        case "toggle_sf":
            conn.talking_to_sf = not conn.talking_to_sf
            if conn.talking_to_sf:
                conn.talking_to_sf_since = time.time()
            else:
                conn.talking_to_sf_since = None
                conn.radio_channel = None
        case "set_channel":
            conn.radio_channel = request.value or None
        case _:
            return _error(f"Unknown action: {request.action}")

    await manager.persist(admin_code)
    return {"status": "success"}


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------

@router.post("/api/leitstelle/{code}/message")
async def send_message(code: str, request: MessageRequest):
    admin_code, ls = _require_leitstelle(code)
    if not admin_code:
        return _error("Invalid code")

    sender = "LS" if code.upper() == admin_code else "SF"

    if request.target_name:
        _append_chat(ls, request.target_name, sender, request.message)
    else:
        for conn in ls.connections:
            if not conn.is_staffelfuehrer and not conn.is_leitstelle:
                _append_chat(ls, conn.name, sender, request.message)

    await manager.persist(admin_code)
    return {"status": "success"}


@router.get("/api/leitstelle/{code}/chat_history")
async def get_chat_history(code: str, target_name: str):
    admin_code, ls = _require_leitstelle(code)
    if not admin_code:
        return _error("Invalid code")
    history = ls.chat_history.get(target_name, [])
    return {"status": "success", "messages": [m.model_dump() for m in history]}


# ---------------------------------------------------------------------------
# Leitstelle actions
# ---------------------------------------------------------------------------

@router.post("/api/leitstelle/{code}/clear_special")
async def clear_special(code: str, request: TargetRequest):
    admin_code = code.upper()
    if admin_code not in manager.leitstellen:
        return _error("Leitstelle not found")
    conn = manager.find_connection(manager.leitstellen[admin_code], request.target_name)
    if not conn:
        return _error("Vehicle not found")
    conn.special = None
    conn.last_blitz_update = None
    conn.last_sprechwunsch_update = None
    await manager.persist(admin_code)
    return {"status": "success"}


@router.post("/api/leitstelle/{code}/clear_kurzstatus")
async def clear_kurzstatus(code: str, request: TargetRequest):
    admin_code = code.upper()
    if admin_code not in manager.leitstellen:
        return _error("Leitstelle not found")
    conn = manager.find_connection(manager.leitstellen[admin_code], request.target_name)
    if not conn:
        return _error("Vehicle not found")
    conn.kurzstatus = None
    conn.last_update = time.time()
    await manager.persist(admin_code)
    return {"status": "success"}


@router.post("/api/leitstelle/{code}/update_note")
async def update_note(code: str, request: NoteRequest):
    admin_code, ls = _require_leitstelle(code)
    if not admin_code:
        return _error("Invalid code")
    if code.upper() == admin_code:
        ls.notes[request.target_name] = request.note
    else:
        ls.sf_notes[request.target_name] = request.note
    await manager.persist(admin_code)
    return {"status": "success"}


@router.post("/api/leitstelle/{code}/set_status")
async def set_status(code: str, request: StatusRequest):
    admin_code = code.upper()
    if admin_code not in manager.leitstellen:
        return _error("Leitstelle not found")
    conn = manager.find_connection(manager.leitstellen[admin_code], request.target_name)
    if not conn:
        return _error("Vehicle not found")
    conn.status = request.status
    now = time.time()
    conn.last_status_update = now
    conn.last_update = now
    await manager.persist(admin_code)
    return {"status": "success"}


@router.post("/api/leitstelle/{code}/claim")
async def ls_claim_vehicle(code: str, request: ClaimRequest):
    admin_code = code.upper()
    if admin_code not in manager.leitstellen:
        return _error("Leitstelle not found")
    conn = manager.find_connection(manager.leitstellen[admin_code], request.target_name)
    if not conn:
        return _error("Vehicle not found")
    if conn.ls_claimed_by and conn.ls_claimed_by != request.sf_name:
        return _error("Vehicle already claimed by another operator")
    conn.ls_claimed_by = request.sf_name
    await manager.persist(admin_code)
    return {"status": "success"}


@router.post("/api/leitstelle/{code}/unclaim")
async def ls_unclaim_vehicle(code: str, request: TargetRequest):
    admin_code = code.upper()
    if admin_code not in manager.leitstellen:
        return _error("Leitstelle not found")
    conn = manager.find_connection(manager.leitstellen[admin_code], request.target_name)
    if not conn:
        return _error("Vehicle not found")
    conn.ls_claimed_by = None
    await manager.persist(admin_code)
    return {"status": "success"}


@router.post("/api/leitstelle/{code}/channel")
async def set_ls_channel(code: str, request: SfChannelRequest):
    admin_code = code.upper()
    if admin_code not in manager.leitstellen:
        return _error("Leitstelle not found")
    ls_conn = next(
        (c for c in manager.leitstellen[admin_code].connections if c.is_leitstelle and c.name == request.name),
        None,
    )
    if not ls_conn:
        return _error("LS connection not found")
    ls_conn.radio_channel = request.channel if request.channel else None
    await manager.persist(admin_code)
    return {"status": "success"}


# ---------------------------------------------------------------------------
# Staffelfuehrer actions
# ---------------------------------------------------------------------------

@router.post("/api/staffelfuehrer/{code}/notice")
async def send_notice(code: str, request: NoticeRequest):
    admin_code, ls = _require_sf(code)
    if not admin_code:
        return _error("Invalid code")

    target = manager.find_connection(ls, request.target_name)
    if not target:
        return _error("Vehicle not found")
    if target.claimed_by != request.sf_name:
        return _error("You must claim the vehicle before requesting it")

    if request.sf_name:
        sf_conn = next((c for c in ls.connections if c.name == request.sf_name and c.is_staffelfuehrer), None)
        if sf_conn:
            target.radio_channel = sf_conn.radio_channel

    ls.notices[request.target_name] = Notice(text=request.text, status="pending")
    await manager.persist(admin_code)
    return {"status": "success"}


@router.post("/api/staffelfuehrer/{code}/acknowledge")
async def acknowledge_notice(code: str, request: TargetRequest):
    admin_code, ls = _require_sf(code)
    if not admin_code:
        return _error("Invalid code")
    if request.target_name in ls.notices:
        del ls.notices[request.target_name]
        await manager.persist(admin_code)
        return {"status": "success"}
    return _error("Notice not found")


@router.post("/api/staffelfuehrer/{code}/claim")
async def claim_vehicle(code: str, request: ClaimRequest):
    admin_code, ls = _require_sf(code)
    if not admin_code:
        return _error("Invalid code")
    conn = manager.find_connection(ls, request.target_name)
    if not conn:
        return _error("Vehicle not found")
    if conn.claimed_by and conn.claimed_by != request.sf_name:
        return _error("Vehicle already claimed by someone else")
    conn.claimed_by = request.sf_name
    await manager.persist(admin_code)
    return {"status": "success"}


@router.post("/api/staffelfuehrer/{code}/unclaim")
async def unclaim_vehicle(code: str, request: TargetRequest):
    admin_code, ls = _require_sf(code)
    if not admin_code:
        return _error("Invalid code")
    conn = manager.find_connection(ls, request.target_name)
    if not conn:
        return _error("Vehicle not found")
    conn.claimed_by = None
    await manager.persist(admin_code)
    return {"status": "success"}


@router.post("/api/staffelfuehrer/{code}/channel")
async def set_sf_channel(code: str, request: SfChannelRequest):
    admin_code, ls = _require_sf(code)
    if not admin_code:
        return _error("Invalid code")
    sf_conn = next((c for c in ls.connections if c.name == request.name and c.is_staffelfuehrer), None)
    if not sf_conn:
        return _error("SF connection not found")
    sf_conn.radio_channel = request.channel if request.channel else None
    await manager.persist(admin_code)
    return {"status": "success"}


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

@router.get("/api/leitstelle/{code}/scenarios")
async def list_scenarios(code: str):
    admin_code = code.upper()
    if admin_code not in manager.leitstellen:
        return _error("Leitstelle nicht gefunden")
    _ensure_scenarios_loaded(admin_code)
    ls = manager.leitstellen[admin_code]
    items = [{"name": n, "beschreibung": r.get("beschreibung", "")} for n, r in ls.scenarios.items()]
    return {"status": "success", "scenarios": items}


@router.post("/api/leitstelle/{code}/scenario/start")
async def start_scenario(code: str, request: ScenarioStartRequest):
    admin_code = code.upper()
    if admin_code not in manager.leitstellen:
        return _error("Leitstelle nicht gefunden")

    _ensure_scenarios_loaded(admin_code)
    ls = manager.leitstellen[admin_code]

    if request.scenario_name not in ls.scenarios:
        return _error("Szenario nicht gefunden")

    try:
        scenario_obj = Scenario.model_validate(ls.scenarios[request.scenario_name])
    except Exception as e:
        logger.error(f"Fehler beim Validieren des Szenarios {request.scenario_name}: {e}")
        return _error("Szenario fehlerhaft")

    funksprueche = scenario_obj.generate_funksprueche(
        fk=request.target_name, ls=ls.name, start_enr=ls.next_enr(),
    )

    scenario_data = scenario_obj.model_dump()
    scenario_data["generated_entries"] = [
        f.model_dump() if isinstance(f, FunkEntry) else f for f in funksprueche
    ]

    ls.active_scenarios[request.target_name] = scenario_data
    ls.checklist_states[request.target_name] = ChecklistState()
    await manager.persist(admin_code)
    return {"status": "success"}


@router.post("/api/leitstelle/{code}/scenario/discard")
async def discard_scenario(code: str, request: TargetRequest):
    admin_code = code.upper()
    if admin_code not in manager.leitstellen:
        return _error("Leitstelle nicht gefunden")
    ls = manager.leitstellen[admin_code]
    ls.active_scenarios.pop(request.target_name, None)
    ls.checklist_states.pop(request.target_name, None)
    await manager.persist(admin_code)
    return {"status": "success"}


@router.post("/api/leitstelle/{code}/scenario/update_state")
async def update_checklist_state(code: str, request: ChecklistUpdateRequest):
    admin_code, ls = _require_leitstelle(code)
    if not admin_code:
        return _error("Leitstelle nicht gefunden")

    old_state = ls.checklist_states.get(request.target_name)
    if old_state:
        old_checked = old_state.checked_entries
        if any(v and not old_checked.get(k) for k, v in request.state.checked_entries.items()):
            conn = manager.find_connection(ls, request.target_name)
            if conn:
                conn.last_activity = time.time()

    ls.checklist_states[request.target_name] = request.state
    await manager.persist(admin_code)
    return {"status": "success"}


@router.post("/api/leitstelle/{code}/scenario/next")
async def next_scenario(code: str, request: TargetRequest):
    admin_code = code.upper()
    if admin_code not in manager.leitstellen:
        return _error("Leitstelle nicht gefunden")

    vehicle_name = request.target_name
    if not vehicle_name:
        return _error("Fahrzeugname fehlt")

    _ensure_scenarios_loaded(admin_code)
    ls = manager.leitstellen[admin_code]

    used = set(ls.used_scenarios.get(vehicle_name, []))
    candidates = [n for n in ls.scenarios if n not in used]
    if not candidates:
        return _error("Keine unbenutzten Szenarien mehr verfügbar")

    chosen_name = random.choice(candidates)
    raw = ls.scenarios[chosen_name]

    try:
        scenario = Scenario.model_validate(raw)
    except Exception as e:
        logger.error(f"Fehler beim Laden des Szenarios {chosen_name}: {e}")
        return _error(f"Szenario fehlerhaft: {chosen_name}")

    funke = scenario.generate_funksprueche(fk=vehicle_name, ls=ls.name, start_enr=ls.next_enr())
    ls.used_scenarios.setdefault(vehicle_name, []).append(chosen_name)

    await manager.persist(admin_code)

    entries = [e.model_dump() if isinstance(e, FunkEntry) else e for e in funke]
    return {
        "status": "success",
        "scenario": {"name": chosen_name, "beschreibung": raw.get("beschreibung", "")},
        "entries": entries,
    }
