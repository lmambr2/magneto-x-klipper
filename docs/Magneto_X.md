# Magneto X support in this Klipper tree

This tree is a **personal fork** for the Peopoly Magneto X.  
**Do not submit these changes to upstream Klipper3d.**

## Peopoly base

Peopoly’s `magneto-x` branch was based on upstream commit:

`5f0d252b408ef0cd182367ba4cc224b8d105f0ec` (2023-05-25, Klipper v0.11 era).

Their public `master` is a history-less squash; use `magneto-x` for archaeology.

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

Arksine’s shell helper (not upstream). Required for MagXY:

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

### Homing behavior

If `[magneto_load_cell]` is loaded, a “Probe triggered prior to movement” condition logs a warning instead of aborting. Prefer clearing the latch (`CLEAR_LOAD_CELL`) before Z home.

## Recommended MCU configs

| Board | Notes |
|-------|-------|
| Octopus Pro H723 USB | + `MAGNETO_RELAX_STEPPER_PAST` |
| Lancer RP2040 CAN | 1 Mbit CAN, no stepper-past option needed |

## External services

Linear motors are armed via Peopoly’s ESP32 bridge + `magneto-manager` HTTP API, not pure Klipper. See the parent workspace `docs/OS_IMAGE.md`.
