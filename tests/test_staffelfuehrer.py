import unittest
from fastapi.testclient import TestClient
import sys
import os
import json
import time

# Add src directory to path to allow importing main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from main import app

class TestStaffelfuehrer(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_staffelfuehrer_flow(self):
        # 1. Create Leitstelle
        resp = self.client.post("/leitstelle", data={"name": "Test Leitstelle"})
        data = resp.json()
        admin_code = data["admin_code"]
        vehicle_code = data["vehicle_code"]
        sf_code = data["staffelfuehrer_code"]

        # 2. Connect Car
        with self.client.websocket_connect(f"/ws/{vehicle_code}?name=Car1") as ws_car:
            ws_car.receive_json() # Initial status

            # 3. Connect Staffelführer
            with self.client.websocket_connect(f"/ws/{sf_code}?name=SF1") as ws_sf:
                ws_car.receive_json() # Car1 receives update that SF1 joined
                data = ws_sf.receive_json() # Initial status (includes Car1)
                
                # Verify that SF1 has is_staffelfuehrer=True and Car1 has is_staffelfuehrer=False
                self.assertTrue(any(c["name"] == "SF1" and c["is_staffelfuehrer"] for c in data["connections"]))
                self.assertTrue(any(c["name"] == "Car1" and not c["is_staffelfuehrer"] for c in data["connections"]))

                # 4. SF sends notice to Car1
                resp = self.client.post(f"/api/staffelfuehrer/{sf_code}/notice", data={
                    "target_name": "Car1",
                    "text": "Anfordern"
                })
                self.assertEqual(resp.status_code, 200)

                # 5. Car1 should receive the notice in status update
                data = ws_car.receive_json()
                self.assertIn("notices", data)
                self.assertIn("Car1", data["notices"])
                self.assertEqual(data["notices"]["Car1"]["status"], "pending")

                # SF should also see it
                data = ws_sf.receive_json()
                self.assertEqual(data["notices"]["Car1"]["status"], "pending")

                # 6. Car1 confirms notice
                ws_car.send_text("confirm_notice")

                # 7. SF should see confirmation
                data = ws_sf.receive_json()
                self.assertEqual(data["notices"]["Car1"]["status"], "confirmed")
                
                # Car1 also sees it updated (though UI might hide it)
                data = ws_car.receive_json()
                self.assertEqual(data["notices"]["Car1"]["status"], "confirmed")

                # 8. SF acknowledges (clears) the notice
                resp = self.client.post(f"/api/staffelfuehrer/{sf_code}/acknowledge", data={
                    "target_name": "Car1"
                })
                self.assertEqual(resp.status_code, 200)

                # 9. Notice should be gone
                data = ws_sf.receive_json()
                self.assertNotIn("Car1", data["notices"])
                
                data = ws_car.receive_json()
                self.assertNotIn("Car1", data["notices"])

    def test_notes_sync(self):
        # 1. Create Leitstelle
        resp = self.client.post("/leitstelle", data={"name": "Test Notes"})
        data = resp.json()
        admin_code = data["admin_code"]
        vehicle_code = data["vehicle_code"]
        sf_code = data["staffelfuehrer_code"]

        # 2. Connect Car
        with self.client.websocket_connect(f"/ws/{vehicle_code}?name=CarNote") as ws_car:
            ws_car.receive_json()

            # 3. Connect Leitstelle view
            with self.client.websocket_connect(f"/ws/{admin_code}?name=LEITSTELLE_VIEW") as ws_ls:
                ws_ls.receive_json()

                # 4. Update Note from LS
                resp = self.client.post(f"/api/leitstelle/{admin_code}/update_note", data={
                    "target_name": "CarNote",
                    "note": "LS Note"
                })
                self.assertEqual(resp.status_code, 200)

                # 5. LS should receive update with note
                data = ws_ls.receive_json()
                car = next(c for c in data["connections"] if c["name"] == "CarNote")
                self.assertEqual(car["note"], "LS Note")

                # 6. Update Note from SF
                resp = self.client.post(f"/api/leitstelle/{sf_code}/update_note", data={
                    "target_name": "CarNote",
                    "note": "SF Overwrite"
                })
                self.assertEqual(resp.status_code, 200)

                # 7. LS should receive update with new note
                data = ws_ls.receive_json()
                car = next(c for c in data["connections"] if c["name"] == "CarNote")
                self.assertEqual(car["note"], "SF Overwrite")

if __name__ == "__main__":
    unittest.main()
