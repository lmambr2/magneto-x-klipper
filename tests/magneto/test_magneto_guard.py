#!/usr/bin/env python3
"""Tests for Magneto asset guard — real checker on this repo + synthetic breaks."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "magneto_guard.py"


def load_guard():
    spec = importlib.util.spec_from_file_location("magneto_guard", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class TestMagnetoGuardRealRepo(unittest.TestCase):
    def test_guard_script_passes_on_this_tree(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(REPO)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            proc.returncode,
            0,
            f"guard failed:\n{proc.stdout}\n{proc.stderr}",
        )
        self.assertIn("OK:", proc.stdout)

    def test_check_manifest_api(self):
        guard = load_guard()
        errors = guard.check_manifest(REPO)
        self.assertEqual(errors, [], errors)

    def test_missing_owned_file_detected(self):
        guard = load_guard()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # Minimal fake tree missing magneto_load_cell
            (root / "magneto").mkdir()
            manifest = json.loads(
                (REPO / "magneto" / "MANIFEST.json").read_text(encoding="utf-8")
            )
            (root / "magneto" / "MANIFEST.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            errors = guard.check_manifest(root, manifest)
            self.assertTrue(any("magneto_load_cell" in e for e in errors), errors)

    def test_dropped_marker_detected(self):
        guard = load_guard()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # Copy real files then strip markers from homing.py
            import shutil

            for rel in (
                "klippy/extras/magneto_load_cell.py",
                "klippy/extras/gcode_shell_command.py",
                "docs/Magneto_X.md",
                "scripts/magneto_guard.py",
                "src/stepper.c",
                "src/Kconfig",
            ):
                src = REPO / rel
                dst = root / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
            (root / "magneto").mkdir()
            shutil.copy2(REPO / "magneto" / "MANIFEST.json", root / "magneto" / "MANIFEST.json")
            # homing without markers
            homing_src = (REPO / "klippy/extras/homing.py").read_text(encoding="utf-8")
            broken = homing_src.replace("MAGNETO-X-BEGIN sticky-probe soft-fail", "REMOVED")
            broken = broken.replace("MAGNETO-X-END sticky-probe soft-fail", "REMOVED")
            dst_h = root / "klippy/extras/homing.py"
            dst_h.parent.mkdir(parents=True, exist_ok=True)
            dst_h.write_text(broken, encoding="utf-8")
            errors = guard.check_manifest(root)
            self.assertTrue(
                any("sticky-probe" in e or "marker" in e for e in errors),
                errors,
            )


class TestMagnetoLoadCellLogic(unittest.TestCase):
    """Unit-test pulse schedule without full Klippy stack."""

    def test_clear_load_cell_pulses_low_then_high(self):
        # Import module by path so we don't need klippy package install
        path = REPO / "klippy/extras/magneto_load_cell.py"
        spec = importlib.util.spec_from_file_location("magneto_load_cell", path)
        mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(mod)

        calls = []

        class Fake:
            pulse_time = 0.4

            def _set_pin(self, value, delay=0.1):
                calls.append((value, delay))

        # Bind real clear_load_cell to fake instance
        mod.MagnetoLoadCell.clear_load_cell(Fake())
        self.assertEqual(calls[0][0], 0)
        self.assertEqual(calls[1][0], 1)
        self.assertGreater(calls[1][1], calls[0][1])
        self.assertAlmostEqual(calls[1][1], 0.1 + 0.4)

    def test_module_exports_load_config(self):
        path = REPO / "klippy/extras/magneto_load_cell.py"
        text = path.read_text(encoding="utf-8")
        self.assertIn("def load_config", text)
        self.assertIn("CLEAR_LOAD_CELL", text)
        self.assertIn("homing:home_rails_begin", text)


class TestGcodeShellCommandSurface(unittest.TestCase):
    def test_shell_module_registers_run_shell_command(self):
        path = REPO / "klippy/extras/gcode_shell_command.py"
        text = path.read_text(encoding="utf-8")
        self.assertIn("RUN_SHELL_COMMAND", text)
        self.assertIn("def load_config_prefix", text)
        self.assertIn("class ShellCommand", text)


if __name__ == "__main__":
    unittest.main()
