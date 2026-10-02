try:
    import urequests as requests
except ImportError:
    import requests

try:
    import ujson as json
except ImportError:
    import json


def fetch_presence(url, stale_s=300, token=None):
    """Fetch presence data from the API.

    token: optional feed token, sent as "Authorization: Bearer <token>". Only needed
    when the server requires sign-in to view the map; leave it None otherwise.

    Returns (people_list, generated_at) on success,
    or (None, error_message) on failure.

    Filters out people not seen within stale_s seconds.
    """
    response = None
    try:
        headers = {"Authorization": "Bearer " + token} if token else {}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            # A 401 body is valid JSON without "people"; do not mistake it for an empty house.
            return (None, "HTTP " + str(response.status_code))
        data = json.loads(response.text)
        raw_people = data.get("people", [])
        generated_at = data.get("generated_at", "")

        # Parse generated_at to epoch for staleness check
        now_epoch = _parse_iso(generated_at)

        people = []
        for p in raw_people:
            loc = p.get("location")
            if loc is None:
                continue

            # Check staleness
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

        return (people, generated_at)
    except OSError as e:
        return (None, "Net: " + str(e))
    except (ValueError, KeyError) as e:
        return (None, "Parse: " + str(e))
    finally:
        if response is not None:
            try:
                response.close()
            except Exception:
                pass


def _parse_iso(s):
    """Parse ISO 8601 timestamp to epoch seconds. Returns None on failure."""
    try:
        # "2026-03-01T08:12:54.102Z" or "2026-03-01T08:12:54Z"
        d = s[:10]
        t = s[11:19]
        year = int(d[0:4])
        month = int(d[5:7])
        day = int(d[8:10])
        hour = int(t[0:2])
        minute = int(t[3:5])
        second = int(t[6:8])
        # MicroPython's time epoch is 2000-01-01
        import utime
        return utime.mktime((year, month, day, hour, minute, second, 0, 0))
    except Exception:
        return None
