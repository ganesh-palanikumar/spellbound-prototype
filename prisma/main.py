"""Prisma entry point."""

import logging
import sys
from aiohttp import web

import config
from server import build_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)

if __name__ == "__main__":
    app = build_app()
    web.run_app(app, host=config.HOST, port=config.PORT)
