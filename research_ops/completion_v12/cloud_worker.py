"""Finite CPU-only research batches with real PostgreSQL, Chromium and HTTP receivers.

Build/qualification does not call any model. LLM batches require an explicit
registration and finite request/time envelope supplied by the paid lifecycle.
"""

import io
import json
import os
import pathlib
import pwd
import shutil
import subprocess
import tarfile
import tempfile
import time

import modal

app = modal.App("afterclick-v12-cpu-batches")
evidence = modal.Volume.from_name(
    "afterclick-v12-research-evidence", create_if_missing=True, version=2
)
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("postgresql", "postgresql-contrib")
    .pip_install(
        "fastapi==0.163.2",
        "uvicorn==0.54.0",
        "sqlalchemy==2.0.58",
        "psycopg[binary]==3.3.9",
        "alembic==1.20.1",
        "httpx==0.28.1",
        "playwright==1.65.2",
        "pydantic==2.14.3",
    )
    .run_commands("python -m playwright install --with-deps chromium")
    .add_local_dir(
        "afterclick", "/workspace/afterclick", copy=True, ignore=["**/__pycache__/**", "**/*.pyc"]
    )
    .add_local_dir("migrations", "/workspace/migrations", copy=True, ignore=["**/__pycache__/**"])
    .add_local_file("alembic.ini", "/workspace/alembic.ini", copy=True)
    .add_local_dir("apps/flowboard-web/dist", "/workspace/apps/flowboard-web/dist", copy=True)
    .env({"PYTHONPATH": "/workspace"})
)


@app.function(
    image=image,
    cpu=(8, 8),
    memory=(16384, 16384),
    min_containers=0,
    max_containers=2,
    buffer_containers=0,
    scaledown_window=2,
    retries=0,
    timeout=600,
    startup_timeout=240,
    volumes={"/evidence": evidence},
)
def batch(payload):
    import importlib.metadata
    import sys
    import traceback

    os.chdir("/workspace")
    sys.path.insert(0, "/workspace")
    from afterclick.completion_v12.benchmark.qualification import qualify_one
    from afterclick.completion_v12.benchmark.qualify_transport import qualify as qualify_native
    from afterclick.completion_v12.benchmark.runner import execute
    from afterclick.completion_v12.benchmark.transport import Transport, save
    from afterclick.completion_v12.evidence import digest

    identifier = payload["batch_id"]
    if not identifier or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in identifier):
        raise ValueError("Unsafe batch identifier")
    root = pathlib.Path("/evidence") / identifier
    root.mkdir(exist_ok=False)
    save(root / "payload.json", payload)
    account = pwd.getpwnam("postgres")
    data = pathlib.Path(tempfile.mkdtemp(prefix="afterclick-pg-"))
    os.chown(data, account.pw_uid, account.pw_gid)
    binary = sorted(
        pathlib.Path("/usr/lib/postgresql").glob("*/bin"), key=lambda p: int(p.parent.name)
    )[-1]

    def pg(program, *args):
        return subprocess.run(
            ["runuser", "-u", "postgres", "--", str(binary / program), *args],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )

    transport = None
    started = time.monotonic()
    error = None
    try:
        pg(
            "initdb",
            "-D",
            str(data),
            "-U",
            "afterclick",
            "-A",
            "trust",
            "--no-locale",
            "-E",
            "UTF8",
        )
        pg(
            "pg_ctl",
            "-D",
            str(data),
            "-l",
            str(data / "server.log"),
            "-o",
            "-h 127.0.0.1 -p 55432 -c max_connections=200 -c shared_buffers=256MB",
            "-w",
            "start",
        )
        pg("createdb", "-h", "127.0.0.1", "-p", "55432", "-U", "afterclick", "afterclick")
        os.environ["DATABASE_URL"] = (
            "postgresql+psycopg://afterclick:afterclick_local@127.0.0.1:55432/afterclick"
        )
        save(
            root / "environment.json",
            dict(
                python=sys.version,
                platform=sys.platform,
                postgres=pg("postgres", "--version").stdout,
                packages={
                    p: importlib.metadata.version(p)
                    for p in [
                        "fastapi",
                        "uvicorn",
                        "sqlalchemy",
                        "psycopg",
                        "alembic",
                        "httpx",
                        "playwright",
                        "pydantic",
                    ]
                },
                cpu_request=8,
                cpu_limit=8,
                memory_mib=16384,
                gpu=None,
                zero_model_calls=payload["mode"] == "REFERENCE_QUALIFICATION",
            ),
        )
        contracts = root / "contracts"
        contracts.mkdir()
        for task_id, contract in payload["contracts"].items():
            save(contracts / (task_id + ".json"), contract)
        if payload["mode"] == "REFERENCE_QUALIFICATION":
            output = root / "qualification"
            output.mkdir()
            archive = output / "source-archive"
            archive.mkdir()
            for path in pathlib.Path("afterclick/completion_v12/benchmark").iterdir():
                if path.suffix in {".py", ".html"}:
                    shutil.copyfile(path, archive / path.name)
            rows = []
            for path in sorted(contracts.glob("*.json")):
                rows.append(qualify_one((str(path), str(output))))
            if payload.get("native", False):
                qualify_native(contracts, root / "native-orchestration", workers=4)
            save(
                root / "summary.json",
                dict(
                    registered=len(rows),
                    attempted=len(rows),
                    qualified=sum(r["status"] == "REFERENCE_QUALIFIED" for r in rows),
                    model_calls=0,
                ),
            )
        elif payload["mode"] == "REGISTERED_LLM_BATCH":
            import hashlib

            for path, expected in payload.get("expected_source_hashes", {}).items():
                if path.startswith("afterclick/"):
                    assert (
                        hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest() == expected
                    ), path
            registration = dict(payload["registration"])
            registration["contracts"] = {
                key: dict(path=str(contracts / (key + ".json")), digest=digest(contract))
                for key, contract in payload["contracts"].items()
            }
            transport = Transport(
                root / "model-traces",
                payload["service_url"],
                payload["model_name"],
                deadline=time.monotonic() + min(480, payload["seconds"]),
                max_calls=payload["max_calls"],
                concurrency=registration["model_concurrency"],
            )
            execute(registration, root / "episodes", transport)
        else:
            raise ValueError("Unknown mode; no default paid behavior")
    except Exception:
        error = traceback.format_exc()
        save(root / "error.json", dict(error=error))
    finally:
        if transport:
            transport.close()
        try:
            pg("pg_ctl", "-D", str(data), "-m", "fast", "-w", "stop")
        except Exception:
            pass
        if (data / "server.log").exists():
            shutil.copyfile(data / "server.log", root / "postgres.log")
        usage = (
            dict(calls=transport.calls, tokens=transport.tokens, uncertain=transport.uncertain)
            if transport
            else dict(calls=0, tokens=0, uncertain=0)
        )
        save(
            root / "runtime.json",
            dict(
                usage=usage,
                error=error,
                elapsed_seconds=time.monotonic() - started,
                retained_volume_path=str(root),
            ),
        )
        evidence.commit()
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode="w:gz", compresslevel=3) as tar:
        tar.add(root, arcname=identifier)
    return dict(
        archive=archive.getvalue(),
        usage=usage,
        error=error,
        elapsed_seconds=time.monotonic() - started,
        retained_volume_path=str(root),
    )


@app.local_entrypoint()
def qualify(output: str):
    import hashlib

    output_path = pathlib.Path(output)
    output_path.mkdir(parents=True, exist_ok=False)
    contracts = {}
    for name in [
        "DEV-RETENTION_EXPORT-L3-FLOWBOARD-01",
        "DEV-RETENTION_EXPORT-L3-OPSCONSOLE-01",
    ]:
        path = pathlib.Path("research_ops/completion_v12/candidate_contracts_v6") / (name + ".json")
        contracts[name] = json.loads(path.read_text())
    payload = dict(
        batch_id="cloud-reference-qualification-v3",
        mode="REFERENCE_QUALIFICATION",
        contracts=contracts,
        native=True,
    )
    (output_path / "registration.json").write_text(json.dumps(payload, indent=2))
    result = batch.remote(payload)
    archive = result.pop("archive")
    (output_path / "evidence.tar.gz").write_bytes(archive)
    result["archive_sha256"] = hashlib.sha256(archive).hexdigest()
    (output_path / "result.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result))


@app.local_entrypoint()
def qualify_manifest(output: str, manifest: str):
    import hashlib

    output_path = pathlib.Path(output)
    output_path.mkdir(parents=True, exist_ok=False)
    payload = dict(
        batch_id="corrected-task-qualification-v1",
        mode="REFERENCE_QUALIFICATION",
        native=False,
        contracts=json.loads(pathlib.Path(manifest).read_text()),
    )
    (output_path / "registration.json").write_text(json.dumps(payload, indent=2))
    result = batch.remote(payload)
    archive = result.pop("archive")
    (output_path / "evidence.tar.gz").write_bytes(archive)
    result["archive_sha256"] = hashlib.sha256(archive).hexdigest()
    (output_path / "result.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result))


@app.local_entrypoint()
def execute_registered(
    run_dir: str, service_url: str, model_name: str, deadline_utc: float, max_calls: int
):
    """Execute a finite registered queue in batches; never selects cells by outcome."""
    import collections
    import concurrent.futures
    import hashlib

    run = pathlib.Path(run_dir)
    registration = json.loads((run / "registration.json").read_text())
    protocol = json.loads((run / "paid-protocol.json").read_text())
    contracts = {
        key: json.loads(pathlib.Path(value["path"]).read_text())
        for key, value in registration["contracts"].items()
    }
    groups = collections.OrderedDict()
    for cell in registration["episodes"]:
        key = (cell["task_id"], cell["world_seed"], cell["admission_ms"], cell.get("clean", False))
        groups.setdefault(key, []).append(cell)
    chunks, current = [], []
    for group in groups.values():
        if current and len(current) + len(group) > 64:
            chunks.append(current)
            current = []
        current.extend(group)
    if current:
        chunks.append(current)
    usage = dict(calls=0, tokens=0, uncertain=0)
    completed_batches = []
    caps = [
        sum(
            registration["limits"]["max_actor_calls"] + (cell["policy"] in {"P3", "P5"})
            for cell in cells
        )
        for cells in chunks
    ]
    if sum(caps) > max_calls:
        raise ValueError("Registered queue exceeds finite request budget")

    def run_chunk(index, cells):
        batch_id = f"{run.name}-b{index:04d}"
        selected = {cell["task_id"] for cell in cells}
        partial = dict(
            registration,
            episodes=cells,
            contracts={k: v for k, v in registration["contracts"].items() if k in selected},
        )
        payload = dict(
            batch_id=batch_id,
            mode="REGISTERED_LLM_BATCH",
            contracts={k: contracts[k] for k in selected},
            registration=partial,
            service_url=service_url,
            model_name=model_name,
            seconds=min(480, int(deadline_utc - time.time() - 20)),
            max_calls=caps[index],
            expected_source_hashes=protocol["source_hashes"],
        )
        result = batch.remote(payload)
        blob = result.pop("archive")
        folder = run / "cloud-batches" / batch_id
        folder.mkdir(parents=True, exist_ok=False)
        archive_path = folder / "evidence.tar.gz"
        archive_path.write_bytes(blob)
        result["archive_sha256"] = hashlib.sha256(blob).hexdigest()
        (folder / "result.json").write_text(json.dumps(result, indent=2))
        with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as archive:
            for member in archive.getmembers():
                target = folder / member.name
                if (
                    not target.resolve().is_relative_to(folder.resolve())
                    or member.issym()
                    or member.islnk()
                ):
                    raise ValueError("Unsafe evidence archive member")
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                elif member.isfile():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with archive.extractfile(member) as stream:
                        target.write_bytes(stream.read())
        return dict(batch_id=batch_id, result=result)

    pending_chunks = iter(enumerate(chunks))
    workers = registration.get("parallel_batches", 1)
    assert 1 <= workers <= 2
    fatal = False
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        active = set()
        while True:
            while not fatal and len(active) < workers and time.time() + 60 < deadline_utc:
                item = next(pending_chunks, None)
                if item is None:
                    break
                active.add(pool.submit(run_chunk, *item))
            if not active:
                break
            done, active = concurrent.futures.wait(
                active, return_when=concurrent.futures.FIRST_COMPLETED
            )
            for future in done:
                record = future.result()
                for key in usage:
                    usage[key] += record["result"]["usage"][key]
                completed_batches.append(record)
                (run / "cloud-usage.json").write_text(json.dumps(usage, indent=2))
                (run / "cloud-batches.json").write_text(json.dumps(completed_batches, indent=2))
                print(json.dumps(dict(batch_id=record["batch_id"], **record["result"])), flush=True)
                fatal |= bool(record["result"]["error"])
    terminal = {
        json.loads(p.read_text())["episode_id"]
        for p in (run / "cloud-batches").glob("**/episodes/*/result.json")
    }
    not_run = [c["episode_id"] for c in registration["episodes"] if c["episode_id"] not in terminal]
    (run / "queue-reconciliation.json").write_text(
        json.dumps(
            dict(
                registered=len(registration["episodes"]),
                terminal=len(terminal),
                not_run=not_run,
                complete=not not_run,
            ),
            indent=2,
        )
    )
    if fatal:
        raise RuntimeError("Cloud infrastructure failed; all returned raw evidence retained")
