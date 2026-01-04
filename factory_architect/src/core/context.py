import os
from pathlib import Path
from loguru import logger

class ProjectContext:
    """
    The Single Source of Truth for Data Locations.
    Enforces the 3-Location Architecture:
    1. Architect Data (Private)
    2. Builder Data (Private)
    3. Shared Data (Public Bridge)
    """

    def __init__(self, project_name: str):
        if not project_name:
            raise ValueError("Project name cannot be empty.")

        self.project_name = project_name.strip().replace(" ", "_")
        self.root = Path("/app")

        # --- LOCATION 1: Factory Architect (Private) ---
        self.arch_root = self.root / "factory_architect/data" / self.project_name
        self.arch_input_dir = self.arch_root / "input"
        self.arch_output_dir = self.arch_root / "output"
        
        # Files
        self.source_entry_file = self.arch_input_dir / "main_entry.json"
        self.plan_json = self.arch_output_dir / "intermediate_plan.json"
        self.dxf_output = self.arch_output_dir / "architecture.dxf"
        self.debug_json = self.arch_output_dir / "debug_geometry.json"

        # --- LOCATION 2: Shared Data (Bridge) ---
        self.shared_root = self.root / "shared_data" / self.project_name
        
        # Files (The Contract)
        self.shared_json = self.shared_root / "layout_contract.json"
        self.shared_dxf = self.shared_root / "layout.dxf"

        # --- LOCATION 3: Factory Builder (Private) ---
        self.builder_root = self.root / "factory_builder/data" / self.project_name
        self.builder_images = self.builder_root / "images"
        self.builder_models = self.builder_root / "models"
        self.builder_scene = self.builder_root / "scene"
        
        # Final Output
        self.final_scene_glb = self.builder_scene / "factory_complete.glb"

    def initialize(self):
        """Creates the directory structure if it doesn't exist."""
        dirs = [
            self.arch_input_dir,
            self.arch_output_dir,
            self.shared_root,
            self.builder_images,
            self.builder_models,
            self.builder_scene
        ]
        
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
            
        logger.info(f"📁 Context initialized for Project: {self.project_name}")
        logger.info(f"   ├── Architect Input: {self.arch_input_dir}")
        logger.info(f"   ├── Shared Bridge:   {self.shared_root}")
        logger.info(f"   └── Builder Out:     {self.builder_scene}")

    def validate_input(self):
        """Ensures the project has a valid entry point."""
        if not self.source_entry_file.exists():
            # Create a template if missing to guide the user
            self.initialize()
            import json
            template = {
                "project_meta": {"name": self.project_name},
                "raw_notes": "Paste your project requirements here..."
            }
            with open(self.source_entry_file, 'w') as f:
                json.dump(template, f, indent=4)
            
            error_msg = f"❌ Input file missing at: {self.source_entry_file}. A template has been created. Please fill it and restart."
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        return True