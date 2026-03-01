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

try:
    import gc
    import config
    import display
    import wifi

    if not wifi.connect(config.WIFI_SSID, config.WIFI_PASSWORD):
        display.show_message("No WiFi", "Check credentials")
        utime.sleep(10)
        import machine
        machine.reset()

    print("WiFi connected")
    import api

    while True:
        if not wifi.ensure_connected(config.WIFI_SSID, config.WIFI_PASSWORD):
            display.show_message("No WiFi")
            gc.collect()
            utime.sleep(config.POLL_INTERVAL_S)
            continue

        people, result = api.fetch_presence(config.API_URL, config.STALE_TIMEOUT_S)

        if people is not None:
            if display.update(people):
                print("Display refreshed")
            else:
                print("No change")
        else:
            print("API error:", result)
            display.show_message("Error", result[:20])

        gc.collect()
        utime.sleep(config.POLL_INTERVAL_S)

except Exception as e:
    sys.print_exception(e)
    utime.sleep(60)
