import unittest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from main import app


class TestScenario(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_scenario_start_and_discard(self):
        resp = self.client.post("/leitstelle", json={"name": "ScenarioTest"})
        admin_code = resp.json()["admin_code"]
        vehicle_code = resp.json()["vehicle_code"]

        # Register vehicle
        self.client.get(f"/api/poll/{vehicle_code}", params={"name": "Car1"})

        # List scenarios
        resp = self.client.get(f"/api/leitstelle/{admin_code}/scenarios")
        self.assertEqual(resp.status_code, 200)
        scenarios = resp.json()["scenarios"]
        self.assertTrue(len(scenarios) > 0)
        scenario_name = scenarios[0]["name"]

        # Start scenario
        resp = self.client.post(f"/api/leitstelle/{admin_code}/scenario/start", json={
            "target_name": "Car1", "scenario_name": scenario_name,
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "success")

        # Verify via poll
        data = self.client.get(f"/api/poll/{admin_code}").json()
        car1 = next(c for c in data["connections"] if c["name"] == "Car1")
        self.assertIsNotNone(car1["active_scenario"])
        self.assertEqual(car1["active_scenario"]["name"], scenario_name)
        self.assertIn("generated_entries", car1["active_scenario"])

        entries = car1["active_scenario"]["generated_entries"]
        self.assertTrue(any(e["message"].startswith("[[E0]][[S0]]") for e in entries))

        # Discard scenario
        resp = self.client.post(f"/api/leitstelle/{admin_code}/scenario/discard", json={"target_name": "Car1"})
        self.assertEqual(resp.status_code, 200)

        data = self.client.get(f"/api/poll/{admin_code}").json()
        car1 = next(c for c in data["connections"] if c["name"] == "Car1")
        self.assertIsNone(car1["active_scenario"])


if __name__ == "__main__":
    unittest.main()
