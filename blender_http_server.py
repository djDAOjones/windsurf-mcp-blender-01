import threading
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import bpy

class BlenderCommandHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        try:
            data = json.loads(post_data.decode('utf-8'))
        except Exception as e:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Invalid JSON')
            return

        # Command format: {"command": "python_code"}
        command = data.get('command')
        if not command:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Missing command')
            return
        try:
            # Optionally set MCP properties from incoming JSON
            props = bpy.context.scene.mcp_chat_props
            for field in ["model", "scene_detail", "prompt_quality", "poly_count"]:
                if field in data:
                    setattr(props, field, data[field])
            # Execute the Python command in Blender's context
            exec(command, {'bpy': bpy, '__builtins__': __builtins__})
            result = {'status': 'success'}
        except Exception as e:
            result = {'status': 'error', 'error': str(e)}
        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps({'result': result}).encode('utf-8'))


def start_blender_http_server(port=8081):
    server = HTTPServer(('127.0.0.1', port), BlenderCommandHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"Blender HTTP server started on port {port}")
    return server

# To use in your add-on:
# import blender_http_server
# blender_http_server.start_blender_http_server(port=8081)
