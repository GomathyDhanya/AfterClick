import socket
import threading
import time
from contextlib import contextmanager

import uvicorn

from afterclick.api import create_app


@contextmanager
def serve(db, static_dir="apps/flowboard-web/dist"):
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    app = create_app(db, static_dir=static_dir)
    server = uvicorn.Server(uvicorn.Config(app, log_level="error", timeout_graceful_shutdown=2))
    thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()
    deadline = time.monotonic() + 15
    while not server.started:
        if not thread.is_alive() or time.monotonic() > deadline:
            raise RuntimeError("FlowBoard failed to start")
        threading.Event().wait(0.01)
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        app.state.stop_streams.set()
        server.should_exit = True
        thread.join(timeout=5)
        sock.close()
        if thread.is_alive():
            raise RuntimeError("FlowBoard did not shut down")
