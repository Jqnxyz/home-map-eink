import sys
import utime

try:
    import main  # runs the loop; only returns/raises on a fatal error
except Exception as e:
    sys.print_exception(e)
    utime.sleep(10)
    import machine
    machine.reset()  # never sit idle after a crash
