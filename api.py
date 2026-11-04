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


def fetch_presence(url, stale_s=300, token=None, ca_der=None, allow_insecure=False, tz_min=0):
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
        last_seen = p.get("last_seen_at")
        away = loc is None
        age = None
        if last_seen and now_epoch:
            seen_epoch = _parse_iso(last_seen)
            if seen_epoch:
                age = now_epoch - seen_epoch
        if not away and age is not None and age >= stale_s:
            away = True
        people.append({
            "name": _ascii(p.get("name", "?")),
            "floor": None if away else _ascii(loc.get("floor_name")),
            "zone": None if away else _ascii(loc.get("zone_name")),
            "away": away,
            "seen": _local_hm(last_seen, tz_min),
            "age_s": age,
        })
    return (people, None)


def _ascii(s):
    """The 5x8 font is ASCII-only: turn typographic quotes/dashes into plain ones so config keys can be plain too."""
    if not s:
        return s
    for a, b in (("\u2019", "'"), ("\u2018", "'"), ("\u201c", '"'), ("\u201d", '"'), ("\u2013", "-"), ("\u2014", "-")):
        s = s.replace(a, b)
    return s


def _local_hm(iso, tz_min):
    """'2026-03-01T08:12:54Z' -> 'HH:MM' shifted by tz_min minutes. None if unparseable."""
    try:
        m = (int(iso[11:13]) * 60 + int(iso[14:16]) + tz_min) % 1440
        return "%02d:%02d" % (m // 60, m % 60)
    except Exception:
        return None


def _parse_iso(s):
    """ISO 8601 -> epoch seconds on the device's own epoch (only differences are used)."""
    try:
        import utime
        return utime.mktime((int(s[0:4]), int(s[5:7]), int(s[8:10]),
                             int(s[11:13]), int(s[14:16]), int(s[17:19]), 0, 0))
    except Exception:
        return None
