from epd_2in13b_v4 import EPD
import config
import renderer


_epd = None
_awake = False
_last_snapshot = None


def _ensure_awake():
    global _epd, _awake
    if _epd is None:
        _epd = EPD(
            rst=config.RST_PIN,
            dc=config.DC_PIN,
            cs=config.CS_PIN,
            busy=config.BUSY_PIN,
        )
    if not _awake:
        _epd.init()
        _awake = True


def _make_snapshot(people):
    """Create a comparable snapshot of the presence data."""
    if people is None:
        return None
    result = []
    for p in people:
        result.append((p.get("name", "?"), p.get("floor"), p.get("zone")))
    result.sort()
    return tuple(result)


def update(people, error=None):
    """Render and display presence data only if changed. Returns True if refreshed."""
    global _last_snapshot
    snap = _make_snapshot(people)
    if snap == _last_snapshot:
        return False
    _last_snapshot = snap
    _ensure_awake()
    renderer.render(_epd.fb_black, _epd.fb_red, people, error)
    _epd.display()
    sleep()
    return True


def sleep():
    global _awake
    if _epd and _awake:
        _epd.sleep()
        _awake = False


def show_message(line1, line2=""):
    global _last_snapshot
    _last_snapshot = None
    _ensure_awake()
    _epd.fb_black.fill(0xFF)
    _epd.fb_red.fill(0xFF)
    import font5x8 as font
    font.draw_text(_epd.fb_black, 10, 40, line1)
    if line2:
        font.draw_text(_epd.fb_black, 10, 56, line2)
    _epd.display()
    sleep()
