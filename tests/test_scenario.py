import unittest
from fastapi.testclient import TestClient
import sys
import os

# Add src directory to path to allow importing main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from main import app

class TestScenario(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_scenario_start_and_discard(self):
        # 1. Create a leitstelle
        resp = self.client.post("/leitstelle", json={"name": "ScenarioTest"})
        admin_code = resp.json()["admin_code"]
        vehicle_code = resp.json()["vehicle_code"]

        # 2. Connect a Car
        with self.client.websocket_connect(f"/ws/{vehicle_code}?name=Car1") as ws_car:
            ws_car.receive_json() # Initial status
            
            # 3. List scenarios
            resp = self.client.get(f"/api/leitstelle/{admin_code}/scenarios")
            self.assertEqual(resp.status_code, 200)
            scenarios = resp.json()["scenarios"]
            self.assertTrue(len(scenarios) > 0)
            scenario_name = scenarios[0]["name"]

            # 4. Start scenario
            resp = self.client.post(f"/api/leitstelle/{admin_code}/scenario/start", json={
                "target_name": "Car1",
                "scenario_name": scenario_name
            })
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json()["status"], "success")

            # 5. Verify via WebSocket
            data = ws_car.receive_json()
            self.assertEqual(data["type"], "status_update")
            car1 = next(c for c in data["connections"] if c["name"] == "Car1")
            self.assertIsNotNone(car1["active_scenario"])
            self.assertEqual(car1["active_scenario"]["name"], scenario_name)
            self.assertIn("generated_entries", car1["active_scenario"])
            
            # Check for our prefix [[E0]][[S0]]
            entries = car1["active_scenario"]["generated_entries"]
            # Die Schlüssel im dict sind englisch (actor, message), 
            # aber im generierten ScenarioData (model_dump) hängen sie vom Modell ab.
            # FunkEntry hat 'actor' und 'message'.
            self.assertTrue(any(e["message"].startswith("[[E0]][[S0]]") for e in entries))

            # 6. Discard scenario
            resp = self.client.post(f"/api/leitstelle/{admin_code}/scenario/discard", json={
                "target_name": "Car1"
            })
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json()["status"], "success")

            # 7. Verify discard via WebSocket
            data = ws_car.receive_json()
            car1 = next(c for c in data["connections"] if c["name"] == "Car1")
            self.assertIsNone(car1["active_scenario"])

if __name__ == "__main__":
    unittest.main()
