# A/B tracks: mainline vs Kalico

`magneto-x-klipper` ships **two long-lived branches** with the same Magneto hardware delta on different host firmwares.

| Branch | Upstream base | Who should use it |
|--------|---------------|-------------------|
| **`magneto-x`** (default) | [Klipper3d/klipper](https://github.com/Klipper3d/klipper) `master` | Most owners; closest to stock Klipper norms; first path for “never worked → get motion” |
| **`magneto-x-kalico`** | [KalicoCrew/kalico](https://github.com/KalicoCrew/kalico) `main` | A/B testing; want Kalico-only extras (`danger_options`, MPC, PID_v, built-in shell, probe QoL) |

Both include:

- `magneto_load_cell` (Lancer latch reset)
- sticky-probe soft-fail in `homing.py`
- optional `MAGNETO_RELAX_STEPPER_PAST` for Octopus MagXY
- MagXY still via `gcode_shell_command` + magneto-manager (shell is **vendored** on mainline, **native** on Kalico)

Neither track puts MagXY closed-loop inside the host stepgen.

## Moonraker / KIAUH

### Default (mainline)

```ini
[update_manager klipper]
type: git_repo
path: ~/klipper
origin: https://github.com/lmambr2/magneto-x-klipper.git
primary_branch: magneto-x
managed_services: klipper
```

### Kalico track

```ini
[update_manager klipper]
type: git_repo
path: ~/klipper
origin: https://github.com/lmambr2/magneto-x-klipper.git
primary_branch: magneto-x-kalico
managed_services: klipper
```

Clone either:

```bash
# A — mainline (recommended first)
git clone -b magneto-x https://github.com/lmambr2/magneto-x-klipper.git ~/klipper

# B — Kalico
git clone -b magneto-x-kalico https://github.com/lmambr2/magneto-x-klipper.git ~/klipper
```

## Switching tracks (A ↔ B)

1. **Backup** `printer_data/config` and note MCU UUIDs / z_offset / PID / mesh.
2. Stop Klipper: `sudo systemctl stop klipper`.
3. Fetch and checkout the other branch (or re-clone into a second directory for true A/B).
4. **Rebuild and reflash** Octopus + Lancer from the tree you will run (MCU protocol must match the host).
5. Keep the same umbrella `config/` package; optionally enable Kalico-only includes (e.g. `danger_options.cfg`) only on the Kalico track.
6. `python3 scripts/magneto_guard.py` then start Klipper.
7. `LM_ENABLE` → home → QGL → short print; compare logs and first-layer quality.

Do **not** mix a mainline host with firmware built from the Kalico tree (or vice versa).

## True side-by-side A/B

Use two directories if you want fast rollback without rebuild confusion:

```bash
git clone -b magneto-x https://github.com/lmambr2/magneto-x-klipper.git ~/klipper-mainline
git clone -b magneto-x-kalico https://github.com/lmambr2/magneto-x-klipper.git ~/klipper-kalico
# Point the systemd unit WorkingDirectory / symlink ~/klipper at the active tree
```

Flash MCUs once per tree; label the `.bin` files.

## Sync policy

| Track | Fetch remote | Merge into |
|-------|--------------|------------|
| `magneto-x` | `upstream` = Klipper3d | `magneto-x` |
| `magneto-x-kalico` | `kalico` = KalicoCrew/kalico | `magneto-x-kalico` |

Do **not** merge the two Magneto branches into each other as a routine — they share *intent* (MANIFEST + markers), not a linear history after the bases diverge.

After every upstream pull on either track:

```bash
python3 scripts/magneto_guard.py
python3 -m unittest discover -s tests/magneto -v
```

## When to prefer Kalico

- Dual-MCU timing flakiness and you want `[danger_options]` trsync knobs (read docs carefully).
- Experimenting with MPC / velocity PID / multi-temp PID profiles.
- Aligning with community guides that assume Kalico (e.g. Schmudus Pi+Beacon path).

## When to stay mainline

- First recovery of a stock Magneto X.
- Want fewer “danger” footguns and simpler support questions.
- Prefer tracking one well-known upstream (Klipper3d).

## Policy

- No Magneto PRs to **Klipper3d/klipper** or **KalicoCrew/kalico**.
- Configs live in [lmambr2/magneto-x](https://github.com/lmambr2/magneto-x) and stay host-track-agnostic where possible.
