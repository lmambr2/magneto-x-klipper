# magneto-x-klipper

**Modern [Klipper](https://www.klipper3d.org/) for the Peopoly Magneto X** (MagXY + Lancer).

This is a **community / personal fork**. Magneto-specific extras live on:

| Branch | Base | Role |
|--------|------|------|
| **`magneto-x`** (default) | Klipper3d | Recommended first |
| **`magneto-x-kalico`** | [Kalico](https://github.com/KalicoCrew/kalico) | Optional A/B |

- Project umbrella: [lmambr2/magneto-x](https://github.com/lmambr2/magneto-x)
- Tracks / switching: [docs/TRACKS.md](docs/TRACKS.md)
- In-tree notes: [docs/Magneto_X.md](docs/Magneto_X.md)
- Upstream sync: [docs/UPSTREAM_SYNC.md](docs/UPSTREAM_SYNC.md) — run `python3 scripts/magneto_guard.py` after every merge
- **Do not open PRs against Klipper3d or KalicoCrew for Magneto patches.**

Not affiliated with Peopoly. Stock Peopoly Klipper is based on a 2023-05-25 (v0.11-era) tree; this fork tracks current Klipper and re-applies only the minimum Magneto hardware support.

### Protecting Magneto changes

```bash
python3 scripts/magneto_guard.py          # fails if Magneto files/markers missing
python3 -m unittest discover -s tests/magneto -v
```

CI workflow: `.github/workflows/magneto-ci.yml`.

---

Welcome to the Klipper project!

[![Klipper](docs/img/klipper-logo-small.png)](https://www.klipper3d.org/)

https://www.klipper3d.org/

The Klipper firmware controls 3d-Printers. It combines the power of a
general purpose computer with one or more micro-controllers. See the
[features document](https://www.klipper3d.org/Features.html) for more
information on why you should use the Klipper software.

Start by [installing Klipper software](https://www.klipper3d.org/Installation.html).

Klipper software is Free Software. See the [license](COPYING) or read
the [documentation](https://www.klipper3d.org/Overview.html). We
depend on the generous support from our
[sponsors](https://www.klipper3d.org/Sponsors.html).
