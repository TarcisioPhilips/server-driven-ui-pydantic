"""Deterministic SDUI screen endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query

from app.models.screen import ScreenResponse
from app.negotiation import adapt_screen
from app.screens.catalog import get_screen, list_screen_ids

router = APIRouter(tags=["screens"])


def _parse_client_version(raw: str | None) -> int:
    if raw is None or raw.strip() == "":
        return 2
    try:
        version = int(raw.strip())
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="X-Client-Version must be an integer (1 or 2)",
        ) from exc
    if version not in (1, 2):
        raise HTTPException(
            status_code=400,
            detail="X-Client-Version must be 1 or 2",
        )
    return version


@router.get("/screens")
def list_screens() -> dict[str, Any]:
    return {"screens": list_screen_ids()}


@router.get("/screens/{screen_id}")
def fetch_screen(
    screen_id: str,
    simulate_unknown: bool = Query(False),
    x_client_version: str | None = Header(default="2", alias="X-Client-Version"),
    x_supported_components: str | None = Header(
        default=None, alias="X-Supported-Components"
    ),
) -> dict[str, Any]:
    screen = get_screen(screen_id)
    if screen is None:
        raise HTTPException(status_code=404, detail=f"Unknown screen: {screen_id}")

    # Fail-fast validation already happened in get_screen via model_validate
    version = _parse_client_version(x_client_version)
    return adapt_screen(
        screen,
        version,
        x_supported_components,
        simulate_unknown=simulate_unknown,
    )


@router.get("/schema/screen")
def screen_json_schema() -> dict[str, Any]:
    """Export JSON Schema for the ScreenResponse contract (for TS codegen)."""
    return ScreenResponse.model_json_schema()
