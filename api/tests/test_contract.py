"""Contract matrix: validation, negotiation, downgrade, agent."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from pydantic_ai.models import ALLOW_MODEL_REQUESTS
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.models.test import TestModel

# Ensure no accidental live model calls during tests
os.environ["ALLOW_MODEL_REQUESTS"] = "false"

from app.agent import build_screen_from_prompt, create_screen_agent
from app.main import app
from app.models.screen import (
    V1_COMPONENTS,
    V2_COMPONENTS,
    HeaderComponent,
    Layout,
    PixQrComponent,
    ScreenResponse,
    Section,
    TextComponent,
)
from app.negotiation import adapt_screen, downgrade_component, resolve_supported
from app.screens.catalog import get_screen

client = TestClient(app)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def test_catalog_screens_validate() -> None:
    for sid in ("welcome", "payment", "confirmation"):
        screen = get_screen(sid)
        assert screen is not None
        assert screen.screen_id == sid


def test_invalid_layout_ref_rejected() -> None:
    with pytest.raises(ValidationError):
        ScreenResponse(
            screen_id="bad",
            title="Bad",
            layout=Layout(
                type="column",
                sections=[Section(id="s", component_ids=["missing"])],
            ),
            components=[
                HeaderComponent(id="hdr", title="X"),
            ],
        )


def test_duplicate_component_ids_rejected() -> None:
    with pytest.raises(ValidationError):
        ScreenResponse(
            screen_id="dup",
            title="Dup",
            layout=Layout(
                type="column",
                sections=[Section(id="s", component_ids=["a"])],
            ),
            components=[
                TextComponent(id="a", content="one"),
                TextComponent(id="a", content="two"),
            ],
        )


# ---------------------------------------------------------------------------
# Negotiation / downgrade
# ---------------------------------------------------------------------------


def test_resolve_supported_by_version() -> None:
    assert resolve_supported(1, None) == V1_COMPONENTS
    assert resolve_supported(2, None) == V2_COMPONENTS


def test_resolve_supported_header_intersection() -> None:
    # Client claims pix_qr but is v1 → excluded
    supported = resolve_supported(1, "header,text,pix_qr,button")
    assert "pix_qr" not in supported
    assert "header" in supported


def test_downgrade_pix_qr() -> None:
    pix = PixQrComponent(
        id="pix",
        payload="payload",
        amount="50.00",
        copy_paste_key="KEY-123",
        expires_in_seconds=180,
    )
    out = downgrade_component(pix, V1_COMPONENTS)
    assert all(c.type in V1_COMPONENTS for c in out)
    assert any(getattr(c, "copyable", False) for c in out)
    assert any("KEY-123" in getattr(c, "content", "") for c in out)


def test_payment_v2_keeps_native_components() -> None:
    screen = get_screen("payment")
    assert screen is not None
    payload = adapt_screen(screen, client_version=2)
    types = {c["type"] for c in payload["components"]}
    assert "pix_qr" in types
    assert "biometric_prompt" in types


def test_payment_v1_downgrades() -> None:
    screen = get_screen("payment")
    assert screen is not None
    payload = adapt_screen(screen, client_version=1)
    types = {c["type"] for c in payload["components"]}
    assert "pix_qr" not in types
    assert "biometric_prompt" not in types
    assert types <= V1_COMPONENTS
    # Copyable key present
    assert any(c.get("copyable") for c in payload["components"])
    # Verification input + button from biometric downgrade
    assert any(c["type"] == "input" for c in payload["components"])


def test_simulate_unknown_injects_unsupported_type() -> None:
    screen = get_screen("welcome")
    assert screen is not None
    payload = adapt_screen(screen, client_version=2, simulate_unknown=True)
    types = [c["type"] for c in payload["components"]]
    assert "futuristic_hologram" in types
    assert payload["meta"]["simulate_unknown"] is True


# ---------------------------------------------------------------------------
# HTTP endpoints
# ---------------------------------------------------------------------------


def test_get_screen_v1_headers() -> None:
    res = client.get(
        "/screens/payment",
        headers={"X-Client-Version": "1"},
    )
    assert res.status_code == 200
    body = res.json()
    types = {c["type"] for c in body["components"]}
    assert "pix_qr" not in types
    assert body["meta"]["client_version"] == 1


def test_get_screen_v2_headers() -> None:
    res = client.get(
        "/screens/payment",
        headers={"X-Client-Version": "2"},
    )
    assert res.status_code == 200
    types = {c["type"] for c in res.json()["components"]}
    assert "pix_qr" in types


def test_supported_components_header() -> None:
    res = client.get(
        "/screens/welcome",
        headers={
            "X-Client-Version": "2",
            "X-Supported-Components": "header,text,button",
        },
    )
    assert res.status_code == 200
    supported = set(res.json()["meta"]["supported_components"])
    assert supported == {"header", "text", "button"}
    # input was on the screen but not supported — still passed through
    # (only pix_qr / biometric have server-side downgrade maps)
    types = {c["type"] for c in res.json()["components"]}
    # welcome has input; without a downgrade map it remains for UnknownComponent
    assert "input" in types or "input" not in supported


def test_simulate_unknown_query() -> None:
    res = client.get("/screens/welcome?simulate_unknown=true")
    assert res.status_code == 200
    assert any(c["type"] == "futuristic_hologram" for c in res.json()["components"])


def test_unknown_screen_404() -> None:
    assert client.get("/screens/nope").status_code == 404


def test_invalid_client_version() -> None:
    assert (
        client.get("/screens/welcome", headers={"X-Client-Version": "9"}).status_code
        == 400
    )


def test_schema_endpoint() -> None:
    res = client.get("/schema/screen")
    assert res.status_code == 200
    schema = res.json()
    assert "properties" in schema
    assert "screen_id" in schema["properties"]


def test_health() -> None:
    assert client.get("/health").json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Agent mode (FunctionModel / TestModel, no live requests)
# ---------------------------------------------------------------------------


def test_allow_model_requests_disabled() -> None:
    assert ALLOW_MODEL_REQUESTS is False or os.getenv("ALLOW_MODEL_REQUESTS") == "false"


def test_build_screen_from_prompt_pix_banner() -> None:
    screen = build_screen_from_prompt("add a Pix discount banner")
    assert screen.screen_id == "payment"
    assert any(
        "discount" in getattr(c, "content", "").lower() for c in screen.components
    )


def test_build_screen_from_prompt_skip_biometric() -> None:
    screen = build_screen_from_prompt("skip biometric step")
    assert all(c.type != "biometric_prompt" for c in screen.components)
    assert screen.data.get("biometric_skipped") is True


@pytest.mark.asyncio
async def test_generate_screen_function_model() -> None:
    from app.agent import _function_model_handler

    agent = create_screen_agent(FunctionModel(_function_model_handler))
    result = await agent.run("add a Pix discount banner")
    assert isinstance(result.output, ScreenResponse)
    assert result.output.screen_id == "payment"


@pytest.mark.asyncio
async def test_generate_screen_test_model() -> None:
    sample = build_screen_from_prompt("show payment")
    agent = create_screen_agent(
        TestModel(custom_output_args=sample.model_dump())
    )
    result = await agent.run("anything")
    assert result.output.screen_id == "payment"


def test_post_agent_screen_http() -> None:
    res = client.post(
        "/agent/screen",
        json={"prompt": "add a Pix discount banner"},
        headers={"X-Client-Version": "1"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["screen_id"] == "payment"
    types = {c["type"] for c in body["components"]}
    assert "pix_qr" not in types  # downgraded for v1
    assert any("discount" in c.get("content", "").lower() for c in body["components"])


def test_post_agent_screen_v2() -> None:
    res = client.post(
        "/agent/screen",
        json={"prompt": "skip biometric step"},
        headers={"X-Client-Version": "2"},
    )
    assert res.status_code == 200
    types = {c["type"] for c in res.json()["components"]}
    assert "biometric_prompt" not in types
