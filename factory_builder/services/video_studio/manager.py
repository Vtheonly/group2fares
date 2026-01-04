import os
from pathlib import Path
from factory_builder.utils import get_logger
from .engines.blender_engine import BlenderEngine
from .engines.ai_engine import AIEngine

log = get_logger("VideoManager")

class VideoStudio:
    def __init__(self, context):
        self.ctx = context
        # Default to blender, but allows env override
        self.mode = os.getenv("VIDEO_ENGINE", "blender").lower()
        
    def produce(self):
        log.info(f"🎬 Video Studio Initialized (Mode: {self.mode})")
        
        # Inputs
        scene_path = self.ctx.final_scene_glb
        contract_path = self.ctx.shared_json
        
        # Outputs (Saved in Builder's Scene Folder)
        video_out = self.ctx.builder_scene / "cinematic.mp4"
        
        if not scene_path.exists():
            log.error(f"Cannot generate video: Scene missing at {scene_path}")
            return

        # Load Layout Metadata (to know machine order)
        import json
        with open(contract_path, "r") as f:
            contract = json.load(f)
            
        # Select Engine
        if self.mode == "ai":
            engine = AIEngine()
        else:
            engine = BlenderEngine()
            
        # Render
        result_path = engine.render(
            scene_path=scene_path,
            metadata={"layout": contract}, # Pass full contract
            output_path=video_out
        )

        if result_path and result_path.exists():
            # Copy camera metadata to Shared Data for Streamlit
            src_meta = self.ctx.builder_scene / "camera_map.json"
            dst_meta = self.ctx.shared_root / "camera_map.json"
            
            if src_meta.exists():
                import shutil
                shutil.copy(src_meta, dst_meta)
                log.info(f"📍 Camera coordinates published to: {dst_meta}")
            
            log.success(f"🎞️ Video Production Complete: {result_path}")
        else:
            log.error("Video production failed.")