#!/usr/bin/env python3
"""Entry point for the packaged server.

The desktop shell starts this with a free port and a random token, waits for
the ready line, and kills it on quit. It also runs on its own for development.

The ``TIMBRE_READY <url>`` line is a contract rather than a log message: the
shell parses it to learn where to point the webview.
"""
from __future__ import annotations

import argparse
import os
import socket
import sys
import threading
import time


def free_port() -> int:
    """Ask the OS for a port nobody is using."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def main() -> int:
    parser = argparse.ArgumentParser(description="Timbre server")
    parser.add_argument("--port", type=int, default=0, help="0 picks a free port")
    parser.add_argument("--token", default="", help="require this bearer token on /api")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument(
        "--exit-with-parent",
        action="store_true",
        help="shut down when stdin closes, which happens when the parent dies",
    )
    args = parser.parse_args()

    if args.token:
        os.environ["TIMBRE_TOKEN"] = args.token

    port = args.port or free_port()

    import uvicorn

    config = uvicorn.Config("app.main:app", host=args.host, port=port, log_level="warning")
    server = uvicorn.Server(config)

    def announce_when_listening() -> None:
        """Print the ready line once the socket is accepting connections.

        Printing it before uvicorn starts listening produces a connection
        refused on the shell's first request.
        """
        while not server.started:
            time.sleep(0.02)
        print(f"TIMBRE_READY http://{args.host}:{port}", flush=True)

    threading.Thread(target=announce_when_listening, daemon=True).start()

    if args.exit_with_parent:

        def exit_when_orphaned() -> None:
            """Exit when stdin closes, which happens when the parent dies.

            The desktop shell holds the write end of that pipe. If the shell is
            killed outright no cleanup code of its own can run, so the pipe
            closing is the only reliable signal. Without this the server
            survives as an orphan holding a port and a loaded model.
            """
            try:
                while sys.stdin.readline():
                    pass
            except (ValueError, OSError):
                pass
            os._exit(0)

        threading.Thread(target=exit_when_orphaned, daemon=True).start()

    server.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
