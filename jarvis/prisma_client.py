"""
Prisma client for Jarvis.

Manages:
  - A persistent WebSocket connection to Prisma (with auto-reconnect)
  - HTTP multipart book uploads to Prisma
"""

import asyncio
import json
import logging
import time
from typing import Optional

import aiohttp

import config
from shared.protocol import ActivateBookMsg, DisplayPageMsg

log = logging.getLogger(__name__)


class PrismaClient:
    def __init__(self) -> None:
        self._session: Optional[aiohttp.ClientSession] = None
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        self._connected = asyncio.Event()

    async def start(self) -> None:
        """Create HTTP session and establish initial WebSocket connection."""
        self._session = aiohttp.ClientSession()
        asyncio.ensure_future(self._ws_loop())

    async def _ws_loop(self) -> None:
        """Connect (and reconnect) to Prisma's WebSocket indefinitely."""
        while True:
            try:
                log.info("Connecting to Prisma WS at %s", config.PRISMA_WS_URL)
                async with self._session.ws_connect(
                    config.PRISMA_WS_URL,
                    heartbeat=config.WS_KEEPALIVE_INTERVAL,
                ) as ws:
                    self._ws = ws
                    self._connected.set()
                    log.info("Connected to Prisma")
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            log.debug("Prisma: %s", msg.data)
                        elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                            break
            except Exception as e:
                log.warning("WS connection failed: %s — retrying in %ds", e, config.WS_RECONNECT_INTERVAL)
            finally:
                self._connected.clear()
                self._ws = None

            await asyncio.sleep(config.WS_RECONNECT_INTERVAL)

    async def _send_ws(self, payload: str) -> None:
        """Wait for connection then send a JSON message over WebSocket."""
        await self._connected.wait()
        if self._ws and not self._ws.closed:
            await self._ws.send_str(payload)
        else:
            log.warning("WS send skipped — not connected")

    async def send_activate_book(self, book_id: str) -> None:
        msg = ActivateBookMsg(book_id=book_id)
        log.info("Sending activate_book: %s", book_id)
        await self._send_ws(msg.to_json())

    async def send_display_page(self, page: int) -> None:
        msg = DisplayPageMsg(page=page)
        log.debug("Sending display_page: %d", page)
        await self._send_ws(msg.to_json())

    async def upload_book(self, form_data: aiohttp.FormData) -> dict:
        """
        Forward a book (as multipart FormData) to Prisma's /books endpoint.

        Returns Prisma's JSON response.
        """
        url = f"{config.PRISMA_BASE_URL}/books"
        log.info("Uploading book to Prisma at %s", url)
        async with self._session.post(url, data=form_data) as resp:
            resp.raise_for_status()
            return await resp.json()

    def send_display_page_sync(self, page: int) -> None:
        """
        Thread-safe wrapper for send_display_page.
        Called from the camera thread via asyncio.run_coroutine_threadsafe.
        """
        asyncio.run_coroutine_threadsafe(self.send_display_page(page), self._loop)

    async def close(self) -> None:
        if self._ws:
            await self._ws.close()
        if self._session:
            await self._session.close()
