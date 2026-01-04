import subprocess
import json
import os
from pathlib import Path
from factory_builder.utils import get_logger
from .base import VideoEngine

log = get_logger("BlenderEngine")

class BlenderEngine(VideoEngine):
    def render(self, scene_path: Path, metadata: dict, output_path: Path) -> Path:
        """
        Calls Blender via subprocess to execute the cinematic_render.py script.
        """
        # Define paths
        script_path = Path(__file__).parent.parent / "scripts" / "cinematic_render.py"
        
        # We need to save the metadata (Machine Order, etc.) to a temp config
        # so the Blender script can read it.
        config_payload = {
            "glb_path": str(scene_path),
            "output_video": str(output_path),
            "output_metadata": str(output_path.parent / "camera_map.json"),
            "machine_order": [m["id"] for m in metadata.get("layout", {}).get("machines", [])]
        }
        
        config_path = output_path.parent / "render_config.json"
        with open(config_path, "w") as f:
            json.dump(config_payload, f)

        log.info("🎥 Launching Blender Headless Engine...")
        
        cmd = [
            "blender",
            "-b",                 # Background mode
            "-P", str(script_path), # Run Python Script
            "--",                 # Pass args to script
            str(config_path)
        ]

        try:
            # Run Blender
            # Capture output to avoid spamming main log unless error
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            log.info("✅ Blender Render Successful")
            return output_path
            
        except subprocess.CalledProcessError as e:
            log.error(f"❌ Blender Error:\n{e.stderr}")
            return None