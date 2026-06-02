"""Standalone runner for the inactivity monitor.

Run the long-lived scheduler (every CHECK_INTERVAL_MINUTES)::

    python -m inactivity_monitor

Run a single check immediately and exit (useful for testing the full
fetch → analyse → Teams pipeline)::

    python -m inactivity_monitor --once

Environment variables are documented in inactivity_monitor/README.md. If a
``.env`` file is present and ``python-dotenv`` is installed it is loaded
automatically.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import signal

from .config import ConfigError, MonitorConfig
from .scheduler import create_scheduler, run_daily_report, run_inactivity_check


def _load_dotenv() -> None:
    """Best-effort .env loading; silently skip if python-dotenv is absent."""
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv()
    except Exception:
        pass


def _configure_logging() -> None:
    """Log to the console and to ``inactivity_monitor/monitor.log``.

    The file handler matters when the worker runs under Windows Task Scheduler
    (with pythonw.exe there is no console), giving a durable record of runs.
    """
    import os

    log_path = os.path.join(os.path.dirname(__file__), "monitor.log")
    formatter = logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s")

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)

    try:
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
    except OSError:
        # If the log file can't be opened (permissions), console logging still works.
        pass


async def _run_forever(config: MonitorConfig) -> None:
    """Start the scheduler and run an initial check, then block until killed."""
    scheduler = create_scheduler(config)
    scheduler.start()
    logging.getLogger(__name__).info("Monitor running. Press Ctrl+C to stop.")

    # Kick off one check right away so we don't wait a full interval.
    await run_inactivity_check(config)

    stop_event = asyncio.Event()

    def _request_stop(*_: object) -> None:
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _request_stop)
        except NotImplementedError:
            # Signal handlers are unsupported on Windows event loops; Ctrl+C
            # still raises KeyboardInterrupt which is handled in main().
            pass

    await stop_event.wait()
    scheduler.shutdown(wait=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Course Tracker inactivity monitor.")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single inactivity check immediately and exit.",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Send the daily analytics report immediately and exit (always sends).",
    )
    args = parser.parse_args()

    _load_dotenv()
    _configure_logging()

    try:
        config = MonitorConfig.from_env()
    except ConfigError as exc:
        raise SystemExit(f"Configuration error: {exc}")

    try:
        if args.report:
            asyncio.run(run_daily_report(config))
        elif args.once:
            asyncio.run(run_inactivity_check(config))
        else:
            asyncio.run(_run_forever(config))
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Interrupted; shutting down.")


if __name__ == "__main__":
    main()
