import json
import os
from loguru import logger
from src.core.config import settings
from src.models.schema import FactoryInput
from src.services.ai_engine import LayoutIntelligence
from src.services.dxf_engine import DXFRenderer

def load_input() -> FactoryInput:
    if not os.path.exists(settings.INPUT_FILE):
        raise FileNotFoundError(f"Input file not found at {settings.INPUT_FILE}")
    
    with open(settings.INPUT_FILE, "r") as f:
        try:
            data = json.load(f)
            return FactoryInput(**data)
        except Exception as e:
            logger.error(f"Failed to parse input.json: {e}")
            raise

def main():
    logger.info("Initializing Factory Architect System...")
    
    try:
        # 1. Ingest
        input_data = load_input()
        
        # 2. Compute (AI)
        ai = LayoutIntelligence()
        layout = ai.compute_layout(input_data)
        
        # Dump Intermediate Logic
        debug_path = os.path.join(settings.OUTPUT_DIR, "debug_layout.json")
        with open(debug_path, "w") as f:
            f.write(layout.model_dump_json(indent=2))

        # 3. Render (CAD)
        dxf_path = os.path.join(settings.OUTPUT_DIR, f"{input_data.project_name}.dxf")
        renderer = DXFRenderer(dxf_path)
        renderer.render(layout)

    except Exception as e:
        logger.critical(f"System Halted: {e}")
        exit(1)

if __name__ == "__main__":
    main()
