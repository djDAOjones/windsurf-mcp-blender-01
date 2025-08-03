from pydantic_settings import BaseSettings
from typing import Optional
import os

class MCPConfig(BaseSettings):
    # MCP Server Configuration
    MCP_HOST: str = "localhost"
    MCP_PORT: int = 8000
    MCP_BASE_URL: str = f"http://{MCP_HOST}:{MCP_PORT}"
    
    # Anthropic API Configuration
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-opus-4-20250514"
    
    # OpenAI API Configuration
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: Optional[str] = None
    
    # Integration Configuration
    WINDSURF_API_KEY: Optional[str] = None
    BLENDER_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create singleton instance
mcp_config = MCPConfig()
