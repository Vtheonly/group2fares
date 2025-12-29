import trimesh
import numpy as np
import os

# 1. Create a dummy mesh (like a placeholder)
mesh1 = trimesh.creation.box(extents=(10,10,10))
mesh1.visual.face_colors = [255,0,0,255]

# 2. Create a dummy valid GLB file
mesh2 = trimesh.creation.icosphere(radius=5)
mesh2.visual.face_colors = [0,255,0,255]
s = trimesh.Scene(mesh2)
s.export('dummy.glb')

# 3. Load the GLB and flatten
loaded = trimesh.load('dummy.glb')
if isinstance(loaded, trimesh.Scene):
    mesh3 = loaded.dump(concatenate=True)
else:
    print("Not a scene?")
    mesh3 = loaded

# Force metadata name that conflicts
mesh3.metadata['name'] = 'BAD_NAME_FROM_METADATA'

# 4. Build Main Scene
scene = trimesh.Scene()
scene.add_geometry(mesh1, node_name="Placeholder_Box")
scene.add_geometry(mesh3, node_name="Loaded_Sphere")

# 5. Export and Inspect
scene.export('test_scene.glb')

loaded_scene = trimesh.load('test_scene.glb')
print("=== Node Names in Result ===")
for node in loaded_scene.graph.nodes_geometry:
    print(node)
