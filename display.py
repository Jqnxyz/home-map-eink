from epd_2in13b_v4 import EPD
import config
import renderer


_epd = None
_inited = False
_last_snapshot = None


def _ensure_ready():
    global _epd, _inited
    if _epd is None:
        _epd = EPD(
            rst=config.RST_PIN,
            dc=config.DC_PIN,
            cs=config.CS_PIN,
            busy=config.BUSY_PIN,
        )
    if not _inited:
        _epd.init()
        _inited = True


def _make_snapshot(people):
    if people is None:
        return None
    result = []
    for p in people:
        result.append((p.get("name", "?"), p.get("floor"), p.get("zone")))
    result.sort()
    return tuple(result)


def update(people, error=None):
    global _last_snapshot
    snap = _make_snapshot(people)
    if snap == _last_snapshot:
        return False
    _last_snapshot = snap
    _ensure_ready()
    renderer.render(_epd.fb_black, _epd.fb_red, people, error)
    _epd.display()
    return True


def show_message(line1, line2=""):
    global _last_snapshot
    _last_snapshot = None
    _ensure_ready()
    _epd.fb_black.fill(0xFF)
    _epd.fb_red.fill(0xFF)
    import font5x8 as font
    font.draw_text(_epd.fb_black, 10, 40, line1)
    if line2:
        font.draw_text(_epd.fb_black, 10, 56, line2)
    _epd.display()
