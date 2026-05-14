import time
from typing import Dict, Optional, Tuple

from models import LeitstelleData, Connection, VehicleStatus, StatusUpdate  # type: ignore
from logging_conf import get_logger  # type: ignore

logger = get_logger("manager")

ONLINE_TIMEOUT = 15
CLEANUP_TIMEOUT = 300

REDIS_KEY_PREFIX = "ls:"


class ConnectionManager:
    def __init__(self):
        self.leitstellen: Dict[str, LeitstelleData] = {}
        self.code_to_admin: Dict[str, str] = {}
        self._redis = None

    # ------------------------------------------------------------------
    # Redis persistence
    # ------------------------------------------------------------------

    async def init_redis(self, redis_url: str):
        import redis.asyncio as aioredis
        try:
            self._redis = aioredis.from_url(redis_url, decode_responses=True)
            await self._redis.ping()
            logger.info(f"Connected to Redis at {redis_url}")
            await self._load_all()
        except Exception as e:
            logger.error(f"Redis unavailable ({e}), running in-memory only")
            self._redis = None

    async def _load_all(self):
        if not self._redis:
            return
        cursor = 0
        while True:
            cursor, keys = await self._redis.scan(cursor=cursor, match=f"{REDIS_KEY_PREFIX}*", count=100)
            for key in keys:
                try:
                    data = await self._redis.get(key)
                    if not data:
                        continue
                    admin_code = key.removeprefix(REDIS_KEY_PREFIX) if isinstance(key, str) else key.decode().removeprefix(REDIS_KEY_PREFIX)
                    ls = LeitstelleData.model_validate_json(data)
                    self.leitstellen[admin_code] = ls
                    self.code_to_admin[ls.vehicle_code] = admin_code
                    self.code_to_admin[ls.staffelfuehrer_code] = admin_code
                except Exception as e:
                    logger.error(f"Failed to load {key} from Redis: {e}")
            if cursor == 0:
                break
        if self.leitstellen:
            logger.info(f"Restored {len(self.leitstellen)} leitstelle(n) from Redis")

    async def persist(self, admin_code: str):
        if not self._redis:
            return
        try:
            ls = self.leitstellen.get(admin_code)
            if ls:
                await self._redis.set(
                    f"{REDIS_KEY_PREFIX}{admin_code}",
                    ls.model_dump_json(exclude={"scenarios"}),
                )
            else:
                await self._redis.delete(f"{REDIS_KEY_PREFIX}{admin_code}")
        except Exception as e:
            logger.error(f"Failed to persist {admin_code}: {e}")

    async def close(self):
        if self._redis:
            await self._redis.aclose()

    # ------------------------------------------------------------------
    # Lookups
    # ------------------------------------------------------------------

    def resolve_admin_code(self, code: str) -> Optional[str]:
        upper = code.upper()
        if upper in self.leitstellen:
            return upper
        return self.code_to_admin.get(upper)

    def get_leitstelle(self, code: str) -> Optional[Tuple[str, LeitstelleData]]:
        admin_code = self.resolve_admin_code(code)
        if not admin_code:
            return None
        return admin_code, self.leitstellen[admin_code]

    def find_connection(self, ls: LeitstelleData, name: str) -> Optional[Connection]:
        return next((c for c in ls.connections if c.name == name), None)

    def is_online(self, connection: Connection) -> bool:
        return (time.time() - connection.last_update) < ONLINE_TIMEOUT

    # ------------------------------------------------------------------
    # Status building
    # ------------------------------------------------------------------

    def build_status_update(self, admin_code: str) -> Optional[StatusUpdate]:
        if admin_code not in self.leitstellen:
            return None

        ls = self.leitstellen[admin_code]
        now = time.time()
        vehicles = []

        # Build lookup for LS/SF channels by operator name
        ls_channels = {c.name: c.radio_channel for c in ls.connections if c.is_leitstelle and c.radio_channel}
        sf_channels = {c.name: c.radio_channel for c in ls.connections if c.is_staffelfuehrer and c.radio_channel}

        for c in ls.connections:
            if c.is_staffelfuehrer or c.is_leitstelle:
                continue

            vehicles.append(VehicleStatus(
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
                is_online=(now - c.last_update) < ONLINE_TIMEOUT,
                talking_to_sf=c.talking_to_sf,
                talking_to_sf_since=c.talking_to_sf_since,
                radio_channel=c.radio_channel,
                claimed_by=c.claimed_by,
                ls_claimed_by=c.ls_claimed_by,
                ls_radio_channel=ls_channels.get(c.ls_claimed_by or ""),
                sf_radio_channel=sf_channels.get(c.claimed_by or ""),
                active_scenario=ls.active_scenarios.get(c.name),
                checklist_state=ls.checklist_states.get(c.name),
                next_todo=self._compute_next_todo(ls, c.name),
                last_activity=c.last_activity,
            ))

        return StatusUpdate(connections=vehicles, notices=ls.notices)

    def _compute_next_todo(self, ls: LeitstelleData, vehicle_name: str) -> Optional[str]:
        active_scen = ls.active_scenarios.get(vehicle_name)
        checklist = ls.checklist_states.get(vehicle_name)
        if not active_scen or not checklist:
            return None

        entries = active_scen.get("generated_entries", [])
        checked = checklist.checked_entries

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
            if not checked.get(key):
                actor = entry.get("actor")
                if actor in ("LS", "SF"):
                    return actor
                break

        return None

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    async def cleanup_inactive(self):
        now = time.time()
        for admin_code in list(self.leitstellen.keys()):
            ls = self.leitstellen[admin_code]
            original = len(ls.connections)

            ls.connections = [c for c in ls.connections if (now - c.last_update) < CLEANUP_TIMEOUT]

            removed = original - len(ls.connections)
            if removed:
                logger.info(f"Cleaned up {removed} inactive connections in {admin_code}")
                active_names = {c.name for c in ls.connections}
                ls.notices = {n: v for n, v in ls.notices.items() if n in active_names}
                await self.persist(admin_code)


manager = ConnectionManager()
