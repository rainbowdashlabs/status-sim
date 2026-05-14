import unittest
from fastapi.testclient import TestClient
import sys
import os
import time
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from main import app
from manager import manager


class TestHeartbeat(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_inactivity_removal(self):
        resp = self.client.post("/leitstelle", json={"name": "Test"})
        admin_code = resp.json()["admin_code"]
        vehicle_code = resp.json()["vehicle_code"]

        # Register via poll
        self.client.get(f"/api/poll/{vehicle_code}", params={"name": "Car1"})
        self.assertEqual(len([c for c in manager.leitstellen[admin_code].connections if not c.is_leitstelle]), 1)

        # Simulate inactivity
        for c in manager.leitstellen[admin_code].connections:
            if c.name == "Car1":
                c.last_update = time.time() - 400

        asyncio.run(manager.cleanup_inactive())

        remaining = [c for c in manager.leitstellen[admin_code].connections if c.name == "Car1"]
        self.assertEqual(len(remaining), 0)

    def test_poll_updates_timestamp(self):
        resp = self.client.post("/leitstelle", json={"name": "Test"})
        admin_code = resp.json()["admin_code"]
        vehicle_code = resp.json()["vehicle_code"]

        # Register
        self.client.get(f"/api/poll/{vehicle_code}", params={"name": "Car1"})
        conn = manager.find_connection(manager.leitstellen[admin_code], "Car1")
        initial_update = conn.last_update

        time.sleep(0.05)

        # Poll again (acts as heartbeat)
        self.client.get(f"/api/poll/{vehicle_code}", params={"name": "Car1"})
        self.assertGreater(conn.last_update, initial_update)


if __name__ == "__main__":
    unittest.main()
