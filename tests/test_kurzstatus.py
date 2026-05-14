import unittest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from main import app


class TestKurzstatus(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_kurzstatus_flow(self):
        resp = self.client.post("/leitstelle", json={"name": "Test Leitstelle"})
        data = resp.json()
        admin_code = data["admin_code"]
        vehicle_code = data["vehicle_code"]

        # Register vehicle
        self.client.get(f"/api/poll/{vehicle_code}", params={"name": "Car1"})

        # Car sends kurzstatus
        self.client.post(f"/api/vehicle/{vehicle_code}/action", json={
            "name": "Car1", "action": "kurzstatus", "value": "Erkundung läuft",
        })

        # LS sees it
        data = self.client.get(f"/api/poll/{admin_code}").json()
        car1 = next(c for c in data["connections"] if c["name"] == "Car1")
        self.assertEqual(car1["kurzstatus"], "Erkundung läuft")

        # Car also sees it
        data = self.client.get(f"/api/poll/{vehicle_code}", params={"name": "Car1"}).json()
        me = next(c for c in data["connections"] if c["name"] == "Car1")
        self.assertEqual(me["kurzstatus"], "Erkundung läuft")

        # LS clears kurzstatus
        resp = self.client.post(f"/api/leitstelle/{admin_code}/clear_kurzstatus", json={"target_name": "Car1"})
        self.assertEqual(resp.status_code, 200)

        # Both see it cleared
        data = self.client.get(f"/api/poll/{admin_code}").json()
        car1 = next(c for c in data["connections"] if c["name"] == "Car1")
        self.assertIsNone(car1["kurzstatus"])


if __name__ == "__main__":
    unittest.main()
