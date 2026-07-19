# SysBot Windows Tools (official)

Official collection of **Windows tool packages** for
[SysBot](https://github.com/syan-dev/sysbot). Each subdirectory is a
self-contained tool package (`README.md` + `tool.py`) — `CLITool` wrappers
around Windows commands, or Windows-only `@tool` code. SysBot's core repo
keeps only cross-platform pure-Python packages; the Windows-specific tools
live here. (Linux/Unix counterparts:
[sysbot-linux-tools-official](https://github.com/syan-dev/sysbot-linux-tools-official),
macOS: [sysbot-macos-tools-official](https://github.com/syan-dev/sysbot-macos-tools-official).)

## Install

```powershell
# Offers every package in this repo
sysbot tools install syan-dev/sysbot-windows-tools-official

# Install a single package
sysbot tools install syan-dev/sysbot-windows-tools-official/network
```

Or copy any package folder into your `~/.sysbot/tools/` and restart SysBot.

## Catalog

| Package          | Tools                              | Runs on | Needs                                        |
|------------------|------------------------------------|---------|----------------------------------------------|
| `network/`       | `ping`, `dns_lookup`, `traceroute` | Windows | `ping`, `nslookup`, `tracert` (built in)     |
| `shutdown-wake/` | `shutdown_and_wake`, `cancel_wake` | Windows | `schtasks`, `shutdown`, `powershell` (built in) + firmware wake-timer support for full power-off |
| `temperature/`   | `temperature`                      | Windows | — (`nvidia-smi` used if present)             |

A tool whose OS or required binary isn't satisfied still registers in SysBot,
but calling it returns a one-line explanation instead of failing.

The `network/` package deliberately uses the same folder and tool names as the
Linux collection's — install the one matching the machine's OS.

## Package layout

```
<tool-name>/            # kebab-case folder = the package
  README.md             # frontmatter (name, description, version, platforms, requires)
  tool.py               # CLITool / @tool definitions
```

See SysBot's [writing-tools](https://github.com/syan-dev/sysbot/blob/main/docs/writing-tools.md)
and [sharing-tools](https://github.com/syan-dev/sysbot/blob/main/docs/sharing-tools.md)
guides for how these packages work.

## Contributing with Claude Code

This repo is wired for [Claude Code](https://code.claude.com/docs): open it and
trust the folder, and you'll be offered SysBot's **`sysbot-tool-dev`** plugin,
whose `add-tool` skill teaches Claude the package conventions. Then just ask —
*"add a tool that lists Windows services"* — and it scaffolds the folder,
frontmatter, platform gating, and catalog row for you. Manual install from any
project:

```
/plugin marketplace add syan-dev/sysbot
/plugin install sysbot-tool-dev@sysbot
```

Details: [Writing Tools with Claude Code](https://github.com/syan-dev/sysbot/blob/main/docs/claude-code.md).
