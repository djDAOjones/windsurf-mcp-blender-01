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
    model: bpy.props.EnumProperty(
        name="Model",
        description="Select the AI model to use",
        items=[
            ("claude-opus", "Claude Opus", "Anthropic Claude Opus"),
            ("gpt-4o", "ChatGPT (GPT-4o)", "OpenAI GPT-4o")
        ],
        default="claude-opus"
    )
    chat_input: bpy.props.StringProperty(name="Prompt", default="Describe the current scene.")
    code_snippet: bpy.props.StringProperty(name="Code Snippet")
    chat_history: bpy.props.CollectionProperty(type=MCPChatEntry)
    chat_history_index: bpy.props.IntProperty(default=-1)

class MCP_OT_SendPrompt(bpy.types.Operator):
    bl_idname = "mcp.send_prompt"
    bl_label = "Send to AI"
    bl_description = "Send the prompt to MCP server and display response"

    def execute(self, context):
        props = context.scene.mcp_chat_props
        # Gather scene context: names, types, locations, rotations, materials
        scene_objects = []
        for obj in bpy.context.scene.objects:
            obj_data = {
                "name": obj.name,
                "type": obj.type,
                "location": list(obj.location),
                "rotation": list(obj.rotation_euler),
                "scale": list(obj.scale)
            }
            # Get material names if mesh
            if hasattr(obj.data, 'materials'):
                obj_data["materials"] = [mat.name for mat in obj.data.materials if mat]
            # Camera settings
            if obj.type == 'CAMERA' and hasattr(obj.data, 'lens'):
                obj_data["lens"] = obj.data.lens
                obj_data["sensor_width"] = obj.data.sensor_width
                obj_data["sensor_height"] = obj.data.sensor_height
            # Light settings
            if obj.type == 'LIGHT' and hasattr(obj.data, 'type'):
                obj_data["light_type"] = obj.data.type
                obj_data["energy"] = getattr(obj.data, 'energy', None)
                obj_data["color"] = list(getattr(obj.data, 'color', ()))
            scene_objects.append(obj_data)
        # Scene-level info
        scn = bpy.context.scene
        render = scn.render
        world = scn.world
        context = {
            "objects": scene_objects,
            "frame": scn.frame_current,
            "render_engine": render.engine,
            "resolution": [render.resolution_x, render.resolution_y],
            "unit_system": scn.unit_settings.system,
            "world_color": list(world.color) if world else None
        }
        payload = {
            "context": context,
            "query": props.chat_input,
            "tool_calls": {"editor": "blender-addon", "features": []},
            "model": props.model  # Pass the selected model to the MCP server
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

class MCP_PT_ChatPanel(bpy.types.Panel):
    bl_label = "MCP AI Chat"
    bl_idname = "MCP_PT_ChatPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'MCP AI Chat'

    def draw(self, context):
        layout = self.layout
        props = context.scene.mcp_chat_props
        layout.prop(props, "model", text="Model")
        layout.prop(props, "chat_input", text="Prompt")
        layout.operator("mcp.send_prompt", text="Send to AI")
        layout.label(text="Chat History:")
        for i, entry in enumerate(props.chat_history):
            box = layout.box()
            box.label(text=f"Prompt: {entry.prompt}")
            box.label(text="Response:")
            box.prop(entry, "response", text="", emboss=False, icon='TEXT')
            box.operator("mcp.copy_response", text="Copy Response").index = i
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
    MCP_PT_ChatPanel,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.mcp_chat_props = bpy.props.PointerProperty(type=MCPChatProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.mcp_chat_props

if __name__ == "__main__":
    register()
