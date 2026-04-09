"""
Global in-memory state for Prisma.

Not persisted across reboots — user must re-activate a book after restart.
"""

active_book_id: str | None = None
current_page: int = 0
