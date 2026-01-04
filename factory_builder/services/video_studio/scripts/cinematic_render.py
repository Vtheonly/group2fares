import bpy
import json
import sys
import math
import os
from mathutils import Vector

# --- ARGUMENT PARSING ---
# Blender ignores args after "--", so we pass our JSON config there
try:
    args_start = sys.argv.index("--") + 1
    config_path = sys.argv[args_start]
except ValueError:
    print("❌ Error: Config path not passed to Blender script")
    sys.exit(1)

with open(config_path, "r") as f:
    config = json.load(f)

GLB_PATH = config["glb_path"]
OUTPUT_VIDEO = config["output_video"]
OUTPUT_METADATA = config["output_metadata"]
MACHINE_ORDER = config.get("machine_order", []) # List of IDs in flow order

# ==========================================
# 1. SETUP & IMPORT
# ==========================================
def reset_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

reset_scene()

print(f"📥 Importing Scene: {GLB_PATH}")
bpy.ops.import_scene.gltf(filepath=GLB_PATH)

# ==========================================
# 2. METADATA & CAMERA CALCULATION
# ==========================================
camera_map = {}
valid_objects = []

print("📷 Computing Smart Camera Coordinates...")

# Map logical flow to actual objects
scene_objects = {obj.name: obj for obj in bpy.context.scene.objects if obj.type == 'MESH'}

# Sort objects based on the flow order provided by the Architect
ordered_objects = []
for m_id in MACHINE_ORDER:
    # Try finding exact match or sanitized match
    obj = scene_objects.get(m_id)
    if not obj:
        # Fallback: check if name contains ID (Blender sometimes renames)
        for name, o in scene_objects.items():
            if m_id in name:
                obj = o
                break
    if obj:
        ordered_objects.append(obj)

if not ordered_objects:
    print("⚠️ No matching machines found. Using all meshes.")
    ordered_objects = list(scene_objects.values())

# Calculate Snap Coordinates per Machine
for obj in ordered_objects:
    # Calculate Bounding Box in World Space
    bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    
    min_x = min([v.x for v in bbox_corners])
    max_x = max([v.x for v in bbox_corners])
    min_y = min([v.y for v in bbox_corners])
    max_y = max([v.y for v in bbox_corners])
    max_z = max([v.z for v in bbox_corners])
    
    center = Vector(((min_x + max_x)/2, (min_y + max_y)/2, (max_z)/2))
    size_x = max_x - min_x
    size_y = max_y - min_y
    max_dim = max(size_x, size_y)

    # 🎥 OPTIMAL SNAP STRATEGY
    # Position: Offset by 1.5x size along Y axis (Front view usually), elevated Z
    zoom_factor = 2.0
    cam_pos = Vector((
        center.x + (size_x * 0.5), 
        center.y - (max_dim * zoom_factor), 
        center.z + (max_dim * 1.0)
    ))

    camera_map[obj.name] = {
        "target": {"x": center.x, "y": center.y, "z": center.z},
        "position": {"x": cam_pos.x, "y": cam_pos.y, "z": cam_pos.z}
    }

# Save Metadata for Streamlit
with open(OUTPUT_METADATA, "w") as f:
    json.dump(camera_map, f, indent=4)
print(f"✅ Camera Metadata saved to: {OUTPUT_METADATA}")

# ==========================================
# 3. CINEMATIC PATH GENERATION
# ==========================================
print("🛤️ Generating Cinematic Path...")

# Create a Curve
curve_data = bpy.data.curves.new('Flypath', type='CURVE')
curve_data.dimensions = '3D'
curve_data.resolution_u = 64
curve_obj = bpy.data.objects.new('Flypath_Obj', curve_data)
bpy.context.collection.objects.link(curve_obj)

spline = curve_data.splines.new('BEZIER')
spline.bezier_points.add(len(ordered_objects) - 1) # First point exists by default

for i, obj in enumerate(ordered_objects):
    meta = camera_map[obj.name]
    pos = meta["position"]
    
    # Set Point Position
    b_point = spline.bezier_points[i]
    b_point.co = (pos["x"], pos["y"], pos["z"])
    b_point.handle_left_type = 'AUTO'
    b_point.handle_right_type = 'AUTO'

# Setup Camera
cam_data = bpy.data.cameras.new("CinemaCam")
cam_obj = bpy.data.objects.new("CinemaCam", cam_data)
bpy.context.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

# Follow Path Constraint
constraint = cam_obj.constraints.new(type='FOLLOW_PATH')
constraint.target = curve_obj
constraint.use_curve_follow = True # Bank/Roll with curve
constraint.forward_axis = 'FORWARD_Z' # Standard for Camera
constraint.up_axis = 'UP_Y'

# Animate path evaluation
curve_obj.data.path_duration = 300 # 300 Frames
curve_obj.data.eval_time = 0
curve_obj.keyframe_insert(data_path="eval_time", frame=1)
curve_obj.data.eval_time = 300
curve_obj.keyframe_insert(data_path="eval_time", frame=300)

# Track To (Always look slightly ahead or at center)
# Simpler approach: Create an Empty that follows the path slightly ahead
# For now, let's just use LOOK_AT constraint to the current machine logic
# (Advanced: Keyframe the 'Track To' target per machine)

# ==========================================
# 4. RENDER SETTINGS
# ==========================================
scene = bpy.context.scene
scene.render.engine = 'CYCLES' # or EEVEE
scene.cycles.device = 'CPU' # Docker compatibility
scene.cycles.samples = 32   # Fast render

scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.fps = 24
scene.frame_start = 1
scene.frame_end = 300

scene.render.filepath = OUTPUT_VIDEO
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'

print(f"🎬 Starting Render: {OUTPUT_VIDEO}")
bpy.ops.render.render(animation=True)
print("✅ Render Complete.")