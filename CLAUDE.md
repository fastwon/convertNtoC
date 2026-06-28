# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Status

Planning stage — **no application code exists yet**. The product spec and architecture live in `docs/DESIGN.md`, and the phased build plan in `docs/ROADMAP.md` (work proceeds stage by stage, P0→P8). This file plus those docs are the source of truth until scaffolding begins. When you scaffold, update them: `docs/DESIGN.md` for product/architecture decisions, `docs/ROADMAP.md` for the plan/progress, and this file for build/run/convention guidance.

## What this is

`convertN2C` = **Convert Novel to Comic**. A project-memory-based app that turns serialized novels into comics while keeping character designs and art style consistent across episodes. The defining constraint that shapes the whole architecture: a *project* owns persistent "global memory" (locked art style + character bank + world bible + rolling per-episode summaries), and every new episode is generated against that memory so episode 1 and episode 5 stay visually and narratively consistent. Read `docs/DESIGN.md` before designing any feature — the memory/consistency model is not obvious from code alone.

## Distribution model — this is a desktop EXE, not a web app

The product ships as a **single Windows EXE** that runs entirely on the end user's PC. There is **no central server and no web deployment**. This drives every architectural choice:

- **Packaging**: PyWebView + PyInstaller → one exe. A PyWebView window hosts the React **static build**; FastAPI runs **in-process, bound to 127.0.0.1** (not exposed). Do not design the backend as a deployed/hosted service.
- **Storage is all local** under `%APPDATA%\convertN2C\` (resolve via `platformdirs`): SQLite for relational data, a local embedded vector store (sqlite-vec recommended, undecided) for character/summary search, and plain files under `projects\<project_id>\` for images. **No S3, no cloud DB.**
- **Distributed to other users; each user brings their own API keys.** No proxy/server of ours sits in front of Claude or the image API — every external call is made from the user's machine with the user's keys, and the user pays for usage.
- **External image generation API** (Replicate/fal etc.) behind the `ImageGenerator` abstraction (`docs/DESIGN.md` §7). Do not hard-wire a provider into business logic.
- **Internet is required** for the generation steps (Claude + image API); the app is otherwise local.

## API key & secret handling (hard rules)

- **Never bundle any API key in the exe, repo, or a plaintext config file.** Keys are entered by the user at first run.
- Store keys via `keyring` (Windows Credential Manager). The LLM/image clients read keys from there, never from constants or env files committed to the repo.
- Never log, serialize, or include keys in exception messages or memory/scratch files.
- Validate a freshly entered key with a cheap call (e.g. Claude `models.list`) and route the user to settings on missing/expired/invalid keys.

## Working with Claude (LLM) — repo conventions

This is an LLM-shaped product. Whenever you write or modify code that calls Claude, **invoke the `claude-api` skill first** and follow its current model IDs and API shapes rather than memory — the API drifts. Key project rules:

- Route **all** Claude calls through a single client module (planned: `app/llm/`). Never scatter `anthropic.Anthropic()` calls across the codebase. The client loads the key from the keyring (see above).
- **Model-per-role** (`docs/DESIGN.md` §6.1): `claude-opus-4-8` for storyboard/continuity reasoning, `claude-sonnet-4-6` for episode summarization, `claude-haiku-4-5` for new-vs-existing character classification. Use exact ID strings; do not append date suffixes. Since the *user* pays, consider a quality↔cost preset (model + effort).
- **Thinking**: adaptive only on these models — `thinking={"type": "adaptive"}`. `budget_tokens` returns 400.
- **Prompt caching is load-bearing for cost and consistency.** Send the project's global memory as a stable `system` prefix with `cache_control` ephemeral; put the current episode's volatile text *after* the breakpoint. Never interpolate `datetime.now()`/UUIDs into the cached prefix. Opus 4.8 minimum cacheable prefix is 4096 tokens. Consider `ttl: "1h"` for an active editing session. See `docs/DESIGN.md` §6.2.
- **Structured output** (character extraction / cross-check): use `output_config={"format": {...}}` (json_schema), not the deprecated `output_format`.
- **Deterministic prompt assembly**: the LLM produces panel breakdowns and descriptions; the final image-prompt string `[style] + [character bank] + [panel description]` is assembled by plain code, not the model — keeps it cache-friendly and reproducible.
- Long/large outputs: stream and use `.get_final_message()` (also gives the desktop UI a progress signal). Novel file uploads: Files API (`file_id` reuse).

## Commands

No build/test/lint tooling exists yet. When scaffolding, record the real commands here. Expected shape once built:

- Frontend: build the React SPA to static assets (Vite recommended; if Next.js, use `output: 'export'`).
- Backend: run FastAPI on 127.0.0.1 for local dev.
- Package: PyInstaller one-file build producing `convertN2C.exe`, with the React static assets included as bundled data.
- In bundled mode, resolve bundled asset paths via `sys._MEIPASS`, not `__file__`.
- Note: PyWebView needs the Edge WebView2 runtime on Windows (present by default on Win11).

## Conventions for new code

- Match the surrounding code's style once it exists; until then follow standard FastAPI (routers/services/schemas) and React SPA idioms.
- Keep the image backend behind `ImageGenerator` (Protocol in `docs/DESIGN.md` §7) so the external-API-vs-local-GPU decision stays swappable.
- Project-scoped data (characters, embeddings, generated panels) must be keyed by `project_id` everywhere — cross-project leakage breaks the core promise.
- All paths are local app-data paths — never assume a server filesystem or cloud bucket.
