# Magneto protection layer

This directory + `scripts/magneto_guard.py` lock in Magneto X behavior when
syncing with the track’s upstream (**Klipper3d** on `magneto-x`, **Kalico** on
`magneto-x-kalico`).

- **`MANIFEST.json`** — owned / base / patched files + required strings/markers  
- **Markers** in tree: `MAGNETO-X-BEGIN` … `MAGNETO-X-END`  
- **CI**: `docs/ci/magneto-ci.yml.example`  
- **Tracks**: [`docs/TRACKS.md`](../docs/TRACKS.md)  
- **Docs**: [`docs/UPSTREAM_SYNC.md`](../docs/UPSTREAM_SYNC.md)

```bash
python3 scripts/magneto_guard.py
python3 -m unittest discover -s tests/magneto -v
```
