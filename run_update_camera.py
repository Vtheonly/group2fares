
import sys
import os
import json
from pathlib import Path

# Add paths
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "factory_builder"))
sys.path.append(os.path.join(os.getcwd(), "factory_architect"))

from factory_builder.config import Config
from factory_builder.services.scene_composer import SceneComposer
from factory_builder.domain import FactoryLayout, FactoryEntity, Vector3, ProductionLine

# Override Config to match local paths
BASE_DIR = Path(os.getcwd())
Config.BASE_DIR = BASE_DIR
Config.CACHE_DIR = BASE_DIR / "factory_builder" / "cache"
Config.MODELS_DIR = Config.CACHE_DIR / "models"
Config.OUTPUT_DIR = BASE_DIR / "data" / "output" # Temporary output

print(f"Models Dir: {Config.MODELS_DIR}")

def update_layout(layout_path):
    print(f"Processing: {layout_path}")
    try:
        with open(layout_path, 'r') as f:
            data = json.load(f)
            
        # Reconstruct FactoryLayout
        entities = []
        for m in data.get('machines', []):
            # Try to find model
            machine_name = m['name'] # or from ID mapping if available
            # We assume name matches cache 
            clean_name = "".join([c if c.isalnum() else "_" for c in machine_name]).strip()
            model_path = Config.MODELS_DIR / f"{clean_name}.glb"
            
            if not model_path.exists():
                print(f"Warning: Model not found for {machine_name} at {model_path}")
                model_path = None
                

            # Fallback for dimensions
            dims = m.get('dimensions') 
            if dims and isinstance(dims, dict):
                 # It's a dict like {'length': 2000, 'width': 2000}
                 w = dims.get('length', dims.get('width', 2000.0))
                 d = dims.get('width', dims.get('depth', 2000.0))
                 dims = (w, d)
            elif not dims:
                # Try size_x, size_y or width/height
                w = m.get('width', 2000.0)
                d = m.get('depth', m.get('height', 2000.0))
                dims = (w, d)
            
            # Debug keys if first machine
            if len(entities) == 0:
                print(f"Machine Keys: {m.keys()}")

            entity = FactoryEntity(
                id=m.get('id', m['name']),
                name=machine_name,
                type="MACHINE",
                position=Vector3(m['position']['x'], m['position']['y'], 0),
                rotation=m.get('rotation', 0),
                model_path=str(model_path) if model_path else None,
                dimensions=dims
            )
            entities.append(entity)

        # Convert layout data to domain object
        layout = FactoryLayout(
            source_file="dummy.dxf",
            width=data['room_width'],
            height=data['room_height'],
            center=Vector3(data['room_width']/2, data['room_height']/2, 0),
            entities=entities
        )
        
        # Build scene to compute coords
        composer = SceneComposer()
        # We don't care about the output GLB really, but we need to run build
        # Save to /dev/null or temp
        temp_out = "temp_u_scene.glb"
        result = composer.build(layout, temp_out)
        
        if isinstance(result, tuple):
            _, camera_data = result
            
            if camera_data:
                data['camera_coords'] = camera_data
                with open(layout_path, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"SUCCESS: Updated {layout_path} with {len(camera_data)} camera coords")
            else:
                print("No camera data computed.")
        else:
            print("Composer returned old format (no camera data). Check code.")
            
    except Exception as e:
        print(f"Error processing {layout_path}: {e}")
        import traceback
        traceback.print_exc()

def main():
    # Find all debug_layout.json
    root = Path(os.getcwd())
    layouts = list(root.rglob("debug_layout.json"))
    
    for l in layouts:
        if "google_drive" in str(l): continue
        if ".git" in str(l): continue
        update_layout(l)

if __name__ == "__main__":
    main()
