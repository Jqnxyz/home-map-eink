import gc
import utime
import config
import wifi
import api
import display


def main():
    # Connect to WiFi first (no display refresh yet)
    print("Connecting to WiFi...")
    if not wifi.connect(config.WIFI_SSID, config.WIFI_PASSWORD):
        display.show_message("No WiFi", "Check credentials")
        utime.sleep(10)
        import machine
        machine.reset()

    print("WiFi connected, fetching data...")
    last_people = None
    last_generated_at = ""

    while True:
        if not wifi.ensure_connected(config.WIFI_SSID, config.WIFI_PASSWORD):
            if last_people is None:
                display.show_message("No WiFi")
            gc.collect()
            utime.sleep(config.POLL_INTERVAL_S)
            continue

        people, result = api.fetch_presence(config.API_URL)

        if people is not None:
            if result != last_generated_at:
                last_people = people
                last_generated_at = result
                print("Refreshing display...")
                display.update(last_people, last_generated_at)
            else:
                print("Data unchanged, skipping refresh")
        else:
            print("API error:", result)
            if last_people is None:
                display.show_message("Error", result[:20])

        gc.collect()
        utime.sleep(config.POLL_INTERVAL_S)


main()
