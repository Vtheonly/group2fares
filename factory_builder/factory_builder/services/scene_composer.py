import trimesh
import numpy as np
from factory_builder.domain import FactoryLayout, FactoryEntity
from factory_builder.config import Config
from factory_builder.utils import get_logger

log = get_logger("Composer")

class SceneComposer:
    def __init__(self):
        self.scene = trimesh.Scene()

    def build(self, layout: FactoryLayout, output_filename: str):
        log.info("🏗️ Assembling Final Scene...")
        
        # 1. Floor
        self._add_floor(layout)
        
        # 2. Objects
        for entity in layout.entities:
            if entity.type == "MACHINE":
                self._place_machine(entity)
            elif entity.type == "PORT":
                self._place_marker(entity, color=[255, 165, 0, 200]) # Orange

        # 3. Export
        out_path = Config.OUTPUT_DIR / output_filename
        self.scene.export(str(out_path))
        log.info(f"🎉 SUCCESS. Scene saved to: {out_path}")

    def _add_floor(self, layout: FactoryLayout):
        w, h = layout.width * 1.2, layout.height * 1.2
        floor = trimesh.creation.box(extents=(w, h, 10))
        floor.visual.face_colors = [200, 200, 200, 255]
        
        # Center and lower slightly
        floor.apply_translation([layout.center.x, layout.center.y, -5])
        self.scene.add_geometry(floor, node_name="floor")

    def _place_machine(self, entity: FactoryEntity):
        mesh = None
        
        # Attempt to load generated model
        if entity.model_path:
            try:
                mesh = trimesh.load(entity.model_path)
                
                # Normalize Scale
                if hasattr(mesh, 'extents'):
                    scale = Config.TARGET_MACHINE_SIZE / np.max(mesh.extents)
                    mesh.apply_scale(scale)
                
                # Rotate X 90 (GLB Y-up vs CAD Z-up)
                rot_x = trimesh.transformations.rotation_matrix(np.pi/2, [1,0,0])
                mesh.apply_transform(rot_x)
            except Exception as e:
                log.warning(f"Failed to load model for {entity.name}: {e}")

        # Fallback Placeholder
        if not mesh:
            mesh = trimesh.creation.box(extents=(2000, 2000, 1000))
            mesh.visual.face_colors = [100, 100, 100, 200]
        
        # Position in Scene
        self._apply_cad_transform(mesh, entity)
        self.scene.add_geometry(mesh, node_name=entity.name)

    def _place_marker(self, entity: FactoryEntity, color):
        mesh = trimesh.creation.cylinder(radius=200, height=1000)
        mesh.visual.face_colors = color
        self._apply_cad_transform(mesh, entity)
        self.scene.add_geometry(mesh, node_name=f"marker_{entity.name}")

    def _apply_cad_transform(self, mesh, entity: FactoryEntity):
        # Rotation around Z
        angle_rad = np.deg2rad(entity.rotation)
        rot_matrix = trimesh.transformations.rotation_matrix(angle_rad, [0, 0, 1])
        mesh.apply_transform(rot_matrix)
        
        # Translation
        mesh.apply_translation([entity.position.x, entity.position.y, 0])
        
        # Sit on floor
        if hasattr(mesh, 'bounds'):
            z_min = mesh.bounds[0][2]
            mesh.apply_translation([0, 0, -z_min])
