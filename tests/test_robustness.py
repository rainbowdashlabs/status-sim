import unittest
from fastapi.testclient import TestClient
import sys
import os
import time

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from main import app

class TestWebSocketRobustness(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_leitstelle_view_refresh_race_condition(self):
        """Simulate quick refreshes of the Leitstelle View."""
        resp = self.client.post("/leitstelle", data={"name": "Test LS"})
        admin_code = resp.json()["admin_code"]
        
        # In a real browser, the old WS might still be closing when the new one opens.
        # However, TestClient is synchronous in its websocket_connect.
        # We can simulate multiple concurrent "LEITSTELLE_VIEW" connections
        # if the server allows it.
        
        # First connection
        with self.client.websocket_connect(f"/ws/{admin_code}?name=LS_VIEW_1") as ws1:
            data1 = ws1.receive_json()
            self.assertEqual(data1["type"], "status_update")
            
            # Second connection (simulating another tab or a refresh where old one isn't gone)
            with self.client.websocket_connect(f"/ws/{admin_code}?name=LS_VIEW_2") as ws2:
                data2 = ws2.receive_json()
                self.assertEqual(data2["type"], "status_update")
                
                # ws1 should still be active and receive update about ws2
                data1_update = ws1.receive_json()
                self.assertEqual(data1_update["type"], "status_update")
                names = [c["name"] for c in data1_update["connections"]]
                # LS_VIEW names are excluded in the JS, but they ARE in the broadcast
                # Wait, does the manager include them?
                # manager.py line 28: is_online=c.ws is not None
                # api.py line 96: connections.filter(c => c.name !== 'LEITSTELLE_VIEW' && !c.is_staffelfuehrer);
                
                # Check if both are in connections
                self.assertTrue(any(c["name"] == "LS_VIEW_1" for c in data1_update["connections"]))
                self.assertTrue(any(c["name"] == "LS_VIEW_2" for c in data1_update["connections"]))

    def test_name_taken_grace_period(self):
        """Test that a recently disconnected name can be taken over if it was very recent."""
        resp = self.client.post("/leitstelle", data={"name": "Test LS"})
        vehicle_code = resp.json()["vehicle_code"]
        
        # 1. Connect a car
        with self.client.websocket_connect(f"/ws/{vehicle_code}?name=Car1") as ws1:
            ws1.receive_json()
            # ws1 is active
        
        # Now ws1 is closed (but connection object might still be in manager with ws=None)
        # Try to reconnect immediately with same name
        with self.client.websocket_connect(f"/ws/{vehicle_code}?name=Car1") as ws2:
            data = ws2.receive_json()
            self.assertEqual(data["type"], "status_update")
            me = next(c for c in data["connections"] if c["name"] == "Car1")
            self.assertTrue(me["is_online"])

if __name__ == "__main__":
    unittest.main()
