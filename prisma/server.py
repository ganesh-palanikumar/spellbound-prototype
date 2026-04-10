"""
Prisma aiohttp server.

Routes:
  GET  /health   — liveness check
  POST /books    — store a new book (multipart: metadata JSON + image files)
  GET  /ws       — WebSocket endpoint for Jarvis commands
"""

import json
import logging
from aiohttp import web

import config
import book_store
import ws_handler
from shared.protocol import BookMetadata

log = logging.getLogger(__name__)


async def health(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


async def post_book(request: web.Request) -> web.Response:
    try:
        reader = await request.multipart()
    except Exception as e:
        raise web.HTTPBadRequest(reason=f"Expected multipart: {e}")

    metadata: BookMetadata | None = None
    images: dict[str, bytes] = {}

    async for part in reader:
        if part.name == "metadata":
            raw = await part.read(decode=True)
            try:
                metadata = BookMetadata.from_dict(json.loads(raw))
            except (KeyError, ValueError) as e:
                raise web.HTTPBadRequest(reason=f"Invalid metadata: {e}")
        elif part.name and part.filename:
            images[part.filename] = await part.read(decode=False)
        elif part.name:
            # field name is the filename (alternative upload style)
            images[part.name] = await part.read(decode=False)

    if metadata is None:
        raise web.HTTPBadRequest(reason="Missing 'metadata' field")
    if not images:
        raise web.HTTPBadRequest(reason="No image files received")

    try:
        book_store.save_book(metadata, images)
    except Exception as e:
        log.error("Failed to save book %s: %s", metadata.book_id, e)
        raise web.HTTPInternalServerError(reason=str(e))

    log.info("Stored book %s (%d pages)", metadata.book_id, metadata.page_count)
    return web.json_response({"status": "ok", "book_id": metadata.book_id})


def build_app() -> web.Application:
    app = web.Application()

    # CORS middleware so the web app (different origin) can call Jarvis/Prisma
    @web.middleware
    async def cors(request, handler):
        response = await handler(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    app.middlewares.append(cors)

    app.router.add_get("/health", health)
    app.router.add_post("/books", post_book)
    app.router.add_get(config.WS_PATH, ws_handler.handle_ws)

    return app
