# Waveshare 2.13" e-Paper (B) V4 driver for Raspberry Pi Pico
# Landscape orientation only, 250x122 pixels

from machine import Pin, SPI
import framebuf
import utime

EPD_WIDTH = 122
EPD_HEIGHT = 250


class EPD:
    def __init__(self, rst=12, dc=8, cs=9, busy=13):
        self.reset_pin = Pin(rst, Pin.OUT)
        self.busy_pin = Pin(busy, Pin.IN, Pin.PULL_UP)
        self.cs_pin = Pin(cs, Pin.OUT)
        self.dc_pin = Pin(dc, Pin.OUT)

        self.epd_w = EPD_WIDTH if EPD_WIDTH % 8 == 0 else (EPD_WIDTH // 8 + 1) * 8
        self.epd_h = EPD_HEIGHT

        # Landscape dimensions for framebuf
        self.width = self.epd_h   # 250
        self.height = self.epd_w  # 128

        self.spi = SPI(1)
        self.spi.init(baudrate=4_000_000)

        # Framebuffers: landscape MONO_VLSB
        buf_size = self.epd_h * self.epd_w // 8
        self.buf_black = bytearray(buf_size)
        self.buf_red = bytearray(buf_size)
        self.fb_black = framebuf.FrameBuffer(self.buf_black, self.width, self.height, framebuf.MONO_VLSB)
        self.fb_red = framebuf.FrameBuffer(self.buf_red, self.width, self.height, framebuf.MONO_VLSB)

    def _cmd(self, c):
        self.dc_pin.value(0)
        self.cs_pin.value(0)
        self.spi.write(bytearray([c]))
        self.cs_pin.value(1)

    def _data(self, d):
        self.dc_pin.value(1)
        self.cs_pin.value(0)
        self.spi.write(bytearray([d]))
        self.cs_pin.value(1)

    def _wait(self):
        while self.busy_pin.value() == 1:
            utime.sleep_ms(10)
        utime.sleep_ms(20)

    def init(self):
        # Hardware reset
        self.reset_pin.value(1)
        utime.sleep_ms(50)
        self.reset_pin.value(0)
        utime.sleep_ms(2)
        self.reset_pin.value(1)
        utime.sleep_ms(50)

        self._wait()
        self._cmd(0x12)  # SW reset
        self._wait()

        self._cmd(0x01)  # Driver output control
        self._data(0xF9)
        self._data(0x00)
        self._data(0x00)

        self._cmd(0x11)  # Data entry mode: landscape
        self._data(0x07)

        # Set window
        self._cmd(0x44)
        self._data(0x00)
        self._data((self.epd_w - 1) >> 3)
        self._cmd(0x45)
        self._data(0x00)
        self._data(0x00)
        self._data((self.epd_h - 1) & 0xFF)
        self._data(((self.epd_h - 1) >> 8) & 0xFF)

        # Set cursor
        self._cmd(0x4E)
        self._data(0x00)
        self._cmd(0x4F)
        self._data(0x00)
        self._data(0x00)

        self._cmd(0x3C); self._data(0x05)  # Border
        self._cmd(0x18); self._data(0x80)  # Temp sensor
        self._cmd(0x21); self._data(0x80); self._data(0x80)  # Display update ctrl

        self._wait()

    def _data_buf(self, buf):
        self.dc_pin.value(1)
        self.cs_pin.value(0)
        self.spi.write(buf)
        self.cs_pin.value(1)

    def _send_plane(self, cmd, buf):
        # Same byte order as before (column groups descending), but one SPI write per group
        # instead of one per byte: ~250x fewer transactions.
        self._cmd(cmd)
        mv = memoryview(buf)
        h = self.epd_h
        for j in range(self.epd_w // 8 - 1, -1, -1):
            self._data_buf(mv[j * h:(j + 1) * h])

    def display(self):
        self._send_plane(0x24, self.buf_black)
        self._send_plane(0x26, self.buf_red)
        self._cmd(0x20)
        self._wait()

    def sleep(self):
        """Deep sleep: the panel holds the image with no power. init() wakes it via hardware reset."""
        self._cmd(0x10)
        self._data(0x01)
        utime.sleep_ms(100)
