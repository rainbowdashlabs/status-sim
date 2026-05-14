import unittest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from main import app


class TestScenarioSync(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_checklist_state_sync(self):
        resp = self.client.post("/leitstelle", json={"name": "SyncTest"})
        admin_code = resp.json()["admin_code"]
        vehicle_code = resp.json()["vehicle_code"]
        sf_code = resp.json()["staffelfuehrer_code"]

        # Register vehicle
        self.client.get(f"/api/poll/{vehicle_code}", params={"name": "Car1"})

        # Start scenario
        resp = self.client.get(f"/api/leitstelle/{admin_code}/scenarios")
        scenario_name = resp.json()["scenarios"][0]["name"]

        self.client.post(f"/api/leitstelle/{admin_code}/scenario/start", json={
            "target_name": "Car1", "scenario_name": scenario_name,
        })

        # Verify initial state
        data = self.client.get(f"/api/poll/{admin_code}").json()
        car1 = next(c for c in data["connections"] if c["name"] == "Car1")
        self.assertIsNotNone(car1["checklist_state"])

        # Update state from LS
        new_state = {
            "expanded_einsaetze": {},
            "expanded_schritte": {},
            "checked_entries": {"0-0-0": True},
        }
        resp = self.client.post(f"/api/leitstelle/{admin_code}/scenario/update_state", json={
            "target_name": "Car1", "state": new_state,
        })
        self.assertEqual(resp.status_code, 200)

        data = self.client.get(f"/api/poll/{admin_code}").json()
        car1 = next(c for c in data["connections"] if c["name"] == "Car1")
        self.assertEqual(car1["checklist_state"]["checked_entries"], {"0-0-0": True})

        # Update state from SF (using SF code)
        new_state_2 = {
            "expanded_einsaetze": {},
            "expanded_schritte": {},
            "checked_entries": {"0-0-0": True, "0-0-1": True},
        }
        resp = self.client.post(f"/api/leitstelle/{sf_code}/scenario/update_state", json={
            "target_name": "Car1", "state": new_state_2,
        })
        self.assertEqual(resp.status_code, 200)

        data = self.client.get(f"/api/poll/{admin_code}").json()
        car1 = next(c for c in data["connections"] if c["name"] == "Car1")
        self.assertTrue(car1["checklist_state"]["checked_entries"]["0-0-1"])
        self.assertEqual(car1["checklist_state"]["expanded_einsaetze"], {})


if __name__ == "__main__":
    unittest.main()
