# Spellbound — Pre-Setup Guide

Run these steps on each device **before** deploying the application code.

---

## Both Devices (Jarvis + Prisma)

SSH into each device and run:

```bash
sudo apt update && sudo apt upgrade -y

# mDNS (device discovery), git, Python tooling
sudo apt install -y python3-pip python3-venv avahi-daemon avahi-utils git

# Enable mDNS so devices are reachable as jarvis.local / prisma.local
sudo systemctl enable avahi-daemon
sudo systemctl start avahi-daemon

# Create app directory
mkdir -p /home/lekha/spellbound
```

---

## Jarvis (Raspberry Pi Zero 2W)

```bash
# Camera stack (libcamera + picamera2 via apt — pip version has issues on Pi)
sudo apt install -y python3-libcamera python3-picamera2

# OpenCV for ArUco marker detection
sudo apt install -y python3-opencv

# Python dependencies
pip3 install aiohttp
```

### Verify camera works

```bash
libcamera-hello --timeout 2000
```

If you see a preview (even briefly), the camera is working. If you get an error, check:
- Camera cable is firmly seated
- Camera is enabled: `sudo raspi-config` → Interface Options → Camera

---

## Prisma (BeagleBone Green)

```bash
# Python dependencies
pip3 install aiohttp Pillow

# Book storage directory
sudo mkdir -p /var/spellbound/books
sudo chown lekha:lekha /var/spellbound/books
```

### Verify framebuffer exists

```bash
ls -la /dev/fb0
```

You should see something like `crw-rw---- 1 root video 29, 0 ... /dev/fb0`.

If `/dev/fb0` is missing, the DLP2000 display driver is not loaded. Check `/boot/uEnv.txt` for the correct display overlay for the DLPC2607 and add it if missing.

### Add lekha to the video group (needed to write to /dev/fb0)

```bash
sudo usermod -aG video lekha
# Log out and back in for this to take effect
```

---

## Verify Connectivity

From **Jarvis**:
```bash
ping -c 3 prisma.local
```

From **Prisma**:
```bash
ping -c 3 jarvis.local
```

From your **laptop** (on the same WiFi):
```bash
ping -c 3 jarvis.local
ping -c 3 prisma.local
```

All three should resolve and respond. If `.local` doesn't resolve, wait ~10 seconds after boot for avahi to advertise, then retry.

---

## Hostname Configuration

Ensure each device has the correct hostname set:

**On Jarvis:**
```bash
sudo hostnamectl set-hostname jarvis
```

**On Prisma:**
```bash
sudo hostnamectl set-hostname prisma
```

Then reboot each device:
```bash
sudo reboot
```

After reboot, `jarvis.local` and `prisma.local` will be resolvable on the network.
