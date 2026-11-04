# WiFi credentials
WIFI_SSID = "your-wifi-ssid"
WIFI_PASSWORD = "your-wifi-password"

# Feed endpoint. Must be https:// . Do NOT put ?token= in the URL (it ends up in proxy logs).
API_URL = "https://your-api-host/api/presence/current"

# Feed token from the server: Settings > Access > Feed access tokens (read-only, revocable).
# Sent as an Authorization: Bearer header, only over verified TLS. Leave empty if the map is public.
# Keep config.py off GitHub (it is gitignored) and untick "Allow the token in the URL" on the token.
FEED_TOKEN = ""

# CA certificate used to verify the server (DER or PEM file copied to the Pico). Required for https.
# Use the root of your certificate chain, e.g. ISRG Root X1 for Let's Encrypt:
#   curl -o isrgrootx1.der https://letsencrypt.org/certs/isrgrootx1.der
#   mpremote cp isrgrootx1.der :
# Behind Cloudflare use its root (e.g. Google Trust Services / Baltimore) instead.
CA_CERT_FILE = "isrgrootx1.der"

# Escape hatch for a lab LAN only: allow http:// and unverified TLS. Never use with a real token.
ALLOW_INSECURE = False

# SPI pin assignments for Waveshare 2.13" e-Paper HAT (B) V4
# Default wiring for Pico 2W (GPIO numbers, not physical pin numbers)
RST_PIN = 12
DC_PIN = 8
CS_PIN = 9
BUSY_PIN = 13
CLK_PIN = 10
DIN_PIN = 11

# Poll interval in seconds (backs off automatically on errors)
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
