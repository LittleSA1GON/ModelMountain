"""Serve the built web app and its real API on loopback for review."""
import argparse
from http.server import ThreadingHTTPServer
import mimetypes
from pathlib import Path
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from api.index import handler


class PreviewHandler(handler):
    def do_GET(self):
        if self.path.startswith("/api/"):
            return self.dispatch()
        folder = ROOT / "web/dist"
        requested = (folder / unquote(urlsplit(self.path).path).lstrip("/")).resolve()
        if not requested.is_relative_to(folder.resolve()):
            return self.send_json(403, {"error": {"code": "forbidden", "message": "Invalid path."}})
        if not requested.is_file():
            requested = folder / "index.html"
        if not requested.exists():
            return self.send_json(503, {"error": {"code": "build_required", "message": "Build web/ before starting preview."}})
        data = requested.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(requested.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8502)
    args = parser.parse_args()
    print(f"Model Mountain web/API: http://127.0.0.1:{args.port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", args.port), PreviewHandler).serve_forever()
