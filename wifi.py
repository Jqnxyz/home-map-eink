import network
import utime


def connect(ssid, password, timeout=15):
    """Connect to WiFi. Returns True on success, False on timeout."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    start = utime.time()
    while not wlan.isconnected():
        if utime.time() - start > timeout:
            return False
        utime.sleep_ms(500)
    print("WiFi connected:", wlan.ifconfig()[0])
    return True


def ensure_connected(ssid, password):
    """Check WiFi and reconnect if dropped. Returns True if connected."""
    wlan = network.WLAN(network.STA_IF)
    if wlan.isconnected():
        return True

    print("WiFi disconnected, reconnecting...")
    wlan.active(False)
    utime.sleep_ms(500)
    wlan.active(True)
    wlan.connect(ssid, password)

    start = utime.time()
    while not wlan.isconnected():
        if utime.time() - start > 15:
            print("WiFi reconnect failed")
            return False
        utime.sleep_ms(500)
    print("WiFi reconnected:", wlan.ifconfig()[0])
    return True
