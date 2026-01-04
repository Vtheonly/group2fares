import json
import shutil
from pathlib import Path
from loguru import logger

# Services
from factory_builder.services.web_scraper import ImageScraper
from factory_builder.services.cloud_client import CloudRenderer
from factory_builder.services.scene_composer import SceneComposer
from factory_builder.services.dxf_parser import DxfParser
from factory_builder.utils import sanitize_filename, get_logger

# Initialize main logger
log = get_logger("BuilderMain")

class FactoryBuilder:
    def __init__(self, context):
        """
        :param context: Instance of src.core.context.ProjectContext
        """
        self.ctx = context
        
        # Define the strict root for builder data based on context
        # Structure: factory_builder/data/<project_name>/
        self.project_root = self.ctx.builder_root 
        self.machines_dir = self.project_root / "machines"
        self.scene_dir = self.project_root / "scene"

    def execute(self):
        log.info("="*60)
        log.info(f"🔨 FACTORY BUILDER STARTED: {self.ctx.project_name}")
        log.info("="*60)
        
        # 1. VERIFY HANDOVER (Shared Bridge)
        if not self.ctx.shared_json.exists():
            log.error(f"❌ Contract file missing: {self.ctx.shared_json}")
            return
        if not self.ctx.shared_dxf.exists():
            log.error(f"❌ DXF Layout missing: {self.ctx.shared_dxf}")
            return

        # 2. PARSE DXF
        # We rely on the DXF for the "Truth" of geometry
        layout = DxfParser().parse(str(self.ctx.shared_dxf))
        log.info(f"📋 Layout loaded: {len(layout.entities)} entities")

        # 3. ASSET PIPELINE (Images & Models)
        self._process_assets(layout)


        # 4. SCENE CONSTRUCTION
        log.info("🏗️  Assembling Final Scene...")
        self.scene_dir.mkdir(parents=True, exist_ok=True)
        final_scene_path = self.ctx.final_scene_glb
        
        composer = SceneComposer()
        success = composer.build(layout, str(final_scene_path))
        
        if success:
            log.success(f"🎉 BUILD COMPLETE")
            
            # 5. VIDEO PRODUCTION (New Step)
            log.info("🎥 Starting Video Production Phase...")
            studio = VideoStudio(self.ctx)
            studio.produce()
            
        else:
            log.error("❌ Scene composition failed.")        
        

    def _process_assets(self, layout):
        """
        Iterates through machines, creating folders and generating assets.
        """
        scraper = ImageScraper()
        renderer = CloudRenderer()

        machines = [e for e in layout.entities if e.type == "MACHINE"]
        total = len(machines)

        log.info(f"🎨 Starting Asset Pipeline for {total} machines...")

        for idx, machine in enumerate(machines, 1):
            log.info(f"🔹 [{idx}/{total}] Machine: {machine.name}")

            # A. Create Unique Folder for this Machine
            # Path: factory_builder/data/<project>/machines/<Safe_Name>/
            safe_name = sanitize_filename(machine.name)
            machine_folder = self.machines_dir / safe_name
            machine_folder.mkdir(parents=True, exist_ok=True)

            # Define specific file paths for this machine
            img_path = machine_folder / "reference_image.png"
            model_path = machine_folder / "3d_model.glb"

            # B. Scrape Image (If missing)
            if not img_path.exists():
                log.info(f"     📷 Scraping reference image...")
                success = scraper.find_and_save(machine.name, img_path)
                if success:
                    log.info("     ✅ Image saved.")
                    machine.image_path = str(img_path)
                else:
                    log.warning(f"     ⚠️ Image scrape failed.")
            else:
                log.info("     ✅ Image already exists.")
                machine.image_path = str(img_path)

            # C. Generate 3D Model (If missing and image exists)
            if not model_path.exists():
                if machine.image_path:
                    log.info(f"     🧠 Generating 3D Model (Cloud GPU)...")
                    success = renderer.generate(machine.image_path, model_path)
                    if success:
                        machine.model_path = str(model_path)
                else:
                    log.warning("     ⚠️ Skipping 3D gen (no image).")
            else:
                log.info("     ✅ 3D Model already exists.")
                machine.model_path = str(model_path)

            # D. Ensure Composer knows the path (even if cached)
            if model_path.exists():
                machine.model_path = str(model_path)