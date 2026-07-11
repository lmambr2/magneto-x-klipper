# Magneto X load-cell reset helper
#
# The stock Peopoly Lancer toolhead uses an STC8051 + CS1237 front-end that
# asserts a digital probe signal. After a trigger the sensor must be reset via
# a GPIO pulse before the next probe/home can succeed.
#
# This is intentionally separate from upstream Klipper's load_cell /
# load_cell_probe modules, which expect a direct ADC (HX71x / ADS1220 / etc.).
#
# Derived from Peopoly's Magneto X Klipper fork (GPL-3.0).
#
# Copyright (C) 2024  Peopoly
# Copyright (C) 2026  Magneto-X modernization
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import logging


class MagnetoLoadCell:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object('gcode')
        pins = self.printer.lookup_object('pins')
        self.reset_pin_name = config.get('pin')
        self.load_cell_reset_pin = pins.setup_pin(
            'digital_out', self.reset_pin_name)
        self.load_cell_reset_pin.setup_max_duration(0.)
        # Idle high; pulse low to clear the latch on the load-cell MCU.
        self.load_cell_reset_pin.setup_start_value(1, 1, False)
        self.pulse_time = config.getfloat(
            'pulse_time', 0.4, minval=0.05, maxval=2.0)
        self.gcode.register_command(
            'LC28', self.cmd_LC28, desc=self.cmd_LC28_help)
        self.gcode.register_command(
            'LL28', self.cmd_LL28, desc=self.cmd_LL28_help)
        self.gcode.register_command(
            'LH28', self.cmd_LH28, desc=self.cmd_LH28_help)
        self.gcode.register_command(
            'CLEAR_LOAD_CELL', self.cmd_LC28, desc=self.cmd_LC28_help)
        # Auto-clear before Z home / probe sequences when configured.
        self.auto_clear = config.getboolean('auto_clear_on_home', True)
        if self.auto_clear:
            self.printer.register_event_handler(
                "homing:home_rails_begin", self._handle_home_rails_begin)
        logging.info("magneto_load_cell: reset pin %s", self.reset_pin_name)

    def _handle_home_rails_begin(self, homing_state, rails):
        # Clear latch if any rail is homing using the probe endstop.
        for rail in rails:
            for es, name in rail.get_endstops():
                if name == 'probe':
                    self.clear_load_cell()
                    return

    def _set_pin(self, value, delay=0.1):
        reactor = self.printer.get_reactor()
        eventtime = reactor.monotonic() + delay
        print_time = self.load_cell_reset_pin.get_mcu().estimated_print_time(
            eventtime)
        self.load_cell_reset_pin.set_digital(print_time, value)
        return print_time

    def clear_load_cell(self):
        """Pulse the reset line low, then high, and dwell until complete.

        PR-K2: callers must not rely on an external G4 — the toolhead dwells
        for the full pulse window so the next probe sees a cleared latch.
        """
        self._set_pin(0, delay=0.1)
        self._set_pin(1, delay=0.1 + self.pulse_time)
        toolhead = self.printer.lookup_object('toolhead')
        # Cover schedule offset (0.1) + pulse + small settle margin
        toolhead.dwell(self.pulse_time + 0.25)

    cmd_LC28_help = "Clear / reset the Magneto X load-cell latch"
    def cmd_LC28(self, gcmd):
        self.clear_load_cell()
        gcmd.respond_info("Load cell cleared")

    cmd_LL28_help = "Force Magneto load-cell reset pin LOW"
    def cmd_LL28(self, gcmd):
        self._set_pin(0)
        gcmd.respond_info("Load cell pin LOW")

    cmd_LH28_help = "Force Magneto load-cell reset pin HIGH"
    def cmd_LH28(self, gcmd):
        self._set_pin(1)
        gcmd.respond_info("Load cell pin HIGH")


def load_config(config):
    return MagnetoLoadCell(config)
