# Magneto X support in this tree

Repo: **magneto-x-klipper**  
This file is on branch **`magneto-x-kalico`** (Kalico base).  
Sibling track: branch **`magneto-x`** (mainline Klipper3d base).

Umbrella project: [magneto-x](https://github.com/lmambr2/magneto-x) (configs, host OS, research).

This tree is a **community/personal fork** for the Peopoly Magneto X.  
**Do not submit these changes to upstream Klipper3d or KalicoCrew/kalico.**

## Tracks (A/B)

| Branch | Base | Default? | See |
|--------|------|----------|-----|
| **`magneto-x`** | [Klipper3d/klipper](https://github.com/Klipper3d/klipper) | **Yes** (recommended first) | [TRACKS.md](TRACKS.md) |
| **`magneto-x-kalico`** | [KalicoCrew/kalico](https://github.com/KalicoCrew/kalico) | Optional A/B | [TRACKS.md](TRACKS.md) |

Same Magneto hardware extras on both. Switch base only after backups; flash MCUs from the tree you run.

## Peopoly base (archaeology)

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

**On this Kalico track**, shell commands ship with Kalico (see [Kalico additions](https://docs.kalico.gg/Kalico_Additions.html)).  
Still required for MagXY arm/disarm via magneto-manager:

```ini
[gcode_shell_command LINEAR_MOTOR_ENABLE]
command: curl -sG http://127.0.0.1:8880/send_command --data-urlencode command=ENABLE
timeout: 3.
verbose: False
```

(On the mainline `magneto-x` branch the same module is vendored in-tree because Klipper3d does not ship it.)

### MCU option `MAGNETO_RELAX_STEPPER_PAST`

Under **Enable extra low-level configuration options**, enable:

> Magneto X: relax 'Stepper too far in past' shutdown

Only for the **Octopus** MagXY step/dir outputs.

### Homing behavior

If `[magneto_load_cell]` is loaded, a “Probe triggered prior to movement” condition logs a warning instead of aborting. Prefer clearing the latch (`CLEAR_LOAD_CELL`) before Z home.

## Recommended MCU configs

| Board | Notes |
|-------|-------|
| Octopus Pro H723 USB | + `MAGNETO_RELAX_STEPPER_PAST` |
| Lancer RP2040 CAN | Stock Linux Hub CAN is **250000** (not 1 Mbit); no stepper-past option needed |

## Kalico-only extras (optional)

Useful on this track only (see [docs.kalico.gg](https://docs.kalico.gg/Kalico_Additions.html)):

- `[danger_options]` — e.g. multi-MCU trsync timeout tuning (Schmudus path)
- MPC / velocity PID / PID profiles
- Built-in shell, dockable probe helpers, macro QoL

These are **not** required for first Magneto motion. Prefer leaving danger options off until the machine homes and prints on stock-like settings.

## External services

Linear motors are armed via Peopoly’s ESP32 bridge + `magneto-manager` HTTP API, not pure Klipper/Kalico. See the umbrella `docs/OS_IMAGE.md`.

## Surviving upstream syncs

Magneto assets are listed in [`magneto/MANIFEST.json`](../magneto/MANIFEST.json).  
Patched upstream regions use `MAGNETO-X-BEGIN` / `MAGNETO-X-END` markers.

```bash
python3 scripts/magneto_guard.py
python3 -m unittest discover -s tests/magneto -v
```

See [UPSTREAM_SYNC.md](UPSTREAM_SYNC.md) for the merge/rebase procedure (Kalico remote).
