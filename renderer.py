import config

# Layout constants
SCREEN_W = 250
SCREEN_H = 122
HEADER_H = 12
FLOOR_COL_W = 56
NAME_COL_X = FLOOR_COL_W + 4
NAME_COL_W = SCREEN_W - NAME_COL_X - 2
CHAR_W = 8
CHAR_H = 8
MAX_NAME_CHARS = NAME_COL_W // CHAR_W


def render(fb_black, fb_red, people, generated_at, error=None):
    """Render the presence display onto the two framebuffers.

    Args:
        fb_black: FrameBuffer for black layer
        fb_red: FrameBuffer for red layer
        people: list of person dicts, or None if error
        generated_at: timestamp string from API
        error: error message string, or None
    """
    fb_black.fill(0xFF)  # white background
    fb_red.fill(0xFF)

    # Header
    fb_black.text("PRESENCE", 0, 2, 0x00)

    if error and people is None:
        # Show error below header
        fb_red.text(error[:30], 0, HEADER_H + 10, 0x00)
        return

    # Timestamp in top-right
    time_str = _format_time(generated_at)
    if time_str:
        tx = SCREEN_W - len(time_str) * CHAR_W
        fb_black.text(time_str, tx, 2, 0x00)

    # Separator line
    fb_black.hline(0, HEADER_H - 1, SCREEN_W, 0x00)

    # Group people by floor
    floor_people = _group_by_floor(people or [])

    # Draw floor rows
    body_h = SCREEN_H - HEADER_H
    row_h = body_h // len(config.FLOORS)

    for i, floor in enumerate(config.FLOORS):
        y = HEADER_H + i * row_h
        text_y = y + (row_h - CHAR_H) // 2  # vertically center text

        # Floor name
        fb_black.text(floor, 2, text_y, 0x00)

        # Vertical divider
        fb_black.vline(FLOOR_COL_W, y, row_h, 0x00)

        # Row separator (except last)
        if i < len(config.FLOORS) - 1:
            fb_black.hline(0, y + row_h - 1, SCREEN_W, 0x00)

        # Names
        names = floor_people.get(floor, [])
        if not names:
            continue

        _draw_names(fb_black, fb_red, names, NAME_COL_X, text_y)


def _format_time(generated_at):
    """Extract HH:MM from an ISO timestamp string."""
    if not generated_at:
        return ""
    try:
        # Handle "2024-01-15T14:32:00Z" or similar
        t_idx = generated_at.index("T")
        time_part = generated_at[t_idx + 1:t_idx + 6]  # "14:32"
        return time_part
    except (ValueError, IndexError):
        return ""


def _group_by_floor(people):
    """Group present people by floor name. Skip people with no location."""
    floors = {}
    for p in people:
        floor = p.get("floor")
        if floor is None:
            continue
        name = p.get("name", "?")
        zone = p.get("zone", "")
        highlight = (zone == config.HIGHLIGHT_ZONE)
        if floor not in floors:
            floors[floor] = []
        floors[floor].append((name, highlight))
    return floors


def _draw_names(fb_black, fb_red, names, x, y):
    """Draw comma-separated names, red for highlighted ones, truncating if needed."""
    remaining = MAX_NAME_CHARS
    first = True

    for name, highlight in names:
        prefix = "" if first else ", "
        text = prefix + name
        first = False

        if len(text) > remaining:
            # Truncate
            if remaining > 3:
                trunc = text[:remaining - 3] + "..."
                fb = fb_red if highlight else fb_black
                fb.text(trunc, x, y, 0x00)
                x += len(trunc) * CHAR_W
            break

        fb = fb_red if highlight else fb_black
        # Draw prefix in black if highlighted name has a prefix
        if highlight and prefix:
            fb_black.text(prefix, x, y, 0x00)
            x += len(prefix) * CHAR_W
            fb_red.text(name, x, y, 0x00)
            x += len(name) * CHAR_W
        else:
            fb.text(text, x, y, 0x00)
            x += len(text) * CHAR_W

        remaining -= len(text)
