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

# 12-hour clock for the away "seen" time (2:05pm instead of 14:05).
CLOCK_12H = False

# Font for names on tiles: "regular" or "bold". (Only the bundled 5x8 bitmap font is available.)
NAME_FONT = "regular"

# Who to show (case-insensitive names as they appear in Home Map). At most 6 tiles fit; extras show as "+N".
PEOPLE_PRIORITY = []   # ordering only: listed names come first, in this order, e.g. ["Alice", "Ben"]
PEOPLE_ONLY = []       # if not empty, show only these people
PEOPLE_HIDE = []       # never show these people
# Short display names (max 6 characters at the large font), keyed by the name in Home Map. Case-insensitive.
PEOPLE_NICKNAMES = {}  # e.g. {"Iman Fandi": "Iman"}
AWAY_HIDE_AFTER_S = 86400  # hide away people not seen for this long (0 = never hide); 86400 = 24 h
SHOW_AWAY = True       # show away people as dashed tiles after those who are home

# Minutes to add to UTC for the "seen HH:MM" time on away tiles (e.g. 480 for UTC+8).
TZ_OFFSET_MIN = 0

# Floors, highest first, as named in Home Map. Sets the order of people on the display.
FLOOR_ORDER = ["Fourth Floor", "Third Floor", "Second Floor", "Main Floor"]

# Short names for floors. Tiles show "<floor nickname> <zone>" cut to 12 characters when a zone has no nickname below.
FLOOR_NICKNAMES = {
    "Fourth Floor": "4F",
    "Third Floor": "3F",
    "Second Floor": "2F",
    "Main Floor": "1F",
}

# Short names for specific zones: (floor name, zone name) -> text shown on the tile (max 12 characters).
# Names are matched with plain quotes (typographic quotes from the server are converted to ' automatically).
ZONE_NICKNAMES = {
    ("Main Floor", "Living Room"): "1F Living",
    ("Second Floor", "Bedroom"): "2F Bedroom",
}
