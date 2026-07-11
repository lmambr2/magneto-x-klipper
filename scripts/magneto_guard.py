#!/usr/bin/env python3
"""Guard Magneto X assets against silent loss during upstream Klipper syncs.

Checks magneto/MANIFEST.json:
  - owned files exist and contain required symbols
  - patched files retain MAGNETO-X-BEGIN/END markers and required strings
  - Magneto Python modules py_compile cleanly

Usage (from magneto-x-klipper repo root):
  python3 scripts/magneto_guard.py
  python3 scripts/magneto_guard.py --json
  python3 scripts/magneto_guard.py --root /path/to/repo
"""

from __future__ import annotations

import argparse
import json
import py_compile
import sys
from pathlib import Path


def default_repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_manifest(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def check_manifest(repo_root: Path, manifest: dict | None = None) -> list[str]:
    """Return a list of error strings (empty if OK)."""
    repo_root = repo_root.resolve()
    manifest_path = repo_root / "magneto" / "MANIFEST.json"
    if manifest is None:
        if not manifest_path.is_file():
            return [f"manifest missing: {manifest_path}"]
        manifest = load_manifest(manifest_path)

    errors: list[str] = []

    def exists(rel: str) -> bool:
        return (repo_root / rel).is_file()

    def text_of(rel: str) -> str:
        return (repo_root / rel).read_text(encoding="utf-8", errors="replace")

    for entry in manifest.get("owned_files", []):
        rel = entry["path"]
        if not exists(rel):
            errors.append(f"missing owned file: {rel}")
            continue
        body = text_of(rel)
        for needle in entry.get("must_contain", []):
            if needle not in body:
                errors.append(f"{rel}: missing required string {needle!r}")

    for entry in manifest.get("patched_files", []):
        rel = entry["path"]
        if not exists(rel):
            errors.append(f"missing patched file: {rel}")
            continue
        body = text_of(rel)
        markers = entry.get("markers", [])
        for m in markers:
            if m not in body:
                errors.append(
                    f"{rel}: missing marker {m!r} "
                    f"(upstream merge may have dropped the Magneto patch)"
                )
        begins = [m for m in markers if "BEGIN" in m]
        ends = [m for m in markers if "END" in m]
        for b, e in zip(begins, ends):
            if b in body and e in body and body.find(b) > body.find(e):
                errors.append(f"{rel}: marker order wrong ({b!r} after {e!r})")
        for needle in entry.get("must_contain", []):
            if needle not in body:
                errors.append(f"{rel}: missing required string {needle!r}")

    for rel in (
        "klippy/extras/magneto_load_cell.py",
        "klippy/extras/gcode_shell_command.py",
        "scripts/magneto_guard.py",
    ):
        p = repo_root / rel
        if not p.is_file():
            continue
        try:
            py_compile.compile(str(p), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(f"py_compile failed for {rel}: {exc}")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Repo root (default: parent of scripts/)",
    )
    parser.add_argument(
        "--json", action="store_true", help="Print machine-readable result"
    )
    args = parser.parse_args(argv)
    root = (args.root or default_repo_root()).resolve()
    errors = check_manifest(root)
    ok = not errors
    if args.json:
        print(json.dumps({"ok": ok, "errors": errors, "root": str(root)}))
    else:
        print(f"Magneto guard — root={root}")
        if ok:
            print("OK: all owned files, markers, and py_compile checks passed.")
        else:
            print("FAILED:")
            for e in errors:
                print(f"  - {e}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
