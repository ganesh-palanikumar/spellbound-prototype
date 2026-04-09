"""
WebSocket command handler for Prisma.

Receives commands from Jarvis and dispatches to book_store / display_controller.
"""

import logging
from aiohttp import web

import state
import book_store
import display_controller
from shared.protocol import (
    parse_ws_message,
    ActivateBookMsg,
    DisplayPageMsg,
    AckMsg,
    ErrorMsg,
)

log = logging.getLogger(__name__)


async def handle_ws(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse(heartbeat=30)
    await ws.prepare(request)
    log.info("Jarvis connected from %s", request.remote)

    async for msg in ws:
        if msg.type == web.WSMsgType.TEXT:
            await _dispatch(ws, msg.data)
        elif msg.type == web.WSMsgType.ERROR:
            log.error("WebSocket error: %s", ws.exception())

    log.info("Jarvis disconnected")
    return ws


async def _dispatch(ws: web.WebSocketResponse, raw: str) -> None:
    try:
        cmd = parse_ws_message(raw)
    except (ValueError, KeyError) as e:
        log.warning("Malformed WS message: %s — %s", raw, e)
        await ws.send_str(ErrorMsg(ref_type="unknown", message=str(e)).to_json())
        return

    if isinstance(cmd, ActivateBookMsg):
        await _activate_book(ws, cmd)
    elif isinstance(cmd, DisplayPageMsg):
        await _display_page(ws, cmd)


async def _activate_book(ws: web.WebSocketResponse, cmd: ActivateBookMsg) -> None:
    if not book_store.book_exists(cmd.book_id):
        log.warning("activate_book: unknown book_id=%s", cmd.book_id)
        await ws.send_str(
            ErrorMsg(ref_type="activate_book", message=f"book not found: {cmd.book_id}").to_json()
        )
        return

    state.active_book_id = cmd.book_id
    state.current_page = 0
    log.info("Active book set to %s", cmd.book_id)
    await ws.send_str(AckMsg(ref_type="activate_book").to_json())


async def _display_page(ws: web.WebSocketResponse, cmd: DisplayPageMsg) -> None:
    if state.active_book_id is None:
        await ws.send_str(
            ErrorMsg(ref_type="display_page", message="no active book").to_json()
        )
        return

    try:
        display_controller.show_page(state.active_book_id, cmd.page)
        state.current_page = cmd.page
        await ws.send_str(AckMsg(ref_type="display_page").to_json())
    except FileNotFoundError as e:
        log.error("display_page failed: %s", e)
        await ws.send_str(
            ErrorMsg(ref_type="display_page", message=str(e)).to_json()
        )
