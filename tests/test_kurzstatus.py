import unittest
from fastapi.testclient import TestClient
import sys
import os
import json

# Add src directory to path to allow importing main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from main import app

class TestKurzstatus(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_kurzstatus_flow(self):
        # 1. Create Leitstelle
        resp = self.client.post("/leitstelle", data={"name": "Test Leitstelle"})
        data = resp.json()
        admin_code = data["admin_code"]
        vehicle_code = data["vehicle_code"]

        # 2. Connect Leitstelle View
        with self.client.websocket_connect(f"/ws/{admin_code}?name=LEITSTELLE_VIEW") as ws_ls:
            ws_ls.receive_json() # Initial status

            # 3. Connect Car
            with self.client.websocket_connect(f"/ws/{vehicle_code}?name=Car1") as ws_car:
                ws_ls.receive_json() # Update: Car1 joined
                ws_car.receive_json() # Initial status

                # 4. Car sends Kurzstatus
                ws_car.send_text("kurzstatus:Erkundung läuft")
                
                # 5. LS receives update
                data = ws_ls.receive_json()
                car1 = next(c for c in data["connections"] if c["name"] == "Car1")
                self.assertEqual(car1["kurzstatus"], "Erkundung läuft")

                # Car also receives updated state
                data = ws_car.receive_json()
                me = next(c for c in data["connections"] if c["name"] == "Car1")
                self.assertEqual(me["kurzstatus"], "Erkundung läuft")

                # 6. LS acknowledges Kurzstatus
                resp = self.client.post(f"/api/leitstelle/{admin_code}/clear_kurzstatus", data={
                    "target_name": "Car1"
                })
                self.assertEqual(resp.status_code, 200)

                # 7. Both should see it cleared
                data = ws_ls.receive_json()
                car1 = next(c for c in data["connections"] if c["name"] == "Car1")
                self.assertIsNone(car1["kurzstatus"])

                data = ws_car.receive_json()
                me = next(c for c in data["connections"] if c["name"] == "Car1")
                self.assertIsNone(me["kurzstatus"])

if __name__ == "__main__":
    unittest.main()
