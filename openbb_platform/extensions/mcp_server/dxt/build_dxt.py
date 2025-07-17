#!/usr/bin/env python3
"""
Build script for creating OpenBB MCP Server DXT package.

This script builds the DXT package by:
1. Creating the necessary directory structure
2. Copying the OpenBB MCP server files
3. Bundling Python dependencies
4. Creating the final DXT zip file
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

def run_command(cmd, cwd=None, capture_output=True):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=capture_output, text=True)
    if result.returncode != 0:
        print(f"Error running command: {result.stderr}")
        sys.exit(1)
    return result

def create_build_directory():
    """Create and return a temporary build directory."""
    build_dir = Path(tempfile.mkdtemp(prefix="openbb_mcp_dxt_"))
    print(f"Build directory: {build_dir}")
    return build_dir

def copy_dxt_files(build_dir: Path):
    """Copy DXT files to build directory."""
    dxt_dir = Path(__file__).parent
    
    # Copy manifest.json
    shutil.copy2(dxt_dir / "manifest.json", build_dir / "manifest.json")
    
    # Copy server directory
    server_src = dxt_dir / "server"
    server_dst = build_dir / "server"
    shutil.copytree(server_src, server_dst)
    
    # Copy assets if they exist
    assets_src = dxt_dir / "assets"
    if assets_src.exists():
        assets_dst = build_dir / "assets"
        shutil.copytree(assets_src, assets_dst)
    
    print("DXT files copied successfully")

def bundle_dependencies(build_dir: Path):
    """Bundle Python dependencies into the lib directory."""
    lib_dir = build_dir / "lib"
    lib_dir.mkdir(exist_ok=True)
    
    # Get the path to the MCP server extension
    mcp_server_dir = Path(__file__).parent.parent
    
    # Install dependencies to lib directory
    pip_cmd = [
        sys.executable, "-m", "pip", "install",
        "--target", str(lib_dir),
        "--no-deps",  # Don't install dependencies of dependencies for now
        str(mcp_server_dir)
    ]
    
    try:
        run_command(pip_cmd)
        print("Dependencies bundled successfully")
    except Exception as e:
        print(f"Warning: Could not bundle dependencies: {e}")
        print("You may need to manually install dependencies or create a virtual environment")

def create_requirements_txt(build_dir: Path):
    """Create requirements.txt for reference."""
    requirements_content = """# OpenBB MCP Server DXT Requirements
# These dependencies should be bundled in the lib/ directory

openbb-core>=1.4.3
fastmcp>=2.10.5
fastapi
uvicorn
pydantic
starlette
"""
    
    with open(build_dir / "requirements.txt", "w") as f:
        f.write(requirements_content)

def create_dxt_package(build_dir: Path, output_path: Path):
    """Create the final DXT zip package."""
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(build_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(build_dir)
                zipf.write(file_path, arcname)
    
    print(f"DXT package created: {output_path}")

def main():
    """Main build function."""
    print("Building OpenBB MCP Server DXT package...")
    
    # Create build directory
    build_dir = create_build_directory()
    
    try:
        # Copy DXT files
        copy_dxt_files(build_dir)
        
        # Bundle dependencies
        bundle_dependencies(build_dir)
        
        # Create requirements.txt for reference
        create_requirements_txt(build_dir)
        
        # Create the DXT package
        output_dir = Path(__file__).parent
        output_path = output_dir / "openbb-mcp-server.dxt"
        create_dxt_package(build_dir, output_path)
        
        print(f"✅ DXT package built successfully: {output_path}")
        print(f"Package size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
        
    except Exception as e:
        print(f"❌ Build failed: {e}")
        sys.exit(1)
    
    finally:
        # Clean up build directory
        shutil.rmtree(build_dir)

if __name__ == "__main__":
    main()