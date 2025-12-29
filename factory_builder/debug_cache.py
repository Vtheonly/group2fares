import trimesh
import os
from pathlib import Path

# Check cache directory
cache_dir = Path("cache/models")
files = list(cache_dir.glob("*.glb"))
print(f"Found {len(files)} models in cache.")

for f in files:
    print(f"\n--- Analyzing {f.name} ---")
    loaded = trimesh.load(f)
    print(f"Type: {type(loaded)}")
    
    mesh = None
    if isinstance(loaded, trimesh.Scene):
        print(" It is a Scene. Converting to geometry...")
        mesh = loaded.to_geometry() # Using the new method
        # If it returns a dict of matches, we handle that
        if isinstance(mesh, dict):
             print(f" to_geometry returned dict keys: {list(mesh.keys())}")
             # Concatenate all
             mesh = trimesh.util.concatenate(list(mesh.values()))
    else:
        mesh = loaded

    print(f"Final Mesh Type: {type(mesh)}")
    if hasattr(mesh, 'metadata'):
        print(f"Metadata: {mesh.metadata}")
    
    # Try adding to a new scene
    s = trimesh.Scene()
    s.add_geometry(mesh, node_name="FORCED_NAME")
    s.export('temp_debug.glb')
    
    # Verify
    s2 = trimesh.load('temp_debug.glb')
    display_names = [n for n in s2.graph.nodes_geometry]
    print(f"Exported Node Names: {display_names}")
