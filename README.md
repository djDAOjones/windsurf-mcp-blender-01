# Windsurf MCP Integration

This project implements the Model Context Protocol (MCP) integration for Windsurf and Blender using Anthropic's MCP system.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
Create a `.env` file with your Anthropic API key:
```
ANTHROPIC_API_KEY=your_api_key_here
```

## Components

- `mcp_server.py`: Main MCP server implementation
- `windsurf_integration.py`: Windsurf-specific integration
- `blender_integration.py`: Blender-specific integration
- `config.py`: Configuration management

## Usage

Run the MCP server:
```bash
python mcp_server.py
```

The server will handle connections from both Windsurf and Blender clients.
