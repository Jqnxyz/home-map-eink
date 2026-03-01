import urequests
import ujson


def fetch_presence(url, timeout=10):
    """Fetch presence data from the API.

    Returns (people_list, generated_at) on success,
    or (None, error_message) on failure.

    Each person in people_list is a dict with at least:
      - name: str
      - floor: str or None
      - zone: str or None
    """
    response = None
    try:
        response = urequests.get(url, timeout=timeout)
        data = ujson.loads(response.text)
        people = data.get("people", [])
        generated_at = data.get("generated_at", "")
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
