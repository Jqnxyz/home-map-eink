# home-map-eink

Raspberry Pi Pico 2W + Waveshare 2.13" e-ink display showing family
presence/location from a home API. People who change floors since the
last update are highlighted in red.

## Hardware

- Raspberry Pi Pico 2W
- Waveshare 2.13" e-Paper HAT (B) V4 (tri-color: black/white/red)

### Wiring

| Display Pin | Pico 2W GPIO | Physical Pin |
|-------------|--------------|--------------|
| RST         | GPIO 12      | Pin 16       |
| DC          | GPIO 8       | Pin 11       |
| CS          | GPIO 9       | Pin 12       |
| BUSY        | GPIO 13      | Pin 17       |
| CLK (SCK)   | GPIO 10      | Pin 14       |
| DIN (MOSI)  | GPIO 11      | Pin 15       |
| VCC         | 3.3V         | Pin 36       |
| GND         | GND          | Pin 38       |

## Setup

### 1. Flash MicroPython

Download the latest Pico 2W MicroPython UF2 from [micropython.org](https://micropython.org/download/RPI_PICO2_W/) and flash it.

### 2. Configure

```
cp config.example.py config.py
# Edit config.py: fill in WIFI_SSID, WIFI_PASSWORD, API_URL (and FEED_TOKEN if the
# server requires sign-in),
# and customize FLOORS / ZONE_MAP / FLOOR_MAP for your home layout.
```

### 3. Upload files

Using `mpremote`, `rshell`, or Thonny — upload all `.py` files to the root of the device:

```
mpremote connect /dev/tty.usbmodem* cp boot.py main.py api.py config.py \
  display.py renderer.py wifi.py epd_2in13b_v4.py font5x8.py :
```

### 4. Run

The device boots automatically and starts the main loop. Check serial output for WiFi connection status and errors.

## API Contract

`API_URL` must return a JSON array in this shape:

```json
[
  {
    "name": "Alice",
    "floor": "Second Floor",
    "zone": "Bedroom",
    "last_seen": "2026-03-01T12:00:00Z"
  }
]
```

People whose `last_seen` is older than `STALE_TIMEOUT_S` seconds are hidden from the display.

## Configuration Reference

| Key                   | Default | Description |
|-----------------------|---------|-------------|
| `WIFI_SSID`           | —       | WiFi network name |
| `WIFI_PASSWORD`       | —       | WiFi password |
| `API_URL`             | —       | Presence API endpoint |
| `FEED_TOKEN`          | `""`    | Optional feed token, sent as `Authorization: Bearer ...`. Only needed if the server requires sign-in to view the map |
| `RST_PIN` … `DIN_PIN` | 8–13   | SPI GPIO pin assignments |
| `POLL_INTERVAL_S`     | 60      | Seconds between API polls |
| `STALE_TIMEOUT_S`     | 300     | Seconds before a person is hidden |
| `FLOORS`              | —       | Ordered list of display rows (top→bottom) |
| `ZONE_MAP`            | —       | `(floor, zone)` → display row label |
| `FLOOR_MAP`           | —       | Fallback floor → display row label |

## File Overview

| File                | Purpose |
|---------------------|---------|
| `boot.py`           | MicroPython entry point; runs main, shows errors on display |
| `main.py`           | Main loop: WiFi connect, poll API, render |
| `api.py`            | Fetch & parse presence JSON |
| `display.py`        | Change detection and movement tracking |
| `renderer.py`       | Layout & draw to e-ink framebuffer |
| `wifi.py`           | WiFi connect / reconnect |
| `epd_2in13b_v4.py`  | Waveshare display driver |
| `font5x8.py`        | 5×8 bitmap font |
| `config.example.py` | Config template (safe to commit) |
| `test_boot.py`      | Standalone display hardware test |
