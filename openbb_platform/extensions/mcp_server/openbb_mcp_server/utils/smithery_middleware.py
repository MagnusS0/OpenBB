from __future__ import annotations

from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .smithery_session import SESSIONS


class SmitheryConfigMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        # Only care about the MCP endpoint
        if request.url.path.endswith("/mcp"):
            # Persist config on initial GET (Smithery sends config as query params)
            if request.method.upper() == "GET":
                # Capture current query params as a simple dict
                query_config = {k: v for k, v in request.query_params.multi_items()}
                response = await call_next(request)
                # After the MCP server assigns a session, it should return an Mcp-Session-Id header
                session_id = response.headers.get("Mcp-Session-Id")
                if session_id and query_config:
                    SESSIONS.set(session_id, query_config)
                return response

            # For POST/DELETE, attach previously stored config for this session to the request state
            if request.method.upper() in {"POST", "DELETE"}:
                session_id = request.headers.get("Mcp-Session-Id")
                if session_id:
                    cfg = SESSIONS.get(session_id)
                    if cfg is not None:
                        request.state.smithery_config = cfg

        # Default flow
        return await call_next(request)