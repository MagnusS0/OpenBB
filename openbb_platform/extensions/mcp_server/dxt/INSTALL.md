# OpenBB MCP Server DXT Installation Guide

This guide explains how to install and use the OpenBB MCP Server DXT (Desktop Extension) with different MCP clients.

## Prerequisites

- MCP client that supports DXT format (e.g., Claude Desktop)
- Python 3.10 or higher (for manual installation)
- Active internet connection (for data provider APIs)

## Installation Methods

### Method 1: Single-Click Installation (Recommended)

1. **Download the DXT package**:
   - Download `openbb-mcp-server.dxt` from the releases or build it yourself
   
2. **Install in Claude Desktop**:
   - Open Claude Desktop
   - Drag and drop the `openbb-mcp-server.dxt` file into the Claude Desktop window
   - Follow the installation wizard

3. **Configure settings**:
   - **Default Tool Categories**: Set to "admin" for minimal startup (recommended)
   - **Enable Tool Discovery**: Leave enabled to dynamically discover tools
   - **API Keys Configuration**: Add your data provider API keys (optional)

### Method 2: Manual Installation

If your MCP client doesn't support DXT files directly, you can extract and configure manually:

1. **Extract the DXT package**:
   ```bash
   unzip openbb-mcp-server.dxt -d openbb-mcp-server
   ```

2. **Install dependencies**:
   ```bash
   cd openbb-mcp-server
   pip install -r requirements.txt
   ```

3. **Configure your MCP client**:
   Add the following to your MCP client configuration:
   ```json
   {
     "mcpServers": {
       "openbb-mcp": {
         "command": "python",
         "args": ["/path/to/openbb-mcp-server/server/main.py", "--transport", "stdio"],
         "env": {
           "OPENBB_MCP_DEFAULT_TOOL_CATEGORIES": "admin",
           "OPENBB_MCP_ENABLE_TOOL_DISCOVERY": "true"
         }
       }
     }
   }
   ```

## Configuration Options

### Tool Categories

Choose which data categories to enable:
- `admin`: Discovery and management tools (always recommended)
- `equity`: Stock market data
- `crypto`: Cryptocurrency data
- `economy`: Economic indicators
- `news`: Financial news
- `fixedincome`: Bond and fixed income data
- `etf`: ETF data
- `derivatives`: Options and futures
- `currency`: Foreign exchange
- `commodity`: Commodity data
- `index`: Market indices
- `regulators`: Regulatory data

### API Keys

Configure API keys for premium data providers:

```json
{
  "fmp": {
    "api_key": "your_financial_modeling_prep_key"
  },
  "alpha_vantage": {
    "api_key": "your_alpha_vantage_key"
  },
  "polygon": {
    "api_key": "your_polygon_key"
  },
  "fred": {
    "api_key": "your_fred_key"
  }
}
```

## Usage Examples

### Starting with Discovery Tools

1. Set **Default Tool Categories** to "admin"
2. Enable **Tool Discovery**
3. In your MCP client, use the discovery tools:
   - `discover_tool_categories`: See available categories
   - `list_available_tools`: Browse tools in specific categories
   - `enable_tool_categories`: Activate the tools you need

### Direct Category Access

1. Set **Default Tool Categories** to specific categories (e.g., "equity,news")
2. Tools from those categories will be immediately available
3. No need to use discovery tools first

### Example Workflow

1. **Start with discovery**:
   ```
   User: What financial data can you access?
   Assistant: Let me check what tools are available.
   [Uses: discover_tool_categories]
   ```

2. **Enable specific tools**:
   ```
   User: I need stock market data for Apple
   Assistant: I'll enable equity tools for you.
   [Uses: enable_tool_categories with "equity"]
   ```

3. **Access financial data**:
   ```
   User: Get me Apple's stock price
   Assistant: [Uses: openbb_equity_price_quote with symbol="AAPL"]
   ```

## Troubleshooting

### Common Issues

1. **"Module not found" errors**:
   - Ensure all dependencies are bundled in the lib/ directory
   - Check that Python version is compatible (3.10+)

2. **API key issues**:
   - Verify API keys are correctly formatted in JSON
   - Check that the data provider is supported by OpenBB

3. **Connection errors**:
   - Ensure MCP client is properly configured
   - Check transport type (stdio for most clients)

### Debug Mode

Enable debug logging by setting environment variable:
```bash
OPENBB_MCP_DEBUG=true
```

### Getting Help

- Check the OpenBB MCP Server documentation
- Review the DXT README.md file
- File issues on the OpenBB GitHub repository
- Join the OpenBB community Discord

## Supported MCP Clients

- Claude Desktop (recommended)
- Cursor IDE
- VS Code with MCP extension
- Any MCP client supporting DXT format

## Data Providers

The OpenBB MCP Server supports numerous data providers:
- Financial Modeling Prep (FMP)
- Alpha Vantage
- Polygon
- FRED (Federal Reserve Economic Data)
- Yahoo Finance
- And many more...

Check the OpenBB documentation for a complete list of supported providers and their API key requirements.