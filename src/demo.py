"""Demo mode: populates a leitstelle with simulated vehicles that act autonomously."""

import asyncio
import json
import os
import random
import time

from manager import manager  # type: ignore
from models import LeitstelleData, Connection, ChatMessage, ChecklistState, Notice  # type: ignore
from scenario_models import Scenario, FunkEntry  # type: ignore
from logging_conf import get_logger  # type: ignore

logger = get_logger("demo")

ADMIN_CODE = "DEMO0001"
VEHICLE_CODE = "DEMO0002"
SF_CODE = "DEMO0003"

VEHICLES = [
    "LHF 2300/1",
    "LHF 4200/1",
    "LHF 1100/1",
    "DLK 1200/1",
    "RTW 1500/1",
    "RTW 3400/2",
    "NEF 2105",
    "ELW 3117",
]

KURZSTATUS = [
    "Lage bestä., Maßn. eing.",
    "Lage bestä., Gef-Abw. eing.",
    "Keine Feststellung, Erk. läuft",
    "Fehlalarm BMA",
    "Müco, 1 C-Rohr, EstuK",
]

LS_MESSAGES = [
    "Einsatzbereit melden",
    "Wie ist die Lage vor Ort?",
    "Nachalarmierung ist raus",
    "Polizei ist informiert",
    "Einsatzleiter übernimmt",
    "Bitte Lagemeldung",
    "Rettungsdienst ist unterwegs",
    "Wasserversorgung sicherstellen",
]

VALID_NEXT = {
    "1": ["2", "3"],
    "2": ["1", "3"],
    "3": ["1", "4", "2"],
    "4": ["1", "7"],
    "7": ["8"],
    "8": ["1"],
}

SCENARIOS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "scenarios")


def _load_random_scenario():
    files = [f for f in os.listdir(SCENARIOS_DIR) if f.endswith(".json")]
    if not files:
        return None
    path = os.path.join(SCENARIOS_DIR, random.choice(files))
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _start_scenario_for(ls: LeitstelleData, vehicle_name: str):
    raw = _load_random_scenario()
    if not raw:
        return
    try:
        scenario = Scenario.model_validate(raw)
    except Exception:
        return
    entries = scenario.generate_funksprueche(fk=vehicle_name, ls=ls.name, start_enr=ls.next_enr())
    data = scenario.model_dump()
    data["generated_entries"] = [e.model_dump() if isinstance(e, FunkEntry) else e for e in entries]
    ls.active_scenarios[vehicle_name] = data
    ls.checklist_states[vehicle_name] = ChecklistState()


async def run_demo():
    await asyncio.sleep(1)

    if ADMIN_CODE in manager.leitstellen:
        logger.info("Demo leitstelle already exists (restored from Redis), skipping creation")
        ls = manager.leitstellen[ADMIN_CODE]
    else:
        ls = LeitstelleData(
            name="Demo Leitstelle Berlin",
            vehicle_code=VEHICLE_CODE,
            staffelfuehrer_code=SF_CODE,
        )
        manager.leitstellen[ADMIN_CODE] = ls
        manager.code_to_admin[VEHICLE_CODE] = ADMIN_CODE
        manager.code_to_admin[SF_CODE] = ADMIN_CODE

        now = time.time()
        for name in VEHICLES:
            ls.connections.append(Connection(
                name=name,
                last_update=now,
                last_status_update=now,
                last_activity=now,
                status=random.choice(["1", "2", "3"]),
            ))

        # Give a couple of vehicles an active scenario
        for v in random.sample(VEHICLES, min(3, len(VEHICLES))):
            _start_scenario_for(ls, v)

        await manager.persist(ADMIN_CODE)

    logger.info("=" * 60)
    logger.info("  DEMO MODE ACTIVE")
    logger.info(f"  Leitstelle : http://localhost:8000/leitstelle/{ADMIN_CODE}")
    logger.info(f"  Vehicle    : http://localhost:8000/status?code={VEHICLE_CODE}&name=MeinFahrzeug")
    logger.info(f"  SF         : http://localhost:8000/staffelfuehrer/{SF_CODE}")
    logger.info(f"  Vehicle code : {VEHICLE_CODE}")
    logger.info(f"  SF code      : {SF_CODE}")
    logger.info("=" * 60)

    heartbeat_task = asyncio.create_task(_heartbeat_loop(ls))
    action_task = asyncio.create_task(_action_loop(ls))
    try:
        await asyncio.gather(heartbeat_task, action_task)
    except asyncio.CancelledError:
        heartbeat_task.cancel()
        action_task.cancel()


async def _heartbeat_loop(ls: LeitstelleData):
    """Keep all demo vehicles online."""
    while True:
        now = time.time()
        for c in ls.connections:
            if not c.is_staffelfuehrer and not c.is_leitstelle:
                c.last_update = now
        await asyncio.sleep(5)


async def _action_loop(ls: LeitstelleData):
    """Periodically simulate random vehicle activity."""
    while True:
        await asyncio.sleep(random.uniform(2, 6))

        vehicles = [c for c in ls.connections if not c.is_staffelfuehrer and not c.is_leitstelle]
        if not vehicles:
            continue

        vehicle = random.choice(vehicles)
        action = random.choices(
            ["status", "kurzstatus", "clear_kurzstatus", "special",
             "message", "toggle_sf", "scenario", "notice", "checklist_tick"],
            weights=[35, 10, 8, 10, 12, 5, 5, 5, 10],
        )[0]

        now = time.time()

        if action == "status":
            options = VALID_NEXT.get(vehicle.status, ["2"])
            vehicle.status = random.choice(options)
            vehicle.last_status_update = now
            vehicle.last_activity = now

        elif action == "kurzstatus":
            vehicle.kurzstatus = random.choice(KURZSTATUS)
            vehicle.last_activity = now

        elif action == "clear_kurzstatus":
            vehicle.kurzstatus = None

        elif action == "special":
            sig = random.choice(["0", "5"])
            if vehicle.special == sig:
                vehicle.special = None
                if sig == "0":
                    vehicle.last_blitz_update = None
                else:
                    vehicle.last_sprechwunsch_update = None
            else:
                vehicle.special = sig
                if sig == "0":
                    vehicle.last_blitz_update = now
                else:
                    vehicle.last_sprechwunsch_update = now

        elif action == "message":
            history = ls.chat_history.setdefault(vehicle.name, [])
            history.append(ChatMessage(sender="LS", text=random.choice(LS_MESSAGES), timestamp=now))
            if len(history) > 200:
                history[:] = history[-200:]

        elif action == "toggle_sf":
            vehicle.talking_to_sf = not vehicle.talking_to_sf
            if vehicle.talking_to_sf:
                vehicle.talking_to_sf_since = now
                vehicle.radio_channel = str(random.choice([401, 402, 403, 406, 410]))
            else:
                vehicle.talking_to_sf_since = None
                vehicle.radio_channel = None
            vehicle.last_activity = now

        elif action == "scenario":
            if vehicle.name not in ls.active_scenarios:
                _start_scenario_for(ls, vehicle.name)

        elif action == "notice":
            if vehicle.name not in ls.notices and not vehicle.talking_to_sf:
                ls.notices[vehicle.name] = Notice(text="Sprechwunsch Staffelführer", status="pending")
            elif vehicle.name in ls.notices and ls.notices[vehicle.name].status == "pending":
                ls.notices[vehicle.name].status = "confirmed"
                ls.notices[vehicle.name].confirmed_at = now
            elif vehicle.name in ls.notices and ls.notices[vehicle.name].status == "confirmed":
                del ls.notices[vehicle.name]

        elif action == "checklist_tick":
            state = ls.checklist_states.get(vehicle.name)
            scen = ls.active_scenarios.get(vehicle.name)
            if state and scen:
                entries = scen.get("generated_entries", [])
                # Find next unchecked entry
                for i, entry in enumerate(entries):
                    msg = entry.get("message", "")
                    if not msg.startswith("[[E"):
                        continue
                    end_e = msg.find("]]", 3)
                    e_part = msg[3:end_e]
                    s_start = msg.find("[[S", end_e)
                    end_s = msg.find("]]", s_start + 3)
                    s_part = msg[s_start + 3:end_s]
                    prefix = msg[:end_s + 2]
                    f_idx = sum(1 for prev in entries[:i] if prev.get("message", "").startswith(prefix))
                    key = f"{e_part}-{s_part}-{f_idx}"
                    if not state.checked_entries.get(key):
                        state.checked_entries[key] = True
                        vehicle.last_activity = now
                        # Check a few consecutive entries at once
                        for _ in range(random.randint(0, 3)):
                            i += 1
                            if i >= len(entries):
                                break
                            msg2 = entries[i].get("message", "")
                            if not msg2.startswith("[[E"):
                                continue
                            end_e2 = msg2.find("]]", 3)
                            e2 = msg2[3:end_e2]
                            s_start2 = msg2.find("[[S", end_e2)
                            end_s2 = msg2.find("]]", s_start2 + 3)
                            s2 = msg2[s_start2 + 3:end_s2]
                            prefix2 = msg2[:end_s2 + 2]
                            f2 = sum(1 for prev in entries[:i] if prev.get("message", "").startswith(prefix2))
                            state.checked_entries[f"{e2}-{s2}-{f2}"] = True
                        break
                # If all checked, discard and start new
                total = len([e for e in entries if e.get("message", "").startswith("[[E")])
                done = sum(1 for v in state.checked_entries.values() if v)
                if total > 0 and done >= total:
                    del ls.active_scenarios[vehicle.name]
                    del ls.checklist_states[vehicle.name]

        await manager.persist(ADMIN_CODE)
