import json
import time
from typing import Dict, List, Optional
from src.models import LeitstelleData, Connection, VehicleStatus, StatusUpdate, Notice
from src.logging_conf import get_logger

logger = get_logger("manager")

class ConnectionManager:
    def __init__(self):
        self.leitstellen: Dict[str, LeitstelleData] = {}
        self.code_to_admin: Dict[str, str] = {}

    async def broadcast_status(self, admin_code: str):
        if admin_code not in self.leitstellen:
            return
        
        ls = self.leitstellen[admin_code]
        vehicle_statuses = [
            VehicleStatus(
                name=c.name,
                status=c.status,
                special=c.special,
                kurzstatus=c.kurzstatus,
                last_update=c.last_update,
                last_status_update=c.last_status_update,
                last_blitz_update=c.last_blitz_update,
                last_sprechwunsch_update=c.last_sprechwunsch_update,
                is_staffelfuehrer=c.is_staffelfuehrer,
                note=ls.notes.get(c.name, ""),
                sf_note=ls.sf_notes.get(c.name, ""),
                is_online=c.ws is not None,
                talking_to_sf=c.talking_to_sf
            ) for c in ls.connections if not c.is_staffelfuehrer and not c.is_leitstelle
        ]
        
        status_update = StatusUpdate(
            connections=vehicle_statuses,
            notices=ls.notices
        )
        
        message = status_update.model_dump_json()
        
        for connection in ls.connections:
            if connection.ws:
                try:
                    await connection.ws.send_text(message)
                except Exception as e:
                    logger.error(f"Error sending message to {connection.name}: {e}")

    async def cleanup_inactive(self):
        now = time.time()
        for admin_code in list(self.leitstellen.keys()):
            ls = self.leitstellen[admin_code]
            original_count = len(ls.connections)
            
            new_connections = []
            for c in ls.connections:
                if c.ws is not None:
                    # Active connections: cleanup after 3 minutes of inactivity (heartbeat)
                    if now - c.last_update < 180:
                        new_connections.append(c)
                else:
                    # Disconnected state: keep for 5 minutes (300 seconds)
                    if c.disconnected_at and now - c.disconnected_at < 300:
                        new_connections.append(c)
            
            ls.connections = new_connections
            
            if len(ls.connections) < original_count:
                logger.info(f"Cleaned up {original_count - len(ls.connections)} inactive connections in {admin_code}")
                active_names = {c.name for c in ls.connections}
                ls.notices = {name: notice for name, notice in ls.notices.items() if name in active_names}
                await self.broadcast_status(admin_code)

manager = ConnectionManager()
