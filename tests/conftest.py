"""Shared fixtures: a tiny fake OpenAI-compatible server for end-to-end page tests."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest


class FakeOpenAIServer:
    """Serves ``/v1/chat/completions`` (streaming and non-streaming) with canned replies.

    ``reply`` may be a string or a callable ``(request_json) -> str``.
    Every request body is recorded in ``requests`` for assertions.
    """

    def __init__(self) -> None:
        self.reply: str | callable = "pong"
        self.status = 200
        self.requests: list[dict] = []
        server = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):  # silence
                pass

            def do_POST(self):  # noqa: N802
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length) or b"{}")
                server.requests.append(body)
                if server.status != 200:
                    self.send_response(server.status)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": {"message": "nope"}}).encode())
                    return

                text = server.reply(body) if callable(server.reply) else server.reply
                if body.get("stream"):
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream")
                    self.end_headers()
                    for i in range(0, len(text), 7):
                        chunk = {
                            "id": "x",
                            "object": "chat.completion.chunk",
                            "created": 0,
                            "model": body.get("model", "fake"),
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {"content": text[i : i + 7]},
                                    "finish_reason": None,
                                }
                            ],
                        }
                        self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode())
                    self.wfile.write(b"data: [DONE]\n\n")
                else:
                    payload = {
                        "id": "x",
                        "object": "chat.completion",
                        "created": 0,
                        "model": body.get("model", "fake"),
                        "choices": [
                            {
                                "index": 0,
                                "message": {"role": "assistant", "content": text},
                                "finish_reason": "stop",
                            }
                        ],
                        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                    }
                    data = json.dumps(payload).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)

        self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)

    @property
    def base_url(self) -> str:
        host, port = self._httpd.server_address[:2]
        return f"http://{host}:{port}/v1"

    def start(self) -> FakeOpenAIServer:
        self._thread.start()
        return self

    def stop(self) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()


@pytest.fixture
def fake_server():
    server = FakeOpenAIServer().start()
    yield server
    server.stop()
