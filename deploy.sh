#!/usr/bin/env bash
# Push firmware and/or config to the Pico, restart it, and show the boot log.
#
#   ./deploy.sh              code + config   (default)
#   ./deploy.sh code         code only
#   ./deploy.sh config       config.py only
#   ./deploy.sh all          code + config + CA cert (first install)
#   ./deploy.sh status       just show the log (no copy, no restart)
#
# Env: PORT=/dev/tty.usbmodemXXXX  (auto-detected if unset)
#      MPR_VENV=~/.venvs/mpremote   (created and filled on first run if mpremote is not on PATH)
#      LOG_SECONDS=40               (how long to watch the log; 0 to skip)
set -euo pipefail
cd "$(dirname "$0")"

MODE="${1:-default}"
LOG_SECONDS="${LOG_SECONDS:-40}"
CODE=(boot.py main.py api.py secure_http.py display.py renderer.py wifi.py epd_2in13b_v4.py font5x8.py)

# --- tools -----------------------------------------------------------------
if command -v mpremote >/dev/null 2>&1 && python3 -c "import serial" 2>/dev/null; then
  MPR=mpremote; PY=python3
else
  VENV="${MPR_VENV:-$HOME/.venvs/mpremote}"
  if [ ! -x "$VENV/bin/mpremote" ]; then
    echo "Setting up mpremote in $VENV"
    python3 -m venv "$VENV" && "$VENV/bin/pip" install -q mpremote
  fi
  MPR="$VENV/bin/mpremote"; PY="$VENV/bin/python"
fi

PORT="${PORT:-$(ls /dev/tty.usbmodem* /dev/ttyACM* 2>/dev/null | head -1 || true)}"
[ -n "$PORT" ] || { echo "No Pico found (looked for /dev/tty.usbmodem*, /dev/ttyACM*). Set PORT=..." >&2; exit 1; }
echo "Device: $PORT"

[ -f config.py ] || [ "$MODE" = status ] || { echo "config.py missing: cp config.example.py config.py and fill it in" >&2; exit 1; }

# --- helpers ---------------------------------------------------------------
interrupt() {   # Ctrl-C twice: stop the running main loop so mpremote can take over
  "$PY" - "$PORT" <<'PYEOF'
import sys, time, serial
s = serial.Serial(sys.argv[1], 115200, timeout=1)
s.write(b"\x03\x03"); time.sleep(1); s.close()
PYEOF
}

mpr() { "$MPR" connect "$PORT" resume "$@"; }   # 'resume': do not soft-reset (that would restart the loop)

watch_log() {
  [ "$LOG_SECONDS" -gt 0 ] || return 0
  echo "--- boot log (${LOG_SECONDS}s) ---"
  "$PY" - "$PORT" "$LOG_SECONDS" <<'PYEOF'
import sys, time, serial
s = serial.Serial(sys.argv[1], 115200, timeout=1)
end = time.time() + int(sys.argv[2]); out = b""
while time.time() < end:
    out += s.read(200)
print(out.decode(errors="replace")[-600:])
PYEOF
}

# --- run -------------------------------------------------------------------
if [ "$MODE" = status ]; then watch_log; exit 0; fi

case "$MODE" in
  default) FILES=("${CODE[@]}" config.py) ;;
  code)    FILES=("${CODE[@]}") ;;
  config)  FILES=(config.py) ;;
  all)     FILES=("${CODE[@]}" config.py) ; [ -f isrgrootx1.der ] && FILES+=(isrgrootx1.der) ;;
  *) echo "Usage: $0 [code|config|all|status]" >&2; exit 2 ;;
esac

for try in 1 2 3; do
  interrupt
  if mpr cp "${FILES[@]}" : ; then break; fi
  [ "$try" = 3 ] && { echo "Copy failed 3 times. Unplug/replug the Pico and retry." >&2; exit 1; }
  echo "Retrying ($try)..."
done

mpr exec "import machine; machine.soft_reset()" >/dev/null 2>&1 || true
echo "Restarted."
watch_log
