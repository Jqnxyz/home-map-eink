import sys
try:
    import main
except Exception as e:
    sys.print_exception(e)
    # Keep the error visible
    import utime
    utime.sleep(30)
