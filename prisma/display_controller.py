"""
DLP2000 display controller via Linux framebuffer (/dev/fb0).

Usage:
    display_controller.show_page(book_id, page_number)
"""

import fcntl
import mmap
import struct
import logging
from pathlib import Path

from PIL import Image

import config
import book_store

log = logging.getLogger(__name__)

# ioctl codes for framebuffer info
FBIOGET_VSCREENINFO = 0x4600

# Cached framebuffer properties (populated on first use)
_fb_width: int = 0
_fb_height: int = 0
_fb_bpp: int = 0    # bits per pixel


def _get_fb_info() -> tuple[int, int, int]:
    """Read framebuffer dimensions and bit depth via ioctl."""
    global _fb_width, _fb_height, _fb_bpp
    if _fb_width:
        return _fb_width, _fb_height, _fb_bpp

    with open(config.FRAMEBUFFER_DEVICE, "rb") as fb:
        # FBIOGET_VSCREENINFO returns a fb_var_screeninfo struct.
        # First two uint32 fields are xres and yres; field at offset 24 is bits_per_pixel.
        buf = bytearray(160)
        fcntl.ioctl(fb, FBIOGET_VSCREENINFO, buf)
        xres, yres = struct.unpack_from("II", buf, 0)
        bpp = struct.unpack_from("I", buf, 24)[0]

    _fb_width, _fb_height, _fb_bpp = xres, yres, bpp
    log.info("Framebuffer: %dx%d @ %d bpp", xres, yres, bpp)
    return xres, yres, bpp


def _image_to_fb_bytes(image_path: Path, width: int, height: int, bpp: int) -> bytes:
    """Load a JPEG, resize to framebuffer dimensions, return raw bytes."""
    img = Image.open(image_path).convert("RGB")
    img = img.resize((width, height), Image.LANCZOS)

    if bpp == 16:
        # RGB565: pack each pixel into 2 bytes
        r, g, b = img.split()
        r_arr = bytes(r)
        g_arr = bytes(g)
        b_arr = bytes(b)
        out = bytearray(width * height * 2)
        for i in range(width * height):
            rv = r_arr[i] >> 3
            gv = g_arr[i] >> 2
            bv = b_arr[i] >> 3
            pixel = (rv << 11) | (gv << 5) | bv
            out[i * 2]     = pixel & 0xFF
            out[i * 2 + 1] = (pixel >> 8) & 0xFF
        return bytes(out)
    else:
        # Assume 24 or 32 bpp — write as RGB (or RGBX for 32)
        if bpp == 32:
            img_out = Image.new("RGBA", img.size, (0, 0, 0, 255))
            img_out.paste(img)
            return img_out.tobytes()
        return img.tobytes()


def show_page(book_id: str, page: int) -> None:
    """
    Display the given page of the given book on the DLP2000.

    Raises:
        FileNotFoundError: if the book or page doesn't exist on disk.
        OSError: if the framebuffer device can't be opened.
    """
    path = book_store.image_path(book_id, page)
    w, h, bpp = _get_fb_info()
    raw = _image_to_fb_bytes(path, w, h, bpp)

    with open(config.FRAMEBUFFER_DEVICE, "rb+") as fb:
        fb_map = mmap.mmap(fb.fileno(), w * h * (bpp // 8), mmap.MAP_SHARED, mmap.PROT_WRITE)
        fb_map.seek(0)
        fb_map.write(raw)
        fb_map.close()

    log.info("Displayed book=%s page=%d (%dx%d)", book_id, page, w, h)


def clear() -> None:
    """Fill the framebuffer with black."""
    w, h, bpp = _get_fb_info()
    with open(config.FRAMEBUFFER_DEVICE, "rb+") as fb:
        fb_map = mmap.mmap(fb.fileno(), w * h * (bpp // 8), mmap.MAP_SHARED, mmap.PROT_WRITE)
        fb_map.seek(0)
        fb_map.write(b"\x00" * w * h * (bpp // 8))
        fb_map.close()
