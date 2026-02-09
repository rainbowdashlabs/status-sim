import unittest
from fastapi.testclient import TestClient
import sys
import os

# Add src directory to path to allow importing main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from main import app

class TestLeitstelle(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_create_leitstelle_form(self):
        response = self.client.post("/leitstelle", data={"name": "Test Leitstelle"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        self.assertIn("admin_code", response.json())
        self.assertIn("vehicle_code", response.json())

    def test_get_index(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Leitstelle Simulator".encode("utf-8"), response.content)

    def test_websocket_status_update(self):
        # Create a leitstelle
        resp = self.client.post("/leitstelle", data={"name": "Test"})
        admin_code = resp.json()["admin_code"]
        vehicle_code = resp.json()["vehicle_code"]

        # 1. Connect Leitstelle View
        with self.client.websocket_connect(f"/ws/{admin_code}?name=LEITSTELLE_VIEW") as ws_ls:
            # LS View receives initial state (itself)
            data = ws_ls.receive_json()
            self.assertEqual(data["type"], "status_update")
            
            # 2. Connect a Car
            with self.client.websocket_connect(f"/ws/{vehicle_code}?name=Car1") as ws_car:
                # LS View should receive an update about Car1
                data = ws_ls.receive_json()
                self.assertEqual(data["type"], "status_update")
                cars = [c for c in data["connections"] if c["name"] != "LEITSTELLE_VIEW"]
                self.assertTrue(any(c["name"] == "Car1" for c in cars))

                # Car1 receives initial state
                data = ws_car.receive_json()
                self.assertEqual(data["type"], "status_update")

                # 3. Update status from Car
                ws_car.send_text("status:3")
                
                # LS View receives update
                data = ws_ls.receive_json()
                self.assertEqual(data["type"], "status_update")
                car1 = next(c for c in data["connections"] if c["name"] == "Car1")
                self.assertEqual(car1["status"], "3")
                self.assertIsNone(car1["special"])
                self.assertIn("last_update", car1)
                self.assertIsInstance(car1["last_update"], (int, float))

                # 4. Toggle special status 5
                ws_car.send_text("status:5")
                data = ws_ls.receive_json()
                car1 = next(c for c in data["connections"] if c["name"] == "Car1")
                self.assertEqual(car1["status"], "3") # Main status remains 3
                self.assertEqual(car1["special"], "5")

                # 5. Toggle special status 0 (exclusive)
                ws_car.send_text("status:0")
                data = ws_ls.receive_json()
                car1 = next(c for c in data["connections"] if c["name"] == "Car1")
                self.assertEqual(car1["status"], "3")
                self.assertEqual(car1["special"], "0")

                # 6. Change main status while special is active
                ws_car.send_text("status:4")
                data = ws_ls.receive_json()
                car1 = next(c for c in data["connections"] if c["name"] == "Car1")
                self.assertEqual(car1["status"], "4")
                self.assertEqual(car1["special"], "0")

    def test_private_message(self):
        # Create a leitstelle
        resp = self.client.post("/leitstelle", data={"name": "Test"})
        admin_code = resp.json()["admin_code"]
        vehicle_code = resp.json()["vehicle_code"]

        with self.client.websocket_connect(f"/ws/{vehicle_code}?name=Car1") as ws_car1:
            ws_car1.receive_json() # Initial status
            
            with self.client.websocket_connect(f"/ws/{vehicle_code}?name=Car2") as ws_car2:
                ws_car1.receive_json() # Car1 receives update that Car2 joined
                ws_car2.receive_json() # Car2 receives initial status
                
                # Send private message to Car1
                resp = self.client.post(f"/api/leitstelle/{admin_code}/message", data={
                    "message": "Hello Car1",
                    "target_name": "Car1"
                })
                self.assertEqual(resp.status_code, 200)
                
                # Car1 should receive it
                msg1 = ws_car1.receive_text()
                self.assertEqual(msg1, "LS: Hello Car1")
                
                # Car2 should NOT receive it
                self.client.post(f"/api/leitstelle/{admin_code}/message", data={"message": "Broadcast"})
                msg2 = ws_car2.receive_text()
                self.assertEqual(msg2, "LS: Broadcast")

    def test_get_leitstelle_view_not_found(self):
        response = self.client.get("/leitstelle/NONEXISTENT", follow_redirects=False)
        # Expect redirect to start page
        self.assertIn(response.status_code, (302, 303, 307, 308))
        self.assertTrue(response.headers.get("location", "").endswith("/"))

    def test_get_status_page_not_found(self):
        response = self.client.get("/status?code=NONEXISTENT&name=Test", follow_redirects=False)
        # Expect redirect to start page
        self.assertIn(response.status_code, (302, 303, 307, 308))
        self.assertTrue(response.headers.get("location", "").endswith("/"))

    def test_clear_special_status(self):
        # Create a leitstelle
        resp = self.client.post("/leitstelle", data={"name": "Test"})
        admin_code = resp.json()["admin_code"]
        vehicle_code = resp.json()["vehicle_code"]

        # Connect LS and Car
        with self.client.websocket_connect(f"/ws/{admin_code}?name=LEITSTELLE_VIEW") as ws_ls:
            ws_ls.receive_json() # Initial status
            
            with self.client.websocket_connect(f"/ws/{vehicle_code}?name=Car1") as ws_car:
                ws_ls.receive_json() # Car1 joined
                ws_car.receive_json() # Initial status
                
                # Set special status from car
                ws_car.send_text("status:5")
                data = ws_ls.receive_json()
                car1 = next(c for c in data["connections"] if c["name"] == "Car1")
                self.assertEqual(car1["special"], "5")
                
                # Clear special status from LS (via API)
                resp = self.client.post(f"/api/leitstelle/{admin_code}/clear_special", data={
                    "target_name": "Car1"
                })
                self.assertEqual(resp.status_code, 200)
                self.assertEqual(resp.json()["status"], "success")
                
                # Verify broadcast
                data = ws_ls.receive_json()
                # Skip the previous "status:5" broadcast if it's still in the buffer
                if data.get("connections") and any(c["name"] == "Car1" and c["special"] == "5" for c in data["connections"]):
                     data = ws_ls.receive_json()
                
                car1 = next(c for c in data["connections"] if c["name"] == "Car1")
                self.assertIsNone(car1["special"])
                
                # Verify Car also receives it
                data = ws_car.receive_json()
                # Same for car
                if data.get("connections") and any(c["name"] == "Car1" and c["special"] == "5" for c in data["connections"]):
                    data = ws_car.receive_json()
                
                self.assertEqual(data["type"], "status_update")
                me = next(c for c in data["connections"] if c["name"] == "Car1")
                self.assertIsNone(me["special"])

if __name__ == "__main__":
    unittest.main()
