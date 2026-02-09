from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from fastapi import WebSocket

class Notice(BaseModel):
    text: str
    status: str  # 'pending'|'confirmed'
    confirmed_at: Optional[float] = None

class Connection(BaseModel):
    ws: Optional[WebSocket] = None
    name: str
    status: str = "2"
    special: Optional[str] = None
    kurzstatus: Optional[str] = None
    last_update: float
    last_status_update: float
    last_blitz_update: Optional[float] = None
    last_sprechwunsch_update: Optional[float] = None
    is_staffelfuehrer: bool = False
    disconnected_at: Optional[float] = None
    talking_to_sf: bool = False

    class Config:
        arbitrary_types_allowed = True

class VehicleStatus(BaseModel):
    name: str
    status: str
    special: Optional[str] = None
    kurzstatus: Optional[str] = None
    last_update: float
    last_status_update: float
    last_blitz_update: Optional[float] = None
    last_sprechwunsch_update: Optional[float] = None
    is_staffelfuehrer: bool
    note: str = ""
    is_online: bool = True
    talking_to_sf: bool = False

class StatusUpdate(BaseModel):
    type: str = "status_update"
    connections: List[VehicleStatus]
    notices: Dict[str, Notice]

class LeitstelleData(BaseModel):
    name: str
    vehicle_code: str
    staffelfuehrer_code: str
    connections: List[Connection] = Field(default_factory=list)
    messages: List[str] = Field(default_factory=list)
    notices: Dict[str, Notice] = Field(default_factory=dict)
    notes: Dict[str, str] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True
