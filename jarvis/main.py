"""Jarvis entry point."""

import asyncio
import logging
import sys
from concurrent.futures import ThreadPoolExecutor

from aiohttp import web

import config
from prisma_client import PrismaClient
from http_server import build_app
from camera_loop import run_camera_loop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)

log = logging.getLogger(__name__)


async def main() -> None:
    loop = asyncio.get_event_loop()

    # Start Prisma client (WebSocket + HTTP)
    prisma = PrismaClient()
    await prisma.start()

    # Start HTTP server for web app
    app = build_app(prisma)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, config.HOST, config.PORT)
    await site.start()
    log.info("Jarvis HTTP server listening on %s:%d", config.HOST, config.PORT)

    # Start camera loop in a thread (blocking, CPU-bound)
    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="camera")
    loop.run_in_executor(executor, run_camera_loop, prisma, loop)
    log.info("Camera loop started")

    # Keep running until interrupted
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        log.info("Shutting down Jarvis")
        await runner.cleanup()
        await prisma.close()
        executor.shutdown(wait=False)


if __name__ == "__main__":
    asyncio.run(main())
