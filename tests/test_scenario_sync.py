import unittest
from fastapi.testclient import TestClient
import sys
import os
import json

# Add src directory to path to allow importing main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from main import app

class TestScenarioSync(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_checklist_state_sync(self):
        # 1. Create a leitstelle
        resp = self.client.post("/leitstelle", json={"name": "SyncTest"})
        admin_code = resp.json()["admin_code"]
        vehicle_code = resp.json()["vehicle_code"]
        sf_code = resp.json()["staffelfuehrer_code"]

        # 2. Connect a Car
        with self.client.websocket_connect(f"/ws/{vehicle_code}?name=Car1") as ws_car:
            ws_car.receive_json() # Initial status
            
            # 3. Start scenario
            # First get scenario name
            resp = self.client.get(f"/api/leitstelle/{admin_code}/scenarios")
            scenario_name = resp.json()["scenarios"][0]["name"]
            
            self.client.post(f"/api/leitstelle/{admin_code}/scenario/start", json={
                "target_name": "Car1",
                "scenario_name": scenario_name
            })
            
            # Car receives update with scenario and empty state
            data = ws_car.receive_json()
            self.assertIsNotNone(data["connections"][0]["checklist_state"])
            
            # 4. Update state (mocked by API call - only checked_entries should matter now)
            new_state = {
                "expanded_einsaetze": {},
                "expanded_schritte": {},
                "checked_entries": {"0-0-0": True}
            }
            
            resp = self.client.post(f"/api/leitstelle/{admin_code}/scenario/update_state", json={
                "target_name": "Car1",
                "state": new_state
            })
            self.assertEqual(resp.status_code, 200)
            
            # 5. Verify Car receives updated state via WebSocket
            data = ws_car.receive_json()
            synced_state = data["connections"][0]["checklist_state"]
            self.assertEqual(synced_state["checked_entries"], {"0-0-0": True})

            # 6. Update state from Staffelführer (mocked by API call)
            # Staffelführer uses its own code, which should also work for this endpoint as it's an admin-like endpoint
            new_state_2 = {
                "expanded_einsaetze": {},
                "expanded_schritte": {},
                "checked_entries": {"0-0-0": True, "0-0-1": True}
            }
            
            resp = self.client.post(f"/api/leitstelle/{sf_code}/scenario/update_state", json={
                "target_name": "Car1",
                "state": new_state_2
            })
            self.assertEqual(resp.status_code, 200)
            
            # 7. Verify Car receives updated state
            data = ws_car.receive_json()
            synced_state_2 = data["connections"][0]["checklist_state"]
            self.assertEqual(synced_state_2["checked_entries"]["0-0-1"], True)
            # Expansion states should be empty as we don't sync them anymore
            self.assertEqual(synced_state_2["expanded_einsaetze"], {})
            self.assertEqual(synced_state_2["expanded_schritte"], {})

if __name__ == "__main__":
    unittest.main()
