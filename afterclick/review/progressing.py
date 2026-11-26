"""Versioned controlled-cut replay with progressing SQL/HTTP consequence workers.

Never modifies OECR v1 or the original experimental scheduler. The evaluator may
pause at a declared checkpoint; after admission every branch advances while
policy inference/tools execute. Actual worker jitter is measured, not erased.
"""

import threading
import time

from sqlalchemy import select

from afterclick import domain
from afterclick.infrastructure import schema as core
from afterclick.oecr.client import capture, certify, validate
from afterclick.tcope.workloads import WorkloadWorld, runtime


class ProgressingWorld(WorkloadWorld):
    def __init__(self, spec):
        super().__init__(spec)
        self.cut_stop = threading.Event()
        self.cut_thread = None
        self.worker_intervals = []

    def start(self):
        if self.cut_thread and self.cut_thread.is_alive():
            raise ValueError("Worker already progressing")
        with self.db.engine.connect() as c:
            self.offset = c.execute(select(runtime.c.clock_ms)).scalar_one()
        self.anchor = time.monotonic()
        self.cut_stop.clear()
        self.mock_stop.clear()

        def work():
            while not self.cut_stop.wait(0.02):
                began = time.time()
                try:
                    ms = self.elapsed()
                    # Actual elapsed-time mapping, with jitter retained in events.
                    with self.db.engine.connect() as c:
                        current = domain.rows(c, core.runtime)[0]["logical_time"]
                    domain.advance(self.db, max(current, ms))
                    self.step(ms)
                    self.worker_intervals.append(
                        dict(start_wall=began, stop_wall=time.time(), clock_ms=ms)
                    )
                except Exception as exc:
                    self.worker_errors.append(type(exc).__name__ + ": " + str(exc))
                    self.cut_stop.set()

        self.cut_thread = threading.Thread(target=work, daemon=True)
        self.mock_thread = self.cut_thread
        self.cut_thread.start()

    def pause_workers(self):
        self.cut_stop.set()
        if self.cut_thread:
            self.cut_thread.join(5)
            if self.cut_thread.is_alive():
                raise RuntimeError("Cannot establish cut: worker still in flight")
        if self.worker_errors:
            raise RuntimeError("Worker errors prevent valid cut: " + str(self.worker_errors))
        with self.db.engine.connect() as c:
            self.offset = c.execute(select(runtime.c.clock_ms)).scalar_one()
        self.anchor = None

    def finish(self):
        self.pause_workers()
        # No fabricated future advancement after the observation horizon.


def checkpoint(world, gateway, conversation):
    gateway.page.evaluate("window.oecr.pause()")
    world.browser_pause(gateway.page)
    world.pause_workers()
    return capture(world, gateway, conversation)


def admit(world, gateway, envelope, conversation):
    cp = validate(envelope)
    cert = certify(world, gateway, cp, conversation)
    if not cert["valid"]:
        raise ValueError("PROGRESSING_REPLAY_ADMISSION_REJECTED: " + str(cert))
    return cert


def resume(world, gateway):
    # Clock starts immediately before browser queue/timer release.
    world.start()
    gateway.page.evaluate("window.oecr.resume()")
    world.browser_resume(gateway.page)
