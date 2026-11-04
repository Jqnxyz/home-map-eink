import sys
import utime
from machine import Pin, SPI

# Early SPI1 init — required on Pico 2W cold boot before WiFi
# touches the CYW43 chip, otherwise SPI1 pin mux breaks
utime.sleep(1)
spi = SPI(1)
spi.init(baudrate=4_000_000)
rst = Pin(12, Pin.OUT)
busy = Pin(13, Pin.IN, Pin.PULL_UP)
rst.value(1); utime.sleep_ms(50)
rst.value(0); utime.sleep_ms(2)
rst.value(1); utime.sleep_ms(50)
spi.deinit()
del spi, rst, busy

import gc
import machine
import config
import display
import wifi
import api


def _cfg(name, default):
    return getattr(config, name, default)


def _load_ca():
    path = _cfg("CA_CERT_FILE", "")
    if not path:
        return None
    with open(path, "rb") as f:
        return f.read()


def _sleep(seconds):
    utime.sleep(seconds)


def _check_config():
    url = config.API_URL
    token = _cfg("FEED_TOKEN", "")
    insecure = _cfg("ALLOW_INSECURE", False)
    if "token=" in url:
        return "Token in URL"       # would leak into proxy logs; use FEED_TOKEN
    if url.startswith("http://") and not insecure:
        return "Use https://"
    if url.startswith("https://") and not _cfg("CA_CERT_FILE", "") and not insecure:
        return "Need CA_CERT_FILE"
    if token and url.startswith("http://"):
        return "Token needs https"
    return None


def run():
    bad = _check_config()
    if bad:
        display.show_message("Config error", bad)
        _sleep(3600)
        machine.reset()

    ca = _load_ca()
    token = _cfg("FEED_TOKEN", "") or None
    insecure = _cfg("ALLOW_INSECURE", False)
    poll = config.POLL_INTERVAL_S
    shown = None          # last message put on the panel, to avoid refreshing for the same text
    failures = 0
    time_ok = False

    if not wifi.connect(config.WIFI_SSID, config.WIFI_PASSWORD):
        display.show_message("No WiFi", "Check credentials")
        _sleep(30)
        machine.reset()

    while True:
        delay = poll
        if not wifi.ensure_connected(config.WIFI_SSID, config.WIFI_PASSWORD):
            failures += 1
        else:
            if not time_ok:
                time_ok = wifi.sync_time()  # cert validity needs a real clock
            people, err = api.fetch_presence(
                config.API_URL, config.STALE_TIMEOUT_S, token, ca, insecure)
            if people is not None:
                failures = 0
                shown = None
                if display.update(people):
                    print("Display refreshed")
            else:
                failures += 1
                print("fetch failed:", err)
                if err.kind == "rate":
                    delay = max(poll, err.retry_after or 300)
                elif err.kind == "auth":
                    delay = 300   # not going to fix itself; do not hammer (server rate-limits bad tokens)
                    msg = ("Token rejected", "Recreate feed token")
                    if shown != msg:
                        display.show_message(*msg)
                        shown = msg
                elif failures >= 3:
                    msg = ("Offline", err.text[:20])
                    if shown != msg:
                        display.show_message(*msg)
                        shown = msg
                # fewer than 3 blips: keep the last good picture on the panel

        if failures >= 30:
            machine.reset()   # last resort for a wedged network stack
        # back off on repeated transport failures (max 5x poll)
        if failures > 1 and delay == poll:
            delay = poll * min(failures, 5)
        gc.collect()
        _sleep(delay)


try:
    run()
except Exception as e:
    sys.print_exception(e)
    utime.sleep(10)
    machine.reset()
