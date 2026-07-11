# Magneto X MagXY linear-motor enable/disable (PR-K7)
#
# Replaces gcode_shell_command + curl for MagXY arm/disarm. Only fixed
# ENABLE / DISABLE (and optional VERSION) — no arbitrary serial strings
# from gcode.
#
# Backends:
#   http   — hardened magneto-manager at 127.0.0.1:8880 (default; safe when
#            manager already owns the CH340 serial port)
#   serial — direct pyserial to ESP32 ("USB Serial" @ 115200); do not run
#            magneto-manager against the same port at the same time
#
# Copyright (C) 2026  Magneto-X modernization
# This file may be distributed under the terms of the GNU GPLv3 license.

from __future__ import annotations

import logging
import urllib.error
import urllib.parse
import urllib.request

ALLOWED_SERIAL_CMDS = frozenset({"ENABLE", "DISABLE", "VERSION"})


class MagnetoLinearMotor:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object("gcode")
        self.backend = config.getchoice(
            "backend", {"http": "http", "serial": "serial"}, "http"
        )
        self.timeout = config.getfloat("timeout", 3.0, above=0.1, maxval=30.0)
        self.manager_url = config.get(
            "manager_url", "http://127.0.0.1:8880"
        ).rstrip("/")
        self.serial_port = config.get("serial_port", "")
        self.baud = config.getint("baud", 115200, minval=9600, maxval=921600)
        self.serial_match = config.get("serial_match", "USB Serial")
        # Stock macros used G4 P500 before enable — optional dwell here
        self.enable_dwell = config.getfloat(
            "enable_dwell", 0.5, minval=0.0, maxval=5.0
        )
        self._ser = None
        self._last_error = None
        self._enabled = None  # unknown until first command

        self.gcode.register_command(
            "MAGNETO_LINEAR_ENABLE",
            self.cmd_ENABLE,
            desc=self.cmd_ENABLE_help,
        )
        self.gcode.register_command(
            "MAGNETO_LINEAR_DISABLE",
            self.cmd_DISABLE,
            desc=self.cmd_DISABLE_help,
        )
        self.gcode.register_command(
            "MAGNETO_LINEAR_STATUS",
            self.cmd_STATUS,
            desc=self.cmd_STATUS_help,
        )
        self.gcode.register_command(
            "MAGNETO_LINEAR_VERSION",
            self.cmd_VERSION,
            desc=self.cmd_VERSION_help,
        )
        # Optional short aliases used by stock macros / panels
        if config.getboolean("register_lm_aliases", True):
            self.gcode.register_command(
                "LM_ENABLE", self.cmd_ENABLE, desc=self.cmd_ENABLE_help
            )
            self.gcode.register_command(
                "LM_DISABLE", self.cmd_DISABLE, desc=self.cmd_DISABLE_help
            )

        logging.info(
            "magneto_linear_motor: backend=%s manager=%s",
            self.backend,
            self.manager_url if self.backend == "http" else self.serial_port,
        )

    def get_status(self, eventtime=None):
        return {
            "backend": self.backend,
            "enabled": self._enabled,
            "last_error": self._last_error,
        }

    def _http_get(self, path, query=None):
        q = ("?" + urllib.parse.urlencode(query)) if query else ""
        url = "%s%s%s" % (self.manager_url, path, q)
        try:
            with urllib.request.urlopen(url, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                return resp.status, body
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            return e.code, body
        except Exception as e:
            raise self.printer.command_error(
                "magneto_linear_motor HTTP failed: %s" % (e,)
            )

    def _open_serial(self):
        if self._ser is not None:
            try:
                if self._ser.is_open:
                    return self._ser
            except Exception:
                pass
            self._ser = None
        try:
            import serial
            import serial.tools.list_ports
        except ImportError:
            raise self.printer.command_error(
                "magneto_linear_motor serial backend needs pyserial"
            )
        port = self.serial_port
        if not port:
            for p in serial.tools.list_ports.comports():
                if self.serial_match in (p.description or ""):
                    port = p.device
                    break
        if not port:
            raise self.printer.command_error(
                "magneto_linear_motor: no serial port "
                "(set serial_port= or plug ESP32 CH340)"
            )
        try:
            self._ser = serial.Serial(port, self.baud, timeout=self.timeout)
        except Exception as e:
            raise self.printer.command_error(
                "magneto_linear_motor open %s failed: %s" % (port, e)
            )
        return self._ser

    def _serial_send(self, cmd):
        cmd = cmd.strip().upper()
        if cmd not in ALLOWED_SERIAL_CMDS:
            raise self.printer.command_error(
                "magneto_linear_motor: command not allowed"
            )
        ser = self._open_serial()
        try:
            ser.reset_input_buffer()
            ser.write((cmd + "\n").encode("ascii"))
            ser.flush()
            # optional short read for VERSION
            if cmd == "VERSION":
                line = ser.readline().decode("utf-8", errors="replace").strip()
                return line
        except Exception as e:
            try:
                ser.close()
            except Exception:
                pass
            self._ser = None
            raise self.printer.command_error(
                "magneto_linear_motor serial write failed: %s" % (e,)
            )
        return None

    def _send(self, cmd):
        cmd = cmd.strip().upper()
        if cmd not in ALLOWED_SERIAL_CMDS:
            raise self.printer.command_error(
                "magneto_linear_motor: command not allowed"
            )
        self._last_error = None
        if self.backend == "http":
            if cmd == "VERSION":
                status, body = self._http_get("/get_os_version")
                if status != 200:
                    self._last_error = body
                    raise self.printer.command_error(
                        "manager version HTTP %s: %s" % (status, body)
                    )
                return body
            status, body = self._http_get(
                "/send_command", {"command": cmd}
            )
            if status != 200:
                self._last_error = body
                raise self.printer.command_error(
                    "manager HTTP %s: %s" % (status, body)
                )
            return body
        # serial
        return self._serial_send(cmd)

    cmd_ENABLE_help = "Enable MagXY linear motors (ENABLE to ESP32)"

    def cmd_ENABLE(self, gcmd):
        if self.enable_dwell > 0.0:
            self.printer.lookup_object("toolhead").dwell(self.enable_dwell)
        self._send("ENABLE")
        self._enabled = True
        gcmd.respond_info("MagXY ENABLE sent (%s)" % (self.backend,))

    cmd_DISABLE_help = "Disable MagXY linear motors (DISABLE to ESP32)"

    def cmd_DISABLE(self, gcmd):
        self._send("DISABLE")
        self._enabled = False
        gcmd.respond_info("MagXY DISABLE sent (%s)" % (self.backend,))

    cmd_STATUS_help = "Report MagXY module backend and last known enable state"

    def cmd_STATUS(self, gcmd):
        gcmd.respond_info(
            "magneto_linear_motor backend=%s enabled=%s last_error=%s"
            % (self.backend, self._enabled, self._last_error)
        )
        if self.backend == "http":
            try:
                status, body = self._http_get("/health")
                gcmd.respond_info("manager health HTTP %s: %s" % (status, body))
            except Exception as e:
                gcmd.respond_info("manager health failed: %s" % (e,))

    cmd_VERSION_help = "Query manager or ESP32 version string"

    def cmd_VERSION(self, gcmd):
        body = self._send("VERSION")
        gcmd.respond_info("version: %s" % (body,))


def load_config(config):
    return MagnetoLinearMotor(config)
