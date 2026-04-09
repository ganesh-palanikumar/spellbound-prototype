"""
Jarvis HTTP server.

Accepts requests from the web app and forwards them to Prisma.

Routes:
  GET  /health    — liveness check
  POST /books     — receive book from web app, proxy to Prisma
  POST /activate  — receive activation request, send to Prisma over WS
"""

import json
import logging

import aiohttp
from aiohttp import web

from prisma_client import PrismaClient

log = logging.getLogger(__name__)


def build_app(prisma: PrismaClient) -> web.Application:
    @web.middleware
    async def cors(request: web.Request, handler):
        if request.method == "OPTIONS":
            return web.Response(headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            })
        response = await handler(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response

    app = web.Application(middlewares=[cors])

    async def health(request: web.Request) -> web.Response:
        return web.json_response({"status": "ok", "device": "jarvis"})

    async def post_book(request: web.Request) -> web.Response:
        """Receive multipart book upload from web app, proxy to Prisma."""
        try:
            reader = await request.multipart()
        except Exception as e:
            raise web.HTTPBadRequest(reason=f"Expected multipart: {e}")

        # Re-assemble the multipart data to forward to Prisma
        form = aiohttp.FormData()
        async for part in reader:
            data = await part.read(decode=False)
            if part.name == "metadata":
                form.add_field("metadata", data.decode("utf-8"), content_type="application/json")
            elif part.filename:
                form.add_field(part.name, data, filename=part.filename, content_type=part.content_type or "image/jpeg")
            else:
                form.add_field(part.name, data, content_type=part.content_type or "application/octet-stream")

        try:
            result = await prisma.upload_book(form)
        except aiohttp.ClientResponseError as e:
            log.error("Prisma rejected book upload: %s", e)
            raise web.HTTPBadGateway(reason=f"Prisma error: {e.message}")
        except Exception as e:
            log.error("Book upload failed: %s", e)
            raise web.HTTPInternalServerError(reason=str(e))

        return web.json_response(result)

    async def post_activate(request: web.Request) -> web.Response:
        """Receive activation request from web app, forward to Prisma over WS."""
        try:
            body = await request.json()
            book_id = body["book_id"]
        except (json.JSONDecodeError, KeyError):
            raise web.HTTPBadRequest(reason="Expected JSON body with 'book_id'")

        await prisma.send_activate_book(book_id)
        return web.json_response({"status": "ok", "book_id": book_id})

    app.router.add_get("/health", health)
    app.router.add_post("/books", post_book)
    app.router.add_post("/activate", post_activate)
    app.router.add_route("OPTIONS", "/books", lambda r: web.Response())
    app.router.add_route("OPTIONS", "/activate", lambda r: web.Response())

    return app
