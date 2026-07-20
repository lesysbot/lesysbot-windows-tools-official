---
name: temperature
description: CPU/board and GPU temperature readings (WMI thermal zones + nvidia-smi)
version: 1.0.0
platforms: [windows]
requires: []
---
# temperature

Reports current **thermal-zone and GPU temperatures** in one call. Board/CPU
readings come from the ACPI thermal zones Windows exposes through WMI
(`MSAcpi_ThermalZoneTemperature`, read via PowerShell) — no pip dependency.
NVIDIA GPUs are read via `nvidia-smi` when it's on PATH.

**Runs on:** Windows  ·  **Needs:** nothing (`nvidia-smi` used if present)

## Tools
- `/temperature` — grouped readings, e.g.:

  ```
  Thermal zones:
    TZ00_0: 28°C
  GPU:
    GPU0 NVIDIA GeForce RTX 3080: 51°C
  ```

## Honest limitations

Windows gives no unprivileged, universal CPU-core-temperature API. Many
consumer boards leave the ACPI thermal zones empty, or only let Administrators
query them — in that case the tool says so instead of failing. For full
per-core sensor data, install
[LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor)
and check there; NVIDIA GPU readings work anywhere `nvidia-smi` does.

## Install

```powershell
lesysbot tools install lesysbot/lesysbot-windows-tools-official/temperature
```

Or drop this `temperature/` folder into your `~/.lesysbot/tools/` and restart LeSysBot.
