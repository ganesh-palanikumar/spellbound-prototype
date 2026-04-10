"""
Spellbound shared message protocol.

All WebSocket messages between Jarvis and Prisma use these types.
JSON serialization: use msg.to_dict() to send, Msg.from_dict(d) to receive.
"""

from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from typing import Literal


# ---------------------------------------------------------------------------
# Jarvis → Prisma (WebSocket commands)
# ---------------------------------------------------------------------------

@dataclass
class ActivateBookMsg:
    book_id: str
    type: Literal["activate_book"] = "activate_book"

    def to_dict(self) -> dict:
        return {"type": self.type, "book_id": self.book_id}

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass
class DisplayPageMsg:
    page: int
    type: Literal["display_page"] = "display_page"

    def to_dict(self) -> dict:
        return {"type": self.type, "page": self.page}

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


# ---------------------------------------------------------------------------
# Prisma → Jarvis (WebSocket responses)
# ---------------------------------------------------------------------------

@dataclass
class AckMsg:
    ref_type: str
    status: str = "ok"
    type: Literal["ack"] = "ack"

    def to_dict(self) -> dict:
        return {"type": self.type, "ref_type": self.ref_type, "status": self.status}

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass
class ErrorMsg:
    ref_type: str
    message: str
    type: Literal["error"] = "error"

    def to_dict(self) -> dict:
        return {"type": self.type, "ref_type": self.ref_type, "message": self.message}

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


# ---------------------------------------------------------------------------
# HTTP payloads (used for documentation / validation)
# ---------------------------------------------------------------------------

@dataclass
class PageEntry:
    """One entry in the book's page list."""
    page: int        # 1-based page number
    filename: str    # e.g. "page_001.jpg"


@dataclass
class BookMetadata:
    """
    JSON metadata sent alongside image files in the multipart book upload.

    HTTP field name: "metadata"
    Image fields: one per page, field name = filename (e.g. "page_001.jpg")
    """
    book_id: str
    title: str
    pages: list[PageEntry]

    @property
    def page_count(self) -> int:
        return len(self.pages)

    def to_dict(self) -> dict:
        return {
            "book_id": self.book_id,
            "title": self.title,
            "page_count": self.page_count,
            "pages": [{"page": p.page, "filename": p.filename} for p in self.pages],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, d: dict) -> BookMetadata:
        return cls(
            book_id=d["book_id"],
            title=d["title"],
            pages=[PageEntry(page=p["page"], filename=p["filename"]) for p in d["pages"]],
        )


# ---------------------------------------------------------------------------
# Parse an incoming WebSocket message dict into a typed object
# ---------------------------------------------------------------------------

def parse_ws_message(raw: str) -> ActivateBookMsg | DisplayPageMsg | AckMsg | ErrorMsg:
    d = json.loads(raw)
    t = d.get("type")
    if t == "activate_book":
        return ActivateBookMsg(book_id=d["book_id"])
    if t == "display_page":
        return DisplayPageMsg(page=d["page"])
    if t == "ack":
        return AckMsg(ref_type=d["ref_type"], status=d.get("status", "ok"))
    if t == "error":
        return ErrorMsg(ref_type=d["ref_type"], message=d["message"])
    raise ValueError(f"Unknown message type: {t!r}")
