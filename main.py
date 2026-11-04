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


def _title(err):
    return {"auth": "Token rejected", "rate": "Rate limited"}.get(err.kind, "Refresh failed")


def _lines(err, failures, delay, token):
    return [
        err.text,
        "Failures in a row: %d" % failures,
        "Token: " + ("set" if token else "NOT SET"),
        "Server: " + config.API_URL.split("/")[2][:30],
        "Next try in %ds" % delay,
        "Recreate token in Settings" if err.kind == "auth" else "Check WiFi / server",
    ]


def run():
    bad = _check_config()
    if bad:
        display.show_status("Config error", [bad, "Fix config.py and re-upload"])
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
        display.show_status("No WiFi", ["SSID: " + config.WIFI_SSID[:30], "Check WIFI_SSID / password", "Retrying in 30s"])
        _sleep(30)
        machine.reset()

    while True:
        delay = poll
        if not wifi.ensure_connected(config.WIFI_SSID, config.WIFI_PASSWORD):
            failures += 1
            if failures >= 3 and shown != ("wifi", ""):
                display.show_status("No WiFi", ["SSID: " + config.WIFI_SSID[:30], "Failures in a row: %d" % failures,
                                                "Next try in %ds" % (poll * min(failures, 5))])
                shown = ("wifi", "")
        else:
            if not time_ok:
                time_ok = wifi.sync_time()  # cert validity needs a real clock
            people, err = api.fetch_presence(
                config.API_URL, config.STALE_TIMEOUT_S, token, ca, insecure, _cfg("TZ_OFFSET_MIN", 0))
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
                    delay = 300   # will not fix itself; do not hammer (server rate-limits bad tokens)
                if err.kind == "auth" or failures >= 3:
                    # Status page only when refreshes are failing. A blip or two keeps the last good picture.
                    sig = (err.kind, err.text)
                    if shown != sig:
                        display.show_status(_title(err), _lines(err, failures, delay, token))
                        shown = sig
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
