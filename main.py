import gc
import utime
import config


def main():
    utime.sleep(1)

    # Init display BEFORE WiFi — SPI must be set up first
    import display
    display.show_message("Starting...")

    import wifi
    print("Connecting to WiFi...")
    if not wifi.connect(config.WIFI_SSID, config.WIFI_PASSWORD):
        display.show_message("No WiFi", "Check credentials")
        utime.sleep(10)
        import machine
        machine.reset()

    print("WiFi connected, fetching data...")
    import api

    while True:
        if not wifi.ensure_connected(config.WIFI_SSID, config.WIFI_PASSWORD):
            display.show_message("No WiFi")
            gc.collect()
            utime.sleep(config.POLL_INTERVAL_S)
            continue

        people, result = api.fetch_presence(config.API_URL, config.STALE_TIMEOUT_S)

        if people is not None:
            for p in people:
                print(p.get("name"), "->", p.get("floor"), "|", p.get("zone"))
            if display.update(people):
                print("Display refreshed")
            else:
                print("No change")
        else:
            print("API error:", result)
            display.show_message("Error", result[:20])

        gc.collect()
        utime.sleep(config.POLL_INTERVAL_S)


main()
