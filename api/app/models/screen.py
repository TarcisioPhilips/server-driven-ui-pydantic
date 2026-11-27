"""Versioned SDUI contract: layout, components, data, and actions.

Designed so an optional A2UI 1.0 adapter can map these models in v2
without rewriting the component catalog.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, model_validator

# ---------------------------------------------------------------------------
# Actions (separated from presentation)
# ---------------------------------------------------------------------------


class NavigateAction(BaseModel):
    type: Literal["navigate"] = "navigate"
    screen_id: str


class SubmitAction(BaseModel):
    type: Literal["submit"] = "submit"
    endpoint: str
    method: Literal["POST", "PUT"] = "POST"


class OpenModalAction(BaseModel):
    type: Literal["open_modal"] = "open_modal"
    modal_id: str
    title: str | None = None


Action = Annotated[
    NavigateAction | SubmitAction | OpenModalAction,
    Field(discriminator="type"),
]

# ---------------------------------------------------------------------------
# Components (fintech catalog)
# ---------------------------------------------------------------------------

# App v1 (legacy): header, text, input, button
# App v2 (current): + pix_qr, biometric_prompt

V1_COMPONENTS: frozenset[str] = frozenset({"header", "text", "input", "button"})
V2_COMPONENTS: frozenset[str] = V1_COMPONENTS | {"pix_qr", "biometric_prompt"}


class HeaderComponent(BaseModel):
    type: Literal["header"] = "header"
    id: str
    title: str
    subtitle: str | None = None


class TextComponent(BaseModel):
    type: Literal["text"] = "text"
    id: str
    content: str
    variant: Literal["body", "caption", "alert", "success"] = "body"
    copyable: bool = False


class InputComponent(BaseModel):
    type: Literal["input"] = "input"
    id: str
    label: str
    name: str
    input_type: Literal["text", "email", "password", "tel"] = "text"
    placeholder: str | None = None
    required: bool = False


class ButtonComponent(BaseModel):
    type: Literal["button"] = "button"
    id: str
    label: str
    action: Action
    variant: Literal["primary", "secondary", "danger"] = "primary"


class PixQrComponent(BaseModel):
    """Pix QR payment — App v2 only; downgraded for v1 clients."""

    type: Literal["pix_qr"] = "pix_qr"
    id: str
    payload: str
    amount: str
    copy_paste_key: str
    expires_in_seconds: int = 300


class BiometricPromptComponent(BaseModel):
    """Biometric verification — App v2 only; downgraded for v1 clients."""

    type: Literal["biometric_prompt"] = "biometric_prompt"
    id: str
    title: str
    reason: str
    fallback_label: str = "Use verification code"
    action: Action


Component = Annotated[
    HeaderComponent
    | TextComponent
    | InputComponent
    | ButtonComponent
    | PixQrComponent
    | BiometricPromptComponent,
    Field(discriminator="type"),
]

# ---------------------------------------------------------------------------
# Layout / structure (separate from component instances)
# ---------------------------------------------------------------------------


class Section(BaseModel):
    id: str
    component_ids: list[str] = Field(min_length=1)


class Layout(BaseModel):
    type: Literal["column", "stack"] = "column"
    sections: list[Section] = Field(min_length=1)


# ---------------------------------------------------------------------------
# ScreenResponse — the wire contract
# ---------------------------------------------------------------------------


class ScreenResponse(BaseModel):
    """Canonical SDUI payload shared by REST and Generative UI agent modes."""

    schema_version: Literal["1.0"] = "1.0"
    screen_id: str
    title: str
    layout: Layout
    components: list[Component] = Field(min_length=1)
    data: dict[str, Any] = Field(default_factory=dict)
    meta: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _layout_refs_must_exist(self) -> ScreenResponse:
        ids = {c.id for c in self.components}
        if len(ids) != len(self.components):
            raise ValueError("component ids must be unique")
        for section in self.layout.sections:
            missing = [cid for cid in section.component_ids if cid not in ids]
            if missing:
                raise ValueError(
                    f"layout section '{section.id}' references unknown "
                    f"component ids: {missing}"
                )
        return self
