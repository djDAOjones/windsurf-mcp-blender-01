import requests
import sys

MCP_URL = "http://127.0.0.1:8000/blender/command"

payload = {
    "command": "bpy.ops.mesh.primitive_cube_add()"
}

try:
    resp = requests.post(MCP_URL, json=payload, timeout=5)
    print("Status:", resp.status_code)
    print("Response:", resp.text)
except Exception as e:
    print("Error:", e)
    sys.exit(1)
