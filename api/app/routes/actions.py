"""Simple action endpoints referenced by submit actions."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.negotiation import adapt_screen
from app.screens.catalog import get_screen

router = APIRouter(prefix="/actions", tags=["actions"])


@router.post("/confirm-payment")
def confirm_payment() -> dict[str, Any]:
    """Submit handler: returns the confirmation screen (client v2 defaults)."""
    screen = get_screen("confirmation")
    assert screen is not None
    return {
        "ok": True,
        "next_screen": adapt_screen(screen, client_version=2),
    }
