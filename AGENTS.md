# magneto-x-klipper — Agent Steering (fork)

This repo is the **host + MCU** half of the Magneto X modernization.

**Full project steering** (configs, MagXY manager, security, deploy, dual-repo map) lives in the umbrella:

→ **[lmambr2/magneto-x `AGENTS.md`](https://github.com/lmambr2/magneto-x/blob/master/AGENTS.md)**

If you only have this clone, still obey the rules below.

---

## Branches

| Branch | Base | Role |
|--------|------|------|
| **`magneto-x`** | Klipper3d | **Default** — use unless asked for Kalico |
| **`magneto-x-kalico`** | Kalico | Optional A/B |

Do not open PRs to **Klipper3d/klipper** or **KalicoCrew/kalico** with Magneto patches.

---

## Magneto assets

- Manifest: `magneto/MANIFEST.json`
- Guard: `python3 scripts/magneto_guard.py`
- Tests: `python3 -m unittest discover -s tests/magneto -v`
- Patched regions use `MAGNETO-X-BEGIN` / `MAGNETO-X-END`
- Docs: `docs/Magneto_X.md`, `docs/TRACKS.md`, `docs/UPSTREAM_SYNC.md`

After every upstream merge/rebase, guard **must** pass.

---

## Hard rules (fork-specific)

1. Keep Magneto delta **minimal** (`magneto_load_cell`, shell, sticky-probe, optional stepper-past).
2. **`magneto_load_cell` ≠** upstream `load_cell_probe`.
3. `MAGNETO_RELAX_STEPPER_PAST` default **n**; Octopus-only after real “too far in past” A/B.
4. Same track for host + MCU firmware when flashing.
5. No Magmotor binaries, secrets, or printer models in this tree.

---

## Before completing tasks in this repo

```bash
python3 scripts/magneto_guard.py
python3 -m unittest discover -s tests/magneto -v
```

Behavioral defaults (simplicity, surgical diffs, confirm before destructive flash) match the umbrella `AGENTS.md`.
