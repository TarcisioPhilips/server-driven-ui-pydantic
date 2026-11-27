"""Generative UI agent endpoint — same contract as deterministic screens."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.agent import generate_screen
from app.negotiation import adapt_screen
from app.routes.screens import _parse_client_version

router = APIRouter(prefix="/agent", tags=["agent"])


class AgentScreenRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000)
    simulate_unknown: bool = False


@router.post("/screen")
async def agent_screen(
    body: AgentScreenRequest,
    x_client_version: str | None = Header(default="2", alias="X-Client-Version"),
    x_supported_components: str | None = Header(
        default=None, alias="X-Supported-Components"
    ),
) -> dict[str, Any]:
    try:
        screen = await generate_screen(body.prompt)
    except Exception as exc:  # noqa: BLE001 — surface agent failures cleanly
        raise HTTPException(status_code=502, detail=f"Agent failed: {exc}") from exc

    version = _parse_client_version(x_client_version)
    return adapt_screen(
        screen,
        version,
        x_supported_components,
        simulate_unknown=body.simulate_unknown,
    )
