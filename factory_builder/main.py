import argparse
from factory_builder.config import Config
from factory_builder.services.dxf_parser import DxfParser
from factory_builder.services.web_scraper import ImageScraper
from factory_builder.services.cloud_client import CloudRenderer
from factory_builder.services.scene_composer import SceneComposer
from factory_builder.utils import get_logger

log = get_logger("Main")

def main():
    parser = argparse.ArgumentParser(description="DXF to 3D Factory Pipeline")
    parser.add_argument("dxf_file", help="Filename inside the 'input' folder")
    args = parser.parse_args()

    # 1. Setup
    Config.setup_directories()
    input_path = Config.INPUT_DIR / args.dxf_file
    
    if not input_path.exists():
        log.error(f"Input file not found: {input_path}")
        return

    # 2. Parse DXF
    layout = DxfParser().parse(str(input_path))

    # 3. Scout Images (Local or Web)
    ImageScraper().process_entities(layout.entities)

    # 4. Generate 3D Models (Cloud API)
    CloudRenderer().generate_models(layout.entities)

    # 5. Assemble Scene
    output_name = f"{input_path.stem}_scene_gray.glb"
    SceneComposer().build(layout, output_name)

if __name__ == "__main__":
    main()
