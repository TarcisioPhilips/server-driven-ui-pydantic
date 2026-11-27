"""Client capability negotiation and server-side component downgrade."""

from __future__ import annotations

from typing import Any

from app.models.screen import (
    V1_COMPONENTS,
    V2_COMPONENTS,
    Action,
    BiometricPromptComponent,
    ButtonComponent,
    Component,
    InputComponent,
    Layout,
    NavigateAction,
    OpenModalAction,
    PixQrComponent,
    ScreenResponse,
    Section,
    SubmitAction,
    TextComponent,
)


def resolve_supported(
    client_version: int,
    supported_header: str | None,
) -> frozenset[str]:
    """Resolve the set of components this client can render."""
    base = V1_COMPONENTS if client_version <= 1 else V2_COMPONENTS
    if not supported_header or not supported_header.strip():
        return base
    requested = {c.strip() for c in supported_header.split(",") if c.strip()}
    # Intersection: never advertise more than the client's version allows
    return frozenset(requested & set(base)) if requested else base


def _clone_action(action: Action) -> Action:
    if isinstance(action, NavigateAction):
        return NavigateAction(screen_id=action.screen_id)
    if isinstance(action, SubmitAction):
        return SubmitAction(endpoint=action.endpoint, method=action.method)
    return OpenModalAction(modal_id=action.modal_id, title=action.title)


def downgrade_component(
    component: Component,
    supported: frozenset[str],
) -> list[Component]:
    """Adapt an unsupported component into safe v1 equivalents."""
    if component.type in supported:
        return [component]

    if isinstance(component, PixQrComponent):
        return [
            TextComponent(
                id=f"{component.id}_label",
                content=f"Pay R$ {component.amount} via Pix (copy & paste)",
                variant="body",
            ),
            TextComponent(
                id=f"{component.id}_key",
                content=component.copy_paste_key,
                variant="caption",
                copyable=True,
            ),
            TextComponent(
                id=f"{component.id}_hint",
                content=f"Code expires in {component.expires_in_seconds // 60} min",
                variant="caption",
            ),
        ]

    if isinstance(component, BiometricPromptComponent):
        return [
            TextComponent(
                id=f"{component.id}_info",
                content=f"{component.title}: {component.reason}",
                variant="alert",
            ),
            InputComponent(
                id=f"{component.id}_code",
                label="Verification code",
                name=f"{component.id}_code",
                input_type="tel",
                placeholder="6-digit code",
                required=True,
            ),
            ButtonComponent(
                id=f"{component.id}_verify",
                label=component.fallback_label,
                action=_clone_action(component.action),
                variant="primary",
            ),
        ]

    # Unmapped types pass through so the client can show UnknownComponent.
    return [component]


def adapt_screen(
    screen: ScreenResponse,
    client_version: int,
    supported_header: str | None = None,
    *,
    simulate_unknown: bool = False,
) -> dict[str, Any]:
    """Apply capability negotiation; always return a JSON-serializable dict.

    When ``simulate_unknown`` is true, an intentionally unsupported component
    is injected so the frontend can demonstrate graceful fallback.
    """
    supported = resolve_supported(client_version, supported_header)

    new_components: list[Component] = []
    id_map: dict[str, list[str]] = {}

    for comp in screen.components:
        replacements = downgrade_component(comp, supported)
        id_map[comp.id] = [r.id for r in replacements]
        new_components.extend(replacements)

    new_sections: list[Section] = []
    for section in screen.layout.sections:
        expanded: list[str] = []
        for cid in section.component_ids:
            expanded.extend(id_map.get(cid, [cid]))
        new_sections.append(Section(id=section.id, component_ids=expanded))

    adapted = ScreenResponse(
        schema_version=screen.schema_version,
        screen_id=screen.screen_id,
        title=screen.title,
        layout=Layout(type=screen.layout.type, sections=new_sections),
        components=new_components,
        data=dict(screen.data),
        meta={
            **screen.meta,
            "client_version": client_version,
            "supported_components": sorted(supported),
            "adapted": True,
            "simulate_unknown": simulate_unknown,
        },
    )
    payload = adapted.model_dump()

    if simulate_unknown:
        unknown_id = "sim_unknown_widget"
        payload["components"].append(
            {
                "type": "futuristic_hologram",
                "id": unknown_id,
                "content": "Holographic payment confirmation (unsupported)",
            }
        )
        payload["layout"]["sections"].append(
            {"id": "unknown_demo", "component_ids": [unknown_id]}
        )

    return payload
