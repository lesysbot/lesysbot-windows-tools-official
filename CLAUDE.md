# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with
code in this repository.

This is an **official SysBot tools collection**: every top-level subdirectory
is a self-contained tool package (`README.md` + `tool.py`) for
[SysBot](https://github.com/syan-dev/sysbot). There is no application code
here — packages are loaded by a SysBot install, not by anything in this repo.

## Writing a tool package

Prefer the `add-tool` skill from the `sysbot-tool-dev` plugin (this repo's
`.claude/settings.json` offers it on first open; manual install:
`/plugin marketplace add syan-dev/sysbot` then
`/plugin install sysbot-tool-dev@sysbot`). The short version:

- Package = top-level kebab-case folder with `README.md` (frontmatter: `name`,
  `description`, `version`, `platforms`, `requires`) + `tool.py`.
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
  `_run(cmd: list[str])` helper so `_tests/` can monkeypatch it (see
  `shutdown-wake/` and `_tests/test_shutdown_wake.py`) — tests must pass on
  any OS without touching Task Scheduler or real hardware.

## Commands

```bash
# Lint
ruff check .

# Tests (hardware-free, run on any OS)
pytest _tests/

# Run SysBot against this checkout (packages hot-reload on save; on Windows)
$env:SYSBOT_MCP__TOOLS_DIR="$PWD"; sysbot --provider cli
# then in the CLI: /help (tool listed?), /<name> <args> (runs without the LLM)
```

Full reference:
[writing-tools](https://github.com/syan-dev/sysbot/blob/main/docs/writing-tools.md),
[sharing-tools](https://github.com/syan-dev/sysbot/blob/main/docs/sharing-tools.md),
[claude-code](https://github.com/syan-dev/sysbot/blob/main/docs/claude-code.md).
