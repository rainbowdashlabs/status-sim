from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from fastapi import WebSocket

class MessageRequest(BaseModel):
    message: str
    target_name: Optional[str] = None

class TargetRequest(BaseModel):
    target_name: str

class NoticeRequest(BaseModel):
    target_name: str
    text: str

class NoteRequest(BaseModel):
    target_name: str
    note: str

class StatusRequest(BaseModel):
    target_name: str
    status: str

class LeitstelleCreateRequest(BaseModel):
    name: str

class ScenarioStartRequest(BaseModel):
    target_name: str
    scenario_name: str

class Notice(BaseModel):
    text: str
    status: str  # 'pending'|'confirmed'
    confirmed_at: Optional[float] = None

class ChatMessage(BaseModel):
    sender: str
    text: str
    timestamp: float

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
    is_leitstelle: bool = False
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
    sf_note: str = ""
    is_online: bool = True
    talking_to_sf: bool = False
    active_scenario: Optional[dict] = None

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
    sf_notes: Dict[str, str] = Field(default_factory=dict)
    chat_history: Dict[str, List[ChatMessage]] = Field(default_factory=dict)
    active_scenarios: Dict[str, dict] = Field(default_factory=dict) # vehicle_name -> scenario_data
    # Map of scenario name -> raw Scenario JSON path or object cache (lazy loaded in API)
    scenarios: Dict[str, dict] = Field(default_factory=dict)
    # Track which scenarios have been used per vehicle (vehicle name -> list of scenario names)
    used_scenarios: Dict[str, List[str]] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True
