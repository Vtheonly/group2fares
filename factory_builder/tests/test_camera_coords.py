
import sys
import os
from pathlib import Path
import unittest
from unittest.mock import MagicMock

# Setup path to import factory_builder
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "factory_builder"))

from factory_builder.services.scene_composer import SceneComposer

class TestCameraCoords(unittest.TestCase):
    def test_compute_coords(self):
        composer = SceneComposer()
        
        # Mock bounding box for a 2000x2000x2000 machine at origin
        # Center: 0,0,1000. Size: 2000,2000,2000
        bbox_info = {
            'center': [0.0, 0.0, 1000.0],
            'size': [2000.0, 2000.0, 2000.0]
        }
        
        composer._compute_camera_coords("TestMachine", bbox_info)
        
        result = composer.camera_data.get("TestMachine")
        self.assertIsNotNone(result)
        
        # Verify Target (should match center)
        self.assertAlmostEqual(result['target']['x'], 0.0)
        self.assertAlmostEqual(result['target']['y'], 0.0)
        self.assertAlmostEqual(result['target']['z'], 1000.0)
        
        # Verify Position (should be center + zoom_dist)
        # Max dim is 2000. Zoom dist is 2000 * 2.5 = 5000
        # Position should be 0+5000, 0+5000, 1000+5000 -> 5000, 5000, 6000
        self.assertAlmostEqual(result['position']['x'], 5000.0)
        self.assertAlmostEqual(result['position']['y'], 5000.0)
        self.assertAlmostEqual(result['position']['z'], 6000.0)
        
        print("Camera Coords Test Passed!")
        print(f"Computed: {result}")

if __name__ == '__main__':
    unittest.main()
