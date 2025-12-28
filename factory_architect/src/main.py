import json
import os
import sys
from loguru import logger
from src.core.config import settings
from src.models.schema import FactoryInput
from src.services.ai_engine import LayoutIntelligence, PlanerIntelligence
from src.services.dxf_engine import DXFRenderer

def main():
    logger.info("Initializing Factory Architect System...")
    
    planer = PlanerIntelligence()
    intelligence = LayoutIntelligence()
    
    try:
        # Phase 0: Planning (from project notes if available)
        main_entry_path = os.path.join(os.path.dirname(settings.INPUT_FILE), "main_entry.json")
        
        if os.path.exists(main_entry_path):
            logger.info(f"Discovery: Found project notes at {main_entry_path}. Initiating Planning...")
            with open(main_entry_path, "r") as f:
                notes = json.load(f)
            
            # Extract production line input
            factory_input = planer.generate_input_schema(notes)
            
            # Save for transparency and next run
            with open(settings.INPUT_FILE, "w") as f:
                json.dump(factory_input.model_dump(), f, indent=4)
            logger.success(f"Plan created and saved to {settings.INPUT_FILE}")
        else:
            # Traditional Ingest
            if not os.path.exists(settings.INPUT_FILE):
                logger.error("No project notes (main_entry.json) or layout input (input.json) found.")
                return
            with open(settings.INPUT_FILE, "r") as f:
                data = json.load(f)
                factory_input = FactoryInput(**data)

        # Phase 1: Layout Computation (AI)
        layout = intelligence.compute_layout(factory_input)
        
        # Phase 2: Render (CAD)
        debug_path = os.path.join(settings.OUTPUT_DIR, "debug_layout.json")
        with open(debug_path, "w") as f:
            f.write(layout.model_dump_json(indent=2))

        dxf_path = os.path.join(settings.OUTPUT_DIR, f"{factory_input.project_name}.dxf")
        renderer = DXFRenderer(dxf_path)
        renderer.render(layout)

        logger.success("Pipeline completed successfully.")

    except Exception as e:
        logger.critical(f"System Halted: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
