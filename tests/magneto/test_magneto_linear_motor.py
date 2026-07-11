#!/usr/bin/env python3
"""Unit tests for magneto_linear_motor (no full Klippy)."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
MOD_PATH = REPO / "klippy/extras/magneto_linear_motor.py"


def load_mod():
    spec = importlib.util.spec_from_file_location("mlm", MOD_PATH)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class TestAllowlist(unittest.TestCase):
    def test_allowed_set(self):
        mod = load_mod()
        self.assertEqual(mod.ALLOWED_SERIAL_CMDS, frozenset({"ENABLE", "DISABLE", "VERSION"}))

    def test_module_surface(self):
        text = MOD_PATH.read_text(encoding="utf-8")
        self.assertIn("class MagnetoLinearMotor", text)
        self.assertIn("MAGNETO_LINEAR_ENABLE", text)
        self.assertIn("backend", text)
        self.assertIn("def load_config", text)
        self.assertNotIn("shell=True", text)


class TestHttpBackend(unittest.TestCase):
    def test_send_rejects_unknown(self):
        mod = load_mod()

        class P:
            def command_error(self, msg):
                return RuntimeError(msg)

            def lookup_object(self, name):
                class G:
                    def register_command(self, *a, **k):
                        pass
                return G()

        class C:
            def get_printer(self):
                return P()
            def getchoice(self, name, opts, default):
                return "http"
            def getfloat(self, *a, **k):
                return 3.0
            def get(self, name, default=""):
                return default if name != "manager_url" else "http://127.0.0.1:8880"
            def getint(self, *a, **k):
                return 115200
            def getboolean(self, name, default=False):
                return False

        m = mod.MagnetoLinearMotor(C())
        with self.assertRaises(RuntimeError):
            m._send("RTU_MODE")



if __name__ == "__main__":
    unittest.main()
