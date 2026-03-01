# Waveshare 2.13" e-Paper (B) V4 driver for Raspberry Pi Pico
# Adapted from https://github.com/waveshareteam/Pico_ePaper_Code
# Landscape orientation only, 250x122 pixels

from machine import Pin, SPI
import framebuf
import utime

EPD_WIDTH = 122
EPD_HEIGHT = 250


class EPD:
    """Landscape-mode driver for Waveshare 2.13" B V4 (250x122, black/white/red)."""

    def __init__(self, rst=12, dc=8, cs=9, busy=13):
        self.reset_pin = Pin(rst, Pin.OUT)
        self.busy_pin = Pin(busy, Pin.IN, Pin.PULL_UP)
        self.cs_pin = Pin(cs, Pin.OUT)
        self.dc_pin = Pin(dc, Pin.OUT)

        # Width rounded up to multiple of 8
        self.epd_w = EPD_WIDTH if EPD_WIDTH % 8 == 0 else (EPD_WIDTH // 8 + 1) * 8
        self.epd_h = EPD_HEIGHT

        # Landscape dimensions for framebuf
        self.width = self.epd_h   # 250
        self.height = self.epd_w  # 128

        # Use SPI1 with default pins (SCK=GP10, MOSI=GP11)
        self.spi = SPI(1)
        self.spi.init(baudrate=4_000_000)

        # Framebuffers: landscape MONO_VLSB
        buf_size = self.epd_h * self.epd_w // 8  # 4000
        self.buf_black = bytearray(buf_size)
        self.buf_red = bytearray(buf_size)
        self.fb_black = framebuf.FrameBuffer(self.buf_black, self.width, self.height, framebuf.MONO_VLSB)
        self.fb_red = framebuf.FrameBuffer(self.buf_red, self.width, self.height, framebuf.MONO_VLSB)

    def _write_cmd(self, cmd):
        self.dc_pin.value(0)
        self.cs_pin.value(0)
        self.spi.write(bytearray([cmd]))
        self.cs_pin.value(1)

    def _write_data(self, data):
        self.dc_pin.value(1)
        self.cs_pin.value(0)
        self.spi.write(bytearray([data]))
        self.cs_pin.value(1)

    def _write_data_buf(self, buf):
        self.dc_pin.value(1)
        self.cs_pin.value(0)
        self.spi.write(bytearray(buf))
        self.cs_pin.value(1)

    def _wait_busy(self):
        while self.busy_pin.value() == 1:
            utime.sleep_ms(10)
        utime.sleep_ms(20)

    def _reset(self):
        self.reset_pin.value(1)
        utime.sleep_ms(50)
        self.reset_pin.value(0)
        utime.sleep_ms(2)
        self.reset_pin.value(1)
        utime.sleep_ms(50)

    def _set_windows(self, x_start, y_start, x_end, y_end):
        self._write_cmd(0x44)
        self._write_data((x_start >> 3) & 0xFF)
        self._write_data((x_end >> 3) & 0xFF)
        self._write_cmd(0x45)
        self._write_data(y_start & 0xFF)
        self._write_data((y_start >> 8) & 0xFF)
        self._write_data(y_end & 0xFF)
        self._write_data((y_end >> 8) & 0xFF)

    def _set_cursor(self, x, y):
        self._write_cmd(0x4E)
        self._write_data(x & 0xFF)
        self._write_cmd(0x4F)
        self._write_data(y & 0xFF)
        self._write_data((y >> 8) & 0xFF)

    def init(self):
        self._reset()
        self._wait_busy()
        self._write_cmd(0x12)  # SW reset
        self._wait_busy()

        self._write_cmd(0x01)  # Driver output control
        self._write_data(0xF9)
        self._write_data(0x00)
        self._write_data(0x00)

        self._write_cmd(0x11)  # Data entry mode: landscape
        self._write_data(0x07)

        self._set_windows(0, 0, self.epd_w - 1, self.epd_h - 1)
        self._set_cursor(0, 0)

        self._write_cmd(0x3C)  # Border waveform
        self._write_data(0x05)

        self._write_cmd(0x18)  # Temperature sensor
        self._write_data(0x80)

        self._write_cmd(0x21)  # Display update control
        self._write_data(0x80)
        self._write_data(0x80)

        self._wait_busy()

    def _reorder_landscape(self, buf):
        """Reorder MONO_VLSB framebuffer bytes for landscape display."""
        out = bytearray(self.epd_h * self.epd_w // 8)
        idx = 0
        for j in range(self.epd_w // 8 - 1, -1, -1):
            for i in range(self.epd_h):
                out[idx] = buf[i + j * self.epd_h]
                idx += 1
        return out

    def display(self):
        """Send framebuffers to display with landscape byte reordering."""
        self._write_cmd(0x24)
        self._write_data_buf(self._reorder_landscape(self.buf_black))

        self._write_cmd(0x26)
        self._write_data_buf(self._reorder_landscape(self.buf_red))

        self._write_cmd(0x20)  # Activate display update
        self._wait_busy()

    def clear(self):
        self._write_cmd(0x24)
        self._write_data_buf(bytearray([0xFF] * (self.epd_h * self.epd_w // 8)))
        self._write_cmd(0x26)
        self._write_data_buf(bytearray([0xFF] * (self.epd_h * self.epd_w // 8)))
        self._write_cmd(0x20)
        self._wait_busy()

    def sleep(self):
        self._write_cmd(0x10)
        self._write_data(0x01)
        utime.sleep_ms(2000)
        self.reset_pin.value(0)
