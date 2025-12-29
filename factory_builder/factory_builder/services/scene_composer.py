import trimesh
import numpy as np
from factory_builder.domain import FactoryLayout, FactoryEntity, ProductionLine
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
        
        # 2. Machines
        for entity in layout.entities:
            if entity.type == "MACHINE":
                self._place_machine(entity)
            elif entity.type == "PORT":
                self._place_marker(entity, color=[255, 165, 0, 200])  # Orange
        
        # 3. Production Lines (Blue pipes with red turns)
        for line in layout.production_lines:
            self._add_production_line(line)

        # 4. Export
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
            log.info(f"Loading model for {entity.name}: {entity.model_path}")
            try:
                loaded = trimesh.load(entity.model_path)
                
                # If it's a Scene (GLB), flatten to single mesh
                if isinstance(loaded, trimesh.Scene):
                    mesh = loaded.dump(concatenate=True)
                else:
                    mesh = loaded

                # Normalize Scale
                if hasattr(mesh, 'extents'):
                    scale = Config.TARGET_MACHINE_SIZE / np.max(mesh.extents)
                    mesh.apply_scale(scale)
                
                # Rotate X 90 (GLB Y-up vs CAD Z-up)
                rot_x = trimesh.transformations.rotation_matrix(np.pi/2, [1,0,0])
                mesh.apply_transform(rot_x)
                log.info(f"✅ Loaded 3D model for: {entity.name}")
            except Exception as e:
                log.warning(f"Failed to load model for {entity.name}: {e}")
                mesh = None
        else:
            log.warning(f"⬜ No model_path for {entity.name} - using placeholder")

        # Fallback Placeholder
        if not mesh:
            length, width = entity.dimensions
            log.info(f"Using placeholder for {entity.name}: {length}x{width}")
            mesh = trimesh.creation.box(extents=(length, width, 1000))
            mesh.visual.face_colors = [100, 100, 100, 200]
        
        # Position in Scene
        self._apply_cad_transform(mesh, entity)
        # Use clean_name for node to ensure GLB compatibility
        self.scene.add_geometry(mesh, node_name=entity.clean_name)

    def _place_marker(self, entity: FactoryEntity, color):
        """Place orange cylinder marker for ports (input/output)."""
        mesh = trimesh.creation.cylinder(radius=200, height=1000)
        mesh.visual.face_colors = color
        self._apply_cad_transform(mesh, entity)
        self.scene.add_geometry(mesh, node_name=f"port_{entity.clean_name}")

    def _add_production_line(self, line: ProductionLine):
        """Render production line as blue pipes with red 90° turn markers."""
        if len(line.vertices) < 2:
            return
        
        PIPE_RADIUS = 100
        BLUE = [30, 144, 255, 255]  # Dodger blue
        RED = [255, 50, 50, 255]    # Bright red
        
        vertices = line.vertices
        
        for i in range(len(vertices) - 1):
            p1 = np.array([vertices[i].x, vertices[i].y, 500])  # Elevate pipes
            p2 = np.array([vertices[i+1].x, vertices[i+1].y, 500])
            
            # Create pipe segment
            pipe = self._create_pipe_segment(p1, p2, PIPE_RADIUS)
            if pipe:
                pipe.visual.face_colors = BLUE
                self.scene.add_geometry(pipe, node_name=f"pipe_{line.id}_{i}")
            
            # Check for 90° turn (compare with next segment if exists)
            if i > 0:
                p0 = np.array([vertices[i-1].x, vertices[i-1].y, 500])
                angle = self._angle_between_segments(p0, p1, p2)
                
                # If angle is close to 90° (between 80° and 100°)
                if 80 <= abs(angle) <= 100:
                    corner = trimesh.creation.icosphere(radius=PIPE_RADIUS * 1.5)
                    corner.visual.face_colors = RED
                    corner.apply_translation(p1)
                    self.scene.add_geometry(corner, node_name=f"turn_{line.id}_{i}")
        
        # Add orange markers at connection endpoints (machine ports)
        start = vertices[0]
        end = vertices[-1]
        
        for idx, pt in enumerate([start, end]):
            marker = trimesh.creation.cylinder(radius=150, height=800)
            marker.visual.face_colors = [255, 165, 0, 255]  # Orange
            marker.apply_translation([pt.x, pt.y, 400])
            port_name = line.from_id if idx == 0 else line.to_id
            self.scene.add_geometry(marker, node_name=f"conn_{port_name}_{line.id}")

    def _create_pipe_segment(self, p1: np.ndarray, p2: np.ndarray, radius: float):
        """Create a cylinder between two 3D points."""
        direction = p2 - p1
        length = np.linalg.norm(direction)
        if length < 1:
            return None
        
        # Create cylinder along Z axis, then rotate to align with direction
        pipe = trimesh.creation.cylinder(radius=radius, height=length)
        
        # Calculate rotation to align Z-axis with direction
        direction_normalized = direction / length
        z_axis = np.array([0, 0, 1])
        
        # Rotation axis (cross product)
        axis = np.cross(z_axis, direction_normalized)
        axis_norm = np.linalg.norm(axis)
        
        if axis_norm > 1e-6:
            axis = axis / axis_norm
            angle = np.arccos(np.clip(np.dot(z_axis, direction_normalized), -1, 1))
            rotation = trimesh.transformations.rotation_matrix(angle, axis)
            pipe.apply_transform(rotation)
        
        # Move to midpoint
        midpoint = (p1 + p2) / 2
        pipe.apply_translation(midpoint)
        
        return pipe

    def _angle_between_segments(self, p0: np.ndarray, p1: np.ndarray, p2: np.ndarray) -> float:
        """Calculate angle at p1 between segments p0->p1 and p1->p2."""
        v1 = p0 - p1
        v2 = p2 - p1
        
        # Use only X-Y plane
        v1 = v1[:2]
        v2 = v2[:2]
        
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
        angle_rad = np.arccos(np.clip(cos_angle, -1, 1))
        return 180 - np.degrees(angle_rad)  # Interior angle

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
