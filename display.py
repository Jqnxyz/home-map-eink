from epd_2in13b_v4 import EPD
import config
import renderer


_epd = None
_awake = False


def _ensure_awake():
    """Init the display if it's asleep or not yet created."""
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


def update(people, generated_at, error=None):
    """Render and display presence data, then sleep the display."""
    _ensure_awake()
    renderer.render(_epd.fb_black, _epd.fb_red, people, generated_at, error)
    _epd.display()
    sleep()


def sleep():
    """Put the display into low-power sleep."""
    global _awake
    if _epd and _awake:
        _epd.sleep()
        _awake = False


def show_message(line1, line2=""):
    """Show a simple status message, then sleep the display."""
    _ensure_awake()
    _epd.fb_black.fill(0xFF)
    _epd.fb_red.fill(0xFF)
    _epd.fb_black.text(line1, 10, 40, 0x00)
    if line2:
        _epd.fb_black.text(line2, 10, 56, 0x00)
    _epd.display()
    sleep()
