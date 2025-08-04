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

            # Screenshot logic using bpy.app.timers for safe execution
            import io, base64, math
            screenshots = []
            mode = getattr(props, 'screenshot_mode', '1')
            # Robustly select an object for camera positioning
            obj = getattr(bpy.context, 'active_object', None)
            if obj is None:
                # Try to select the first mesh object as fallback
                mesh_objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
                if mesh_objs:
                    obj = mesh_objs[0]
                else:
                    obj = None
            scene = bpy.context.scene
            cam = scene.camera
            original_matrix = None
            if cam is not None:
                original_matrix = cam.matrix_world.copy()
            def capture():
                buf = io.BytesIO()
                bpy.ops.screen.screenshot(filepath="/tmp/_mcp_temp.png", full=True)
                with open("/tmp/_mcp_temp.png", "rb") as f:
                    img_bytes = f.read()
                return base64.b64encode(img_bytes).decode('utf-8')
            def rotate_camera(angle_deg, axis='Z'):
                if cam is not None:
                    rot = math.radians(angle_deg)
                    if axis == 'Z':
                        cam.rotation_euler[2] += rot
                    elif axis == 'Y':
                        cam.rotation_euler[1] += rot
                    elif axis == 'X':
                        cam.rotation_euler[0] += rot
            def set_camera_ortho(direction):
                if cam is not None:
                    cam.data.type = 'ORTHO'
                    cam.location = obj.location.copy()
                    if direction == 'FRONT':
                        cam.location.y += 10
                        cam.rotation_euler = (0, 0, 0)
                    elif direction == 'BACK':
                        cam.location.y -= 10
                        cam.rotation_euler = (0, math.pi, 0)
                    elif direction == 'LEFT':
                        cam.location.x -= 10
                        cam.rotation_euler = (0, 0, math.pi/2)
                    elif direction == 'RIGHT':
                        cam.location.x += 10
                        cam.rotation_euler = (0, 0, -math.pi/2)
                    elif direction == 'TOP':
                        cam.location.z += 10
                        cam.rotation_euler = (-math.pi/2, 0, 0)
                    elif direction == 'BOTTOM':
                        cam.location.z -= 10
                        cam.rotation_euler = (math.pi/2, 0, 0)
            def restore_camera():
                if cam is not None and original_matrix is not None:
                    cam.matrix_world = original_matrix
                    cam.data.type = 'PERSP'
            # Use a timer to safely perform camera moves and screenshots
            def screenshot_sequence():
                try:
                    if mode == '1':
                        screenshots.append({'view': 'default', 'image': capture()})
                    elif mode == '2':
                        screenshots.append({'view': 'default', 'image': capture()})
                        rotate_camera(180)
                        bpy.context.view_layer.update()
                        screenshots.append({'view': '180deg', 'image': capture()})
                        restore_camera()
                    elif mode == '12':
                        # 6 rotational views (60° apart)
                        screenshots.append({'view': 'default', 'image': capture()})
                        for i in range(1,6):
                            rotate_camera(60)
                            bpy.context.view_layer.update()
                            screenshots.append({'view': f'rot_{i*60}deg', 'image': capture()})
                        restore_camera()
                        # 6 orthographic face-on views
                        for direction in ['FRONT','BACK','LEFT','RIGHT','TOP','BOTTOM']:
                            set_camera_ortho(direction)
                            bpy.context.view_layer.update()
                            screenshots.append({'view': f'ortho_{direction.lower()}', 'image': capture()})
                        restore_camera()
                    result.update({'screenshots': screenshots})
                except Exception as e:
                    result['status'] = 'error'
                    result['error'] = str(e)
                return None # Stops the timer
            result = {'status': 'success'}
            bpy.app.timers.register(screenshot_sequence)

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
