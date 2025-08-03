import bpy
import requests
import json
from typing import Dict, Any
from config import mcp_config

class BlenderMCP:
    def __init__(self):
        self.mcp_url = f"{mcp_config.MCP_BASE_URL}/mcp/query"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {mcp_config.BLENDER_API_KEY}"
        }

    def get_scene_context(self) -> Dict[str, Any]:
        """
        Get the current Blender scene context
        """
        scene = bpy.context.scene
        context = {
            "scene": {
                "name": scene.name,
                "frame": scene.frame_current,
                "objects": [
                    {
                        "name": obj.name,
                        "type": obj.type,
                        "location": list(obj.location),
                        "rotation": list(obj.rotation_euler)
                    }
                    for obj in scene.objects
                ]
            }
        }
        return context

    def query(self, query: str) -> str:
        """
        Send a query to the MCP server from Blender
        """
        try:
            context = self.get_scene_context()
            
            payload = {
                "context": context,
                "query": query,
                "tool_calls": {
                    "editor": "blender",
                    "features": ["scene_analysis", "object_manipulation", "animation_assist"]
                }
            }

            response = requests.post(
                self.mcp_url,
                headers=self.headers,
                json=payload
            )

            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                raise Exception(f"MCP request failed: {response.text}")

        except Exception as e:
            raise Exception(f"Error querying MCP: {str(e)}")

    def analyze_scene(self) -> str:
        """
        Analyze the current Blender scene
        """
        return self.query("Analyze the current scene and provide feedback")

    def suggest_modifications(self) -> str:
        """
        Get suggestions for scene modifications
        """
        return self.query("Suggest improvements for the current scene")

    def get_animation_assistance(self) -> str:
        """
        Get animation assistance
        """
        return self.query("Provide animation suggestions for the current scene")

# Blender operator example
# This would need to be registered in Blender's addon system
# class MCPQueryOperator(bpy.types.Operator):
#     bl_idname = "mcp.query"
#     bl_label = "Query MCP"
#     bl_options = {"REGISTER", "UNDO"}
#     
#     def execute(self, context):
#         blender_mcp = BlenderMCP()
#         result = blender_mcp.analyze_scene()
#         print(f"MCP Analysis: {result}")
#         return {'FINISHED'}
