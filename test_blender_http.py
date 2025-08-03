import requests
import json

# Test command: add a cube in Blender
payload = {
    "command": """
import bpy
# Remove all objects for a clean start (optional)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Seat
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
seat = bpy.context.active_object
seat.scale[2] = 0.2

# Backrest
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, -0.9, 2))
backrest = bpy.context.active_object
backrest.scale[0] = 0.9
backrest.scale[1] = 0.1
backrest.scale[2] = 0.8

# Leg positions
leg_locations = [(-0.8, -0.8, 0.4), (0.8, -0.8, 0.4), (-0.8, 0.8, 0.4), (0.8, 0.8, 0.4)]
for x, y, z in leg_locations:
    bpy.ops.mesh.primitive_cube_add(size=0.4, location=(x, y, z))
    leg = bpy.context.active_object
    leg.scale[2] = 1.2
"""
}

try:
    response = requests.post("http://127.0.0.1:8081/", json=payload)
    print("Status:", response.status_code)
    print("Response:", response.text)
except Exception as e:
    print("Error:", e)
