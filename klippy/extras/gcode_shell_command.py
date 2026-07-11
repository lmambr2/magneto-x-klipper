# Run a shell command via gcode
#
# Copyright (C) 2019  Eric Callahan <arksine.code@gmail.com>
# Copyright (C) 2026  Magneto-X modernization (GCodeCommand API update)
#
# This file may be distributed under the terms of the GNU GPLv3 license.
#
# NOTE: Intentionally not in upstream Klipper (security). Required on Magneto X
# for LM_ENABLE / LM_DISABLE which call the magneto-manager HTTP API.
#
# PR-K5: PARAMS are rejected by default (allow_params: False) so malicious
# gcode cannot append argv to curl/shell. Deploy only fixed allowlisted cmds.
import logging
import os
import shlex
import subprocess


class ShellCommand:
    def __init__(self, config):
        self.name = config.get_name().split()[-1]
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object('gcode')
        cmd = os.path.expanduser(config.get('command'))
        self.command = shlex.split(cmd)
        self.timeout = config.getfloat('timeout', 2., above=0.)
        self.verbose = config.getboolean('verbose', True)
        # Magneto default: no PARAMS (security). Set allow_params: True only
        # for trusted, non-production experiments.
        self.allow_params = config.getboolean('allow_params', False)
        self.proc_fd = None
        self.partial_output = ""
        self.gcode.register_mux_command(
            "RUN_SHELL_COMMAND", "CMD", self.name,
            self.cmd_RUN_SHELL_COMMAND,
            desc=self.cmd_RUN_SHELL_COMMAND_help)

    def _process_output(self, eventime):
        if self.proc_fd is None:
            return
        try:
            data = os.read(self.proc_fd, 4096)
        except Exception:
            return
        data = self.partial_output + data.decode(errors='replace')
        if '\n' not in data:
            self.partial_output = data
            return
        if data[-1] != '\n':
            split = data.rfind('\n') + 1
            self.partial_output = data[split:]
            data = data[:split]
        else:
            self.partial_output = ""
        self.gcode.respond_info(data)

    cmd_RUN_SHELL_COMMAND_help = "Run a linux shell command"
    def cmd_RUN_SHELL_COMMAND(self, gcmd):
        raw_params = gcmd.get('PARAMS', None)
        if raw_params not in (None, ''):
            if not self.allow_params:
                raise gcmd.error(
                    "PARAMS not allowed for shell command {%s} "
                    "(set allow_params: True only if you trust all gcode)"
                    % (self.name,))
            gcode_params = shlex.split(raw_params)
        else:
            gcode_params = []
        reactor = self.printer.get_reactor()
        hdl = None
        try:
            proc = subprocess.Popen(
                self.command + gcode_params,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        except Exception:
            logging.exception(
                "shell_command: Command {%s} failed" % (self.name,))
            raise gcmd.error("Error running command {%s}" % (self.name,))
        try:
            if self.verbose:
                self.proc_fd = proc.stdout.fileno()
                self.gcode.respond_info(
                    "Running Command {%s}...:" % (self.name,))
                hdl = reactor.register_fd(self.proc_fd, self._process_output)
            eventtime = reactor.monotonic()
            endtime = eventtime + self.timeout
            complete = False
            while eventtime < endtime:
                eventtime = reactor.pause(eventtime + .05)
                if proc.poll() is not None:
                    complete = True
                    break
            if not complete:
                proc.terminate()
            if self.verbose:
                if self.partial_output:
                    self.gcode.respond_info(self.partial_output)
                    self.partial_output = ""
                if complete:
                    msg = "Command {%s} finished" % (self.name,)
                else:
                    msg = "Command {%s} timed out" % (self.name,)
                self.gcode.respond_info(msg)
        finally:
            if hdl is not None:
                reactor.unregister_fd(hdl)
            self.proc_fd = None


def load_config_prefix(config):
    return ShellCommand(config)
