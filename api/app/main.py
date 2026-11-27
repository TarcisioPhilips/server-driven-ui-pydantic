"""FastAPI entrypoint for Server-Driven UI."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Quiet the pydantic-ai banner in CI / local runs
os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from app.routes import actions, agent, screens

app = FastAPI(
    title="Server-Driven UI (Pydantic)",
    description="Fintech onboarding/checkout SDUI + safe Generative UI",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(screens.router)
app.include_router(agent.router)
app.include_router(actions.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
