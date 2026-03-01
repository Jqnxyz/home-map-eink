import config

# Layout constants
SCREEN_W = 250
SCREEN_H = 122
Y_OFFSET = 6  # framebuffer is 128px tall, display is 122px
FLOOR_COL_W = 72
NAME_COL_X = FLOOR_COL_W + 4
NAME_COL_W = SCREEN_W - NAME_COL_X - 2
CHAR_W = 8
CHAR_H = 8
MAX_NAME_CHARS = NAME_COL_W // CHAR_W


def render(fb_black, fb_red, people, error=None):
    fb_black.fill(0xFF)
    fb_red.fill(0xFF)

    y0 = Y_OFFSET

    if error and people is None:
        fb_red.text(error[:30], 0, y0 + 10, 0x00)
        return

    floor_people = _group_by_floor(people or [])

    row_h = SCREEN_H // len(config.FLOORS)

    for i, floor in enumerate(config.FLOORS):
        y = y0 + i * row_h
        text_y = y + (row_h - CHAR_H) // 2

        # Floor label
        fb_black.text(floor, 2, text_y, 0x00)

        # Vertical divider
        fb_black.vline(FLOOR_COL_W, y, row_h, 0x00)

        # Names
        names = floor_people.get(floor, [])
        if names:
            _draw_names(fb_black, fb_red, names, NAME_COL_X, text_y)


def _group_by_floor(people):
    """Group present people by display row label using zone mapping."""
    floors = {}
    for p in people:
        api_floor = p.get("floor")
        if api_floor is None:
            continue
        zone = p.get("zone", "")
        # Try (floor, zone) mapping first, then floor-only fallback
        row = config.ZONE_MAP.get((api_floor, zone))
        if row is None:
            row = config.FLOOR_MAP.get(api_floor, api_floor)
        name = p.get("name", "?")
        highlight = (zone == config.HIGHLIGHT_ZONE)
        if row not in floors:
            floors[row] = []
        floors[row].append((name, highlight))
    return floors


def _draw_names(fb_black, fb_red, names, x, y):
    # Check if full names fit
    full_len = sum(len(n) for n, _ in names) + 2 * (len(names) - 1)
    truncate = full_len > MAX_NAME_CHARS

    remaining = MAX_NAME_CHARS
    first = True

    for name, highlight in names:
        disp_name = name[:3] if truncate else name
        prefix = "" if first else ", "
        text = prefix + disp_name
        first = False

        if len(text) > remaining:
            break

        if highlight and prefix:
            fb_black.text(prefix, x, y, 0x00)
            x += len(prefix) * CHAR_W
            fb_red.text(disp_name, x, y, 0x00)
            x += len(disp_name) * CHAR_W
        else:
            fb = fb_red if highlight else fb_black
            fb.text(text, x, y, 0x00)
            x += len(text) * CHAR_W

        remaining -= len(text)
