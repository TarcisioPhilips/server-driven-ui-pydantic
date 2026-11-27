# AGENTS.md — Engineering standards

Standards for every contributor and coding agent working in this repo.

## Codebase hygiene

- **Remove and reuse before adding.** Prefer deleting dead paths, consolidating duplicates, and extending existing modules over introducing new layers, wrappers, or abstractions.
- Keep the monorepo **lean and optimized**: zero bloat, no speculative frameworks, no “just in case” config.
- Match existing patterns in `api/` and `web/`; do not invent parallel styles.

## Python tooling (`api/`)

- **`uv` is the standard Python package manager** for this repo. Runtime deps live in `[project].dependencies`; dev deps in `[dependency-groups].dev` inside `api/pyproject.toml`. Commit `api/uv.lock`.
- Local setup / tests / run: `uv sync`, `uv sync --frozen`, `uv run pytest`, `uv run uvicorn app.main:app --reload --port 8000` (from `api/`).
- **Do not** add or restore `requirements.txt`, parallel pip install instructions, or a second dependency list that duplicates `pyproject.toml`.

## Pull requests & CI

- Ship **small, focused PRs** with a clear contract or UX outcome.
- CI must be green before merge: backend `uv sync --frozen` + `uv run pytest`, frontend `typecheck` + `vitest` + `build` (see `.github/workflows/ci.yml`).
- **Delete branches after merge.**

## Secrets & planning docs

- **Never commit secrets**, API keys, or `.env` files (`.env` / `.env.*` are gitignored; `.env.example` is fine).
- **Do not commit internal planning docs.** `.plans/` stays gitignored.

## SDUI contract is the source of truth

- `ScreenResponse` (Pydantic v2 in `api/app/models/screen.py`) is the **single wire contract** for:
  - deterministic REST (`GET /screens/{screen_id}`)
  - Generative UI agent mode (`POST /agent/screen`, PydanticAI `output_type=ScreenResponse`)
  - frontend TypeScript types in `web/src/types/sdui.ts`
- Always preserve **backward compatibility**:
  - App v1 ↔ v2 negotiation via `X-Client-Version` / `X-Supported-Components`
  - server-side downgrade for `pix_qr` / `biometric_prompt`
  - client-side `UnknownComponent` fallback (including `?simulate_unknown=true`)
- Keep **contract tests** current when the schema or negotiation rules change (pytest matrix + vitest registry/`UnknownComponent` coverage).
- Prefer exporting / syncing from `GET /schema/screen` rather than hand-drifting TS types.

## Documentation

- Keep **`README.md` accurate to the code** (quickstart, endpoints, architecture diagram). Update it in the same PR as behavior changes.
- Prefer short, correct docs over aspirational fluff (**doc-lag** hygiene: if docs disagree with the repo, fix the docs or the code in that PR).
