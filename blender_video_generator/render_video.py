import bpy
import math
import os
import sys
from mathutils import Vector

# ==========================================
# CONFIGURATION
# ==========================================
# Path to GLB file (mounted inside Docker)
path_to_glb = "/input/model.glb"
output_path = "/output/factory_flyover.mp4"

# Animation Settings
TOTAL_FRAMES = 300       # Duration of animation (300 frames @ 24fps = ~12.5 seconds)
CAMERA_HEIGHT = 8.0      # How high the camera sits
CAMERA_DISTANCE = 10.0   # How far back (width-wise) the camera sits
ZOOM_AMOUNT = 0.5        # How much to zoom in (percentage: 0.5 = 50% closer)

# ==========================================
# SETUP SCENE
# ==========================================
def reset_scene():
    # clear scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

def setup_render():
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = TOTAL_FRAMES
    scene.render.fps = 24
    
    # Set Resolution
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100

    # usage of CYCLES for headless compatibility
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 16  # Low samples for speed
    
    # Output Settings
    scene.render.filepath = output_path
    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = 'H264'
    scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'
    scene.render.ffmpeg.ffmpeg_preset = 'GOOD'

# ==========================================
# LOGIC
# ==========================================
reset_scene()
setup_render()

# 1. Import the GLB
if not os.path.exists(path_to_glb):
    print(f"Error: File not found at {path_to_glb}")
    sys.exit(1)

print(f"Loading: {path_to_glb}")
try:
    bpy.ops.import_scene.gltf(filepath=path_to_glb)
except Exception as e:
    print(f"Error importing GLB: {e}")
    sys.exit(1)

print(f"Import finished. Objects in scene: {len(bpy.context.scene.objects)}")


# 2. Calculate the 'Big Rectangle' (Bounding Box)
min_x, max_x = float('inf'), float('-inf')
min_y, max_y = float('inf'), float('-inf')
min_z, max_z = float('inf'), float('-inf')

all_objects = bpy.context.selected_objects
if not all_objects:
    all_objects = bpy.context.scene.objects

mesh_objects = [obj for obj in all_objects if obj.type == 'MESH']

# Fallback if no meshes found
if not mesh_objects:
    print("Warning: No mesh objects found. Using defaults.")
    min_x, max_x = -10, 10
    min_y, max_y = -10, 10
    min_z, max_z = 0, 5
else:
    for obj in mesh_objects:
        # Get world coordinates of corners
        bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        for corner in bbox_corners:
            min_x = min(min_x, corner.x)
            max_x = max(max_x, corner.x)
            min_y = min(min_y, corner.y)
            max_y = max(max_y, corner.y)
            min_z = min(min_z, corner.z)
            max_z = max(max_z, corner.z)

# Calculate Center and Dimensions
center_x = (min_x + max_x) / 2
center_y = (min_y + max_y) / 2
center_z = (min_z + max_z) / 2
length_x = max_x - min_x
width_y = max_y - min_y

print(f"Line detected: Length {length_x:.2f}m, Width {width_y:.2f}m")

# Determine which axis is the 'Long' axis (The production line direction)
is_x_long = length_x > width_y
start_pos = min_x if is_x_long else min_y
end_pos = max_x if is_x_long else max_y

# ==========================================
# CREATE CAMERA RIG
# ==========================================

# Create a Focus Point (Empty) that the camera will look at
bpy.ops.object.empty_add(type='SPHERE', location=(center_x, center_y, center_z))
focus_target = bpy.context.active_object
focus_target.name = "Camera_Focus_Target"

# Create the Camera
bpy.ops.object.camera_add(location=(0, 0, 0))
cam = bpy.context.active_object
cam.name = "Flyover_Camera"
bpy.context.scene.camera = cam

# Add "Track To" constraint so Camera always looks at the Focus Point
constraint = cam.constraints.new(type='TRACK_TO')
constraint.target = focus_target
constraint.track_axis = 'TRACK_NEGATIVE_Z'
constraint.up_axis = 'UP_Y'

# ==========================================
# ANIMATION (KEYFRAMING)
# ==========================================
print("Generating Animation...")

# Helper to set location keyframe
def set_loc(obj, x, y, z, frame):
    obj.location = (x, y, z)
    obj.keyframe_insert(data_path="location", frame=frame)

# --- FRAME 1: START ---
# Focus target starts at the beginning of the machine line
target_start_x = min_x if is_x_long else center_x
target_start_y = center_y if is_x_long else min_y

set_loc(focus_target, target_start_x, target_start_y, center_z, 1)

# Camera starts offset (High and Wide)
cam_start_x = target_start_x + (5 if not is_x_long else 0)
cam_start_y = target_start_y - CAMERA_DISTANCE if is_x_long else target_start_y
set_loc(cam, cam_start_x, cam_start_y, CAMERA_HEIGHT, 1)

# --- FRAME MIDDLE: ZOOM IN ---
mid_frame = TOTAL_FRAMES / 2
target_mid_x = center_x
target_mid_y = center_y

set_loc(focus_target, target_mid_x, target_mid_y, center_z, mid_frame)

# Camera dips down and gets closer (The "Zoom a bit" effect)
close_dist = CAMERA_DISTANCE * (1 - ZOOM_AMOUNT)
low_height = CAMERA_HEIGHT * 0.6

cam_mid_x = target_mid_x + (5 if not is_x_long else 0)
cam_mid_y = target_mid_y - close_dist if is_x_long else target_mid_y
set_loc(cam, cam_mid_x, cam_mid_y, low_height, mid_frame)

# --- FRAME END: FINISH ---
target_end_x = max_x if is_x_long else center_x
target_end_y = center_y if is_x_long else max_y

set_loc(focus_target, target_end_x, target_end_y, center_z, TOTAL_FRAMES)

# Camera pulls back up and finishes
cam_end_x = target_end_x + (5 if not is_x_long else 0)
cam_end_y = target_end_y - CAMERA_DISTANCE if is_x_long else target_end_y
set_loc(cam, cam_end_x, cam_end_y, CAMERA_HEIGHT, TOTAL_FRAMES)

# --- MAKE MOVEMENT SMOOTH ---
# Set interpolation to Bezier (Smooth start/stop/turn)
if cam.animation_data and cam.animation_data.action:
    for fcurve in cam.animation_data.action.fcurves:
        for kf in fcurve.keyframe_points:
            kf.interpolation = 'BEZIER'

# ==========================================
# LIGHTING
# ==========================================
bpy.ops.object.light_add(type='SUN', location=(0, 0, 20))
sun = bpy.context.active_object
sun.data.energy = 5

print("Starting render...")
# Render Animation
bpy.ops.render.render(animation=True)
print(f"Render complete! Saved to {output_path}")
