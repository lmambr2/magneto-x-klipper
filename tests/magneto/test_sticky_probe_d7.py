#!/usr/bin/env python3
"""Synthetic D7 sticky-probe policy tests (no full Klippy stack)."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


class TestStickyProbeD7Source(unittest.TestCase):
    def test_homing_contains_d7_contract(self):
        text = (REPO / "klippy/extras/homing.py").read_text(encoding="utf-8")
        self.assertIn("MAGNETO-X-BEGIN sticky-probe soft-fail", text)
        self.assertIn("MAGNETO-X-END sticky-probe soft-fail", text)
        self.assertIn("magneto_load_cell", text)
        self.assertIn("after load-cell clear retry", text)
        self.assertIn("cleared load cell and retried once", text)
        # Must clear then retry, not only log-and-continue
        self.assertIn("clear_load_cell", text)
        self.assertIn("HomingMove(self.printer, endstops)", text)
        # Hard fail without module (single or double quotes)
        self.assertTrue(
            "magneto_load_cell', None)" in text
            or 'magneto_load_cell", None)' in text
            or "lookup_object('magneto_load_cell'" in text
            or 'lookup_object("magneto_load_cell"' in text,
            "missing magneto_load_cell lookup",
        )

    def test_load_cell_dwells_in_clear(self):
        text = (REPO / "klippy/extras/magneto_load_cell.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("toolhead.dwell", text)
        self.assertIn("pulse_time", text)


class FakeStickyHomingLogic(unittest.TestCase):
    """Mirror D7 decision table without importing klippy."""

    def d7(self, sticky_first, sticky_second, has_module):
        """Return ('ok'|'hard'|'retry_ok', message_key)."""
        if not sticky_first:
            return "ok", None
        if not has_module:
            return "hard", "prior"
        # clear + retry
        if sticky_second:
            return "hard", "after_retry"
        return "retry_ok", "cleared"

    def test_no_sticky(self):
        self.assertEqual(self.d7(False, False, True)[0], "ok")

    def test_no_module_hard(self):
        self.assertEqual(self.d7(True, False, False), ("hard", "prior"))

    def test_sticky_clears(self):
        self.assertEqual(self.d7(True, False, True), ("retry_ok", "cleared"))

    def test_sticky_twice_hard(self):
        self.assertEqual(self.d7(True, True, True), ("hard", "after_retry"))


if __name__ == "__main__":
    unittest.main()
