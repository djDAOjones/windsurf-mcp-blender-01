import requests

MCP_URL = "http://127.0.0.1:8000/blender/command"

# Python code to make a simple toy train in Blender
train_code = '''
import bpy
bpy.ops.object.select_all(action='DESELECT')
# Engine
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
engine = bpy.context.selected_objects[0]
engine.name = 'Train_Engine'
# Chimney
bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=1, location=(0.8, 0, 2))
chimney = bpy.context.selected_objects[0]
chimney.name = 'Chimney'
# Car 1
bpy.ops.mesh.primitive_cube_add(size=1.5, location=(3, 0, 0.75))
car1 = bpy.context.selected_objects[0]
car1.name = 'Train_Car1'
# Car 2
bpy.ops.mesh.primitive_cube_add(size=1.5, location=(6, 0, 0.75))
car2 = bpy.context.selected_objects[0]
car2.name = 'Train_Car2'
# Wheels
for x in [ -0.7, 0.7, 2.3, 3.7, 5.3, 6.7]:
    for y in [-0.6, 0.6]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=0.3, location=(x, y, 0.3), rotation=(1.5708,0,0))
'''

payload = {
    "command": train_code,
    "model": "gpt",
    "scene_detail": "transforms",
    "prompt_quality": "3",
    "poly_count": "2"
}

resp = requests.post(MCP_URL, json=payload, timeout=10)
print("Status:", resp.status_code)
print("Response:", resp.text)
