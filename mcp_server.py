from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import anthropic
from anthropic import Anthropic
from config import mcp_config
import os

# OpenAI support
try:
    import openai
except ImportError:
    openai = None

app = FastAPI(title="MCP Server")

# Initialize Anthropic client
anthropic_client = Anthropic(api_key=mcp_config.ANTHROPIC_API_KEY)

class MCPRequest(BaseModel):
    context: Dict[str, Any]
    query: str
    tool_calls: Optional[Dict[str, Any]] = None

class MCPResponse(BaseModel):
    response: str
    tool_calls: Optional[Dict[str, Any]] = None

@app.post("/mcp/query")
async def handle_mcp_query(request: MCPRequest) -> MCPResponse:
    try:
        # Construct the prompt with context and query
        prompt = f"""You are an MCP server handling requests from Windsurf and Blender.
        Current context: {request.context}
        
        Query: {request.query}
        
        Please provide a helpful response:"""
        
        # Check for OpenAI config
        openai_api_key = os.getenv("OPENAI_API_KEY", "")
        openai_model = os.getenv("OPENAI_MODEL", "gpt-4o")
        if openai and openai_api_key:
            openai.api_key = openai_api_key
            chat_response = openai.chat.completions.create(
                model=openai_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000
            )
            content = chat_response.choices[0].message.content if chat_response.choices else ""
            return MCPResponse(
                response=content,
                tool_calls=request.tool_calls
            )
        else:
            # Make API call to Claude
            response = anthropic_client.messages.create(
                model=mcp_config.ANTHROPIC_MODEL,
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return MCPResponse(
                response="".join(block.text for block in response.content),
                tool_calls=request.tool_calls
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": mcp_config.ANTHROPIC_MODEL}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=mcp_config.MCP_HOST, port=mcp_config.MCP_PORT)
