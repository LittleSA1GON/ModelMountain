"""Serve one reviewed ZIP to the authorized Devpost upload flow over loopback only."""
from __future__ import annotations

import argparse
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import time


def serve(archive: Path, port: int, seconds: int) -> None:
    data = archive.read_bytes()
    if archive.suffix.lower() != ".zip" or not 0 < len(data) <= 35 * 1024 * 1024:
        raise ValueError("Use a reviewed ZIP no larger than Devpost's 35 MiB attachment limit")
    digest = hashlib.sha256(data).hexdigest()

    class Handler(BaseHTTPRequestHandler):
        def permitted(self):
            return (self.path == "/source.zip" and self.headers.get("Host") == f"127.0.0.1:{port}"
                    and self.headers.get("Origin") == "https://devpost.com")

        def cors(self):
            self.send_header("Access-Control-Allow-Origin", "https://devpost.com")
            self.send_header("Access-Control-Allow-Private-Network", "true")
            self.send_header("Access-Control-Allow-Methods", "GET")
            self.send_header("Access-Control-Allow-Headers", "*")
            self.send_header("Vary", "Origin")
            self.send_header("Cache-Control", "no-store")

        def do_OPTIONS(self):
            if not self.permitted() or self.headers.get("Access-Control-Request-Method") != "GET":
                self.send_error(403)
                return
            self.send_response(204)
            self.cors()
            self.end_headers()

        def do_GET(self):
            if not self.permitted():
                self.send_error(403)
                return
            self.send_response(200)
            self.cors()
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Content-Disposition", f'attachment; filename="{archive.name}"')
            self.send_header("X-Artifact-SHA256", digest)
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, fmt, *args):
            print(fmt % args, flush=True)

    server = HTTPServer(("127.0.0.1", port), Handler)
    server.timeout = 1
    deadline = time.monotonic() + seconds
    print(f"Serving {archive.name}; sha256={digest}; bytes={len(data)}; expires_in={seconds}s", flush=True)
    try:
        while time.monotonic() < deadline:
            server.handle_request()
    finally:
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--port", type=int, default=8799)
    parser.add_argument("--seconds", type=int, default=7200)
    args = parser.parse_args()
    if not 1 <= args.seconds <= 7200 or not 1024 <= args.port <= 65535:
        parser.error("Use an unprivileged port and a lifetime from 1 to 7200 seconds")
    serve(args.archive.resolve(strict=True), args.port, args.seconds)
