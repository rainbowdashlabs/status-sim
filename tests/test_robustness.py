import unittest
from fastapi.testclient import TestClient
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from main import app
from manager import manager


class TestPollingRobustness(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_multiple_polls_same_vehicle(self):
        """Multiple rapid polls for the same vehicle should work fine."""
        resp = self.client.post("/leitstelle", json={"name": "Test LS"})
        vehicle_code = resp.json()["vehicle_code"]

        for _ in range(5):
            data = self.client.get(f"/api/poll/{vehicle_code}", params={"name": "Car1"}).json()
            self.assertEqual(data["type"], "status_update")
            self.assertTrue(any(c["name"] == "Car1" for c in data["connections"]))

    def test_reconnect_after_inactivity(self):
        """A vehicle that stopped polling can reconnect with the same name."""
        resp = self.client.post("/leitstelle", json={"name": "Test LS"})
        admin_code = resp.json()["admin_code"]
        vehicle_code = resp.json()["vehicle_code"]

        # Initial registration
        self.client.get(f"/api/poll/{vehicle_code}", params={"name": "Car1"})

        # Simulate inactivity by setting last_update to the past
        conn = manager.find_connection(manager.leitstellen[admin_code], "Car1")
        conn.last_update = time.time() - 60

        # Should still be able to poll (reconnect)
        data = self.client.get(f"/api/poll/{vehicle_code}", params={"name": "Car1"}).json()
        self.assertEqual(data["type"], "status_update")
        me = next(c for c in data["connections"] if c["name"] == "Car1")
        self.assertTrue(me["is_online"])


if __name__ == "__main__":
    unittest.main()
