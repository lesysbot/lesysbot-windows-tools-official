# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with
code in this repository.

This is an **official LeSysBot tools collection**: every subdirectory of
`tools/` is a self-contained tool package (`README.md` + `tool.py`) for
[LeSysBot](https://github.com/lesysbot/lesysbot). There is no application code
here — packages are loaded by a LeSysBot install, not by anything in this repo.

## Writing a tool package

Prefer the `add-tool` skill from the `lesysbot-tool-dev` plugin (this repo's
`.claude/settings.json` offers it on first open; manual install:
`/plugin marketplace add lesysbot/lesysbot` then
`/plugin install lesysbot-tool-dev@lesysbot`). The short version:

- Package = kebab-case folder under `tools/` with `README.md` (frontmatter:
  `name`, `description`, `version`, `platforms`, `requires`) + `tool.py`.
- `tool.py`: `CLITool` for a single shell command, `@tool`-decorated functions
  for Python logic (type hints become the LLM's JSON schema). Return a string.
- This collection is **Windows-specific by charter** — declare
  `platforms=["windows"]` and `requires=[...]` for PATH executables.
  Cross-platform pure-Python tools belong in the core repo's `tools/` instead;
  Linux/macOS variants live in their own official collections.
- Windows commands ship with the OS (`schtasks`, `shutdown`, `powershell`,
  `tracert`, …) — still declare them in `requires` so the gating stays honest.
- Destructive actions: `confirm=True` or `confirm="message?"` on the tool.
- Helpers go in a package-local `_`-prefixed file (`_helpers.py`); the loader
  ignores it, `tool.py` imports it at module top level.
- Add a row to the **Catalog** table in the root `README.md`.
- Subprocess-driven `@tool` packages route every command through a module-level
  `_run(cmd: list[str])` helper so `tests/` can monkeypatch it (see
  `tools/shutdown-wake/` and `tests/test_shutdown_wake.py`) — tests must pass on
  any OS without touching Task Scheduler or real hardware.

## Commands

```bash
# Lint
ruff check .

# Tests (hardware-free, run on any OS)
pytest tests/

# Run LeSysBot against this checkout (packages hot-reload on save; on Windows)
$env:LESYSBOT_MCP__TOOLS_DIR="$PWD\tools"; lesysbot --provider cli
# then in the CLI: /help (tool listed?), /<name> <args> (runs without the LLM)
```

Full reference:
[writing-tools](https://github.com/lesysbot/lesysbot/blob/main/docs/writing-tools.md),
[sharing-tools](https://github.com/lesysbot/lesysbot/blob/main/docs/sharing-tools.md),
[claude-code](https://github.com/lesysbot/lesysbot/blob/main/docs/claude-code.md).
