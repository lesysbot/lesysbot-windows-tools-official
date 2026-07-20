"""Parsing logic in the temperature package — no WMI or GPU needed."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_TOOL_PY = Path(__file__).resolve().parents[1] / "tools" / "temperature" / "tool.py"

spec = importlib.util.spec_from_file_location("_win_temperature_under_test", _TOOL_PY)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_parses_thermal_zone_lines():
    out = "ACPI\\ThermalZone\\TZ00_0,3010\nACPI\\ThermalZone\\TZ01_0,3231"
    assert mod._parse_thermal(out) == ["TZ00_0: 28°C", "TZ01_0: 50°C"]


def test_skips_junk_and_dead_sensors():
    out = "\n".join([
        "ACPI\\ThermalZone\\TZ00_0,not-a-number",
        "ACPI\\ThermalZone\\TZ01_0,65535",  # 6280°C — dead sensor
        "ACPI\\ThermalZone\\TZ02_0,2520",   # -21.15°C — below plausible range
        "ACPI\\ThermalZone\\TZ03_0,3100",
    ])
    assert mod._parse_thermal(out) == ["TZ03_0: 37°C"]


def test_handles_missing_instance_name():
    assert mod._parse_thermal(",3010") == ["thermal zone: 28°C"]


def test_empty_output_gives_no_readings():
    assert mod._parse_thermal("") == []
