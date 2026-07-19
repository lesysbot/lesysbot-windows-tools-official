---
name: shutdown-wake
description: Power off and auto-wake later via a Task Scheduler wake timer
version: 1.0.0
platforms: [windows]
requires: [schtasks, shutdown, powershell]
---
# shutdown-wake

Powers the machine off **and brings it back** at a chosen time — the Windows
analog of the Linux collection's rtcwake package. It registers a Scheduled
Task with *WakeToRun* (a Windows wake timer) before scheduling the shutdown,
so the firmware wakes the machine again on its own.

**Runs on:** Windows  ·  **Needs:** `schtasks`, `shutdown`, `powershell` (all ship with Windows)

## Tools
- `/shutdown_and_wake minutes=60` — power off in 1 minute, wake ~60 minutes
  after the power-off. Asks for confirmation first.
- `/cancel_wake` — abort the pending shutdown **and** delete the wake task.
  (The core `power` package's `/cancel_shutdown` doesn't know about the wake
  task — after it, the machine would still wake up.)

## How reliable is the wake-up?

- **Sleep / hibernate:** wake timers are a first-class Windows feature — this
  works on any machine whose power plan allows wake timers
  (*Power Options → Advanced → Sleep → Allow wake timers*, on by default).
- **Full shutdown:** waking from S5 needs firmware cooperation. Enable the
  BIOS/UEFI RTC alarm or "wake timers" option and disable ErP/deep-off modes.
  With Fast Startup enabled (the Windows default), `shutdown /s` is a hybrid
  hibernate, which wakes on most hardware. Test once before relying on it.
- Verify a timer is armed with `powercfg /waketimers` (needs an elevated
  prompt).

## Install

```powershell
sysbot tools install syan-dev/sysbot-windows-tools-official/shutdown-wake
```

Or drop this `shutdown-wake/` folder into your `~/.sysbot/tools/` and restart SysBot.
