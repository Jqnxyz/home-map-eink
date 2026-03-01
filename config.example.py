# WiFi credentials
WIFI_SSID = "your-wifi-ssid"
WIFI_PASSWORD = "your-wifi-password"

# API endpoint — URL that returns JSON presence data
API_URL = "https://your-api-host/api/presence/current"

# SPI pin assignments for Waveshare 2.13" e-Paper HAT (B) V4
# Default wiring for Pico 2W (GPIO numbers, not physical pin numbers)
RST_PIN = 12
DC_PIN = 8
CS_PIN = 9
BUSY_PIN = 13
CLK_PIN = 10
DIN_PIN = 11

# Poll interval in seconds
POLL_INTERVAL_S = 60

# Hide people not seen within this many seconds
STALE_TIMEOUT_S = 300

# Floor/zone display rows (top to bottom, highest floor first)
FLOORS = ["4F", "3F", "2F", "1F"]

# Map (floor_name, zone_name) -> display row label
# Keys are the exact strings returned by your API
ZONE_MAP = {
    ("Ground Floor", "Living Room"): "1F",
    ("Second Floor", "Bedroom"): "2F",
}

# Fallback floor mapping for zones not in ZONE_MAP
FLOOR_MAP = {
    "Ground Floor": "1F",
    "Second Floor": "2F",
    "Third Floor": "3F",
    "Fourth Floor": "4F",
}
