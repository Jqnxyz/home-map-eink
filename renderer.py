import config
import font5x8 as font

# Layout constants
SCREEN_W = 250
SCREEN_H = 122
Y_OFFSET = 6  # framebuffer is 128px tall, display is 122px
FLOOR_COL_W = 58
NAME_COL_X = FLOOR_COL_W + 3
NAME_COL_W = SCREEN_W - NAME_COL_X - 2
MAX_NAME_CHARS = NAME_COL_W // font.CHAR_W


def render(fb_black, fb_red, people, error=None):
    fb_black.fill(0xFF)
    fb_red.fill(0xFF)

    y0 = Y_OFFSET

    if error and people is None:
        font.draw_text(fb_red, 0, y0 + 10, error[:40])
        return

    floor_people = _group_by_floor(people or [])

    row_h = SCREEN_H // len(config.FLOORS)

    for i, floor in enumerate(config.FLOORS):
        y = y0 + i * row_h
        text_y = y + (row_h - font.HEIGHT) // 2

        # Floor label
        font.draw_text(fb_black, 2, text_y, floor)

        # Vertical divider
        fb_black.vline(FLOOR_COL_W, y, row_h, 0x00)

        # Names
        names = floor_people.get(floor, [])
        if names:
            _draw_names(fb_black, fb_red, names, NAME_COL_X, text_y)


def _group_by_floor(people):
    floors = {}
    for p in people:
        api_floor = p.get("floor")
        if api_floor is None:
            continue
        zone = p.get("zone", "")
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
            font.draw_text(fb_black, x, y, prefix)
            x += len(prefix) * font.CHAR_W
            font.draw_text(fb_red, x, y, disp_name)
            x += len(disp_name) * font.CHAR_W
        else:
            fb = fb_red if highlight else fb_black
            font.draw_text(fb, x, y, text)
            x += len(text) * font.CHAR_W

        remaining -= len(text)
