"""Wake-timer logic in the shutdown-wake package.

Loads shutdown-wake/tool.py straight from its file (as the registry would)
and records every subprocess call through a patched _run — so these run on
any OS without touching Task Scheduler or shutting anything down.

Kept in a ``_``-prefixed directory so neither SysBot's loader nor its
installer treats it as a tool package. Tests are sync and drive the async
tools via asyncio.run(), so plain ``pytest _tests/`` works with no
pytest-asyncio configuration.
"""
from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path

import pytest

_TOOL_PY = Path(__file__).resolve().parents[1] / "shutdown-wake" / "tool.py"


def run(coro):
    return asyncio.run(coro)


class FakeRun:
    """Stand-in for tool._run: records commands, fails configured prefixes."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []
        self.fail_prefixes: set[str] = set()

    async def __call__(self, cmd: list[str], timeout: float = 30.0) -> tuple[int, str]:
        self.calls.append(cmd)
        joined = " ".join(cmd)
        if any(joined.startswith(p) for p in self.fail_prefixes):
            return 1, "boom"
        return 0, ""

    def commands(self) -> list[str]:
        return [" ".join(c) for c in self.calls]


@pytest.fixture()
def wake(monkeypatch):
    spec = importlib.util.spec_from_file_location("_win_shutdown_wake_under_test", _TOOL_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fake = FakeRun()
    monkeypatch.setattr(mod, "_run", fake)
    return mod, fake


def test_rejects_non_positive_minutes(wake):
    mod, fake = wake
    reply = run(mod.shutdown_and_wake(minutes=0))
    assert "at least 1" in reply
    assert fake.calls == []


def test_coerces_string_minutes(wake):
    """Slash commands pass args as strings — '/shutdown_and_wake minutes=0'."""
    mod, fake = wake
    assert "at least 1" in run(mod.shutdown_and_wake(minutes="0"))
    assert "whole number" in run(mod.shutdown_and_wake(minutes="soon"))
    assert fake.calls == []
    assert "power off in 1 minute" in run(mod.shutdown_and_wake(minutes="60"))


def test_registers_wake_task_then_schedules_shutdown(wake):
    mod, fake = wake
    reply = run(mod.shutdown_and_wake(minutes=60))
    assert "power off in 1 minute" in reply and "wake itself again" in reply
    arm, poweroff = fake.commands()
    assert arm.startswith("powershell -NoProfile -Command")
    assert "Register-ScheduledTask" in arm and "-WakeToRun" in arm
    assert f"-TaskName '{mod._TASK_NAME}'" in arm
    assert poweroff == "shutdown /s /t 60"


def test_arm_failure_aborts_shutdown(wake):
    mod, fake = wake
    fake.fail_prefixes = {"powershell"}
    reply = run(mod.shutdown_and_wake(minutes=60))
    assert "Nothing was shut down" in reply
    assert not any(c.startswith("shutdown") for c in fake.commands())


def test_shutdown_failure_deletes_wake_task(wake):
    mod, fake = wake
    fake.fail_prefixes = {"shutdown /s"}
    reply = run(mod.shutdown_and_wake(minutes=60))
    assert "deleted again" in reply
    assert f"schtasks /Delete /TN {mod._TASK_NAME} /F" in fake.commands()


def test_cancel_deletes_registered_task(wake):
    """FakeRun answers the schtasks /Query probe with success = task exists."""
    mod, fake = wake
    reply = run(mod.cancel_wake())
    assert "Cancelled the pending shutdown" in reply
    assert "Deleted the wake task" in reply
    assert fake.commands() == [
        "shutdown /a",
        f"schtasks /Query /TN {mod._TASK_NAME}",
        f"schtasks /Delete /TN {mod._TASK_NAME} /F",
    ]


def test_cancel_without_task_skips_delete(wake):
    mod, fake = wake
    fake.fail_prefixes = {"schtasks /Query"}
    reply = run(mod.cancel_wake())
    assert "No wake task was registered" in reply
    assert not any("Delete" in c for c in fake.commands())


def test_cancel_failure_reports_but_still_deletes_task(wake):
    mod, fake = wake
    fake.fail_prefixes = {"shutdown /a"}
    reply = run(mod.cancel_wake())
    assert "No shutdown was cancelled" in reply
    assert "Deleted the wake task" in reply
    assert f"schtasks /Delete /TN {mod._TASK_NAME} /F" in fake.commands()
