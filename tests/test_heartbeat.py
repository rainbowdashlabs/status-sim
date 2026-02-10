import unittest
from fastapi.testclient import TestClient
import sys
import os
import time
import asyncio

# Add src directory to path to allow importing main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from main import app
try:
    from src.manager import manager
except ImportError:
    # Fallback when sys.path points directly to src directory
    from manager import manager  # type: ignore

class TestHeartbeat(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_inactivity_removal(self):
        # 1. Create Leitstelle
        resp = self.client.post("/leitstelle", data={"name": "Test"})
        admin_code = resp.json()["admin_code"]
        vehicle_code = resp.json()["vehicle_code"]

        # 2. Connect Car
        with self.client.websocket_connect(f"/ws/{vehicle_code}?name=Car1") as ws:
            ws.receive_json() # Initial status
            
            # Verify Car1 is connected
            self.assertEqual(len(manager.leitstellen[admin_code].connections), 1)
            
            # Manually set last_update to more than 3 minutes ago
            manager.leitstellen[admin_code].connections[0].last_update = time.time() - 200
            
            # Run cleanup logic
            asyncio.run(manager.cleanup_inactive())
            
            # Verify Car1 is removed
            self.assertEqual(len(manager.leitstellen[admin_code].connections), 0)

    def test_heartbeat_updates_timestamp(self):
        resp = self.client.post("/leitstelle", data={"name": "Test"})
        admin_code = resp.json()["admin_code"]
        vehicle_code = resp.json()["vehicle_code"]

        with self.client.websocket_connect(f"/ws/{vehicle_code}?name=Car1") as ws:
            ws.receive_json()
            
            conn = manager.leitstellen[admin_code].connections[0]
            initial_update = conn.last_update
            
            # Wait a bit
            time.sleep(0.1)
            
            # Send heartbeat
            ws.send_text("heartbeat")
            
            # Give it a moment to process
            time.sleep(0.1)
            
            self.assertGreater(conn.last_update, initial_update)

if __name__ == "__main__":
    unittest.main()
