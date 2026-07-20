"""Shutdown + auto-wake on Windows — power off, then have a wake timer power back on.

Once a machine is off, no software can turn it on again — so
``shutdown_and_wake`` first registers a Scheduled Task with *WakeToRun* at the
requested time (Windows' wake-timer mechanism), then schedules the shutdown.
Mirrors the Linux collection's rtcwake-based package.

The power-off is **scheduled 60 s out** rather than run immediately: an
instant poweroff kills this process before the reply can reach the user, so a
remote (Telegram/Slack) user never learns whether the command was accepted.
Just before the scheduled time (~10 s to spare) a final heads-up is pushed to
the requesting user via ``notify_later``.

Wake timers reliably wake Windows from **sleep and hibernate**. Waking from a
full shutdown additionally needs firmware support ("wake timers"/RTC alarm
enabled, ErP off) — see the README. ``cancel_wake`` aborts the pending
shutdown *and* deletes the wake task; the armed state is read back from Task
Scheduler rather than kept in memory, so it survives restarts. The bundled
``power`` package's ``/cancel_shutdown`` knows nothing about the wake task —
use ``/cancel_wake``.
"""
from __future__ import annotations

import asyncio
import time
from datetime import datetime

from lesysbot.mcp import notify_later, tool

# shutdown fires 60 s after scheduling; announce shortly before, leaving
# enough margin for the message to actually get out.
_ANNOUNCE_AFTER = 50.0

_TASK_NAME = "LeSysBotWake"

_pending_announce: asyncio.Task | None = None


def _announce_later(text: str) -> None:
    """Schedule the just-before-shutdown heads-up, replacing any pending one."""
    global _pending_announce
    _cancel_announce()
    _pending_announce = notify_later(text, _ANNOUNCE_AFTER)


def _cancel_announce() -> None:
    global _pending_announce
    if _pending_announce is not None and not _pending_announce.done():
        _pending_announce.cancel()
    _pending_announce = None


async def _run(cmd: list[str], timeout: float = 30.0) -> tuple[int, str]:
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


def _arm_command(wake_iso: str) -> list[str]:
    """PowerShell command registering the WakeToRun task at ``wake_iso``."""
    script = (
        "$action = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument '/c exit'; "
        f"$trigger = New-ScheduledTaskTrigger -Once -At '{wake_iso}'; "
        "$settings = New-ScheduledTaskSettingsSet -WakeToRun; "
        f"Register-ScheduledTask -TaskName '{_TASK_NAME}' -Action $action "
        "-Trigger $trigger -Settings $settings -Force | Out-Null"
    )
    return ["powershell", "-NoProfile", "-Command", script]


async def _wake_task_armed() -> bool:
    """True when the wake task currently exists in Task Scheduler."""
    code, _ = await _run(["schtasks", "/Query", "/TN", _TASK_NAME])
    return code == 0


async def _delete_wake_task() -> tuple[int, str]:
    return await _run(["schtasks", "/Delete", "/TN", _TASK_NAME, "/F"])


@tool(
    description=(
        "Power off this machine in 1 minute and automatically wake it again "
        "after the given number of minutes (Task Scheduler wake timer)"
    ),
    confirm="⚠️ This will POWER OFF the machine in 1 minute and auto-start it again later. Proceed?",
    platforms=["windows"],
    requires=["schtasks", "shutdown", "powershell"],
)
async def shutdown_and_wake(minutes: int = 60) -> str:
    """Register the wake task, then schedule a power-off 60 s from now."""
    try:
        # Slash commands (and some LLMs) pass numbers as strings.
        minutes = int(minutes)
    except (TypeError, ValueError):
        return f"minutes must be a whole number, got {minutes!r}."
    if minutes < 1:
        return "minutes must be at least 1."
    # The wake delay counts from the actual power-off (60 s out), not from now.
    wake_epoch = int(time.time()) + 60 + minutes * 60
    wake_dt = datetime.fromtimestamp(wake_epoch)
    code, out = await _run(_arm_command(wake_dt.strftime("%Y-%m-%dT%H:%M:%S")))
    if code != 0:
        return (
            f"Could not register the wake task (exit {code}): {out or 'unknown error'}. "
            "Registering a Scheduled Task normally works for your own user — if it "
            "failed, check that the Task Scheduler service is running. Nothing was "
            "shut down."
        )
    code, out = await _run(["shutdown", "/s", "/t", "60"])
    if code != 0:
        await _delete_wake_task()
        return (
            f"The wake task was registered but the shutdown failed (exit {code}): "
            f"{out or 'unknown error — may need elevated privileges.'} "
            "The wake task was deleted again."
        )
    wake_at = wake_dt.strftime(
        "%H:%M" if wake_dt.date() == datetime.now().date() else "%a %H:%M"
    )
    _announce_later(
        f"⏻ Powering off now — the machine is set to wake again around {wake_at}. Goodbye!"
    )
    return (
        "✅ Shutdown scheduled — the machine will power off in 1 minute and "
        f"wake itself again around {wake_at} (from sleep/hibernate always; from "
        "full power-off only if the firmware supports wake timers). "
        "Use /cancel_wake to abort both."
    )


@tool(
    description="Cancel a pending shutdown-and-wake: abort the shutdown and delete the wake task",
    confirm="Cancel the pending shutdown and delete the wake task?",
    platforms=["windows"],
    requires=["schtasks", "shutdown", "powershell"],
)
async def cancel_wake() -> str:
    """Cancel the scheduled shutdown and delete any registered wake task."""
    parts: list[str] = []
    code, out = await _run(["shutdown", "/a"])
    if code == 0:
        _cancel_announce()
        parts.append("Cancelled the pending shutdown.")
    else:
        # Don't cancel the announcement here: if the abort failed, the
        # shutdown is still coming and the heads-up should fire.
        parts.append(
            f"No shutdown was cancelled (exit {code}): "
            f"{out or 'none pending, or elevated privileges needed'}."
        )
    if await _wake_task_armed():
        del_code, del_out = await _delete_wake_task()
        if del_code == 0:
            parts.append("Deleted the wake task.")
        else:
            parts.append(
                f"Could not delete the wake task (exit {del_code}): "
                f"{del_out or 'unknown error'} — the machine may still wake "
                "at the scheduled time."
            )
    else:
        parts.append("No wake task was registered.")
    return " ".join(parts)
