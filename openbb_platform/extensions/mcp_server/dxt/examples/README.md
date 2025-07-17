# OpenBB MCP Server DXT Examples

This directory contains examples of how to use the OpenBB MCP Server DXT with different MCP clients.

## Claude Desktop Configuration

After installing the DXT through drag-and-drop, Claude Desktop will automatically create a configuration similar to:

```json
{
  "mcpServers": {
    "openbb-mcp": {
      "command": "python",
      "args": [
        "/Users/username/.claude/extensions/openbb-mcp-server/server/main.py",
        "--transport",
        "stdio"
      ],
      "env": {
        "OPENBB_MCP_DEFAULT_TOOL_CATEGORIES": "admin",
        "OPENBB_MCP_ENABLE_TOOL_DISCOVERY": "true",
        "OPENBB_MCP_DESCRIBE_ALL_RESPONSES": "false",
        "OPENBB_MCP_API_KEYS_CONFIG": "{\"fmp\":{\"api_key\":\"your_key_here\"}}",
        "PYTHONPATH": "/Users/username/.claude/extensions/openbb-mcp-server/lib"
      }
    }
  }
}
```

## Cursor IDE Configuration

For Cursor IDE, add to your `mcp.json`:

```json
{
  "mcpServers": {
    "openbb-mcp": {
      "command": "python",
      "args": [
        "/path/to/extracted/openbb-mcp-server/server/main.py",
        "--transport",
        "stdio"
      ],
      "env": {
        "OPENBB_MCP_DEFAULT_TOOL_CATEGORIES": "equity,news",
        "OPENBB_MCP_ENABLE_TOOL_DISCOVERY": "true",
        "OPENBB_MCP_API_KEYS_CONFIG": "{\"fmp\":{\"api_key\":\"your_fmp_key\"}}"
      }
    }
  }
}
```

## VS Code Configuration

For VS Code with MCP extension support:

```json
{
  "mcpServers": {
    "openbb-mcp": {
      "command": "python",
      "args": [
        "/path/to/extracted/openbb-mcp-server/server/main.py",
        "--transport",
        "stdio"
      ],
      "env": {
        "OPENBB_MCP_DEFAULT_TOOL_CATEGORIES": "admin",
        "OPENBB_MCP_ENABLE_TOOL_DISCOVERY": "true"
      }
    }
  }
}
```

## Environment Variables Reference

The DXT server supports these environment variables:

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `OPENBB_MCP_DEFAULT_TOOL_CATEGORIES` | Categories enabled at startup | "admin" | "equity,crypto,news" |
| `OPENBB_MCP_ALLOWED_TOOL_CATEGORIES` | Allowed categories (empty = all) | "" | "equity,news" |
| `OPENBB_MCP_ENABLE_TOOL_DISCOVERY` | Enable discovery tools | "true" | "true" or "false" |
| `OPENBB_MCP_DESCRIBE_ALL_RESPONSES` | Include response info | "false" | "true" or "false" |
| `OPENBB_MCP_API_KEYS_CONFIG` | API keys JSON configuration | "{}" | See below |

## API Keys Configuration Examples

### Single Provider
```json
{
  "fmp": {
    "api_key": "your_financial_modeling_prep_key"
  }
}
```

### Multiple Providers
```json
{
  "fmp": {
    "api_key": "your_fmp_key"
  },
  "alpha_vantage": {
    "api_key": "your_av_key"
  },
  "polygon": {
    "api_key": "your_polygon_key"
  }
}
```

### Advanced Configuration
```json
{
  "fmp": {
    "api_key": "your_fmp_key"
  },
  "fred": {
    "api_key": "your_fred_key"
  },
  "alpha_vantage": {
    "api_key": "your_av_key",
    "premium": true
  }
}
```

## Usage Examples

### Discovery Workflow

1. **Start with admin tools only**:
   ```
   OPENBB_MCP_DEFAULT_TOOL_CATEGORIES="admin"
   ```

2. **Discover available categories**:
   ```
   User: What financial data categories are available?
   Assistant: [Uses discover_tool_categories]
   Available categories: equity, crypto, economy, news, fixedincome, etf, derivatives, currency, commodity, index, regulators
   ```

3. **Enable specific categories**:
   ```
   User: I need stock market data
   Assistant: [Uses enable_tool_categories with "equity"]
   I've enabled equity tools for you.
   ```

4. **Use the tools**:
   ```
   User: Get Apple's current stock price
   Assistant: [Uses openbb_equity_price_quote with symbol="AAPL"]
   ```

### Direct Access Workflow

1. **Start with specific categories**:
   ```
   OPENBB_MCP_DEFAULT_TOOL_CATEGORIES="equity,news"
   ```

2. **Tools are immediately available**:
   ```
   User: Get Tesla's stock price and recent news
   Assistant: [Uses openbb_equity_price_quote and openbb_news_company]
   ```

## Command Line Testing

You can test the DXT server directly from the command line:

```bash
# Extract the DXT package
unzip openbb-mcp-server.dxt -d test-dir

# Set environment variables
export OPENBB_MCP_DEFAULT_TOOL_CATEGORIES="admin"
export OPENBB_MCP_ENABLE_TOOL_DISCOVERY="true"
export OPENBB_MCP_API_KEYS_CONFIG='{"fmp":{"api_key":"your_key"}}'

# Run the server
cd test-dir
python server/main.py --transport stdio
```

## Troubleshooting Examples

### Issue: Import Error
```bash
Error: Could not import OpenBB MCP server: No module named 'openbb_mcp_server'
```

**Solution**: Ensure dependencies are bundled correctly:
```bash
# Check if lib directory exists
ls -la lib/

# Check PYTHONPATH
echo $PYTHONPATH
```

### Issue: API Key Not Working
```bash
Warning: Invalid API keys configuration: Expecting property name enclosed in double quotes
```

**Solution**: Ensure JSON is properly formatted:
```json
{
  "fmp": {
    "api_key": "your_key_here"
  }
}
```

### Issue: No Tools Available
```bash
No tools available in the current configuration
```

**Solution**: Check category configuration:
```bash
# Enable discovery tools
export OPENBB_MCP_DEFAULT_TOOL_CATEGORIES="admin"

# Or enable specific categories
export OPENBB_MCP_DEFAULT_TOOL_CATEGORIES="equity,news"
```