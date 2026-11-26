"""Owned larger-model server: bounded startup without prefill graph compilation.

Exact target image/weights/cache are retained. The original user endpoint is
never addressed. This replaces only the new study-owned serving application.
"""

import modal

app = modal.App("ep-afterclick-v12-qwen36-35b")
image = modal.Image.from_id("im-uOEP9csO45VqZPqJyN8PRd")
weights = modal.Volume.from_id("vo-NVlTzVZuRGrSXPyGJGG6n0")


@app.server(
    image=image,
    gpu="H200",
    cpu=4,
    memory=32768,
    min_containers=0,
    max_containers=1,
    buffer_containers=0,
    target_concurrency=32,
    max_concurrency=64,
    scaledown_window=60,
    startup_timeout=300,
    exit_grace_period=25,
    unauthenticated=True,
    port=8000,
    routing_region="us-east",
    volumes={"/flash-endpoint-model": weights},
)
class Server:
    @modal.enter()
    def startup(self):
        import subprocess

        subprocess.Popen(
            [
                "python",
                "-m",
                "sglang.launch_server",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
                "--model-path",
                "/flash-endpoint-model/huggingface/hub/models--Qwen--Qwen3.6-35B-A3B-FP8/snapshots/c653bba46dfa06e9658dcc0b0dc87fe4685f14a2",
                "--served-model-name",
                "afterclick-v12-qwen36-35b",
                "--tp",
                "1",
                "--context-length",
                "65536",
                "--mem-fraction-static",
                "0.75",
                "--max-running-requests",
                "32",
                "--chunked-prefill-size",
                "8192",
                "--disable-prefill-cuda-graph",
                "--disable-decode-cuda-graph",
                "--reasoning-parser",
                "qwen3",
                "--tool-call-parser",
                "qwen3_coder",
                "--model-loader-extra-config",
                '{"enable_multithread_load":true,"num_threads":8}',
                "--trust-remote-code",
                "--enable-metrics",
                "--log-requests",
            ]
        )
