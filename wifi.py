import network
import utime


def _wait(wlan, timeout):
    start = utime.time()
    while not wlan.isconnected():
        if utime.time() - start > timeout:
            return False
        utime.sleep_ms(500)
    return True


def connect(ssid, password, timeout=20):
    """Connect to WiFi. Returns True on success."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    ok = _wait(wlan, timeout)
    if ok:
        print("WiFi up:", wlan.ifconfig()[0])
    return ok


def ensure_connected(ssid, password, timeout=20):
    wlan = network.WLAN(network.STA_IF)
    if wlan.isconnected():
        return True
    print("WiFi lost, reconnecting")
    wlan.active(False)
    utime.sleep_ms(500)
    return connect(ssid, password, timeout)


def sync_time():
    """Set the RTC from NTP. TLS certificate validity checks need a sane clock. Returns True on success."""
    try:
        import ntptime
        for _ in range(3):
            try:
                ntptime.settime()
                return True
            except OSError:
                utime.sleep(2)
    except ImportError:
        pass
    return False
