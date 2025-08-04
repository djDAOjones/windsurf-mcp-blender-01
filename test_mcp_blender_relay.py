import requests
import sys
import time

MCP_URL = "http://127.0.0.1:8000/blender/command"

# Fetch relay_sleep from Blender
def get_relay_sleep():
    payload = {
        "command": "import bpy; print('RELAY_SLEEP:', bpy.context.scene.mcp_chat_props.relay_sleep)"
    }
    try:
        resp = requests.post(MCP_URL, json=payload, timeout=5)
        text = resp.text
        # Parse the printed value from the response
        import re
        match = re.search(r"RELAY_SLEEP: (\d+\.\d+)", text)
        if match:
            return float(match.group(1))
        else:
            return 1.0  # default
    except Exception as e:
        print("Error fetching relay_sleep:", e)
        return 1.0

relay_sleep = get_relay_sleep()
print(f"Using relay sleep: {relay_sleep} seconds")

commands = [
    "bpy.ops.object.select_all(action='SELECT')",
    "bpy.ops.object.delete(use_global=False)",
    "bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1)); cube = bpy.data.objects[-1]; cube.name = 'Test_Cube'"
]

for cmd in commands:
    payload = {"command": f"import bpy; {cmd}"}
    try:
        resp = requests.post(MCP_URL, json=payload, timeout=5)
        print("Status:", resp.status_code)
        print("Response:", resp.text)
    except Exception as e:
        print("Error:", e)
        sys.exit(1)
    time.sleep(relay_sleep)
