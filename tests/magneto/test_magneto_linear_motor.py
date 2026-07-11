#!/usr/bin/env python3
"""Unit tests for magneto_linear_motor (PR-K7)."""

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


def make_config(backend="http", url="http://127.0.0.1:8880", aliases=False,
                allow_remote=False):
    mod = load_mod()

    class Err(Exception):
        pass

    class P:
        command_error = RuntimeError

        def lookup_object(self, name):
            class G:
                def register_command(self, *a, **k):
                    pass

            return G()

        def add_object(self, name, obj):
            pass

        def config_error(self, msg):
            return Err(msg)

    class C:
        def __init__(self):
            self._p = P()

        def get_name(self):
            return "magneto_linear_motor"

        def get_printer(self):
            return self._p

        def getchoice(self, name, opts, default):
            return backend

        def getfloat(self, *a, **k):
            return 0.0  # no dwell in unit tests

        def get(self, name, default=""):
            if name == "manager_url":
                return url
            return default

        def getint(self, *a, **k):
            return 115200

        def getboolean(self, name, default=False):
            if name == "register_lm_aliases":
                return aliases
            if name == "allow_remote_manager":
                return allow_remote
            return default

        def error(self, msg):
            return Err(msg)

    return mod, C()


class TestAllowlist(unittest.TestCase):
    def test_allowed_set(self):
        mod = load_mod()
        self.assertEqual(
            mod.ALLOWED_CMDS, frozenset({"ENABLE", "DISABLE", "VERSION"})
        )

    def test_module_surface(self):
        text = MOD_PATH.read_text(encoding="utf-8")
        self.assertIn("class MagnetoLinearMotor", text)
        self.assertIn("MAGNETO_LINEAR_ENABLE", text)
        self.assertIn("allow_remote_manager", text)
        self.assertIn("def load_config", text)


class TestHttpBackend(unittest.TestCase):
    def test_send_rejects_unknown(self):
        mod, cfg = make_config()
        m = mod.MagnetoLinearMotor(cfg)
        with self.assertRaises(RuntimeError):
            m._send("RTU_MODE")

    def test_remote_manager_blocked(self):
        mod, cfg = make_config(url="http://192.168.1.5:8880")
        with self.assertRaises(Exception):
            mod.MagnetoLinearMotor(cfg)

    def test_remote_allowed_when_flag(self):
        mod, cfg = make_config(
            url="http://192.168.1.5:8880", allow_remote=True
        )
        m = mod.MagnetoLinearMotor(cfg)
        self.assertEqual(m.backend, "http")

    def test_http_enable(self):
        mod, cfg = make_config()
        m = mod.MagnetoLinearMotor(cfg)

        class G:
            def respond_info(self, msg):
                self.msg = msg

        with mock.patch.object(
            m, "_http_get", return_value=(200, '{"suc":"Send success"}')
        ) as h:
            m.cmd_ENABLE(G())
            self.assertEqual(h.call_args[0][0], "/send_command")
            self.assertEqual(h.call_args[0][1]["command"], "ENABLE")
        self.assertTrue(m._enabled)


if __name__ == "__main__":
    unittest.main()
