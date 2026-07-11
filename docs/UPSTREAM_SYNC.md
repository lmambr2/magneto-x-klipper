# Syncing magneto-x-klipper with upstream Klipper

Magneto-specific work lives on branch **`magneto-x`**. Upstream Klipper is
tracked as `master` (or remote `upstream/master`).

## What survives a merge automatically?

| Kind | Paths | Risk |
|------|--------|------|
| **Owned files** (Magneto-only) | `klippy/extras/magneto_load_cell.py`, `gcode_shell_command.py`, `magneto/*`, `scripts/magneto_guard.py`, `docs/Magneto_X.md` | Low — git will not delete them unless you resolve a conflict by deleting |
| **Patched upstream files** | `homing.py`, `src/stepper.c`, `src/Kconfig` | **High** — conflicts; easy to drop Magneto hunks by mistake |

There is **no** way to make `git merge` refuse to overwrite a patched line forever.
Protection is:

1. **Isolated owned modules** (extras load by filename — safe)
2. **`MAGNETO-X-BEGIN` / `MAGNETO-X-END` markers** in every patched region
3. **`scripts/magneto_guard.py` + CI** that fails if markers/files vanish
4. **Unit tests** for load-cell pulse logic + guard itself

## Recommended sync procedure

```bash
cd ~/klipper   # or this clone

# 1) Fetch upstream (Klipper3d)
git remote add upstream https://github.com/Klipper3d/klipper.git 2>/dev/null || true
git fetch upstream

# 2) Update tracking branch (optional clean master)
git checkout master
git merge --ff-only upstream/master   # or reset --hard if you keep master pure

# 3) Bring master into magneto-x
git checkout magneto-x
python3 scripts/magneto_guard.py      # baseline: must pass BEFORE merge
git merge master                      # or: git rebase master

# 4) Resolve conflicts carefully:
#    - Keep MAGNETO-X-BEGIN ... MAGNETO-X-END blocks in homing.py / stepper.c / Kconfig
#    - Never delete klippy/extras/magneto_*.py or gcode_shell_command.py

# 5) Re-verify
python3 scripts/magneto_guard.py
python3 -m unittest discover -s tests/magneto -v

# 6) Only then push
git push origin magneto-x
```

## If a test / guard fails after merge

| Symptom | Meaning | Fix |
|---------|---------|-----|
| `missing owned file: klippy/extras/magneto_load_cell.py` | File deleted in conflict resolution | Restore from pre-merge commit |
| `missing marker MAGNETO-X-BEGIN …` | Upstream rewrite of `probing_move` / stepper scheduling dropped our hunk | Re-apply patch by hand; update markers if API moved |
| `missing required string magneto_load_cell` in homing.py | Soft-fail branch gone | Re-insert sticky-probe block |
| Unit test `clear_load_cell` fails | Pulse logic changed | Intentional? Update test + docs; or restore behavior |

## When upstream *should* force a Magneto change

Guard/tests cannot invent new features. Re-read and adapt when:

- `PrinterHoming.probing_move` signature or homing events change
- Step generation no longer uses the “too far in past” path
- Klipper adds a first-class digital-probe reset (maybe replace `magneto_load_cell`)
- Shell/gcode APIs break `gcode_shell_command`

After adapting, update `magneto/MANIFEST.json` `must_contain` / markers so CI encodes the new contract.

## Do not

- Open PRs to **Klipper3d/klipper** with Magneto patches
- Squash Magneto + upstream into one unreadable commit without markers
- Run `git merge -X theirs` on `homing.py` / `stepper.c` (will wipe Magneto)

## Quick check

```bash
python3 scripts/magneto_guard.py --json
```
