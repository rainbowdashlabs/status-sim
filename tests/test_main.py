import unittest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from main import app


class TestLeitstelle(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def _create(self, name="Test"):
        resp = self.client.post("/leitstelle", json={"name": name})
        d = resp.json()
        return d["admin_code"], d["vehicle_code"], d["staffelfuehrer_code"]

    def _poll(self, code, name=None):
        params = {"name": name} if name else {}
        return self.client.get(f"/api/poll/{code}", params=params).json()

    def _action(self, code, name, action, value=None):
        body = {"name": name, "action": action}
        if value is not None:
            body["value"] = value
        return self.client.post(f"/api/vehicle/{code}/action", json=body)

    def test_create_leitstelle(self):
        response = self.client.post("/leitstelle", json={"name": "Test Leitstelle"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        self.assertIn("admin_code", response.json())
        self.assertIn("vehicle_code", response.json())

    def test_get_index(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"<div id=\"app\">", response.content)

    def test_poll_status_update(self):
        admin_code, vehicle_code, _ = self._create()

        # Register vehicle via poll
        data = self._poll(vehicle_code, "Car1")
        self.assertEqual(data["type"], "status_update")
        self.assertTrue(any(c["name"] == "Car1" for c in data["connections"]))

        # Change status
        self._action(vehicle_code, "Car1", "status", "3")
        data = self._poll(admin_code)
        car1 = next(c for c in data["connections"] if c["name"] == "Car1")
        self.assertEqual(car1["status"], "3")
        self.assertIsNone(car1["special"])

        # Toggle special status 5
        self._action(vehicle_code, "Car1", "status", "5")
        data = self._poll(admin_code)
        car1 = next(c for c in data["connections"] if c["name"] == "Car1")
        self.assertEqual(car1["status"], "3")
        self.assertEqual(car1["special"], "5")

        # Toggle special status 0
        self._action(vehicle_code, "Car1", "status", "0")
        data = self._poll(admin_code)
        car1 = next(c for c in data["connections"] if c["name"] == "Car1")
        self.assertEqual(car1["status"], "3")
        self.assertEqual(car1["special"], "0")

        # Change main status while special is active
        self._action(vehicle_code, "Car1", "status", "4")
        data = self._poll(admin_code)
        car1 = next(c for c in data["connections"] if c["name"] == "Car1")
        self.assertEqual(car1["status"], "4")
        self.assertEqual(car1["special"], "0")

    def test_private_message(self):
        admin_code, vehicle_code, _ = self._create()

        # Register two vehicles
        self._poll(vehicle_code, "Car1")
        self._poll(vehicle_code, "Car2")

        # Send private message to Car1
        resp = self.client.post(f"/api/leitstelle/{admin_code}/message", json={
            "message": "Hello Car1",
            "target_name": "Car1",
        })
        self.assertEqual(resp.status_code, 200)

        # Car1 should see it in poll messages
        data = self._poll(vehicle_code, "Car1")
        self.assertTrue(any(m["text"] == "Hello Car1" for m in data.get("messages", [])))

        # Car2 should NOT see it
        data = self._poll(vehicle_code, "Car2")
        self.assertFalse(any(m["text"] == "Hello Car1" for m in data.get("messages", [])))

        # Broadcast
        self.client.post(f"/api/leitstelle/{admin_code}/message", json={"message": "Broadcast"})
        data = self._poll(vehicle_code, "Car2")
        self.assertTrue(any(m["text"] == "Broadcast" for m in data.get("messages", [])))

    def test_chat_history_persists_messages(self):
        admin_code, vehicle_code, _ = self._create("Chat")

        self._poll(vehicle_code, "CarChat")

        self.client.post(f"/api/leitstelle/{admin_code}/message", json={
            "message": "Hallo",
            "target_name": "CarChat",
        })

        resp = self.client.get(f"/api/leitstelle/{admin_code}/chat_history", params={"target_name": "CarChat"})
        self.assertEqual(resp.status_code, 200)
        history = resp.json()["messages"]
        self.assertTrue(any(m["text"] == "Hallo" and m["sender"] == "LS" for m in history))

    def test_get_leitstelle_view_not_found(self):
        response = self.client.get("/leitstelle/NONEXISTENT", follow_redirects=False)
        self.assertIn(response.status_code, (302, 303, 307, 308))

    def test_get_status_page_not_found(self):
        response = self.client.get("/status?code=NONEXISTENT&name=Test", follow_redirects=False)
        self.assertIn(response.status_code, (302, 303, 307, 308))

    def test_clear_special_status(self):
        admin_code, vehicle_code, _ = self._create()

        self._poll(vehicle_code, "Car1")

        # Set special status
        self._action(vehicle_code, "Car1", "status", "5")
        data = self._poll(admin_code)
        car1 = next(c for c in data["connections"] if c["name"] == "Car1")
        self.assertEqual(car1["special"], "5")

        # Clear special
        resp = self.client.post(f"/api/leitstelle/{admin_code}/clear_special", json={"target_name": "Car1"})
        self.assertEqual(resp.status_code, 200)

        data = self._poll(admin_code)
        car1 = next(c for c in data["connections"] if c["name"] == "Car1")
        self.assertIsNone(car1["special"])


if __name__ == "__main__":
    unittest.main()
