from fastapi import APIRouter, Request, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import uuid
import time
import os
from datetime import datetime
from src.manager import manager
from src.models import LeitstelleData, Connection, Notice

router = APIRouter()

current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(current_dir, "templates")
templates = Jinja2Templates(directory=templates_dir)
templates.env.globals['current_year'] = datetime.now().year

@router.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    return templates.TemplateResponse(request, "index.html")

@router.post("/leitstelle")
async def create_leitstelle(name: str = Form(...)):
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

@router.websocket("/ws/{code}")
async def websocket_endpoint(websocket: WebSocket, code: str, name: str = None):
    if name is None:
        name = websocket.query_params.get("name", "Unknown")
    
    code = code.upper()
    admin_code = None
    is_staffelfuehrer = False
    
    if code in manager.leitstellen:
        admin_code = code
    elif code in manager.code_to_admin:
        admin_code = manager.code_to_admin[code]
        if manager.leitstellen[admin_code].staffelfuehrer_code == code:
            is_staffelfuehrer = True
    
    if admin_code is None:
        await websocket.close(code=1008)
        return
    
    # Check for duplicate vehicle names
    existing_connection = next((c for c in manager.leitstellen[admin_code].connections if c.name == name), None)
    if not is_staffelfuehrer and existing_connection and existing_connection.ws is not None:
        await websocket.close(code=1008, reason="Name already taken")
        return

    await websocket.accept()
    
    if existing_connection:
        connection = existing_connection
        connection.ws = websocket
        connection.last_update = time.time()
        connection.disconnected_at = None
    else:
        connection = Connection(
            ws=websocket,
            name=name,
            last_update=time.time(),
            last_status_update=time.time(),
            is_staffelfuehrer=is_staffelfuehrer
        )
        manager.leitstellen[admin_code].connections.append(connection)
    
    # print(f"New connection: {name} to {admin_code}")
    await manager.broadcast_status(admin_code)
    
    try:
        while True:
            data = await websocket.receive_text()
            if data.startswith("status:"):
                new_status = data.split(":", 1)[1]
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
                        if current not in ["2", "3", "4","6", "8"]:
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
    except WebSocketDisconnect:
        # print(f"WebSocket disconnected: {name}")
        pass
    except Exception as e:
        # print(f"Error in websocket_endpoint for {name}: {e}")
        pass
    finally:
        if admin_code in manager.leitstellen:
            if connection.ws == websocket:
                connection.ws = None
                connection.disconnected_at = time.time()
            await manager.broadcast_status(admin_code)

@router.post("/api/leitstelle/{code}/message")
async def send_message(code: str, message: str = Form(...), target_name: str = Form(None)):
    code_upper = code.upper()
    admin_code = None
    prefix = ""
    
    if code_upper in manager.leitstellen:
        admin_code = code_upper
        prefix = "LS: "
    elif code_upper in manager.code_to_admin:
        admin_code = manager.code_to_admin[code_upper]
        prefix = "SF: "
    
    if admin_code is None:
        return {"status": "error", "message": "Invalid code"}
    
    prefixed_message = f"{prefix}{message}"
    
    for connection in manager.leitstellen[admin_code].connections:
        if target_name is None or connection.name == target_name:
            await connection.ws.send_text(prefixed_message)
    
    return {"status": "success"}

@router.post("/api/leitstelle/{code}/clear_special")
async def clear_special(code: str, target_name: str = Form(...)):
    admin_code = code.upper()
    if admin_code not in manager.leitstellen:
        return {"status": "error", "message": "Leitstelle not found"}
    
    for connection in manager.leitstellen[admin_code].connections:
        if connection.name == target_name:
            connection.special = None
            connection.last_blitz_update = None
            connection.last_sprechwunsch_update = None
            await manager.broadcast_status(admin_code)
            return {"status": "success"}
    
    return {"status": "error", "message": "Vehicle not found"}

@router.post("/api/staffelfuehrer/{code}/notice")
async def send_notice(code: str, target_name: str = Form(...), text: str = Form(...)):
    sf_code = code.upper()
    if sf_code not in manager.code_to_admin:
        return {"status": "error", "message": "Invalid code"}
    
    admin_code = manager.code_to_admin[sf_code]
    if manager.leitstellen[admin_code].staffelfuehrer_code != sf_code:
        return {"status": "error", "message": "Unauthorized"}
    
    manager.leitstellen[admin_code].notices[target_name] = Notice(text=text, status="pending")
    await manager.broadcast_status(admin_code)
    return {"status": "success"}

@router.post("/api/staffelfuehrer/{code}/acknowledge")
async def acknowledge_notice(code: str, target_name: str = Form(...)):
    sf_code = code.upper()
    if sf_code not in manager.code_to_admin:
        return {"status": "error", "message": "Invalid code"}
    
    admin_code = manager.code_to_admin[sf_code]
    if manager.leitstellen[admin_code].staffelfuehrer_code != sf_code:
        return {"status": "error", "message": "Unauthorized"}
    
    if target_name in manager.leitstellen[admin_code].notices:
        del manager.leitstellen[admin_code].notices[target_name]
        await manager.broadcast_status(admin_code)
        return {"status": "success"}
    
    return {"status": "error", "message": "Notice not found"}

@router.post("/api/leitstelle/{code}/clear_kurzstatus")
async def clear_kurzstatus(code: str, target_name: str = Form(...)):
    admin_code = code.upper()
    if admin_code not in manager.leitstellen:
        return {"status": "error", "message": "Leitstelle not found"}
    
    for connection in manager.leitstellen[admin_code].connections:
        if connection.name == target_name:
            connection.kurzstatus = None
            connection.last_update = time.time()
            await manager.broadcast_status(admin_code)
            return {"status": "success"}
    
    return {"status": "error", "message": "Vehicle not found"}

@router.post("/api/leitstelle/{code}/update_note")
async def update_note(code: str, target_name: str = Form(...), note: str = Form(...)):
    admin_code = None
    if code in manager.leitstellen:
        admin_code = code
    elif code in manager.code_to_admin:
        admin_code = manager.code_to_admin[code]
    
    if admin_code is None:
        return {"status": "error", "message": "Invalid code"}
    
    manager.leitstellen[admin_code].notes[target_name] = note
    await manager.broadcast_status(admin_code)
    return {"status": "success"}

@router.post("/api/leitstelle/{code}/set_status")
async def set_status(code: str, target_name: str = Form(...), status: str = Form(...)):
    admin_code = code.upper()
    if admin_code not in manager.leitstellen:
        return {"status": "error", "message": "Leitstelle not found"}
    
    for connection in manager.leitstellen[admin_code].connections:
        if connection.name == target_name:
            connection.status = status
            connection.last_status_update = time.time()
            connection.last_update = time.time()
            await manager.broadcast_status(admin_code)
            return {"status": "success"}
    
    return {"status": "error", "message": "Vehicle not found"}
