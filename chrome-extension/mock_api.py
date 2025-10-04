#!/usr/bin/env python3
"""Minimal mock API server returning static analysis data."""

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from urllib.parse import urlparse

MOCK_RESPONSE = [
    {
        "id": 0,
        "criteria_name": "Pyramid",
        "explanation": "The inverted piramid criteria for goo journalism is not respected.",
        "flag": -1,
        "score": 0.2,
    },
    {
        "id": 1,
        "criteria_name": "Adjectives",
        "explanation": "The adjective ratio is good and healthy ",
        "flag": 1,
        "score": 0.9,
    },
]


class MockHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status_code: int) -> None:
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def do_OPTIONS(self):  # noqa: N802 - required method name
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):  # noqa: N802 - required method name
        parsed_path = urlparse(self.path)
        if parsed_path.path != "/analyze":
            self.send_error(404, "Not Found")
            return

        # Consume request body even if we ignore it; silence logging.
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length:
            _ = self.rfile.read(content_length)

        self._set_headers(200)
        self.wfile.write(json.dumps(MOCK_RESPONSE).encode("utf-8"))

    def log_message(self, format, *args):  # noqa: A003
        # Quiet default logging to keep console clean.
        return


def run(server_class=HTTPServer, handler_class=MockHandler, port: int = 5000) -> None:
    server_address = ("", port)
    httpd = server_class(server_address, handler_class)
    print(f"Mock API server listening on http://localhost:{port}/analyze")
    httpd.serve_forever()


if __name__ == "__main__":
    run()
