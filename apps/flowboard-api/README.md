# FlowBoard API

The runnable backend lives in the installable `afterclick` package:

```sh
uv run uvicorn afterclick.api:app --host 127.0.0.1 --port 8000
```

This directory documents the app boundary; it contains no duplicate backend implementation.
See the root README and `docs/ARCHITECTURE.md` for domain and research-control modules.
