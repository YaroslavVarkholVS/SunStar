#!/usr/bin/env python3
"""Run a command in its own session, detached from the controlling terminal.

fastapi-cli's rich banner queries /dev/tty for the terminal's colors on
startup. When run as a background job from a non-interactive shell (like a
Makefile recipe backgrounding two dev servers together), that query can hang
forever instead of failing fast, because the process still shares the
terminal's session/process group. Detaching into a new session makes
/dev/tty unavailable, so the query fails immediately and startup proceeds.
"""
import os
import signal
import sys


def main() -> None:
    command = sys.argv[1:]
    if not command:
        sys.exit("usage: run_detached.py <command> [args...]")

    pid = os.fork()
    if pid == 0:
        os.setsid()
        os.execvp(command[0], command)

    def forward(signum: int, _frame: object) -> None:
        os.killpg(pid, signum)

    signal.signal(signal.SIGTERM, forward)
    signal.signal(signal.SIGINT, forward)

    _, status = os.waitpid(pid, 0)
    sys.exit(os.waitstatus_to_exitcode(status))


if __name__ == "__main__":
    main()
