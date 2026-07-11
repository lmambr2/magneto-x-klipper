# Syncing magneto-x-kalico with upstream Kalico

This document is for branch **`magneto-x-kalico`**.  
For the mainline track, checkout **`magneto-x`** and use the Klipper3d procedure in that branch’s `docs/UPSTREAM_SYNC.md`.

Tracks overview: [TRACKS.md](TRACKS.md).

## What survives a merge automatically?

| Kind | Paths | Risk |
|------|--------|------|
| **Owned files** (Magneto-only) | `klippy/extras/magneto_load_cell.py`, `magneto/*`, `scripts/magneto_guard.py`, `docs/Magneto_X.md`, `docs/TRACKS.md` | Low — git will not delete them unless you resolve a conflict by deleting |
| **Base files** (Kalico-provided) | `klippy/extras/gcode_shell_command.py` | Medium — keep Kalico’s version; do not delete |
| **Patched upstream files** | `homing.py`, `src/stepper.c`, `src/Kconfig` | **High** — conflicts; easy to drop Magneto hunks by mistake |

Protection is:

1. **Isolated owned modules** (extras load by filename — safe)
2. **`MAGNETO-X-BEGIN` / `MAGNETO-X-END` markers** in every patched region
3. **`scripts/magneto_guard.py` + CI** that fails if markers/files vanish
4. **Unit tests** for load-cell pulse logic + guard itself

## Recommended sync procedure (Kalico)

```bash
cd ~/klipper   # or this clone

# 1) Fetch Kalico
git remote add kalico https://github.com/KalicoCrew/kalico.git 2>/dev/null || true
git fetch kalico

# 2) Baseline guard
git checkout magneto-x-kalico
python3 scripts/magneto_guard.py

# 3) Merge Kalico main
git merge kalico/main
# or: git rebase kalico/main

# 4) Resolve conflicts carefully:
#    - Keep MAGNETO-X-BEGIN ... MAGNETO-X-END blocks in homing.py / stepper.c / Kconfig
#    - Never delete klippy/extras/magneto_*.py
#    - Prefer Kalico’s gcode_shell_command.py (base_files), not an old mainline copy

# 5) Re-verify
python3 scripts/magneto_guard.py
python3 -m unittest discover -s tests/magneto -v

# 6) Only then push
git push origin magneto-x-kalico
```

## If a test / guard fails after merge

| Symptom | Meaning | Fix |
|---------|---------|-----|
| `missing owned file: klippy/extras/magneto_load_cell.py` | File deleted in conflict resolution | Restore from pre-merge commit |
| `missing base file: .../gcode_shell_command.py` | Kalico module removed | Restore from `kalico/main` |
| `missing marker MAGNETO-X-BEGIN …` | Upstream rewrite dropped our hunk | Re-apply patch by hand; update markers if API moved |
| Unit test `clear_load_cell` fails | Pulse logic changed | Intentional? Update test + docs; or restore behavior |

## Do not

- Open PRs to **KalicoCrew/kalico** or **Klipper3d/klipper** with Magneto patches
- Routinely merge `magneto-x` ↔ `magneto-x-kalico` (diverged bases)
- Run `git merge -X theirs` on `homing.py` / `stepper.c` (will wipe Magneto)

## Quick check

```bash
python3 scripts/magneto_guard.py --json
```
