"""Network tools — Windows-syntax shell commands wrapped as bot tools.

The official Linux collection wraps the Unix variants (``ping -c``,
``traceroute``); these use the Windows flags (``ping -n``, ``tracert``) and
declare ``platforms=["windows"]``. Install one collection's network package or
the other — the tool names match on purpose, and both packages install as a
folder named ``network/``, so they replace each other in ``~/.lesysbot/tools/``.
"""
from lesysbot.mcp import CLITool

_WIN = ["windows"]

ping = CLITool(
    name="ping",
    description="Ping a host to check connectivity and measure latency",
    command="ping -n 3 {host}",
    params={"host": "Hostname or IP address to ping"},
    timeout=15.0,
    platforms=_WIN,
    requires=["ping"],
)

dns_lookup = CLITool(
    name="dns_lookup",
    description="Resolve a domain name to its IP addresses",
    command="nslookup {domain}",
    params={"domain": "Domain name to resolve"},
    platforms=_WIN,
    requires=["nslookup"],
)

traceroute = CLITool(
    name="traceroute",
    description="Trace the network path to a host",
    command="tracert -h 15 -w 1000 {host}",
    params={"host": "Hostname or IP address to trace"},
    timeout=120.0,
    platforms=_WIN,
    requires=["tracert"],
)
