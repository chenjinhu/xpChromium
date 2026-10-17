#!/usr/bin/env python3
"""Serve the device smoke page and selected wire headers over adb reverse."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import urlsplit


PAGE = Path(__file__).resolve().parents[1] / "tests/identity-smoke.html"
HEADER_NAMES = (
    "User-Agent", "Accept-Language", "DNT", "X-Requested-With",
    "Sec-CH-UA", "Sec-CH-UA-Mobile", "Sec-CH-UA-Platform",
    "Sec-CH-UA-Full-Version-List", "Sec-CH-UA-Arch", "Sec-CH-UA-Bitness",
    "Sec-CH-UA-Model", "Sec-CH-UA-Platform-Version",
)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlsplit(self.path).path
        if path in ("/", "/identity-smoke.html"):
            body, kind = PAGE.read_bytes(), "text/html; charset=utf-8"
        elif path == "/headers":
            body = json.dumps({k: self.headers.get(k) for k in HEADER_NAMES},
                              ensure_ascii=False, indent=2).encode()
            kind = "application/json; charset=utf-8"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Accept-CH", ", ".join(HEADER_NAMES[7:]))
        self.end_headers()
        self.wfile.write(body)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be in 1..65535")
    with ThreadingHTTPServer(("127.0.0.1", args.port), Handler) as server:
        print(f"Use adb reverse tcp:{args.port} tcp:{args.port}", flush=True)
        print(f"Open http://127.0.0.1:{args.port}/?headers=1&language=zh-CN&timezone=Asia%2FShanghai&noise=1", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
