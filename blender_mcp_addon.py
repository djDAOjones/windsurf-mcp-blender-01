bl_info = {
    "name": "MCP AI Chat Panel",
    "author": "Cascade + USER",
    "version": (0, 1),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > MCP AI Chat",
    "description": "Chat with Claude/OpenAI via MCP and run code in Blender",
    "category": "3D View",
}

import bpy
import sys
import site
import requests
import re

# Add user site-packages and project path for MCP client imports
sys.path.append(site.getusersitepackages())
sys.path.append('/Users/joe/Library/CloudStorage/OneDrive-OurWiltonTrust/_Joe OE Drive/4_Work/2025-08-02 Windsurf MCP/CascadeProjects/windsurf-project')

from config import mcp_config

class MCPChatEntry(bpy.types.PropertyGroup):
    prompt: bpy.props.StringProperty(name="Prompt")
    response: bpy.props.StringProperty(name="Response", maxlen=16384)

class MCPChatProperties(bpy.types.PropertyGroup):
    relay_sleep: bpy.props.EnumProperty(
        name="Relay Delay",
        description="How long to wait between relay commands (rate limiting)",
        items=[
            ("0.1", "0.1s (Fast)", "Very fast, may overwhelm Blender"),
            ("0.5", "0.5s", "Half a second delay"),
            ("1.0", "1s", "One second delay (recommended)"),
            ("2.0", "2s", "Two seconds delay"),
            ("5.0", "5s (Safe)", "Five seconds delay (very safe)")
        ],
        default="1.0"
    )
    screenshot_mode: bpy.props.EnumProperty(
        name="Screenshots",
        description="How many screenshots to capture for feedback",
        items=[
            ("1", "1 View", "Single screenshot from the default camera/view"),
            ("2", "2 Views (180°)", "Two screenshots: default and 180-degree rotation around object"),
            ("12", "12 Views (Comprehensive)", "6 rotational views (60° apart) and 6 orthographic face-on views")
        ],
        default="1"
    )
    model: bpy.props.EnumProperty(
        name="AI Model",
        description="Choose which AI model to use",
        items=[
            ("claude", "Claude", "Anthropic Claude"),
            ("gpt", "GPT-4o", "OpenAI GPT-4o")
        ],
        default="gpt"
    )
    bypass_prompt_quality: bpy.props.BoolProperty(
        name="Bypass",
        description="Bypass prompt quality (let AI decide)",
        default=True
    )
    bypass_poly_count: bpy.props.BoolProperty(
        name="Bypass",
        description="Bypass poly count (let AI decide)",
        default=True
    )
    scene_detail: bpy.props.EnumProperty(
        name="Scene Detail",
        description="How much scene info to send to AI",
        items=[
            ("summary", "Summary", "Scene summary only"),
            ("objects", "Objects", "Objects only"),
            ("transforms", "Objects + Transforms", "Objects and transforms"),
            ("detailed", "Detailed", "All object properties")
        ],
        default="summary"
    )
    prompt_quality: bpy.props.EnumProperty(
        name="Prompt Quality",
        description="How complex/detailed the AI prompt should be",
        items=[
            ("bypass", "Bypass", "Let AI decide prompt quality"),
            ("1", "Minimal", "Minimal: 1 short sentence, single action, specific"),
            ("2", "Basic", "Basic: 1-2 sentences, a couple actions, specific"),
            ("3", "Moderate", "Moderate: 1 paragraph, 2-3 actions, some open-endedness"),
            ("4", "Detailed", "Detailed: multi-paragraph, several tasks, moderately open-ended"),
            ("5", "Maximal", "Maximal: long, multi-step, highly open-ended, full script/plan")
        ],
        default="bypass"
    )
    poly_count: bpy.props.EnumProperty(
        name="Poly Count",
        description="Approximate mesh density for generated models",
        items=[
            ("bypass", "Bypass", "Let AI decide poly count"),
            ("1", "Ultra Low", "Icon/blockout (~100–500 polygons)"),
            ("2", "Low", "Toy/prototype (~500–2,000 polygons)"),
            ("3", "Medium", "Game asset (~2,000–10,000 polygons)"),
            ("4", "High", "Cinematic (~10,000–50,000 polygons)"),
            ("5", "Ultra High", "Hero/film asset (>50,000 polygons)")
        ],
        default="bypass"
    )

    chat_input: bpy.props.StringProperty(name="Prompt", default="what can you see in Blender?")
    code_snippet: bpy.props.StringProperty(name="Code Snippet")
    chat_history: bpy.props.CollectionProperty(type=MCPChatEntry)
    chat_history_index: bpy.props.IntProperty(default=-1)

class MCP_OT_SendPrompt(bpy.types.Operator):
    bl_idname = "mcp.send_prompt"
    bl_label = "Send to AI"
    bl_description = "Send the prompt to MCP server and display response"

    def execute(self, context):
        props = context.scene.mcp_chat_props
        detail = props.scene_detail
        scn = bpy.context.scene
        render = scn.render
        world = scn.world

        def get_scene_summary():
            counts = {}
            for obj in scn.objects:
                counts[obj.type] = counts.get(obj.type, 0) + 1
            return {
                "scene_name": scn.name,
                "frame": scn.frame_current,
                "object_counts": counts
            }

        def get_objects_basic():
            return [{"name": o.name, "type": o.type} for o in scn.objects]

        def get_objects_transforms():
            return [{
                "name": o.name,
                "type": o.type,
                "location": list(o.location),
                "rotation": list(o.rotation_euler),
                "scale": list(o.scale)
            } for o in scn.objects]

        def get_objects_detailed():
            objs = []
            for o in scn.objects:
                d = {
                    "name": o.name,
                    "type": o.type,
                    "location": list(o.location),
                    "rotation": list(o.rotation_euler),
                    "scale": list(o.scale),
                    "visible": o.visible_get(),
                    "parent": o.parent.name if o.parent else None,
                    "selected": o.select_get()
                }
                if hasattr(o.data, 'materials'):
                    d["materials"] = [mat.name for mat in o.data.materials if mat]
                if o.type == 'CAMERA' and hasattr(o.data, 'lens'):
                    d["lens"] = o.data.lens
                    d["sensor_width"] = o.data.sensor_width
                    d["sensor_height"] = o.data.sensor_height
                if o.type == 'LIGHT' and hasattr(o.data, 'type'):
                    d["light_type"] = o.data.type
                    d["energy"] = getattr(o.data, 'energy', None)
                    d["color"] = list(getattr(o.data, 'color', ()))
                objs.append(d)
            return objs

        # Choose context based on detail level
        if detail == "summary":
            context_data = get_scene_summary()
        elif detail == "objects":
            context_data = {
                "scene": get_scene_summary(),
                "objects": get_objects_basic()
            }
        elif detail == "transforms":
            context_data = {
                "scene": get_scene_summary(),
                "objects": get_objects_transforms()
            }
        else:  # "detailed"
            context_data = {
                "scene": get_scene_summary(),
                "objects": get_objects_detailed()
            }

        # Add some global scene info for all levels except summary
        if detail != "summary":
            context_data["frame"] = scn.frame_current
            context_data["render_engine"] = render.engine
            context_data["resolution"] = [render.resolution_x, render.resolution_y]
            context_data["unit_system"] = scn.unit_settings.system
            context_data["world_color"] = list(world.color) if world else None

        payload = {
            "context": context_data,
            "query": props.chat_input,
            "tool_calls": {"editor": "blender-addon", "features": []},
            "model": props.model
        }
        try:
            url = f"{mcp_config.MCP_BASE_URL}/mcp/query"
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            data = response.json()
            ai_response = data.get("response", "")
            # Store in chat history
            entry = props.chat_history.add()
            entry.prompt = props.chat_input
            entry.response = ai_response
            props.chat_history_index = len(props.chat_history) - 1
            # Extract python code block if present
            match = re.search(r"```python(.*?)```", ai_response, re.DOTALL)
            props.code_snippet = match.group(1).strip() if match else ""
        except Exception as e:
            entry = props.chat_history.add()
            entry.prompt = props.chat_input
            entry.response = f"Error: {e}"
            props.chat_history_index = len(props.chat_history) - 1
            props.code_snippet = ""
        return {'FINISHED'}

class MCP_OT_RunCode(bpy.types.Operator):
    bl_idname = "mcp.run_code"
    bl_label = "Run AI Code"
    bl_description = "Run the code snippet suggested by AI in Blender"

    def execute(self, context):
        props = context.scene.mcp_chat_props
        code = props.code_snippet
        if code:
            try:
                exec(code, {'bpy': bpy, '__builtins__': __builtins__})
                self.report({'INFO'}, "Code executed successfully.")
            except Exception as e:
                self.report({'ERROR'}, f"Error running code: {e}")
        else:
            self.report({'WARNING'}, "No code to run.")
        return {'FINISHED'}

class MCP_OT_CopyResponse(bpy.types.Operator):
    bl_idname = "mcp.copy_response"
    bl_label = "Copy Response"
    index: bpy.props.IntProperty()
    def execute(self, context):
        props = context.scene.mcp_chat_props
        if 0 <= self.index < len(props.chat_history):
            bpy.context.window_manager.clipboard = props.chat_history[self.index].response
            self.report({'INFO'}, "Copied to clipboard!")
        return {'FINISHED'}

class MCP_PT_ChatPanel3DView(bpy.types.Panel):
    bl_label = "MCP AI Chat"
    bl_idname = "MCP_PT_ChatPanel3DView"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'MCP AI Chat'

    def draw(self, context):
        layout = self.layout
        props = context.scene.mcp_chat_props
        row = layout.row()
        row.label(text="Model")
        row.prop(props, "model", text="", expand=False)
        row = layout.row()
        row.label(text="Scene Detail")
        row.prop(props, "scene_detail", text="", expand=False)
        row = layout.row()
        row.label(text="Prompt Quality")
        row.prop(props, "prompt_quality", text="", expand=False)
        row = layout.row()
        row.label(text="Poly Count")
        row.prop(props, "poly_count", text="", expand=False)
        row = layout.row()
        row.label(text="Relay Delay")
        row.prop(props, "relay_sleep", text="", expand=False)
        row = layout.row()
        row.label(text="Screenshots")
        row.prop(props, "screenshot_mode", text="", expand=False)

        if props.code_snippet:
            layout.label(text="Suggested Code:")
            layout.prop(props, "code_snippet", text="")
            layout.operator("mcp.run_code", text="Run AI Code")


classes = [
    MCPChatEntry,
    MCPChatProperties,
    MCP_OT_SendPrompt,
    MCP_OT_RunCode,
    MCP_OT_CopyResponse,
    MCP_PT_ChatPanel3DView,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.mcp_chat_props = bpy.props.PointerProperty(type=MCPChatProperties)
    # Start HTTP server for remote control (only once)
    try:
        import blender_http_server
        if not hasattr(register, "_http_server_started"):
            blender_http_server.start_blender_http_server(port=8081)
            register._http_server_started = True
    except Exception as e:
        print(f"[MCP Addon] Failed to start HTTP server: {e}")

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.mcp_chat_props

if __name__ == "__main__":
    register()
