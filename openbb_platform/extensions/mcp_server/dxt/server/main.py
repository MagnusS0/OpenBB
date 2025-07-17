#!/usr/bin/env python3
"""
OpenBB MCP Server Entry Point for DXT.

This script serves as the entry point for the OpenBB MCP server when run from a DXT extension.
It handles environment setup, API key configuration, and launches the MCP server.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any

def setup_environment():
    """Set up the environment for the OpenBB MCP server."""
    # Add the lib directory to Python path for bundled dependencies
    lib_path = Path(__file__).parent.parent / "lib"
    if lib_path.exists():
        sys.path.insert(0, str(lib_path))

def configure_api_keys():
    """Configure API keys from DXT user configuration."""
    # Get API keys configuration from environment (set by DXT)
    api_keys_config = os.environ.get('OPENBB_MCP_API_KEYS_CONFIG', '{}')
    
    if api_keys_config and api_keys_config != '{}':
        try:
            api_keys = json.loads(api_keys_config)
            
            # Create OpenBB platform configuration directory
            openbb_config_dir = Path.home() / ".openbb_platform"
            openbb_config_dir.mkdir(exist_ok=True)
            
            # Load existing user settings or create new ones
            user_settings_path = openbb_config_dir / "user_settings.json"
            if user_settings_path.exists():
                with open(user_settings_path, 'r') as f:
                    user_settings = json.load(f)
            else:
                user_settings = {}
            
            # Update user settings with API keys
            for provider, config in api_keys.items():
                if provider not in user_settings:
                    user_settings[provider] = {}
                user_settings[provider].update(config)
            
            # Save updated user settings
            with open(user_settings_path, 'w') as f:
                json.dump(user_settings, f, indent=2)
                
        except json.JSONDecodeError as e:
            print(f"Warning: Invalid API keys configuration: {e}", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Could not configure API keys: {e}", file=sys.stderr)

def create_mcp_settings():
    """Create MCP settings from DXT user configuration."""
    openbb_config_dir = Path.home() / ".openbb_platform"
    openbb_config_dir.mkdir(exist_ok=True)
    
    mcp_settings_path = openbb_config_dir / "mcp_settings.json"
    
    # Get settings from environment variables (set by DXT)
    default_categories = os.environ.get('OPENBB_MCP_DEFAULT_TOOL_CATEGORIES', 'admin')
    allowed_categories = os.environ.get('OPENBB_MCP_ALLOWED_TOOL_CATEGORIES', '')
    enable_discovery = os.environ.get('OPENBB_MCP_ENABLE_TOOL_DISCOVERY', 'true').lower() == 'true'
    describe_responses = os.environ.get('OPENBB_MCP_DESCRIBE_ALL_RESPONSES', 'false').lower() == 'true'
    
    # Parse categories
    if default_categories:
        default_categories = [cat.strip() for cat in default_categories.split(',') if cat.strip()]
    else:
        default_categories = ['admin']
    
    if allowed_categories:
        allowed_categories = [cat.strip() for cat in allowed_categories.split(',') if cat.strip()]
    else:
        allowed_categories = None
    
    # Create MCP settings
    mcp_settings = {
        "name": "OpenBB MCP",
        "description": "All OpenBB REST endpoints exposed as MCP tools through DXT extension",
        "default_tool_categories": default_categories,
        "allowed_tool_categories": allowed_categories,
        "enable_tool_discovery": enable_discovery,
        "describe_responses": describe_responses
    }
    
    # Save MCP settings
    with open(mcp_settings_path, 'w') as f:
        json.dump(mcp_settings, f, indent=2)

def main():
    """Main entry point for the DXT OpenBB MCP server."""
    try:
        # Set up environment
        setup_environment()
        
        # Configure API keys from DXT user configuration
        configure_api_keys()
        
        # Create MCP settings from DXT user configuration
        create_mcp_settings()
        
        # Import and run the main OpenBB MCP server
        from openbb_mcp_server.main import main as openbb_mcp_main
        
        # Run the OpenBB MCP server
        openbb_mcp_main()
        
    except ImportError as e:
        print(f"Error: Could not import OpenBB MCP server: {e}", file=sys.stderr)
        print("Make sure OpenBB dependencies are properly bundled in the DXT package.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error starting OpenBB MCP server: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()