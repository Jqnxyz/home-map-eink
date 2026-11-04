import secure_http

try:
    import ujson as json
except ImportError:
    import json

# Returned as the second tuple item on failure. AUTH and RATE are distinct so main can react.
AUTH = "auth"
RATE = "rate"


class FetchError:
    """kind: 'auth' | 'rate' | 'http' | 'net' | 'parse'. text is short and never holds the token."""

    def __init__(self, kind, text, retry_after=None):
        self.kind = kind
        self.text = text
        self.retry_after = retry_after

    def __str__(self):
        return self.text


def fetch_presence(url, stale_s=300, token=None, ca_der=None, allow_insecure=False):
    """Fetch presence. Returns (people, None) or (None, FetchError)."""
    try:
        status, retry, body = secure_http.get(url, token, ca_der, allow_insecure)
    except secure_http.HttpError as e:
        return (None, FetchError("net", str(e)))
    except Exception as e:  # e.g. TLS verification failure raised as ValueError
        return (None, FetchError("net", "TLS/" + type(e).__name__))

    if status == 401 or status == 403:
        return (None, FetchError("auth", "Token rejected"))
    if status == 429:
        return (None, FetchError("rate", "Rate limited", retry))
    if status != 200:
        return (None, FetchError("http", "HTTP " + str(status)))

    try:
        data = json.loads(body)
        raw_people = data["people"]
        generated_at = data.get("generated_at", "")
    except (ValueError, KeyError, TypeError):
        # A 200 that is not the feed (captive portal, wrong URL) must not read as "nobody home".
        return (None, FetchError("parse", "Bad response"))

    now_epoch = _parse_iso(generated_at)
    people = []
    for p in raw_people:
        loc = p.get("location")
        if loc is None:
            continue
        last_seen = p.get("last_seen_at")
        if last_seen and now_epoch:
            seen_epoch = _parse_iso(last_seen)
            if seen_epoch and (now_epoch - seen_epoch) >= stale_s:
                continue
        people.append({
            "name": p.get("name", "?"),
            "floor": loc.get("floor_name"),
            "zone": loc.get("zone_name"),
        })
    return (people, None)


def _parse_iso(s):
    """ISO 8601 -> epoch seconds on the device's own epoch (only differences are used)."""
    try:
        import utime
        return utime.mktime((int(s[0:4]), int(s[5:7]), int(s[8:10]),
                             int(s[11:13]), int(s[14:16]), int(s[17:19]), 0, 0))
    except Exception:
        return None
