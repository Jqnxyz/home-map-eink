import gc
import utime
import config
import wifi
import api
import display


def main():
    # Initialize display and show connecting message
    display.wake()
    display.show_message("Connecting...")
    display.sleep()

    # Connect to WiFi
    if not wifi.connect(config.WIFI_SSID, config.WIFI_PASSWORD):
        display.show_message("No WiFi", "Check credentials")
        display.sleep()
        utime.sleep(10)
        import machine
        machine.reset()

    last_people = None
    last_generated_at = ""
    last_error = None

    while True:
        # Ensure WiFi is still connected
        if not wifi.ensure_connected(config.WIFI_SSID, config.WIFI_PASSWORD):
            last_error = "No WiFi"
            if last_people is None:
                display.update(None, "", last_error)
                display.sleep()
            # Don't refresh display if we have stale data — timestamp shows it's old
            gc.collect()
            utime.sleep(config.POLL_INTERVAL_S)
            continue

        # Fetch presence data
        people, result = api.fetch_presence(config.API_URL)

        if people is not None:
            # New data arrived
            if result != last_generated_at:
                last_people = people
                last_generated_at = result
                last_error = None
                display.update(last_people, last_generated_at)
                display.sleep()
        else:
            # API error — keep stale data if available
            last_error = result
            if last_people is None:
                display.update(None, "", last_error)
                display.sleep()

        gc.collect()
        utime.sleep(config.POLL_INTERVAL_S)


main()
