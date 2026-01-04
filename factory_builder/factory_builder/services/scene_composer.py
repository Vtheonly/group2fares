import trimesh
import numpy as np
import math
from factory_builder.domain import FactoryLayout, FactoryEntity, ProductionLine
from factory_builder.utils import get_logger

log = get_logger("Composer")

class SceneComposer:
    def build(self, layout: FactoryLayout, output_path: str):
        """
        Assembles the factory scene and exports to GLB.
        """
        log.info("   🧩 Initializing Scene Composition...")
        scene = trimesh.Scene()
        
        # 1. Add Floor
        self._add_floor(scene, layout)
        
        # 2. Add Machines
        for entity in layout.entities:
            if entity.type == "MACHINE":
                self._place_machine(scene, entity)
            elif entity.type == "PORT":
                self._place_marker(scene, entity)
        
        # 3. Add Production Lines (Pipes)
        for line in layout.production_lines:
            self._add_production_line(scene, line)

        # 4. Export
        try:
            scene.export(output_path)
            log.info(f"   💾 Scene saved to: {output_path}")
            return True
        except Exception as e:
            log.error(f"   ❌ Failed to export scene: {e}")
            return False

    def _add_floor(self, scene, layout):
        # Create a floor slightly larger than the bounds
        w, h = layout.width * 1.5, layout.height * 1.5
        floor = trimesh.creation.box(extents=(w, h, 20))
        
        # Color: Light concrete gray
        floor.visual.face_colors = [220, 220, 220, 255]
        
        # Position: Centered and slightly below Z=0
        floor.apply_translation([layout.center.x, layout.center.y, -10])
        scene.add_geometry(floor, node_name="floor_concrete")

    def _place_machine(self, scene, entity: FactoryEntity):
        mesh = None
        
        # A. Try Loading 3D Model
        if entity.model_path:
            try:
                # Load GLB
                loaded = trimesh.load(entity.model_path)
                
                # Handle Scene vs Mesh
                if isinstance(loaded, trimesh.Scene):
                    if len(loaded.geometry) == 0:
                        raise ValueError("Empty GLB scene")
                    # Dump all geometries into one mesh
                    mesh = trimesh.util.concatenate(loaded.dump())
                else:
                    mesh = loaded
                
                # Normalize Scale (Target ~3000mm max dimension)
                if hasattr(mesh, 'extents'):
                    current_max = np.max(mesh.extents)
                    if current_max > 0:
                        scale_factor = 3000.0 / current_max
                        mesh.apply_scale(scale_factor)
                
                # Fix Rotation (GLB is usually Y-up, we need Z-up)
                # Rotate 90 deg around X
                rot_fix = trimesh.transformations.rotation_matrix(np.pi/2, [1,0,0])
                mesh.apply_transform(rot_fix)

            except Exception as e:
                log.warning(f"     [!] Failed to load model for {entity.name}: {e}. Using placeholder.")
                mesh = None

        # B. Fallback Placeholder (Box)
        if mesh is None:
            l, w = entity.dimensions
            mesh = trimesh.creation.box(extents=(l, w, 1500))
            mesh.visual.face_colors = [100, 100, 100, 255] # Dark Gray
        
        # C. Apply Layout Transform
        # 1. Rotate around Z (Layout rotation)
        angle_rad = np.radians(entity.rotation)
        rot_layout = trimesh.transformations.rotation_matrix(angle_rad, [0, 0, 1])
        mesh.apply_transform(rot_layout)
        
        # 2. Translate to X, Y
        mesh.apply_translation([entity.position.x, entity.position.y, 0])
        
        # 3. Align bottom to floor (Z=0)
        if hasattr(mesh, 'bounds'):
            z_min = mesh.bounds[0][2]
            mesh.apply_translation([0, 0, -z_min])

        # Add to scene using clean name
        scene.add_geometry(mesh, node_name=entity.clean_name)

    def _place_marker(self, scene, entity):
        # Helper for debugging ports
        m = trimesh.creation.cylinder(radius=150, height=500)
        m.visual.face_colors = [255, 165, 0, 255] # Orange
        m.apply_translation([entity.position.x, entity.position.y, 250])
        scene.add_geometry(m)

    def _add_production_line(self, scene, line: ProductionLine):
        """Renders pipes with elbows."""
        if len(line.vertices) < 2:
            return

        PIPE_RADIUS = 120
        PIPE_HEIGHT = 600 # Height off the floor
        COLOR_PIPE = [30, 144, 255, 255] # Dodger Blue
        COLOR_ELBOW = [255, 69, 0, 255]  # Red Orange

        points = line.vertices
        
        for i in range(len(points) - 1):
            p1 = np.array([points[i].x, points[i].y, PIPE_HEIGHT])
            p2 = np.array([points[i+1].x, points[i+1].y, PIPE_HEIGHT])
            
            # Draw Straight Pipe
            segment = self._create_cylinder_segment(p1, p2, PIPE_RADIUS)
            if segment:
                segment.visual.face_colors = COLOR_PIPE
                scene.add_geometry(segment, node_name=f"pipe_{line.id}_{i}")
            
            # Draw Elbow/Joint at p2 (if not the last point)
            if i < len(points) - 2:
                elbow = trimesh.creation.icosphere(radius=PIPE_RADIUS * 1.4, subdivisions=2)
                elbow.apply_translation(p2)
                elbow.visual.face_colors = COLOR_ELBOW
                scene.add_geometry(elbow, node_name=f"joint_{line.id}_{i}")

        # Add vertical risers at start and end
        for pt in [points[0], points[-1]]:
            ground = np.array([pt.x, pt.y, 0])
            air = np.array([pt.x, pt.y, PIPE_HEIGHT])
            riser = self._create_cylinder_segment(ground, air, PIPE_RADIUS)
            if riser:
                riser.visual.face_colors = [50, 50, 50, 255] # Dark Gray
                scene.add_geometry(riser)

    def _create_cylinder_segment(self, p1, p2, radius):
        """Creates a cylinder mesh connecting p1 and p2."""
        vec = p2 - p1
        length = np.linalg.norm(vec)
        if length < 1.0: return None
        
        # Trimesh cylinder is created along Z. We must rotate it.
        cyl = trimesh.creation.cylinder(radius=radius, height=length, sections=12)
        
        # Rotation matrix to align Z with vec
        z_axis = np.array([0, 0, 1])
        vec_norm = vec / length
        
        # Axis of rotation = cross product
        rot_axis = np.cross(z_axis, vec_norm)
        axis_len = np.linalg.norm(rot_axis)
        
        if axis_len > 1e-6:
            rot_axis = rot_axis / axis_len
            angle = np.arccos(np.clip(np.dot(z_axis, vec_norm), -1.0, 1.0))
            matrix = trimesh.transformations.rotation_matrix(angle, rot_axis)
            cyl.apply_transform(matrix)
        
        # Move to midpoint
        midpoint = (p1 + p2) / 2
        cyl.apply_translation(midpoint)
        
        return cyl