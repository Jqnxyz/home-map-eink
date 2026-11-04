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
# Edit config.py: fill in WIFI_SSID, WIFI_PASSWORD, API_URL,
# and customize FLOOR_ORDER / FLOOR_NICKNAMES / ZONE_NICKNAMES / PEOPLE_NICKNAMES for your home.
```

### 3. Get a CA certificate and a feed token

The display talks to the server over **HTTPS with certificate verification** and authenticates with a
read-only, revocable **feed token** sent in an `Authorization: Bearer` header (never in the URL).

1. On the server: Settings > Access > Feed access tokens > create one (leave "Allow the token in the URL" **unticked**).
2. Download the root CA of your server's certificate chain (Let's Encrypt shown):

```
curl -o isrgrootx1.der https://letsencrypt.org/certs/isrgrootx1.der
```
3. Put the token in `FEED_TOKEN` and the file name in `CA_CERT_FILE` in `config.py`.

The firmware fails closed: it will not send a token over `http://`, over unverified TLS, or in a URL, and it never
follows redirects. A rejected token shows "Token rejected" on the panel instead of an empty map.

### 4. Upload files

```
mpremote connect /dev/tty.usbmodem* cp boot.py main.py api.py secure_http.py config.py \
  display.py renderer.py wifi.py epd_2in13b_v4.py font5x8.py isrgrootx1.der :
```

### 5. Run

The device boots automatically. Serial output shows WiFi status and fetch errors.

## API Contract

`GET API_URL` returns (extra fields are ignored):

```json
{"generated_at": "2026-03-01T12:00:01Z",
 "people": [{"name": "Alice", "location": {"floor_name": "Second Floor", "zone_name": "Bedroom"},
             "last_seen_at": "2026-03-01T12:00:00Z"}]}
```

`location: null` (away) is skipped; people older than `STALE_TIMEOUT_S` are hidden. Any 200 that is not this shape
(captive portal, wrong URL) is an error, not "nobody home".

## Display

One tile per person (up to 6, then "+N"): name (or its nickname), the zone nickname, and for away people the time last seen. A person who
changed location since the last refresh gets a red tile. There is no footer. A status page (title plus details) appears
only when refreshes fail: rejected token, repeated errors, no WiFi or a config error.

## Behaviour

- Keeps the last good picture on a transient failure; shows "Offline" after 3 failures in a row, and only
  refreshes the panel when the message changes (e-ink wear).
- Backs off on repeated errors (up to 5x `POLL_INTERVAL_S`), honours `Retry-After` on 429, and slows to 5 min on a
  rejected token (the server rate-limits bad tokens).
- Syncs the clock over NTP (needed for certificate validity), puts the panel into deep sleep after each refresh,
  and resets itself after a crash or 30 failures in a row.

## Configuration Reference

| Key                   | Default | Description |
|-----------------------|---------|-------------|
| `WIFI_SSID`           | —       | WiFi network name |
| `WIFI_PASSWORD`       | —       | WiFi password |
| `API_URL`             | —       | Presence endpoint, `https://` only |
| `FEED_TOKEN`          | `""`    | Bearer token (leave empty if the map is public) |
| `CA_CERT_FILE`        | —       | CA certificate (DER/PEM) used to verify the server |
| `ALLOW_INSECURE`      | `False` | Lab-only: allow http / unverified TLS |
| `RST_PIN` … `DIN_PIN` | 8–13   | SPI GPIO pin assignments |
| `POLL_INTERVAL_S`     | 60      | Seconds between API polls |
| `STALE_TIMEOUT_S`     | 300     | Seconds before a person is hidden |
| `PEOPLE_PRIORITY`     | `[]`    | Ordering only: these names come first, in this order. Does not override hide/away rules |
| `PEOPLE_ONLY`         | `[]`    | If set, show only these names |
| `PEOPLE_HIDE`         | `[]`    | Never show these names |
| `SHOW_AWAY`           | `True`  | Dashed "Away" tiles after people who are home |
| `TZ_OFFSET_MIN`       | `0`     | Minutes added to UTC for the away "seen" time |
| `PEOPLE_NICKNAMES`    | `{}`    | Real name -> short name on the tile (max 6 chars) |
| `FLOOR_ORDER`         | —       | Floor names, highest first; sets tile order |
| `FLOOR_NICKNAMES`     | —       | Floor name -> short label (e.g. "Main Floor" -> "1F") |
| `ZONE_NICKNAMES`      | —       | `(floor, zone)` -> tile text, max 12 chars; unlisted zones show floor nickname + zone |

## File Overview

| File                | Purpose |
|---------------------|---------|
| `boot.py`           | MicroPython entry point; runs main, shows errors on display |
| `main.py`           | Main loop: WiFi connect, poll API, render |
| `api.py`            | Fetch, classify errors, parse presence JSON |
| `secure_http.py`    | Verified-TLS HTTPS GET with bearer header |
| `display.py`        | Change detection and movement tracking |
| `renderer.py`       | Layout & draw to e-ink framebuffer |
| `wifi.py`           | WiFi connect / reconnect |
| `epd_2in13b_v4.py`  | Waveshare display driver |
| `font5x8.py`        | 5×8 bitmap font |
| `config.example.py` | Config template (safe to commit) |
| `test_boot.py`      | Standalone display hardware test |
| `tests/`            | Host-side tests: `python3 -m unittest discover -s tests` |
