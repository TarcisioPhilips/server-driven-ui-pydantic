"""Deterministic fintech onboarding/checkout screens.

Flow: welcome → payment → confirmation
Payment includes pix_qr + biometric_prompt (downgraded for App v1).
"""

from __future__ import annotations

from app.models.screen import (
    BiometricPromptComponent,
    ButtonComponent,
    HeaderComponent,
    InputComponent,
    Layout,
    NavigateAction,
    PixQrComponent,
    ScreenResponse,
    Section,
    SubmitAction,
    TextComponent,
)

# Sample Pix EMV-ish payload (demo only)
_PIX_PAYLOAD = (
    "00020126580014br.gov.bcb.pix0136123e4567-e12b-12d1-a456-426614174000"
    "5204000053039865406100.005802BR5925ACME FINTECH LTDA6009SAO PAULO"
    "62070503***6304ABCD"
)
_PIX_KEY = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"


def build_welcome() -> ScreenResponse:
    return ScreenResponse(
        screen_id="welcome",
        title="Welcome",
        layout=Layout(
            type="column",
            sections=[
                Section(id="hero", component_ids=["hdr", "intro"]),
                Section(id="form", component_ids=["email", "continue"]),
            ],
        ),
        components=[
            HeaderComponent(
                id="hdr",
                title="Acme Pay",
                subtitle="Secure onboarding & checkout",
            ),
            TextComponent(
                id="intro",
                content="Enter your email to start a verified Pix payment.",
                variant="body",
            ),
            InputComponent(
                id="email",
                label="Email",
                name="email",
                input_type="email",
                placeholder="you@company.com",
                required=True,
            ),
            ButtonComponent(
                id="continue",
                label="Continue to payment",
                action=NavigateAction(screen_id="payment"),
                variant="primary",
            ),
        ],
        data={"flow": "onboarding_checkout", "step": 1},
        meta={"source": "catalog"},
    )


def build_payment() -> ScreenResponse:
    return ScreenResponse(
        screen_id="payment",
        title="Payment",
        layout=Layout(
            type="column",
            sections=[
                Section(id="hero", component_ids=["hdr", "summary"]),
                Section(id="pix", component_ids=["pix"]),
                Section(id="verify", component_ids=["bio"]),
                Section(id="actions", component_ids=["back", "confirm"]),
            ],
        ),
        components=[
            HeaderComponent(
                id="hdr",
                title="Complete your payment",
                subtitle="Pix · R$ 100.00",
            ),
            TextComponent(
                id="summary",
                content="Scan the QR code or use biometrics to authorize.",
                variant="body",
            ),
            PixQrComponent(
                id="pix",
                payload=_PIX_PAYLOAD,
                amount="100.00",
                copy_paste_key=_PIX_KEY,
                expires_in_seconds=300,
            ),
            BiometricPromptComponent(
                id="bio",
                title="Confirm with biometrics",
                reason="Authorize Pix payment of R$ 100.00",
                fallback_label="Verify with SMS code",
                action=NavigateAction(screen_id="confirmation"),
            ),
            ButtonComponent(
                id="back",
                label="Back",
                action=NavigateAction(screen_id="welcome"),
                variant="secondary",
            ),
            ButtonComponent(
                id="confirm",
                label="I've paid",
                action=SubmitAction(endpoint="/actions/confirm-payment", method="POST"),
                variant="primary",
            ),
        ],
        data={
            "flow": "onboarding_checkout",
            "step": 2,
            "amount": "100.00",
            "currency": "BRL",
        },
        meta={"source": "catalog"},
    )


def build_confirmation() -> ScreenResponse:
    return ScreenResponse(
        screen_id="confirmation",
        title="Confirmation",
        layout=Layout(
            type="column",
            sections=[
                Section(id="hero", component_ids=["hdr", "msg"]),
                Section(id="actions", component_ids=["done"]),
            ],
        ),
        components=[
            HeaderComponent(
                id="hdr",
                title="Payment confirmed",
                subtitle="Receipt #ACM-2048",
            ),
            TextComponent(
                id="msg",
                content="R$ 100.00 received via Pix. A receipt was sent to your email.",
                variant="success",
            ),
            ButtonComponent(
                id="done",
                label="Start over",
                action=NavigateAction(screen_id="welcome"),
                variant="primary",
            ),
        ],
        data={"flow": "onboarding_checkout", "step": 3, "status": "paid"},
        meta={"source": "catalog"},
    )


SCREEN_CATALOG: dict[str, ScreenResponse] = {
    "welcome": build_welcome(),
    "payment": build_payment(),
    "confirmation": build_confirmation(),
}


def get_screen(screen_id: str) -> ScreenResponse | None:
    screen = SCREEN_CATALOG.get(screen_id)
    if screen is None:
        return None
    # Re-validate on access so catalog drift fails fast
    return ScreenResponse.model_validate(screen.model_dump())


def list_screen_ids() -> list[str]:
    return list(SCREEN_CATALOG.keys())
