# OpenBB MCP Server DXT Extension

This directory contains the Desktop Extension (DXT) package for the OpenBB MCP Server, enabling single-click installation and configuration of the OpenBB MCP server in compatible applications like Claude Desktop.

## What is DXT?

Desktop Extensions (DXT) are zip archives containing a local MCP server and a `manifest.json` that describes the server and its capabilities. The format enables end users to install local MCP servers with a single click, similar to Chrome extensions or VS Code extensions.

## Package Contents

```
openbb-mcp-server.dxt (ZIP file)
├── manifest.json         # Extension metadata and configuration
├── server/               # Server files
│   └── main.py          # DXT entry point that configures and launches OpenBB MCP server
├── lib/                  # Bundled Python dependencies
├── assets/               # Extension assets (icons, etc.)
└── requirements.txt      # Dependencies reference
```

## Features

- **Single-click installation**: No manual configuration of MCP server settings
- **User-friendly configuration**: GUI-based setup for API keys and server options
- **Bundled dependencies**: All required Python packages included
- **Cross-platform**: Works on macOS, Windows, and Linux
- **API key management**: Secure handling of data provider API keys through DXT user configuration
- **Customizable settings**: Configure tool categories, discovery features, and response descriptions

## User Configuration Options

The DXT extension provides the following configuration options:

### Tool Categories
- **Default Tool Categories**: Categories enabled at startup (default: "admin" for discovery tools only)
- **Allowed Tool Categories**: Restrict which categories can be enabled (empty = all allowed)

### Discovery Settings
- **Enable Tool Discovery**: Allow dynamic tool activation during sessions
- **Describe Responses**: Include response information in tool descriptions

### API Keys
- **API Keys Configuration**: JSON configuration for data provider API keys (e.g., FMP, Alpha Vantage, etc.)

## Building the DXT Package

To build the DXT package from source:

1. Ensure you have Python 3.10+ installed
2. Navigate to the DXT directory:
   ```bash
   cd openbb_platform/extensions/mcp_server/dxt
   ```
3. Run the build script:
   ```bash
   python build_dxt.py
   ```

This will create `openbb-mcp-server.dxt` in the current directory.

## Installation

### Claude Desktop
1. Download the `openbb-mcp-server.dxt` file
2. Open Claude Desktop
3. Drag and drop the `.dxt` file into Claude Desktop
4. Follow the installation prompts to configure your settings
5. The OpenBB MCP server will be available as a tool source

### Other MCP Clients
Any MCP client that supports the DXT format can install and use this extension. Refer to your client's documentation for specific installation instructions.

## Configuration

When installing the DXT extension, you'll be prompted to configure:

1. **Tool Categories**: Choose which OpenBB data categories to enable
2. **Discovery Mode**: Enable/disable dynamic tool discovery
3. **API Keys**: Configure API keys for premium data providers
4. **Response Details**: Choose whether to include response schemas in tool descriptions

## API Key Configuration

The extension supports API key configuration for various data providers. Provide your API keys in JSON format:

```json
{
  "fmp": {
    "api_key": "your_fmp_api_key_here"
  },
  "alpha_vantage": {
    "api_key": "your_alpha_vantage_key_here"
  },
  "polygon": {
    "api_key": "your_polygon_key_here"
  }
}
```

## Available Tool Categories

The OpenBB MCP server provides tools across multiple financial data categories:

- **admin**: Discovery and management tools
- **equity**: Stock data, fundamentals, price history
- **crypto**: Cryptocurrency data and analysis
- **economy**: Economic indicators and data
- **news**: Financial news from various sources
- **fixedincome**: Bond data and rates
- **derivatives**: Options and futures data
- **etf**: ETF information and holdings
- **currency**: Foreign exchange data
- **commodity**: Commodity prices and data
- **index**: Market indices data
- **regulators**: SEC, CFTC regulatory data

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure all dependencies are properly bundled in the lib/ directory
2. **API key issues**: Check that API keys are properly formatted in the configuration
3. **Permission errors**: Make sure the extension has permission to create configuration files in the home directory

### Debug Mode

To enable debug logging, set the environment variable:
```bash
OPENBB_MCP_DEBUG=true
```

## Development

### Directory Structure

- `manifest.json`: Extension metadata and configuration schema
- `server/main.py`: DXT entry point that handles configuration and launches the server
- `build_dxt.py`: Build script for creating the DXT package
- `assets/`: Icons and other static assets

### Customization

To customize the DXT extension:

1. Edit `manifest.json` to modify configuration options or metadata
2. Update `server/main.py` to change how configuration is handled
3. Modify `build_dxt.py` to change the build process
4. Add assets to the `assets/` directory

### Testing

Test the DXT package by:

1. Building the package with `python build_dxt.py`
2. Installing it in a compatible MCP client
3. Verifying that configuration options work correctly
4. Testing tool functionality with various data providers

## License

This DXT extension is licensed under the same terms as the OpenBB Platform (AGPL-3.0-only).

## Support

For issues with the DXT extension, please:

1. Check the troubleshooting section above
2. Review the OpenBB MCP server documentation
3. File an issue on the OpenBB GitHub repository
4. Join the OpenBB community for support