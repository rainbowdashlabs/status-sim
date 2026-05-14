export interface VehicleStatus {
  name: string
  status: string
  special: string | null
  kurzstatus: string | null
  last_update: number
  last_status_update: number
  last_blitz_update: number | null
  last_sprechwunsch_update: number | null
  is_staffelfuehrer: boolean
  note: string
  sf_note: string
  is_online: boolean
  talking_to_sf: boolean
  talking_to_sf_since: number | null
  radio_channel: string | null
  claimed_by: string | null
  ls_claimed_by: string | null
  ls_radio_channel: string | null
  sf_radio_channel: string | null
  active_scenario: any | null
  next_todo: string | null
  last_activity: number
  checklist_state: {
    expanded_einsaetze: Record<string, boolean>
    expanded_schritte: Record<string, boolean>
    checked_entries: Record<string, boolean>
  } | null
}

export interface Notice {
  text: string
  status: string
  confirmed_at?: number
}

export interface ChatMessage {
  sender: string
  text: string
  timestamp: number
}

export interface StatusUpdate {
  type: string
  connections: VehicleStatus[]
  notices: Record<string, Notice>
  messages?: ChatMessage[]
}
