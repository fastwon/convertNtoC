"""Desktop entry point.

Starts the FastAPI server in a background thread bound to 127.0.0.1 (ephemeral
port by default; override with CONVERTN2C_PORT for dev with the Vite proxy),
waits for it to come up, then opens the PyWebView window pointing at it.
"""
from __future__ import annotations

import os
import socket
import threading
import time
import urllib.request

import uvicorn
import webview

from .server import app


def _resolve_port() -> int:
    env = os.environ.get("CONVERTN2C_PORT")
    if env:
        return int(env)
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = int(s.getsockname()[1])
    s.close()
    return port


def _serve(port: int) -> None:
    # uvicorn skips signal-handler install when not on the main thread.
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


def _wait_until_ready(url: str, timeout: float = 15.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(0.15)
    return False


def main() -> None:
    port = _resolve_port()
    threading.Thread(target=_serve, args=(port,), daemon=True).start()

    base = f"http://127.0.0.1:{port}"
    if not _wait_until_ready(f"{base}/api/health"):
        raise RuntimeError("백엔드 서버 기동 실패")

    webview.create_window("convertN2C", base, width=1200, height=800)
    webview.start()


if __name__ == "__main__":
    main()
