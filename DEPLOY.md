# Deploying to the Pico

How to push firmware or config changes to the device from a Mac. Tested with MicroPython 1.27 on a Pico 2 W.

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
