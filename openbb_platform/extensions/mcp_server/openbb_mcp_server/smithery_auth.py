from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, Request
from openbb_core.app.model.user_settings import UserSettings
from openbb_core.app.service.user_service import UserService

router = APIRouter(prefix="/user", tags=["User"])  # unused placeholder to satisfy interface


async def auth_hook() -> None:  # no-op auth
    return None


def _extract_credentials_from_config(cfg: Dict[str, Any]) -> Dict[str, Any]:
    # Accept both flat keys like "polygon_api_key" and nested dot-notation like "credentials.polygon_api_key"
    creds: Dict[str, Any] = {}
    for key, value in cfg.items():
        if not value:
            continue
        # Normalize
        k = key.strip()
        if k.startswith("credentials."):
            k = k.split(".", 1)[1]
        # Only keep likely credential-y keys (heuristic: contains "key" or endswith "token")
        lk = k.lower()
        if "key" in lk or lk.endswith("token") or lk.endswith("secret"):
            creds[lk] = value
    return creds


async def user_settings_hook(request: Request, _: None = Depends(auth_hook)) -> UserSettings:
    # Pull smithery config captured by middleware
    cfg = getattr(request.state, "smithery_config", None)

    # Fall back to global session store using header if not present (defensive)
    if cfg is None:
        session_id = request.headers.get("Mcp-Session-Id")
        if session_id:
            try:
                from .utils.smithery_session import SESSIONS  # lazy import to avoid cycles
                cfg = SESSIONS.get(session_id)
            except Exception:  # pragma: no cover
                cfg = None

    if not cfg:
        # Default to reading from file if no config was provided
        return UserService.read_from_file()

    # Build a transient UserSettings merging credentials only
    base = UserService.read_from_file().model_dump()
    base.setdefault("credentials", {})
    extracted = _extract_credentials_from_config(cfg)
    # Also allow direct OPENBB_*, PROVIDER_* uppercase env-like keys via query
    for key, value in cfg.items():
        if key.isupper():
            base["credentials"][key.lower()] = value
    base["credentials"].update(extracted)
    return UserSettings.model_validate(base)