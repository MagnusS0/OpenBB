# OpenBB MCP Server

This extension enables LLM agents to interact with OpenBB Platform's REST API endpoints through the MCP protocol.

The server supports two transform-based discovery flows:

- `search` mode: hides the full tool catalog and lets agents discover tools with `list_categories`, `search`, `get_schema`, and `call_tool`.
- `Code Mode`: keeps the same discovery flow but adds sandboxed `execute` for chained post-processing and analysis.

Both flows keep the startup token usage low while preserving access to the full OpenBB tool catalog.

## Installation & Usage

```bash
pip install openbb-mcp-server
```

Start the OpenBB MCP server with default settings:

```bash
openbb-mcp
```

Or use the `uvx` command:

```bash
uvx --from openbb-mcp-server --with openbb openbb-mcp
```

### Command Line Options

Enter `openbb-mcp --help` to see the docstring from the command line.

```sh
--help
    Show this help message and exit.

--app <app_path>
    The path to the FastAPI app instance. This can be in the format
    'module.path:app_instance' or a file path 'path/to/app.py'.
    If not provided, the server will run with the default built-in app.

--name <name>
    The name of the FastAPI app instance or factory function in the app file.
    Defaults to 'app'.

--factory
    If set, the app is treated as a factory function that will be called
    to create the FastAPI app instance.

--host <host>
    The host to bind the server to. Defaults to '127.0.0.1'.
    This is a uvicorn argument.

--port <port>
    The port to bind the server to. Defaults to 8000.
    This is a uvicorn argument.

--transport <transport>
    The transport mechanism to use for the MCP server.
    Defaults to 'streamable-http'.

--allowed-categories <categories>
    A comma-separated list of tool categories to allow.
    If not provided, all categories are allowed.

--default-categories <categories>
    A comma-separated list of tool categories to be enabled by default.
    Defaults to 'all'.

--no-tool-discovery
    If set, transform-based tool discovery will be disabled.

--enable-code-mode
    If set, enable FastMCP Code Mode with sandboxed `execute`.

--system-prompt <path>
    Path to a TXT file with the system prompt.

--server-prompts <path>
    Path to a JSON file with a list of server prompts.
```

#### All other arguments are parsed into `MCPSettings`, including flags such as `--enable-code-mode`, `--code-mode-search-max-results`, `--include-tags`, and `--exclude-tags`.

## Configuration

The server can be configured through multiple methods, with settings applied in the following order of precedence:

1. **Command Line Arguments**: Highest priority, overriding all other methods.
2. **Environment Variables**: Each setting can be controlled by an environment variable, which will override the configuration file.
3. **Configuration File**: A JSON file at `~/.openbb_platform/mcp_settings.json` provides the base configuration.
   - If the configuration file does not exist, one will be populated with the defaults.

> **Note:** For some data providers you need to set your API key in the `~/.openbb_platform/user_settings.json` file.

### Authentication

The MCP server supports client-side and server-side authentication to secure your endpoints.

#### Server-Side Authentication

Server-side authentication requires incoming requests to provide credentials. This is configured using the `server_auth` setting, which accepts a tuple of `(username, password)`.

When `server_auth` is enabled, clients must include an `Authorization` header with a `Bearer` token. The token should be a Base64-encoded string of `username:password`.

**Example: Environment Variable**

```env
OPENBB_MCP_SERVER_AUTH='["myuser", "mypass"]'
```

**Example: `mcp_settings.json`**

```json
{
  "server_auth": ["myuser", "mypass"]
}
```

#### Client-Side Authentication

Client-side authentication configures the MCP server to use credentials when making downstream requests. This is useful when the server needs to authenticate with other services.

**Example: Environment Variable**

```env
OPENBB_MCP_CLIENT_AUTH='["client_user", "client_pass"]'
```

**Example: `mcp_settings.json`**

```json
{
  "client_auth": ["client_user", "client_pass"]
}
```

#### Programmatic Authentication

For advanced use cases, you can pass a pre-configured authentication object directly to the `create_mcp_server` function using the `auth` parameter. This allows you to implement custom authentication logic or use third-party authentication providers.

```python
from fastmcp.server.auth.providers import BearerProvider
from openbb_mcp_server.app import create_mcp_server

# Create a custom auth provider
custom_auth = BearerProvider(...)

# Pass it to the server
mcp_server = create_mcp_server(settings, fastapi_app, auth=custom_auth)
```

### Advanced Configuration: Lists and Dictionaries

For settings that accept a list or a dictionary, you have two flexible formats for defining them in both command-line arguments and environment variables.

#### 1. Comma-Separated Strings

This is a simple and readable way to define lists and simple dictionaries.

- **Lists**: Provide a string of comma-separated values.
  - Example: `equity,news,crypto`
- **Dictionaries**: Provide a string of comma-separated `key:value` pairs.
  - Example: `host:0.0.0.0,port:9000`

#### 2. JSON-Encoded Strings

For more complex data structures, or to ensure precise type handling (e.g., for numbers and booleans), you can use a JSON-encoded string.

- **Lists**: A standard JSON array.
  - Example: `'["equity", "news", "crypto"]'`
- **Dictionaries**: A standard JSON object.
  - Example: `'{"host": "0.0.0.0", "port": 9000}'`

**Important Note on Quoting**: When passing JSON-encoded strings on the command line, it is highly recommended to wrap the entire string in **single quotes (`'`)**. This prevents your shell from interpreting the double quotes (`"`) inside the JSON string, which can lead to parsing errors.

#### Practical Examples

Here’s how you can apply these formats in practice:

**Command-Line Arguments:**

```sh
# List with comma-separated values
openbb-mcp --default-categories equity,news

# List with a JSON-encoded string (note the single quotes)
openbb-mcp --default-categories '["equity", "news"]'

# Dictionary with comma-separated key:value pairs
openbb-mcp --uvicorn-config "host:0.0.0.0,port:9000"

# Dictionary with a JSON-encoded string (note the single quotes)
openbb-mcp --uvicorn-config '{"host": "0.0.0.0", "port": 9000, "env_file": "./path_to/.env"}'
```

**Environment Variables (in a `.env` file):**

```env
# List with comma-separated values
OPENBB_MCP_DEFAULT_TOOL_CATEGORIES="equity,news"

# List with a JSON-encoded string
OPENBB_MCP_DEFAULT_TOOL_CATEGORIES='["equity", "news"]'

# Dictionary with comma-separated key:value pairs
OPENBB_MCP_UVICORN_CONFIG="host:0.0.0.0,port:9000"

# Dictionary with a JSON-encoded string
OPENBB_MCP_UVICORN_CONFIG='{"host": "0.0.0.0", "port": 9000, "env_file": "./path_to/.env"}'
```

## Settings Reference

All settings in the `MCPSettings` model can be configured via the `mcp_settings.json` file or as environment variables.

| Setting | Environment Variable | Type | Default | Description |
|---|---|---|---|---|
| `api_prefix` | `OPENBB_MCP_API_PREFIX` | string | `None` | Overrides the API prefix from SystemService. |
| `name` | `OPENBB_MCP_NAME` | string | `"OpenBB MCP"` | Server name. |
| `description` | `OPENBB_MCP_DESCRIPTION` | string | built-in description | Server description. |
| `version` | `OPENBB_MCP_VERSION` | string | `None` | Server version. |
| `instructions` | `OPENBB_MCP_INSTRUCTIONS` | string | `None` | Server instructions sent during the MCP `initialize` handshake. Auto-populated from the system prompt when not set. |
| `default_tool_categories` | `OPENBB_MCP_DEFAULT_TOOL_CATEGORIES` | list[string] | `["all"]` | Categories enabled by default before transforms are applied. |
| `allowed_tool_categories` | `OPENBB_MCP_ALLOWED_TOOL_CATEGORIES` | list[string] | `None` | Restricts exposed tool categories to this list. |
| `enable_code_mode` | `OPENBB_MCP_ENABLE_CODE_MODE` | boolean | `False` | Enable FastMCP Code Mode with sandboxed `execute`. |
| `code_mode_max_duration_secs` | `OPENBB_MCP_CODE_MODE_MAX_DURATION_SECS` | float | `30.0` | Maximum sandbox execution duration in seconds. |
| `code_mode_max_memory` | `OPENBB_MCP_CODE_MODE_MAX_MEMORY` | integer | `536870912` | Maximum sandbox memory allocation in bytes. |
| `code_mode_max_allocations` | `OPENBB_MCP_CODE_MODE_MAX_ALLOCATIONS` | integer | `None` | Optional allocation cap for sandbox execution. |
| `code_mode_max_recursion_depth` | `OPENBB_MCP_CODE_MODE_MAX_RECURSION_DEPTH` | integer | `None` | Optional recursion-depth cap for sandbox execution. |
| `code_mode_gc_interval` | `OPENBB_MCP_CODE_MODE_GC_INTERVAL` | integer | `None` | Optional garbage-collection interval for sandbox execution. |
| `code_mode_search_max_results` | `OPENBB_MCP_CODE_MODE_SEARCH_MAX_RESULTS` | integer | `30` | Maximum cap for discovery results returned by `search`. |
| `code_mode_search_output_format` | `OPENBB_MCP_CODE_MODE_SEARCH_OUTPUT_FORMAT` | string | `"markdown"` | Discovery output format for `search`, `list_categories`, and schema rendering. |
| `enable_tool_discovery` | `OPENBB_MCP_ENABLE_TOOL_DISCOVERY` | boolean | `True` | Enable standalone search discovery mode when Code Mode is disabled. |
| `list_page_size` | `OPENBB_MCP_LIST_PAGE_SIZE` | integer | `None` | Max items per page in MCP list responses. `None` disables pagination. |
| `describe_responses` | `OPENBB_MCP_DESCRIBE_RESPONSES` | boolean | `False` | Include response types in tool descriptions. |
| `system_prompt_file` | `OPENBB_MCP_SYSTEM_PROMPT_FILE` | string | `None` | Path to a text file for the system prompt. |
| `server_prompts_file` | `OPENBB_MCP_SERVER_PROMPTS_FILE` | string | `None` | Path to a JSON file with a list of server prompt definitions. |
| `default_skills_dir` | `OPENBB_MCP_DEFAULT_SKILLS_DIR` | string | bundled skills dir | Path to bundled skill files. Set to `null` to disable. |
| `skills_reload` | `OPENBB_MCP_SKILLS_RELOAD` | boolean | `False` | Reload skill files on every read. Useful during development. |
| `skills_providers` | `OPENBB_MCP_SKILLS_PROVIDERS` | list[string] | `None` | Vendor skill provider short-names to load, for example `claude`, `cursor`, `codex`, or `vscode`. |
| `cache_expiration_seconds` | `OPENBB_MCP_CACHE_EXPIRATION_SECONDS` | float | `None` | Cache expiration time in seconds. `0` disables caching. |
| `on_duplicate_tools` | `OPENBB_MCP_ON_DUPLICATE_TOOLS` | string | `None` | Behavior for duplicate tools (`warn`, `error`, `replace`, `ignore`). |
| `on_duplicate_resources` | `OPENBB_MCP_ON_DUPLICATE_RESOURCES` | string | `None` | Behavior for duplicate resources. |
| `on_duplicate_prompts` | `OPENBB_MCP_ON_DUPLICATE_PROMPTS` | string | `None` | Behavior for duplicate prompts. |
| `resource_prefix_format` | `OPENBB_MCP_RESOURCE_PREFIX_FORMAT` | string | `None` | Format for resource URI prefixes (`protocol` or `path`). |
| `mask_error_details` | `OPENBB_MCP_MASK_ERROR_DETAILS` | boolean | `None` | Mask error details from user functions. |
| `dependencies` | `OPENBB_MCP_DEPENDENCIES` | list[string] | `None` | Dependencies to install in the server environment. |
| `include_tags` | `OPENBB_MCP_INCLUDE_TAGS` | list[string] | `None` | Only expose components matching these tags. |
| `exclude_tags` | `OPENBB_MCP_EXCLUDE_TAGS` | list[string] | `None` | Exclude components matching these tags. |
| `module_exclusion_map` | `OPENBB_MCP_MODULE_EXCLUSION_MAP` | dict[str, str] | `None` | Map API tags to Python module names for exclusion. |
| `uvicorn_config` | `OPENBB_MCP_UVICORN_CONFIG` | dict | `{"host": "127.0.0.1", "port": "8001"}` | Configuration for the Uvicorn server. |
| `httpx_client_kwargs` | `OPENBB_MCP_HTTPX_CLIENT_KWARGS` | dict | `{}` | Configuration for the async httpx client. |
| `client_auth` | `OPENBB_MCP_CLIENT_AUTH` | tuple[string, string] | `None` | `(username, password)` for client-side basic authentication. |
| `server_auth` | `OPENBB_MCP_SERVER_AUTH` | tuple[string, string] | `None` | `(username, password)` for server-side basic authentication. |

> **Note:** Runtime argument keys, in general, `-` and `_` are interchangeable. Nested uvicorn arguments should use `_`.

## Tool Categories

The server organizes OpenBB tools into categories based on the included API routers (paths). Categories depend on the installed extensions, but they generally align with the first path segment after the API prefix.

For example:

- **`equity`**: Stock data, fundamentals, price history, estimates
- **`crypto`**: Cryptocurrency data and analysis
- **`economy`**: Economic indicators, GDP, employment data
- **`news`**: Financial news from various sources
- **`fixedincome`**: Bond data, rates, government securities
- **`derivatives`**: Options and futures data
- **`etf`**: ETF information and holdings
- **`currency`**: Foreign exchange data
- **`commodity`**: Commodity prices and data
- **`index`**: Market indices data
- **`regulators`**: SEC, CFTC regulatory data

Each category contains subcategories that group related functionality, for example `equity_price` and `equity_fundamental`.

## Discovery Modes

### Standalone Search Mode

When `enable_tool_discovery=true` and `enable_code_mode=false`, the server exposes discovery tools instead of the full catalog:

- **`list_categories`**: Return category/subcategory counts, optionally filtered by category, subcategory, or provider.
- **`search`**: BM25-search the OpenBB tool catalog with optional `categories`, `subcategories`, `providers`, and `max_results` filters.
- **`get_schema`**: Return full parameter schemas for one or more discovered tools.
- **`call_tool`**: Execute a discovered tool directly.

This mode keeps the tool surface compact without requiring a per-session activation step.

### Code Mode

When `enable_code_mode=true`, the server installs FastMCP Code Mode on top of the same OpenBB-specific BM25 discovery flow:

- `list_categories` -> `search` -> `get_schema` -> `execute`
- `execute` runs in a sandbox powered by `python-monty`.
- Search supports category, subcategory, and provider-aware filtering.
- Discovery output defaults to compact markdown to reduce token usage.

This is the recommended mode when the agent needs chained analysis, derived calculations, or lightweight post-processing of tool results.

### Fixed Toolset Mode

When `enable_tool_discovery=false` and `enable_code_mode=false`, the server behaves like a regular FastMCP OpenAPI server and exposes the configured OpenBB tools directly. Use `allowed_tool_categories`, `default_tool_categories`, `include_tags`, and `exclude_tags` to control the surface area.

## Root Tools, Prompts, and Resources

Additional root-level MCP features can still be exposed alongside OpenBB API tools:

- `list_prompts` and `execute_prompt` for static prompts and inline prompt definitions.
- `install_skill` for copying a discovered skill into the writable skills provider.
- MCP resources, including bundled skills and the optional `resource://system_prompt`.

`PromptsAsTools` and `ResourcesAsTools` are enabled, so prompts and resources can also be surfaced as callable tools when supported by the MCP client.

## System Prompt

A system prompt file can be added on initialization, or defined in the configuration file, or as an environment variable. It should point to a valid `.txt` file.

The system prompt is exposed as `resource://system_prompt` and is also registered as a prompt named `system_prompt`.

Clients will not automatically use the system prompt, so instruct them to read it as part of their onboarding flow.

## Skills

The server ships with bundled **skill guides**: Markdown documents that teach an agent how to perform complex multi-step tasks with the OpenBB Platform. Skills are exposed as MCP resources and are discoverable through normal MCP resource listing or via the resource transforms.

Each skill is available at a URI of the form `skill://<name>/SKILL.md`.

### Bundled Skills

| Skill | URI | Description |
|---|---|---|
| `develop_extension` | `skill://develop_extension/SKILL.md` | Step-by-step guide for building an OpenBB Platform extension. |
| `build_workspace_app` | `skill://build_workspace_app/SKILL.md` | Guide for building and running OpenBB Workspace applications. |
| `configure_mcp_server` | `skill://configure_mcp_server/SKILL.md` | Reference for configuring and customizing the OpenBB MCP Server. |
| `work_with_server` | `skill://work_with_server/SKILL.md` | Practical guide for working with the OpenBB MCP Server as an agent. |

When any skills are loaded and no `system_prompt_file` is configured, the server automatically adds a brief default system prompt that nudges the agent to discover available skills.

### Skill Settings

| Setting | Description |
|---|---|
| `default_skills_dir` | Path to the bundled skills directory. Set to `null` or an empty string to disable loading the built-in skills. |
| `skills_reload` | Set to `true` to reload skill files from disk on every read. Useful while authoring skill content. |
| `skills_providers` | Vendor skill provider short-names to load. Supported values: `claude`, `cursor`, `vscode`, `copilot`, `codex`, `gemini`, `goose`, `opencode`. |

**Example - disable bundled skills:**

```json
{
  "default_skills_dir": null
}
```

**Example - load vendor skill providers:**

```json
{
  "skills_providers": ["claude", "cursor"]
}
```

**Example - enable skill reload during development:**

```env
OPENBB_MCP_SKILLS_RELOAD=true
```

If a writable `SkillsDirectoryProvider` is configured, `install_skill` can copy a discovered `SKILL.md` resource plus its supporting files into that provider.

## Server Prompts

A server prompts file can be added on initialization, or defined in the configuration file, or as an environment variable. It should point to a valid `.json` file containing a list of prompt definitions.

Each entry in the JSON file is a dictionary with the following properties:

- **`name`**: Name of the prompt.
- **`description`**: A brief description of the prompt.
- **`content`**: The content for rendering the prompt.
- **`arguments`**: Optional list of arguments.
  - **`name`**: Name of the argument.
  - **`type`**: Simple Python type as a string, for example `int`.
  - **`default`**: Supplying a default value makes the parameter optional.
  - **`description`**: Description of the parameter. Supply need-to-know details for the LLM.
- **`tags`**: List of tags to apply to the prompt.

Prompts here should provide the LLM a clear path for executing a workflow combining multiple tools or steps, for example:

```json
[
  {
    "name": "equity_analysis",
    "description": "Perform a comprehensive equity analysis using multiple data sources and metrics",
    "content": "Conduct a comprehensive analysis of {symbol} for {analysis_period}. Follow this workflow:\n1. First, get basic stock quote and recent price performance using equity_price_performance.\n2. Retrieve fundamental data including financial statements, ratios, and key metrics using [equity_fundamental_ratios, equity_fundamental_metrics, quity_fundamental_balance].\n3. Gather recent news and analyst estimates for the company using [news_company, equity_estiments_price_target].\n4. Compare valuation metrics with industry peers using equity_compare_peers.\n5. Summarize findings with investment recommendation.\n\nFocus areas: {focus_areas}\nRisk tolerance: {risk_tolerance}",
    "arguments": [
      {
        "name": "symbol",
        "type": "str",
        "description": "Stock ticker symbol to analyze (e.g., AAPL, TSLA)"
      },
      {
        "name": "analysis_period",
        "type": "str",
        "default": "last 12 months",
        "description": "Time period for the analysis"
      },
      {
        "name": "focus_areas",
        "type": "str",
        "default": "growth, profitability, valuation",
        "description": "Specific areas to focus on in the analysis"
      },
      {
        "name": "risk_tolerance",
        "type": "str",
        "default": "moderate",
        "description": "Risk tolerance level: conservative, moderate, or aggressive"
      }
    ],
    "tags": ["equity", "analysis", "comprehensive"]
  }
]
```

An invalid prompt definition, or prompt argument, will be logged as an error and ignored.

## Inline Prompts

Prompts can be added to an endpoint through the `openapi_extra` dictionary.

Adding prompts here helps the LLM use the endpoint for specific purposes with less reasoning overhead.

Direct the agent to `execute_prompt`, or note that helpful prompts may be included in the tool metadata.

The block below assumes `app` is an instance of `FastAPI`.

```python
@app.get(
    "/economy/gdp",
    openapi_extra={
        "mcp_config": {
            "prompts": [
                {
                    "name": "gdp_summary_prompt",
                    "description": "Generate a brief summary of GDP for a country.",
                    "content": "Provide a concise summary of the GDP for {country} over the last {years} years.",
                    "arguments": [
                        {
                            "name": "years",
                            "type": "int",
                            "default": 5,
                            "description": "Number of years to summarize."
                        }
                    ],
                    "tags": ["economy", "gdp", "summary"]
                },
                {
                    "name": "gdp_comparison_prompt",
                    "description": "Compare the GDP of two countries.",
                    "content": "Compare the GDP growth of {country1} and {country2}.",
                    "arguments": [
                        {
                            "name": "country1",
                            "type": "str",
                            "description": "First country for comparison."
                        },
                        {
                            "name": "country2",
                            "type": "str",
                            "description": "Second country for comparison."
                        }
                    ],
                    "tags": ["economy", "gdp", "comparison"]
                }
            ]
        }
    },
)
def get_gdp_data(country: str, period: Literal["annual", "quarterly"] = "annual"):
    """Get GDP data for a specific country."""
    return {"country": country, "period": period}
```

Along with being added to `list_prompts`, prompts will be included with the tool metadata returned by `list_tools` when the full tool catalog is visible.

The discovery metadata for this tool would look like:

__Economy Tools:__

- __`economy_gdp`__: Get GDP data for a specific country.

  - __Associated Prompts:__

    - `gdp_summary_prompt`: Generate a brief summary of GDP for a country. (Arguments: `years`, `country`)
    - `gdp_comparison_prompt`: Compare the GDP of two countries. (Arguments: `country1`, `country2`)

Use a prompt with the `execute_prompt` tool:

```json
{
  "prompt_name": "gdp_summary_prompt",
  "arguments": {
    "years": 10,
    "country": "Japan"
  }
}
```

Which outputs:

```json
{
  "description": "Generate a brief summary of GDP for a country.",
  "messages": [
    {
      "role": "user",
      "content": {
        "type": "text",
        "text": "Use the tool, economy_gdp, to perform the following task.\n\nProvide a concise summary of the GDP for Japan over the last 10 years."
      }
    }
  ]
}
```

## Inline MCP Configuration

In addition to defining prompts, the `openapi_extra.mcp_config` dictionary allows for more granular control over how your FastAPI routes are exposed as MCP tools.
By using the `MCPConfigModel`, you can validate your configuration and access several powerful properties to customize tool behavior.

It can be imported with:

```
from openbb_mcp_server.models.mcp_config import MCPConfigModel
```

Including this configuration in the `openapi_extra` slot will override any automatically generated value.
You only need to enter the values that you wish to customize.

Below are the properties you can define within `mcp_config`:

- **`expose`** (`Optional[bool]`): Set to `False` to completely hide a route from the MCP server. This is useful for internal or deprecated endpoints that should not be available as tools.
- **`mcp_type`** (`Optional[MCPType]`): Classify the route as a specific MCP type. Valid options are `"tool"`, `"resource"`, or `"resource_template"`.
- **`methods`** (`Optional[list[HTTPMethod]]`): Specify which HTTP methods to expose for a route that supports multiple methods, for example `GET` and `POST`. If omitted, all supported methods are exposed.
- **`exclude_args`** (`Optional[list[str]]`): Provide a list of argument names to exclude from the tool signature.
- **`prompts`** (`Optional[list[dict[str, str]]]`): List of prompts specific to the endpoint.

### MCPConfigModel Validation

Values are validated before inclusion in the server. Invalid configurations are logged as errors and ignored.

```console
ERROR    Invalid MCP config found in route, 'GET /equity/price'. Skipping tool customization because of validation error ->
          1 validation error for MCPConfigModel
          mcp_type
            Input should be 'tool', 'resource' or 'resource_template' [type=enum, input_value='some_setting', input_type=str]
              For further information visit https://errors.pydantic.dev/2.11/v/enum
```

### Example

Here is an example demonstrating how to use these properties to fine-tune a tool's behavior:

```python
@app.get(
    "/some/route",
    openapi_extra={
        "mcp_config": {
            "expose": True,
            "mcp_type": "tool",
            "methods": ["GET"],
            "exclude_args": ["internal_param"],
            "prompts": [
                # ... prompt definitions ...
            ]
        }
    },
)
def some_route(param1: str, internal_param: str = "default"):
    """An example route with advanced MCP configuration."""
    return {"param1": param1}
```

In this example, the `/some/route` endpoint is explicitly exposed as a `tool` for the `GET` method only, and the `internal_param` argument is hidden from the tool interface.

## Client Examples

Start the server with the appropriate transport and configuration for the client. The default transport is `http`.

```bash
# Start with default settings
openbb-mcp

# Use an alternative transport
openbb-mcp --transport sse

# Start with specific categories and custom host/port
openbb-mcp --default-categories equity,news --host 0.0.0.0 --port 8080

# Start with allowed categories restriction
openbb-mcp --allowed-categories equity,crypto,news

# Disable tool discovery for a fixed-tool configuration
openbb-mcp --no-tool-discovery
```

### Claude Desktop

To connect the OpenBB MCP server with Claude Desktop, configure it as a custom MCP server:

1. Locate the Claude Desktop settings file where custom MCP servers are defined.
2. Add the following entry to the `mcpServers` configuration.

```json
{
  "mcpServers": {
    "openbb-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "openbb-mcp-server",
        "--with",
        "openbb",
        "openbb-mcp",
        "--transport",
        "stdio"
      ]
    }
  }
}
```

3. Ensure `uvx` is installed and available in `PATH`.
4. Restart Claude Desktop.

### Cursor

To use OpenBB tools within Cursor, first run the MCP server, then point Cursor at it.

**Step 1: Run the OpenBB MCP Server**

```bash
openbb-mcp
```

The server starts on `http://127.0.0.1:8001` by default.

**Step 2: Configure Cursor**

Add the following configuration to the `mcpServers` object in `mcp.json`:

```json
{
  "mcpServers": {
    "openbb-mcp": {
      "url": "http://localhost:8001/mcp/"
    }
  }
}
```

### VS Code

**Step 1: Enable MCP in VS Code Settings**

Open "Preferences: Open User Settings", search for `mcp`, and enable MCP server integrations under Chat.

<img width="1278" height="411" alt="vs-code-mcp-enable" src="https://github.com/user-attachments/assets/5ace29de-e59c-45c3-b751-c6d92614e0ee" />

**Step 2: Run the OpenBB MCP Server**

```bash
openbb-mcp
```

The server starts on `http://127.0.0.1:8001` by default.

**Step 3: Add Server as HTTP**

Use "MCP: Add Server" from the command palette, select HTTP, and enter the URL shown by the server:

```sh
INFO     Starting MCP server 'OpenBB MCP' with transport 'streamable-http' on http://127.0.0.1:8001/mcp
```

Give it a name, and add it either globally or to a workspace. VS Code will create the corresponding `mcp.json` entry.

<img width="595" height="412" alt="vs-code-mcp-commands" src="https://github.com/user-attachments/assets/9b13a5b6-ec20-43e2-9aae-7982e9fdcae6" />
<img width="594" height="174" alt="vs-code-mcp-add-http" src="https://github.com/user-attachments/assets/d2a06e4b-404a-4317-ad2c-241c1ac5e04b" />
<img width="402" height="195" alt="vs-code-mcp-json" src="https://github.com/user-attachments/assets/fdea335b-0523-4103-be3e-b5d9675c25b3" />
<img width="601" height="442" alt="vs-code-mcp-tools" src="https://github.com/user-attachments/assets/06c39248-aedd-4f53-9560-6dfbae1efaf8" />

**Note**: When adding to the Cline extension, start the server with `--transport sse`.
