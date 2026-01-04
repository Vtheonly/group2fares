import json
import random
import time
from pathlib import Path

class DataLoader:
    @staticmethod
    def load_contract(path: Path) -> dict:
        with open(path, 'r') as f:
            return json.load(f)

    @staticmethod
    def load_camera_map(path: Path) -> dict:
        if not path.exists():
            return {}
        with open(path, 'r') as f:
            return json.load(f)

    @staticmethod
    def generate_telemetry(machines: list) -> dict:
        """Simulates live data for the dashboard."""
        data = {}
        for m in machines:
            # Deterministic ID check
            m_id = m.get('id', m.get('name'))
            
            # Simulate status
            status = "RUNNING" if random.random() > 0.1 else "IDLE"
            if random.random() > 0.98: status = "MAINTENANCE"
            
            data[m_id] = {
                "status": status,
                "temperature": round(random.uniform(40, 85), 1),
                "vibration": round(random.uniform(0.1, 2.5), 2),
                "power": round(random.uniform(10, 50), 1),
                "efficiency": int(random.uniform(70, 99))
            }
        return data