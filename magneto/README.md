# Magneto protection layer

This directory + `scripts/magneto_guard.py` lock in Magneto X behavior when
syncing with upstream Klipper.

- **`MANIFEST.json`** — owned files vs patched files + required strings/markers  
- **Markers** in tree: `MAGNETO-X-BEGIN` … `MAGNETO-X-END`  
- **CI**: `.github/workflows/magneto-ci.yml`  
- **Docs**: [`docs/UPSTREAM_SYNC.md`](../docs/UPSTREAM_SYNC.md)

```bash
python3 scripts/magneto_guard.py
python3 -m unittest discover -s tests/magneto -v
```
