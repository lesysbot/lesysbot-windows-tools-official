---
name: network
description: Windows network diagnostics (ping, nslookup, tracert)
version: 1.0.0
platforms: [windows]
requires: [ping, nslookup, tracert]
---
# network

Windows-flavored network diagnostics: the same `ping`, `dns_lookup`, and
`traceroute` tools as the official Linux collection, using the Windows
commands and flags (`ping -n`, `tracert`).

**Runs on:** Windows  ·  **Needs:** `ping`, `nslookup`, `tracert` (all ship with Windows)

## Tools
- `/ping <host>` — 3 echo requests with latency stats (`ping -n 3`)
- `/dns_lookup <domain>` — resolve a name to its IP addresses (`nslookup`)
- `/traceroute <host>` — network path, max 15 hops (`tracert -h 15 -w 1000`)

Don't install this alongside the Linux collection's `network/` package — the
folder and tool names deliberately match, so the two replace each other.

## Install

```powershell
sysbot tools install syan-dev/sysbot-windows-tools-official/network
```

Or drop this `network/` folder into your `~/.sysbot/tools/` and restart SysBot.
