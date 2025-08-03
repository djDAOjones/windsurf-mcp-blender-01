import requests

MCP_URL = "http://127.0.0.1:8000/blender/command"

payload = {
    "command": "print('Params set from Windsurf!')",
    "model": "gpt",
    "scene_detail": "transforms",
    "prompt_quality": "4",
    "poly_count": "2"
}

resp = requests.post(MCP_URL, json=payload, timeout=5)
print("Status:", resp.status_code)
print("Response:", resp.text)
