#!/usr/bin/env python3
"""
Test script for OpenBB MCP Server DXT package.

This script validates the DXT package structure and tests basic functionality.
"""

import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path

def test_dxt_package(dxt_path: Path):
    """Test the DXT package structure and content."""
    print(f"Testing DXT package: {dxt_path}")
    
    if not dxt_path.exists():
        print(f"❌ DXT package not found: {dxt_path}")
        return False
    
    # Test 1: Check if it's a valid ZIP file
    try:
        with zipfile.ZipFile(dxt_path, 'r') as zipf:
            file_list = zipf.namelist()
            print(f"✅ Valid ZIP file with {len(file_list)} files")
    except zipfile.BadZipFile:
        print("❌ Invalid ZIP file")
        return False
    
    # Test 2: Check required files
    required_files = ['manifest.json', 'server/main.py']
    missing_files = []
    
    for required_file in required_files:
        if required_file not in file_list:
            missing_files.append(required_file)
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return False
    else:
        print("✅ All required files present")
    
    # Test 3: Validate manifest.json
    with zipfile.ZipFile(dxt_path, 'r') as zipf:
        try:
            manifest_content = zipf.read('manifest.json').decode('utf-8')
            manifest = json.loads(manifest_content)
            print("✅ Valid manifest.json")
            
            # Check required manifest fields
            required_fields = ['dxt_version', 'name', 'version', 'description', 'author', 'server']
            missing_fields = []
            
            for field in required_fields:
                if field not in manifest:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"❌ Missing required manifest fields: {missing_fields}")
                return False
            else:
                print("✅ All required manifest fields present")
            
            # Check server configuration
            server_config = manifest.get('server', {})
            if server_config.get('type') != 'python':
                print("❌ Server type should be 'python'")
                return False
            
            if server_config.get('entry_point') != 'server/main.py':
                print("❌ Entry point should be 'server/main.py'")
                return False
            
            print("✅ Valid server configuration")
            
        except json.JSONDecodeError as e:
            print(f"❌ Invalid manifest.json: {e}")
            return False
    
    # Test 4: Check server entry point
    with zipfile.ZipFile(dxt_path, 'r') as zipf:
        try:
            server_content = zipf.read('server/main.py').decode('utf-8')
            if 'def main()' not in server_content:
                print("❌ Server entry point missing main() function")
                return False
            print("✅ Valid server entry point")
        except Exception as e:
            print(f"❌ Could not read server entry point: {e}")
            return False
    
    # Test 5: Check user configuration
    user_config = manifest.get('user_config', {})
    if not user_config:
        print("⚠️  No user configuration defined")
    else:
        print(f"✅ User configuration with {len(user_config)} options")
    
    # Test 6: Check compatibility
    compatibility = manifest.get('compatibility', {})
    if 'python' not in compatibility.get('runtimes', {}):
        print("⚠️  No Python version specified in compatibility")
    else:
        print("✅ Python version compatibility specified")
    
    print(f"✅ DXT package validation passed: {dxt_path.name}")
    return True

def test_manifest_schema(manifest_path: Path):
    """Test manifest.json schema independently."""
    print(f"Testing manifest schema: {manifest_path}")
    
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        # Basic schema validation
        print(f"  Name: {manifest.get('name')}")
        print(f"  Version: {manifest.get('version')}")
        print(f"  Description: {manifest.get('description')}")
        print(f"  Server Type: {manifest.get('server', {}).get('type')}")
        print(f"  Entry Point: {manifest.get('server', {}).get('entry_point')}")
        print(f"  User Config Options: {len(manifest.get('user_config', {}))}")
        print(f"  Tools Count: {len(manifest.get('tools', []))}")
        
        return True
    except Exception as e:
        print(f"❌ Manifest schema test failed: {e}")
        return False

def main():
    """Main test function."""
    print("OpenBB MCP Server DXT Package Test")
    print("=" * 40)
    
    # Find DXT files
    dxt_dir = Path(__file__).parent
    manifest_path = dxt_dir / "manifest.json"
    dxt_path = dxt_dir / "openbb-mcp-server.dxt"
    
    success = True
    
    # Test manifest schema
    if manifest_path.exists():
        success &= test_manifest_schema(manifest_path)
    else:
        print("⚠️  manifest.json not found for schema testing")
    
    print()
    
    # Test DXT package
    if dxt_path.exists():
        success &= test_dxt_package(dxt_path)
    else:
        print(f"⚠️  DXT package not found: {dxt_path}")
        print("Run 'python build_dxt.py' to create the package first")
        success = False
    
    print()
    
    if success:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())