"""Jarvis configuration."""

# Prisma device address (resolved via mDNS)
PRISMA_HOST = "prisma.local"
PRISMA_HTTP_PORT = 8081
PRISMA_WS_URL = f"ws://{PRISMA_HOST}:{PRISMA_HTTP_PORT}/ws"
PRISMA_BASE_URL = f"http://{PRISMA_HOST}:{PRISMA_HTTP_PORT}"

# Jarvis HTTP server (for web app)
HOST = "0.0.0.0"
PORT = 8080

# WebSocket reconnect
WS_RECONNECT_INTERVAL = 5   # seconds between reconnect attempts
WS_KEEPALIVE_INTERVAL = 30  # seconds between pings

# Camera
CAMERA_FPS = 10             # frames per second for ArUco scanning
ARUCO_DICT = "DICT_4X4_50"  # OpenCV ArUco dictionary; marker ID = page number
