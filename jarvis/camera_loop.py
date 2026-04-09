"""
Camera loop for Jarvis.

Captures frames from the Arducam via Picamera2 and detects ArUco markers.
When a marker is detected, its ID is sent to Prisma as a display_page command.

Runs in a ThreadPoolExecutor (CPU-bound, blocking Picamera2 API).
"""

import asyncio
import logging
import time
from typing import Optional

import cv2

import config

log = logging.getLogger(__name__)

# Lazy import to avoid errors on non-Pi machines during development
try:
    from picamera2 import Picamera2
    _HAS_CAMERA = True
except ImportError:
    _HAS_CAMERA = False
    log.warning("picamera2 not available — camera loop will be simulated")


def _get_aruco_dict():
    dict_name = getattr(cv2.aruco, config.ARUCO_DICT)
    return cv2.aruco.getPredefinedDictionary(dict_name)


def _detect_page(frame_rgb, aruco_dict) -> Optional[int]:
    """Return the first detected ArUco marker ID, or None."""
    gray = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2GRAY)
    detector_params = cv2.aruco.DetectorParameters()
    corners, ids, _ = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=detector_params)
    if ids is not None and len(ids) > 0:
        return int(ids[0][0])
    return None


def run_camera_loop(prisma_client, loop: asyncio.AbstractEventLoop) -> None:
    """
    Blocking camera loop. Meant to run in a ThreadPoolExecutor.

    Args:
        prisma_client: PrismaClient instance.
        loop: The main asyncio event loop (for thread-safe coroutine scheduling).
    """
    aruco_dict = _get_aruco_dict()
    frame_interval = 1.0 / config.CAMERA_FPS
    last_page: Optional[int] = None

    if _HAS_CAMERA:
        cam = Picamera2()
        cam_config = cam.create_still_configuration(main={"size": (640, 480), "format": "RGB888"})
        cam.configure(cam_config)
        cam.start()
        log.info("Camera started")

        try:
            while True:
                t0 = time.monotonic()
                frame = cam.capture_array()
                page = _detect_page(frame, aruco_dict)

                if page is not None and page != last_page:
                    log.info("ArUco detected: page %d", page)
                    last_page = page
                    asyncio.run_coroutine_threadsafe(
                        prisma_client.send_display_page(page), loop
                    )

                elapsed = time.monotonic() - t0
                time.sleep(max(0.0, frame_interval - elapsed))
        finally:
            cam.stop()
    else:
        # Simulation mode: print a message and wait
        log.info("Camera simulation mode — no frames will be captured")
        while True:
            time.sleep(60)
