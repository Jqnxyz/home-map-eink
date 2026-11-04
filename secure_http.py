# Minimal HTTPS GET client for MicroPython.
#
# Why not urequests: it cannot verify the server certificate, follows nothing safely, has no
# body cap and no timeout. This client:
#   * refuses plain http:// when a token is supplied (a bearer token over http is readable by
#     anyone on the LAN),
#   * verifies the server certificate against a CA you provide (CA_CERT_FILE) and fails closed,
#   * sends the token only in the Authorization header, never in the URL,
#   * never follows redirects (a redirect could carry the token to another host),
#   * uses HTTP/1.0 so the reply is never chunked, and caps the body size,
#   * never puts the token in an exception message.
import socket
import sys

try:
    import ssl
except ImportError:  # pragma: no cover
    ssl = None

MAX_BODY = 32768
MAX_HEADER = 4096


class HttpError(Exception):
    """Transport/protocol problem. The message never contains the token."""


def _send(s, data):
    # MicroPython sockets (plain and TLS) have write(); CPython sockets only have sendall().
    (s.write if hasattr(s, "write") else s.sendall)(data)


def _recv(s, n):
    return s.read(n) if hasattr(s, "read") else s.recv(n)


def parse_url(url):
    if url.startswith("https://"):
        scheme, rest, port = "https", url[8:], 443
    elif url.startswith("http://"):
        scheme, rest, port = "http", url[7:], 80
    else:
        raise HttpError("bad URL scheme")
    host, _, path = rest.partition("/")
    path = "/" + path
    if "@" in host:
        raise HttpError("credentials in URL")
    if ":" in host:
        host, _, p = host.rpartition(":")
        port = int(p)
    if not host:
        raise HttpError("bad URL host")
    return scheme, host, port, path


def _prep_ca(ca):
    if ca.startswith(b"-----BEGIN"):  # PEM
        if sys.implementation.name == "micropython":
            return ca if ca.endswith(b"\0") else ca + b"\0"  # mbedtls wants PEM NUL-terminated
        return ca.decode()  # CPython (host tests) takes PEM as str
    return ca  # DER


def _tls_context(ca_der, verify):
    if ssl is None:
        raise HttpError("no ssl module")
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    if verify:
        ctx.verify_mode = ssl.CERT_REQUIRED
        ctx.load_verify_locations(cadata=_prep_ca(ca_der))
    else:
        ctx.verify_mode = ssl.CERT_NONE
    return ctx


def get(url, token=None, ca_der=None, allow_insecure=False, timeout=15):
    """GET url. Returns (status, retry_after_or_None, body_bytes).

    token      sent as 'Authorization: Bearer ...' (https only unless allow_insecure)
    ca_der     DER or PEM bytes of the CA/server certificate to trust
    allow_insecure  permit http:// and unverified TLS (never needed in a normal setup)
    """
    scheme, host, port, path = parse_url(url)
    verify = ca_der is not None
    if scheme == "http" and not allow_insecure:
        raise HttpError("http:// refused (use https)")
    if scheme == "https" and not verify and not allow_insecure:
        raise HttpError("no CA cert: refusing unverified TLS")
    if "?" in path and "token=" in path:
        raise HttpError("token in URL not allowed")

    addr = socket.getaddrinfo(host, port, socket.AF_INET)[0][-1]
    s = socket.socket()
    try:
        s.settimeout(timeout)
        s.connect(addr)
        if scheme == "https":
            s = _tls_context(ca_der, verify).wrap_socket(s, server_hostname=host)
        req = "GET %s HTTP/1.0\r\nHost: %s\r\nAccept: application/json\r\nAccept-Encoding: identity\r\nConnection: close\r\nUser-Agent: home-map-eink\r\n" % (path, host)
        if token:
            req += "Authorization: Bearer %s\r\n" % token
        _send(s, (req + "\r\n").encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = _recv(s, 512)
            if not chunk:
                raise HttpError("truncated header")
            buf += chunk
            if len(buf) > MAX_HEADER + MAX_BODY:
                raise HttpError("header too large")
        head, _, body = buf.partition(b"\r\n\r\n")
        lines = head.decode().split("\r\n")
        parts = lines[0].split(" ", 2)
        if len(parts) < 2 or not parts[0].startswith("HTTP/"):
            raise HttpError("bad status line")
        status = int(parts[1])
        retry = None
        length = None
        for ln in lines[1:]:
            k, _, v = ln.partition(":")
            k = k.strip().lower()
            if k == "retry-after":
                try:
                    retry = int(v.strip())
                except ValueError:
                    pass
            elif k == "content-length":
                try:
                    length = int(v.strip())
                except ValueError:
                    raise HttpError("bad content-length")
        if length is not None and length > MAX_BODY:
            raise HttpError("body too large")
        while length is None or len(body) < length:
            chunk = _recv(s, 1024)
            if not chunk:
                break
            body += chunk
            if len(body) > MAX_BODY:
                raise HttpError("body too large")
        if length is not None and len(body) < length:
            raise HttpError("truncated body")
        return status, retry, body
    except OSError as e:
        raise HttpError("net " + str(e))
    finally:
        try:
            s.close()
        except Exception:
            pass
