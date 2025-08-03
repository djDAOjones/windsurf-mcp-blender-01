import requests
from typing import Dict, Any
from config import mcp_config
import json

class WindsurfMCP:
    def __init__(self):
        self.mcp_url = f"{mcp_config.MCP_BASE_URL}/mcp/query"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {mcp_config.WINDSURF_API_KEY}"
        }

    def query(self, context: Dict[str, Any], query: str) -> Dict[str, Any]:
        """
        Send a query to the MCP server from Windsurf
        """
        try:
            payload = {
                "context": context,
                "query": query,
                "tool_calls": {
                    "editor": "windsurf",
                    "features": ["code_completion", "code_review", "debug_assist"]
                }
            }

            response = requests.post(
                self.mcp_url,
                headers=self.headers,
                json=payload
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"MCP request failed: {response.text}")

        except Exception as e:
            raise Exception(f"Error querying MCP: {str(e)}")

    def get_code_suggestions(self, code_context: Dict[str, Any]) -> str:
        """
        Get code suggestions from MCP for Windsurf
        """
        try:
            response = self.query(
                context=code_context,
                query="Provide code suggestions based on the current context"
            )
            return response.get("response", "")
        except Exception as e:
            return f"Error getting suggestions: {str(e)}"

    def analyze_code(self, code_context: Dict[str, Any]) -> str:
        """
        Analyze code using MCP
        """
        try:
            response = self.query(
                context=code_context,
                query="Analyze this code and provide feedback"
            )
            return response.get("response", "")
        except Exception as e:
            return f"Error analyzing code: {str(e)}"

# Example usage
if __name__ == "__main__":
    windsurf_mcp = WindsurfMCP()
    
    # Example code context
    code_context = {
        "file_path": "example.py",
        "code": "def example_function():\n    pass",
        "related_files": ["utils.py", "config.py"]
    }
    
    # Get code suggestions
    suggestions = windsurf_mcp.get_code_suggestions(code_context)
    print("Suggestions:", suggestions)
    
    # Analyze code
    analysis = windsurf_mcp.analyze_code(code_context)
    print("Analysis:", analysis)
