import requests
import json

# Test command: add a cube in Blender
payload = {
    "command": "bpy.ops.mesh.primitive_cube_add()"
}

try:
    response = requests.post("http://127.0.0.1:8081/", json=payload)
    print("Status:", response.status_code)
    print("Response:", response.text)
except Exception as e:
    print("Error:", e)
