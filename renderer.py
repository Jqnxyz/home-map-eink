import config
import font5x8 as font

SCREEN_W = 250
SCREEN_H = 122
Y0 = 8            # framebuffer is 128px tall, display is 122px; leave a margin at the top
COLS = 3
ROWS = 2
GAP = 3
TILE_W = (SCREEN_W - 4 - GAP * (COLS - 1)) // COLS   # 80
TILE_H = 57
MAX_TILES = COLS * ROWS
BLACK, WHITE = 0x00, 0xFF


def _cfg(name, default):
    return getattr(config, name, default)


def where(floor, zone):
    """Short location text for a tile (max 12 chars at the 1x font).

    ZONE_NICKNAMES[(floor, zone)] wins. Otherwise FLOOR_NICKNAMES[floor] + the zone, cut to fit.
    """
    nick = _cfg("ZONE_NICKNAMES", {}).get((floor, zone))
    if nick:
        return nick[:12]
    fl = _cfg("FLOOR_NICKNAMES", {}).get(floor, floor or "?")
    if not zone or zone == floor:
        return fl[:12]
    return (fl + " " + zone)[:12]


def fmt_time(hm):
    """'14:05' -> '2:05pm' when CLOCK_12H is on, else unchanged."""
    if not hm or not _cfg("CLOCK_12H", False):
        return hm
    h, m = int(hm[:2]), hm[3:5]
    return "%d:%s%s" % (h % 12 or 12, m, "pm" if h >= 12 else "am")


def display_name(name):
    """PEOPLE_NICKNAMES (case-insensitive on the real name) or the real name; cut to 6 chars at the 2x font."""
    nicks = _cfg("PEOPLE_NICKNAMES", {})
    low = name.lower()
    for real, nick in nicks.items():
        if real.lower() == low:
            return nick[:6]
    return name[:6]


def _floor_rank(floor):
    order = _cfg("FLOOR_ORDER", [])
    return order.index(floor) if floor in order else 50


def select_people(people):
    """Apply PEOPLE_ONLY / PEOPLE_HIDE / SHOW_AWAY and order by PEOPLE_PRIORITY.

    PEOPLE_PRIORITY only sets the order; it never overrides ONLY/HIDE/SHOW_AWAY (a stale priority person is still away).
    Order: priority names first (in the order listed, home or away), then everyone else who is
    home (highest floor first), then everyone else who is away.
    """
    only = [n.lower() for n in _cfg("PEOPLE_ONLY", [])]
    hide = [n.lower() for n in _cfg("PEOPLE_HIDE", [])]
    prio = [n.lower() for n in _cfg("PEOPLE_PRIORITY", [])]
    show_away = _cfg("SHOW_AWAY", True)

    out = []
    for p in people:
        key = p["name"].lower()
        if only and key not in only:
            continue
        if key in hide:
            continue
        if p.get("away") and not show_away:
            continue
        max_age = _cfg("AWAY_HIDE_AFTER_S", 0)
        if p.get("away") and max_age and (p.get("age_s") is None or p["age_s"] > max_age):
            continue   # away for too long (or never seen): drop the tile
        out.append(p)

    def sort_key(p):
        key = p["name"].lower()
        rank = prio.index(key) if key in prio else 999
        if p.get("away"):
            floor_idx = 99
        else:
            floor_idx = _floor_rank(p["floor"])
        return (rank, 1 if p.get("away") else 0, floor_idx, key)

    out.sort(key=sort_key)
    return out


def _dashed_rect(fb, x, y, w, h, dash=3, gap=3):
    """Rectangle outline drawn as dashes (the whole border, not a line inside a solid one)."""
    step = dash + gap
    for d in range(0, w, step):
        n = min(dash, w - d)
        fb.hline(x + d, y, n, BLACK)
        fb.hline(x + d, y + h - 1, n, BLACK)
    for d in range(0, h, step):
        n = min(dash, h - d)
        fb.fill_rect(x, y + d, 1, n, BLACK)
        fb.fill_rect(x + w - 1, y + d, 1, n, BLACK)


def _tile(fb_black, fb_red, x, y, p, moved):
    away = p.get("away")
    if moved:
        fb_red.fill_rect(x, y, TILE_W, TILE_H, BLACK)
        fb_text, fg = fb_red, WHITE          # erase red where the text goes -> white on red
    else:
        if away:
            _dashed_rect(fb_black, x, y, TILE_W, TILE_H)
        else:
            fb_black.rect(x, y, TILE_W, TILE_H, BLACK)
        fb_text, fg = fb_black, BLACK
    font.draw_text(fb_text, x + 5, y + 5, display_name(p["name"]), fg, 2, _cfg("NAME_FONT", "regular") == "bold")
    if away:
        loc = "Away"
    else:
        loc = where(p["floor"], p["zone"])
    font.draw_text(fb_text, x + 5, y + 27, loc, fg)
    if away and p.get("seen"):
        font.draw_text(fb_text, x + 5, y + 41, "seen " + fmt_time(p["seen"]), fg)


def render(fb_black, fb_red, people, moved=None):
    fb_black.fill(WHITE)
    fb_red.fill(WHITE)
    moved = moved or set()
    shown = select_people(people or [])
    extra = len(shown) - MAX_TILES
    if extra > 0:
        shown = shown[:MAX_TILES - 1]
    for i, p in enumerate(shown):
        x = 2 + (i % COLS) * (TILE_W + GAP)
        y = Y0 + (i // COLS) * (TILE_H + GAP)
        _tile(fb_black, fb_red, x, y, p, p["name"] in moved)
    if extra > 0:
        i = MAX_TILES - 1
        x = 2 + (i % COLS) * (TILE_W + GAP)
        y = Y0 + (i // COLS) * (TILE_H + GAP)
        fb_black.rect(x, y, TILE_W, TILE_H, BLACK)
        font.draw_text(fb_black, x + 5, y + 20, "+%d" % (extra + 1), BLACK, 3)


def render_status(fb_black, fb_red, title, lines):
    """Failure/status page: red title, then up to 6 detail lines."""
    fb_black.fill(WHITE)
    fb_red.fill(WHITE)
    font.draw_text(fb_red, 6, Y0 + 2, title[:20], BLACK, 2)
    fb_black.hline(6, Y0 + 22, SCREEN_W - 12, BLACK)
    y = Y0 + 30
    for ln in lines[:7]:
        font.draw_text(fb_black, 6, y, ln[:40])
        y += 12
