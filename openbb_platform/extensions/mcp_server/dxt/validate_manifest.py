#!/usr/bin/env python3
"""
DXT Manifest Validator for OpenBB MCP Server.

This script validates the manifest.json file against the DXT specification.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional


class ManifestValidator:
    """Validates DXT manifest.json files."""
    
    REQUIRED_FIELDS = {
        "dxt_version": str,
        "name": str,
        "version": str,
        "description": str,
        "author": dict,
        "server": dict,
    }
    
    OPTIONAL_FIELDS = {
        "display_name": str,
        "long_description": str,
        "repository": dict,
        "homepage": str,
        "documentation": str,
        "support": str,
        "icon": str,
        "screenshots": list,
        "tools": list,
        "tools_generated": bool,
        "prompts": list,
        "prompts_generated": bool,
        "keywords": list,
        "license": str,
        "compatibility": dict,
        "user_config": dict,
    }
    
    REQUIRED_AUTHOR_FIELDS = {
        "name": str,
    }
    
    OPTIONAL_AUTHOR_FIELDS = {
        "email": str,
        "url": str,
    }
    
    REQUIRED_SERVER_FIELDS = {
        "type": str,
        "entry_point": str,
        "mcp_config": dict,
    }
    
    VALID_SERVER_TYPES = ["python", "node", "binary"]
    
    def __init__(self, manifest_path: Path):
        """Initialize validator with manifest path."""
        self.manifest_path = manifest_path
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def validate(self) -> bool:
        """Validate the manifest file."""
        try:
            with open(self.manifest_path, 'r') as f:
                manifest = json.load(f)
        except FileNotFoundError:
            self.errors.append(f"Manifest file not found: {self.manifest_path}")
            return False
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in manifest: {e}")
            return False
        
        # Validate required fields
        self._validate_required_fields(manifest)
        
        # Validate optional fields
        self._validate_optional_fields(manifest)
        
        # Validate author section
        if "author" in manifest:
            self._validate_author(manifest["author"])
        
        # Validate server section
        if "server" in manifest:
            self._validate_server(manifest["server"])
        
        # Validate compatibility section
        if "compatibility" in manifest:
            self._validate_compatibility(manifest["compatibility"])
        
        # Validate user config section
        if "user_config" in manifest:
            self._validate_user_config(manifest["user_config"])
        
        # Validate tools section
        if "tools" in manifest:
            self._validate_tools(manifest["tools"])
        
        return len(self.errors) == 0
    
    def _validate_required_fields(self, manifest: Dict[str, Any]) -> None:
        """Validate required top-level fields."""
        for field, expected_type in self.REQUIRED_FIELDS.items():
            if field not in manifest:
                self.errors.append(f"Missing required field: {field}")
            elif not isinstance(manifest[field], expected_type):
                self.errors.append(f"Field '{field}' must be of type {expected_type.__name__}")
    
    def _validate_optional_fields(self, manifest: Dict[str, Any]) -> None:
        """Validate optional top-level fields."""
        for field, expected_type in self.OPTIONAL_FIELDS.items():
            if field in manifest and not isinstance(manifest[field], expected_type):
                self.errors.append(f"Field '{field}' must be of type {expected_type.__name__}")
    
    def _validate_author(self, author: Dict[str, Any]) -> None:
        """Validate author section."""
        for field, expected_type in self.REQUIRED_AUTHOR_FIELDS.items():
            if field not in author:
                self.errors.append(f"Missing required author field: {field}")
            elif not isinstance(author[field], expected_type):
                self.errors.append(f"Author field '{field}' must be of type {expected_type.__name__}")
        
        for field, expected_type in self.OPTIONAL_AUTHOR_FIELDS.items():
            if field in author and not isinstance(author[field], expected_type):
                self.errors.append(f"Author field '{field}' must be of type {expected_type.__name__}")
    
    def _validate_server(self, server: Dict[str, Any]) -> None:
        """Validate server section."""
        for field, expected_type in self.REQUIRED_SERVER_FIELDS.items():
            if field not in server:
                self.errors.append(f"Missing required server field: {field}")
            elif not isinstance(server[field], expected_type):
                self.errors.append(f"Server field '{field}' must be of type {expected_type.__name__}")
        
        # Validate server type
        if "type" in server and server["type"] not in self.VALID_SERVER_TYPES:
            self.errors.append(f"Server type must be one of: {self.VALID_SERVER_TYPES}")
        
        # Validate MCP config
        if "mcp_config" in server:
            self._validate_mcp_config(server["mcp_config"])
    
    def _validate_mcp_config(self, mcp_config: Dict[str, Any]) -> None:
        """Validate MCP config section."""
        if "command" not in mcp_config:
            self.errors.append("Missing required mcp_config field: command")
        elif not isinstance(mcp_config["command"], str):
            self.errors.append("mcp_config.command must be a string")
        
        if "args" not in mcp_config:
            self.errors.append("Missing required mcp_config field: args")
        elif not isinstance(mcp_config["args"], list):
            self.errors.append("mcp_config.args must be a list")
        
        if "env" in mcp_config and not isinstance(mcp_config["env"], dict):
            self.errors.append("mcp_config.env must be a dict")
    
    def _validate_compatibility(self, compatibility: Dict[str, Any]) -> None:
        """Validate compatibility section."""
        if "platforms" in compatibility:
            if not isinstance(compatibility["platforms"], list):
                self.errors.append("compatibility.platforms must be a list")
            else:
                valid_platforms = ["darwin", "win32", "linux"]
                for platform in compatibility["platforms"]:
                    if platform not in valid_platforms:
                        self.warnings.append(f"Unknown platform: {platform}")
        
        if "runtimes" in compatibility:
            if not isinstance(compatibility["runtimes"], dict):
                self.errors.append("compatibility.runtimes must be a dict")
    
    def _validate_user_config(self, user_config: Dict[str, Any]) -> None:
        """Validate user config section."""
        valid_types = ["string", "number", "boolean", "directory", "file"]
        
        for config_name, config_def in user_config.items():
            if not isinstance(config_def, dict):
                self.errors.append(f"User config '{config_name}' must be a dict")
                continue
            
            if "type" not in config_def:
                self.errors.append(f"User config '{config_name}' missing required field: type")
            elif config_def["type"] not in valid_types:
                self.errors.append(f"User config '{config_name}' type must be one of: {valid_types}")
            
            if "title" not in config_def:
                self.errors.append(f"User config '{config_name}' missing required field: title")
            
            # Validate optional fields
            optional_fields = ["description", "required", "default", "multiple", "sensitive", "min", "max"]
            for field in optional_fields:
                if field in config_def:
                    if field in ["required", "multiple", "sensitive"] and not isinstance(config_def[field], bool):
                        self.errors.append(f"User config '{config_name}'.{field} must be a boolean")
                    elif field in ["min", "max"] and not isinstance(config_def[field], (int, float)):
                        self.errors.append(f"User config '{config_name}'.{field} must be a number")
    
    def _validate_tools(self, tools: List[Dict[str, Any]]) -> None:
        """Validate tools section."""
        for i, tool in enumerate(tools):
            if not isinstance(tool, dict):
                self.errors.append(f"Tool {i} must be a dict")
                continue
            
            if "name" not in tool:
                self.errors.append(f"Tool {i} missing required field: name")
            elif not isinstance(tool["name"], str):
                self.errors.append(f"Tool {i} name must be a string")
            
            if "description" in tool and not isinstance(tool["description"], str):
                self.errors.append(f"Tool {i} description must be a string")
    
    def print_results(self) -> None:
        """Print validation results."""
        if self.errors:
            print("❌ Validation Errors:")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print("⚠️  Validation Warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if not self.errors and not self.warnings:
            print("✅ Manifest validation passed!")
        elif not self.errors:
            print("✅ Manifest validation passed with warnings")


def main():
    """Main validation function."""
    if len(sys.argv) != 2:
        print("Usage: python validate_manifest.py <manifest.json>")
        sys.exit(1)
    
    manifest_path = Path(sys.argv[1])
    validator = ManifestValidator(manifest_path)
    
    print(f"Validating manifest: {manifest_path}")
    print("=" * 50)
    
    is_valid = validator.validate()
    validator.print_results()
    
    if not is_valid:
        sys.exit(1)


if __name__ == "__main__":
    main()