"""Baseline structured logging, applied once at app startup.

Writes to stdout in a single-line, greppable format. This is deliberately
just the app-wide baseline (uncaught errors, request-level events) - LLM
call tracing already has its own durable home in the llm_calls table (see
app.llm_adapter), so it doesn't need to go through this config to be
"visible in production."

Any PaaS host (Railway/Render/Fly/Heroku-style) captures and retains stdout
by default, so this alone is enough to inspect logs after the fact there.
It is NOT enough on a bare `docker run`/self-managed VM with no logging
driver configured - see docs/deployment.md for that case.
"""

import logging
import sys


def configure_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    )

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [handler]
