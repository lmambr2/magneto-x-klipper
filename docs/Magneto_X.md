# Magneto X support in this Klipper tree

Repo: **magneto-x-klipper** (branch **`magneto-x-kalico`**, Kalico track).  
Sibling track: branch **`magneto-x`** (mainline Klipper3d) — see [TRACKS.md](TRACKS.md).  
Umbrella project: [magneto-x](https://github.com/lmambr2/magneto-x) (configs, host OS, research).

This tree is a **community/personal fork** for the Peopoly Magneto X.  
**Do not submit these changes to upstream Klipper3d or KalicoCrew/kalico.**

## Peopoly base

Peopoly’s repo `mypeopoly/Klipper`, branch `magneto-x`, was based on upstream commit:

`5f0d252b408ef0cd182367ba4cc224b8d105f0ec` (2023-05-25, Klipper v0.11 era).

Their public `master` is a history-less squash; use their `magneto-x` branch for archaeology only.

## Modules unique to this fork

### `[magneto_load_cell]`

Resets the stock digital load-cell latch on the Lancer toolhead.

```ini
[magneto_load_cell]
pin: MAG_TOOL:gpio24
pulse_time: 0.4
auto_clear_on_home: True
```

G-codes: `CLEAR_LOAD_CELL` / `LC28`, `LL28`, `LH28`.

This is **not** the same as upstream `[load_cell]` / `[load_cell_probe]` (those need a direct ADC).

### `[gcode_shell_command]`

Arksine’s shell helper (**native on this Kalico track**; vendored on `magneto-x` mainline). Required for MagXY:

```ini
[gcode_shell_command LINEAR_MOTOR_ENABLE]
command: curl -sG http://127.0.0.1:8880/send_command --data-urlencode command=ENABLE
timeout: 3.
verbose: False
```

### MCU option `MAGNETO_RELAX_STEPPER_PAST`

Under **Enable extra low-level configuration options**, enable:

> Magneto X: relax 'Stepper too far in past' shutdown

Only for the **Octopus** MagXY step/dir outputs.

Menuconfig (Octopus): STM32H723, 128KiB bootloader, **25 MHz crystal**, USB. Default leave relax **disabled** (D15).

### Homing behavior (D7)

If `[magneto_load_cell]` is loaded and the probe is already triggered before the move:

1. Clear the load-cell latch (`clear_load_cell` / dwell)
2. Retry the probe move **once**
3. If still sticky → hard error

Prefer clearing the latch (`CLEAR_LOAD_CELL` / `LC28`) before Z home. `CLEAR_LOAD_CELL` **dwells** for the full pulse window (PR-K2).

### Shell PARAMS (PR-K5)

`[gcode_shell_command]` rejects non-empty `PARAMS` by default (`allow_params: False`). MagXY curls must be fixed command lines only.

## Recommended MCU configs

| Board | Notes |
|-------|-------|
| Octopus Pro H723 USB | + `MAGNETO_RELAX_STEPPER_PAST` |
| Lancer RP2040 CAN | Stock Linux Hub CAN is **250000** (not 1 Mbit); no stepper-past option needed |

## External services

Linear motors are armed via Peopoly’s ESP32 bridge + `magneto-manager` HTTP API, not pure Klipper. See the parent workspace `docs/OS_IMAGE.md`.

## Surviving upstream syncs

Magneto assets are listed in [`magneto/MANIFEST.json`](../magneto/MANIFEST.json).
Patched upstream regions use `MAGNETO-X-BEGIN` / `MAGNETO-X-END` markers.

```bash
python3 scripts/magneto_guard.py
python3 -m unittest discover -s tests/magneto -v
```

See [UPSTREAM_SYNC.md](UPSTREAM_SYNC.md) for the merge/rebase procedure.
