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

## Blender MCP AI Chat Add-on

- Provides a sidebar panel in Blender for AI-assisted workflows.
- The panel now only exposes dropdowns for key generative AI parameters:
    - **Model** (Claude, GPT-4o)
    - **Scene Detail** (Summary, Objects, Transforms, Detailed)
    - **Prompt Quality** (Minimal, Basic, Moderate, Detailed, Maximal)
    - **Poly Count** (Ultra Low, Low, Medium, High, Ultra High)
- All AI chat/conversation and prompt construction now happens in Windsurf, not in Blender.
- The panel is available only in the 3D Viewport sidebar.
- Dropdown values can be set by the user in Blender or remotely from Windsurf (via MCP protocol). Changes are synced between Blender and Windsurf.

### Features
- Model selection dropdown
- Scene detail dropdown
- Prompt quality dropdown
- Poly count dropdown

### Usage
1. Enable the add-on in Blender.
2. Open the MCP AI Chat panel in the 3D Viewport sidebar.
3. Set desired parameters using the dropdowns. These can also be set remotely from Windsurf.
4. All prompt construction and AI conversation is managed through Windsurf.

## Usage

Run the MCP server:
```bash
python mcp_server.py
```

The server will handle connections from both Windsurf and Blender clients.
