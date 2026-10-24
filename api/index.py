"""Vercel Python function; also reused by the local preview server."""
from http.server import BaseHTTPRequestHandler
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from model_mountain.control_api import APIError, ControlAPI, MAX_BODY, PROJECT_NAME, PROJECT_ID

# Vercel reserves `app` / `application` for ASGI/WSGI entry points. Keep the
# service under a private name so its BaseHTTPRequestHandler entry is selected.
_control = ControlAPI()


class handler(BaseHTTPRequestHandler):
    def send_json(self, code, payload):
        payload = {**payload, "project_name": PROJECT_NAME, "project_id": PROJECT_ID}
        content = json.dumps(payload, allow_nan=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(content)

    def dispatch(self):
        try:
            body = None
            if self.command == "POST":
                if self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
                    raise APIError(415, "json_required", "Use application/json.")
                try:
                    size = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    raise APIError(400, "invalid_length", "Invalid request length.") from None
                if not 0 < size <= MAX_BODY:
                    raise APIError(413, "body_too_large", "Request exceeds the 32 KiB limit.")
                try:
                    body = json.loads(self.rfile.read(size))
                except (ValueError, UnicodeError):
                    raise APIError(400, "invalid_json", "Invalid JSON request.") from None
            self.send_json(200, _control.handle(self.command, self.path, body, dict(self.headers)))
        except APIError as exc:
            self.send_json(exc.status, {"error": {"code": exc.code, "message": exc.message}})
        except Exception:
            self.send_json(500, {"error": {"code": "internal_error", "message": "The operation could not be completed."}})

    do_GET = dispatch
    do_POST = dispatch

    def log_message(self, format, *args):
        # Do not log URL query strings, credentials, question text or model output.
        pass
