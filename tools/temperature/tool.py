"""CPU & GPU temperature on Windows — ACPI thermal zones plus nvidia-smi.

Windows has no ``/sys`` equivalent; the closest built-in source is the WMI
class ``MSAcpi_ThermalZoneTemperature`` (namespace ``root/wmi``), read here
via PowerShell's ``Get-CimInstance``. Many consumer boards don't populate it —
or only expose it to Administrators — so the tool reports what it can and
explains what it can't. NVIDIA GPUs are read via ``nvidia-smi`` when it's on
PATH (the driver installs it system-wide).
"""
from __future__ import annotations

import asyncio
import shutil

from lesysbot.mcp import tool

# One "InstanceName,CurrentTemperature" line per ACPI thermal zone; the value
# is in tenths of a kelvin.
_PS_THERMAL = (
    "Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature "
    '-ErrorAction Stop | ForEach-Object { "$($_.InstanceName),$($_.CurrentTemperature)" }'
)


async def _run(cmd: list[str], timeout: float = 20.0) -> tuple[int, str]:
    """Run a command, returning (returncode, combined stdout+stderr)."""
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout)
    except asyncio.TimeoutError:
        proc.kill()
        return 1, f"timed out after {timeout}s"
    return proc.returncode, stdout.decode(errors="replace").strip()


def _parse_thermal(output: str) -> list[str]:
    """``name,tenths-of-kelvin`` lines → per-zone °C readings."""
    readings: list[str] = []
    for raw in output.splitlines():
        name, _, value = raw.strip().rpartition(",")
        try:
            celsius = float(value) / 10.0 - 273.15
        except ValueError:
            continue
        # Dead/unpopulated zones report absurd values.
        if not -20.0 < celsius < 150.0:
            continue
        zone = name.split("\\")[-1] if name else ""
        readings.append(f"{zone or 'thermal zone'}: {celsius:.0f}°C")
    return readings


async def _nvidia_readings() -> list[str]:
    """GPU temps from nvidia-smi, or [] when it's absent or failing."""
    if shutil.which("nvidia-smi") is None:
        return []
    code, out = await _run([
        "nvidia-smi",
        "--query-gpu=index,name,temperature.gpu",
        "--format=csv,noheader,nounits",
    ])
    if code != 0:
        return []
    readings = []
    for line in out.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 3:
            continue
        index, temp = parts[0], parts[-1]
        gpu_name = ", ".join(parts[1:-1])
        readings.append(f"GPU{index} {gpu_name}: {temp}°C")
    return readings


@tool(
    description="Report current CPU/board and GPU temperatures in °C",
    platforms=["windows"],
)
async def temperature() -> str:
    """Return thermal-zone and GPU temperature readings, grouped per device."""
    code, out = await _run(["powershell", "-NoProfile", "-Command", _PS_THERMAL])
    zones = _parse_thermal(out) if code == 0 else []
    gpu = await _nvidia_readings()

    if not zones and not gpu:
        return (
            "No temperature sensors found. Windows only exposes ACPI thermal "
            "zones (WMI MSAcpi_ThermalZoneTemperature), and many boards don't "
            "populate them — or only allow Administrators to read them. For "
            "rich sensor data install LibreHardwareMonitor; NVIDIA GPU temps "
            "appear once nvidia-smi is on PATH."
        )

    def section(title: str, lines: list[str]) -> str:
        if not lines:
            return f"{title}: no sensor found"
        return f"{title}:\n" + "\n".join(f"  {line}" for line in lines)

    return section("Thermal zones", zones) + "\n" + section("GPU", gpu)
