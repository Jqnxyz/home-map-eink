import utime
from machine import Pin, SPI
import framebuf

print("test: starting")
utime.sleep(2)

spi = SPI(1)
spi.init(baudrate=4_000_000)

rst = Pin(12, Pin.OUT)
dc = Pin(8, Pin.OUT)
cs = Pin(9, Pin.OUT)
busy = Pin(13, Pin.IN, Pin.PULL_UP)

def cmd(c):
    dc.value(0); cs.value(0); spi.write(bytearray([c])); cs.value(1)

def data(d):
    dc.value(1); cs.value(0); spi.write(bytearray([d])); cs.value(1)

def data_buf(buf):
    dc.value(1); cs.value(0); spi.write(bytearray(buf)); cs.value(1)

def wait():
    while busy.value() == 1:
        utime.sleep_ms(10)
    utime.sleep_ms(20)

# Reset
rst.value(1); utime.sleep_ms(50)
rst.value(0); utime.sleep_ms(2)
rst.value(1); utime.sleep_ms(50)

wait()
cmd(0x12)  # SW reset
wait()

cmd(0x01); data(0xF9); data(0x00); data(0x00)  # Driver output
cmd(0x11); data(0x07)  # Data entry mode (landscape)

# Set window
cmd(0x44); data(0x00); data(0x0F)  # X: 0-15
cmd(0x45); data(0x00); data(0x00); data(0xF9); data(0x00)  # Y: 0-249

cmd(0x4E); data(0x00)  # Cursor X
cmd(0x4F); data(0x00); data(0x00)  # Cursor Y

cmd(0x3C); data(0x05)  # Border
cmd(0x18); data(0x80)  # Temp sensor
cmd(0x21); data(0x80); data(0x80)  # Display update ctrl

wait()
print("test: init done")

# Create framebuffers
EPD_W = 128
EPD_H = 250
buf_size = EPD_H * EPD_W // 8

buf_black = bytearray(buf_size)
buf_red = bytearray(buf_size)
fb_black = framebuf.FrameBuffer(buf_black, EPD_H, EPD_W, framebuf.MONO_VLSB)
fb_red = framebuf.FrameBuffer(buf_red, EPD_H, EPD_W, framebuf.MONO_VLSB)

fb_black.fill(0xFF)
fb_red.fill(0xFF)
fb_black.text("BOOT TEST", 10, 20, 0x00)
fb_black.text("It works!", 10, 40, 0x00)

print("test: sending black buffer")
cmd(0x24)
for j in range(EPD_W // 8 - 1, -1, -1):
    for i in range(EPD_H):
        data(buf_black[i + j * EPD_H])

print("test: sending red buffer")
cmd(0x26)
for j in range(EPD_W // 8 - 1, -1, -1):
    for i in range(EPD_H):
        data(buf_red[i + j * EPD_H])

print("test: refresh")
cmd(0x20)
wait()
print("test: done!")
