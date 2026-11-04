# Deploying to the Pico

How to push firmware or config changes to the device from a Mac. Tested with MicroPython 1.27 on a Pico 2 W.

## Quick way: `./deploy.sh`

```bash
./deploy.sh            # code + config, restart, show boot log
./deploy.sh code       # code only
./deploy.sh config     # config.py only
./deploy.sh all        # first install: code + config + CA cert
./deploy.sh status     # just watch the log
```

It finds the Pico, installs `mpremote` into `~/.venvs/mpremote` if needed, interrupts the running loop, copies, restarts
and prints the log (retries the copy up to 3 times). Set `PORT=` if auto-detection picks the wrong device, and
`LOG_SECONDS=0` to skip the log. The manual steps below are what it does.

## One-time setup

```bash
python3 -m venv ~/.venvs/mpremote
~/.venvs/mpremote/bin/pip install mpremote
alias mpr='~/.venvs/mpremote/bin/mpremote connect /dev/tty.usbmodem*'   # your port: ls /dev/tty.usbmodem*
```

Then, in this folder:

1. `cp config.example.py config.py` and fill it in (WiFi, `API_URL`, `FEED_TOKEN`, floor mapping). `config.py` is gitignored.
2. Get the server CA: `curl -o isrgrootx1.der https://letsencrypt.org/certs/isrgrootx1.der` (Let's Encrypt; other CA, use its root).
   Check `openssl x509 -inform der -in isrgrootx1.der -noout -subject -fingerprint -sha256`.
3. Create the feed token: server Settings > Access > Feed access tokens (leave "Allow the token in the URL" unticked) and paste it into `FEED_TOKEN`.

## Pushing changes

The firmware runs its main loop forever, so `mpremote` cannot get control by default
("could not enter raw repl"). Do this every time:

1. Interrupt the loop. Easiest: unplug and replug the Pico, then run the next step within a few seconds. Or send Ctrl-C twice
   over the serial port.
2. Use `resume` so `mpremote` does not soft-reset the board (which would restart the loop):

   ```bash
   # everything (first install, or code changes)
   mpr resume cp boot.py main.py api.py secure_http.py config.py display.py renderer.py wifi.py \
     epd_2in13b_v4.py font5x8.py isrgrootx1.der :

   # config only
   mpr resume cp config.py :
   ```
3. Restart: press the Pico's reset button or replug it. (`mpr resume exec "import machine; machine.soft_reset()"` also works.)

## Copy-paste sequence (what I run)

`pyserial` comes with `mpremote`. Set the two variables once per shell, then run the steps in order.

```bash
export PORT=/dev/tty.usbmodem21201            # ls /dev/tty.usbmodem*
export PY=~/.venvs/mpremote/bin                # the venv from the one-time setup
cd ~/Projects/home-map-eink
```

1. Stop the running loop (Ctrl-C twice over serial):

```bash
$PY/python -c "import serial,time; s=serial.Serial('$PORT',115200,timeout=1); s.write(b'\x03\x03'); time.sleep(1); s.close()"
```

2. Copy files (`resume` stops mpremote from soft-resetting and restarting the loop). Code only, or config only, or both:

```bash
$PY/mpremote connect $PORT resume cp main.py api.py display.py renderer.py font5x8.py wifi.py secure_http.py epd_2in13b_v4.py boot.py :
$PY/mpremote connect $PORT resume cp config.py :
```

3. Restart the program:

```bash
$PY/mpremote connect $PORT resume exec "import machine; machine.soft_reset()"
```

4. Watch the log for ~40 s (expect `WiFi up: ...` then `Display refreshed`):

```bash
$PY/python -c "import serial,time; s=serial.Serial('$PORT',115200,timeout=1); e=time.time()+40; o=b''
while time.time()<e: o+=s.read(200)
print(o.decode(errors='replace')[-400:])"
```

If a step fails with `could not enter raw repl`, repeat step 1 and retry. Add `isrgrootx1.der` to the copy list only the first time.

## Checking it

Quick fetch test without waiting for the loop (note `config` may be cached, so drop it first):

```bash
mpr resume exec "
import sys; sys.modules.pop('config', None)
import config, api
ca = open(config.CA_CERT_FILE, 'rb').read()
p, e = api.fetch_presence(config.API_URL, 300, config.FEED_TOKEN or None, ca)
print(len(p) if p is not None else None, e.kind if e else None)"
```

Expected: a number of people and `None`. Normal boot output is `WiFi up: <ip>` then `Display refreshed`.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `could not enter raw repl` | Loop is running. Replug, then use `resume` (above). |
| Panel: "Token rejected" | Empty/wrong/revoked `FEED_TOKEN`, or the config never reached the device. Re-copy `config.py`. |
| Panel: "Offline" + `net TLS...` | CA file missing/wrong, or the clock isn't set (needs WiFi + NTP). |
| Panel: "Config error" | `API_URL` not `https://`, token in the URL, or no `CA_CERT_FILE`. |
| Panel: "No WiFi" | Check SSID/password; the board resets and retries. |
| `exec` shows old config values | Python cached the module; pop it from `sys.modules` as above. |
