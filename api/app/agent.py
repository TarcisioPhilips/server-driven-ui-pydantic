"""Safe Generative UI agent — same ScreenResponse contract as REST.

Works with zero API keys via FunctionModel (deterministic mock).
When OPENAI_API_KEY or ANTHROPIC_API_KEY is set, uses a real LLM.
"""

from __future__ import annotations

import os
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from app.models.screen import (
    BiometricPromptComponent,
    ButtonComponent,
    HeaderComponent,
    Layout,
    NavigateAction,
    PixQrComponent,
    ScreenResponse,
    Section,
    TextComponent,
)
from app.screens.catalog import build_payment, build_welcome

SYSTEM_PROMPT = """You are a Server-Driven UI generator for a fintech onboarding/checkout flow.
Return a ScreenResponse JSON matching the schema exactly.
Available screens: welcome, payment, confirmation.
Components: header, text, input, button, pix_qr, biometric_prompt.
Actions: navigate, submit, open_modal.
Keep copy professional and concise. Amounts in BRL.
"""


def _extract_prompt(messages: list[ModelMessage]) -> str:
    """Prefer the latest user prompt; ignore system instructions."""
    for msg in reversed(messages):
        for part in reversed(list(getattr(msg, "parts", []))):
            if type(part).__name__ != "UserPromptPart":
                continue
            content = getattr(part, "content", None)
            if isinstance(content, str) and content.strip():
                return content.strip()
    return ""


def _with_banner(screen: ScreenResponse, banner: str) -> ScreenResponse:
    banner_id = "agent_banner"
    comps = list(screen.components)
    comps.insert(
        1,
        TextComponent(id=banner_id, content=banner, variant="alert"),
    )
    sections = []
    for i, section in enumerate(screen.layout.sections):
        ids = list(section.component_ids)
        if i == 0 and "hdr" in ids:
            # Insert banner after header in first section
            idx = ids.index("hdr") + 1
            ids.insert(idx, banner_id)
        sections.append(Section(id=section.id, component_ids=ids))
    if not any(banner_id in s.component_ids for s in sections):
        sections[0] = Section(
            id=sections[0].id,
            component_ids=[banner_id, *sections[0].component_ids],
        )
    return ScreenResponse(
        screen_id=screen.screen_id,
        title=screen.title,
        layout=Layout(type=screen.layout.type, sections=sections),
        components=comps,
        data={**screen.data, "agent_modified": True},
        meta={**screen.meta, "source": "agent", "mode": "function_model"},
    )


def _skip_biometric(screen: ScreenResponse) -> ScreenResponse:
    comps = [c for c in screen.components if c.type != "biometric_prompt"]
    removed = {c.id for c in screen.components if c.type == "biometric_prompt"}
    sections = [
        Section(
            id=s.id,
            component_ids=[cid for cid in s.component_ids if cid not in removed],
        )
        for s in screen.layout.sections
        if any(cid not in removed for cid in s.component_ids)
    ]
    # Ensure at least one section remains valid
    sections = [s for s in sections if s.component_ids]
    note = TextComponent(
        id="bio_skipped",
        content="Biometric step skipped per your request. Confirm payment when ready.",
        variant="caption",
    )
    comps.insert(2, note)
    if sections:
        sections[0] = Section(
            id=sections[0].id,
            component_ids=[*sections[0].component_ids[:2], "bio_skipped", *sections[0].component_ids[2:]],
        )
    return ScreenResponse(
        screen_id=screen.screen_id,
        title=screen.title,
        layout=Layout(type=screen.layout.type, sections=sections),
        components=comps,
        data={**screen.data, "biometric_skipped": True, "agent_modified": True},
        meta={**screen.meta, "source": "agent", "mode": "function_model"},
    )


def build_screen_from_prompt(prompt: str) -> ScreenResponse:
    """Deterministic generative UI from a natural-language prompt."""
    lower = prompt.lower()

    if "skip" in lower and "biometric" in lower:
        return _skip_biometric(build_payment())

    if "pix" in lower and ("discount" in lower or "banner" in lower or "promo" in lower):
        return _with_banner(
            build_payment(),
            "Pix discount: pay now and save 5% on this checkout.",
        )

    if "welcome" in lower or "onboard" in lower or "email" in lower:
        if "banner" in lower or "promo" in lower:
            return _with_banner(build_welcome(), "Limited offer: fee-free Pix transfers this week.")
        return build_welcome().model_copy(
            update={"meta": {**build_welcome().meta, "source": "agent", "mode": "function_model"}}
        )

    if "confirm" in lower:
        from app.screens.catalog import build_confirmation

        screen = build_confirmation()
        return screen.model_copy(
            update={"meta": {**screen.meta, "source": "agent", "mode": "function_model"}}
        )

    if "payment" in lower or "pix" in lower or "pay" in lower:
        screen = build_payment()
        return screen.model_copy(
            update={"meta": {**screen.meta, "source": "agent", "mode": "function_model"}}
        )

    # Default: welcome with an agent note reflecting the prompt
    base = build_welcome()
    return _with_banner(base, f"Agent note: {prompt[:120]}")


def _function_model_handler(
    messages: list[ModelMessage],
    info: AgentInfo,
) -> ModelResponse:
    prompt = _extract_prompt(messages)
    screen = build_screen_from_prompt(prompt)
    payload = screen.model_dump()
    if info.output_tools:
        tool = info.output_tools[0]
        return ModelResponse(
            parts=[ToolCallPart(tool_name=tool.name, args=payload)]
        )
    # Fallback: text JSON (shouldn't hit with output_type set)
    import json

    from pydantic_ai.messages import TextPart

    return ModelResponse(parts=[TextPart(content=json.dumps(payload))])


def _select_model() -> Any:
    """Prefer a real LLM when keys exist; otherwise FunctionModel mock."""
    if os.getenv("OPENAI_API_KEY"):
        from pydantic_ai.models.openai import OpenAIChatModel

        return OpenAIChatModel(os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    if os.getenv("ANTHROPIC_API_KEY"):
        from pydantic_ai.models.anthropic import AnthropicModel

        return AnthropicModel(os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-0"))
    return FunctionModel(_function_model_handler, model_name="sdui-mock")


def create_screen_agent(model: Any | None = None) -> Agent[None, ScreenResponse]:
    return Agent(
        model or _select_model(),
        output_type=ScreenResponse,
        system_prompt=SYSTEM_PROMPT,
        name="sdui-screen-agent",
    )


async def generate_screen(prompt: str, model: Any | None = None) -> ScreenResponse:
    agent = create_screen_agent(model)
    result = await agent.run(prompt)
    screen = result.output
    # Ensure agent provenance in meta
    meta = {**screen.meta, "source": screen.meta.get("source", "agent")}
    return screen.model_copy(update={"meta": meta})
