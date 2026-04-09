"""
Book storage on Prisma's filesystem.

Layout under BOOKS_DIR:
  <book_id>/
    metadata.json
    page_001.jpg
    page_002.jpg
    ...
"""

import json
import os
from pathlib import Path

import config
from shared.protocol import BookMetadata


def book_dir(book_id: str) -> Path:
    return Path(config.BOOKS_DIR) / book_id


def book_exists(book_id: str) -> bool:
    return (book_dir(book_id) / "metadata.json").exists()


def save_book(metadata: BookMetadata, images: dict[str, bytes]) -> None:
    """
    Persist a book to disk.

    Args:
        metadata: Parsed BookMetadata object.
        images: Dict mapping filename (e.g. "page_001.jpg") → raw JPEG bytes.
    """
    dest = book_dir(metadata.book_id)
    dest.mkdir(parents=True, exist_ok=True)

    # Write metadata
    with open(dest / "metadata.json", "w") as f:
        json.dump(metadata.to_dict(), f, indent=2)

    # Write image files
    for filename, data in images.items():
        with open(dest / filename, "wb") as f:
            f.write(data)


def load_metadata(book_id: str) -> BookMetadata:
    with open(book_dir(book_id) / "metadata.json") as f:
        return BookMetadata.from_dict(json.load(f))


def image_path(book_id: str, page: int) -> Path:
    """
    Return the filesystem path for a given page number (1-based).
    Raises FileNotFoundError if page is out of range.
    """
    meta = load_metadata(book_id)
    for entry in meta.pages:
        if entry.page == page:
            p = book_dir(book_id) / entry.filename
            if not p.exists():
                raise FileNotFoundError(f"Image file missing: {p}")
            return p
    raise FileNotFoundError(f"Page {page} not found in book {book_id}")


def list_books() -> list[str]:
    """Return all book IDs currently stored."""
    root = Path(config.BOOKS_DIR)
    if not root.exists():
        return []
    return [d.name for d in root.iterdir() if (d / "metadata.json").exists()]
