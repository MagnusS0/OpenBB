# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install system deps as needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create app dir
WORKDIR /app

# Copy package files
COPY ./pyproject.toml ./README.md ./openbb_mcp_server ./ /app/

# Install uv and project
RUN pip install --upgrade pip \
 && pip install "uv>=0.2" \
 && uv pip install --system .

# Expose port (Smithery sets PORT)
ENV PORT=8001 \
    OPENBB_API_AUTH=true \
    OPENBB_API_AUTH_EXTENSION=openbb_smithery_auth \
    OPENBB_MCP_ENABLE_TOOL_DISCOVERY=false \
    OPENBB_MCP_NAME="OpenBB MCP"
EXPOSE 8001

# Default command: start HTTP server; Smithery sends GET /mcp
CMD ["python", "-c", "from openbb_mcp_server.main import main; main()"]