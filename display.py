from epd_2in13b_v4 import EPD
import config
import renderer


_epd = None


def wake():
    """Initialize the e-ink display."""
    global _epd
    _epd = EPD(
        rst=config.RST_PIN,
        dc=config.DC_PIN,
        cs=config.CS_PIN,
        busy=config.BUSY_PIN,
    )
    _epd.init()
    _epd.clear()


def update(people, generated_at, error=None):
    """Render and display presence data."""
    global _epd
    _epd.init()
    renderer.render(_epd.fb_black, _epd.fb_red, people, generated_at, error)
    _epd.display()


def sleep():
    """Put the display into low-power sleep."""
    global _epd
    if _epd:
        _epd.sleep()


def show_message(line1, line2=""):
    """Show a simple status message (e.g. 'Connecting...')."""
    global _epd
    _epd.init()
    _epd.fb_black.fill(0xFF)
    _epd.fb_red.fill(0xFF)
    _epd.fb_black.text(line1, 10, 40, 0x00)
    if line2:
        _epd.fb_black.text(line2, 10, 56, 0x00)
    _epd.display()
