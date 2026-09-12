"""Small dependency-free Chrome DevTools Protocol HTTP/WebSocket transport."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import socket
import ssl
import struct
import threading
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


class CdpTransportError(RuntimeError):
    """CDP discovery, framing, or protocol response failed."""


def http_json(endpoint: str, path: str, *, timeout: float = 5.0) -> Any:
    """Fetch one JSON value from a CDP HTTP discovery endpoint."""

    base = endpoint.rstrip("/") + "/"
    url = urljoin(base, path.lstrip("/"))
    request = Request(url, headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = response.read()
    except OSError as error:
        raise CdpTransportError(f"CDP HTTP request failed for {url}: {error}") from error
    try:
        return json.loads(payload.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise CdpTransportError(f"CDP endpoint returned invalid JSON at {url}") from error


def discover_targets(endpoint: str, *, timeout: float = 5.0) -> list[dict[str, Any]]:
    """Return normalized entries from CDP's ``/json/list`` endpoint."""

    payload = http_json(endpoint, "/json/list", timeout=timeout)
    if not isinstance(payload, list) or not all(isinstance(item, dict) for item in payload):
        raise CdpTransportError("CDP /json/list did not return a list of targets")
    return [dict(item) for item in payload]


def browser_version(endpoint: str, *, timeout: float = 5.0) -> dict[str, Any]:
    """Return CDP browser/version discovery metadata."""

    payload = http_json(endpoint, "/json/version", timeout=timeout)
    if not isinstance(payload, dict):
        raise CdpTransportError("CDP /json/version did not return an object")
    return dict(payload)


@dataclass(frozen=True, slots=True)
class CdpResponse:
    request_id: int
    result: dict[str, Any] | None
    error: dict[str, Any] | None


class CdpWebSocket:
    """Minimal synchronous RFC 6455 client suitable for local CDP targets."""

    def __init__(self, websocket_url: str, *, timeout: float = 10.0) -> None:
        self.websocket_url = websocket_url
        self.timeout = timeout
        self._socket: socket.socket | None = None
        self._next_id = 1
        self._lock = threading.Lock()

    def __enter__(self) -> "CdpWebSocket":
        self.connect()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        del exc_type, exc, traceback
        self.close()

    def connect(self) -> None:
        if self._socket is not None:
            return
        parsed = urlparse(self.websocket_url)
        if parsed.scheme not in {"ws", "wss"} or not parsed.hostname:
            raise CdpTransportError(f"invalid CDP WebSocket URL: {self.websocket_url}")
        port = parsed.port or (443 if parsed.scheme == "wss" else 80)
        stream = socket.create_connection((parsed.hostname, port), timeout=self.timeout)
        if parsed.scheme == "wss":
            context = ssl.create_default_context()
            stream = context.wrap_socket(stream, server_hostname=parsed.hostname)
        stream.settimeout(self.timeout)
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        host = parsed.hostname if parsed.port is None else f"{parsed.hostname}:{parsed.port}"
        request = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        ).encode("ascii")
        stream.sendall(request)
        response = _read_http_headers(stream)
        status = response.split(b"\r\n", 1)[0]
        if b" 101 " not in status:
            stream.close()
            raise CdpTransportError(
                f"CDP WebSocket upgrade failed: {status.decode('latin-1', errors='replace')}"
            )
        headers = _parse_headers(response)
        expected_accept = base64.b64encode(
            hashlib.sha1(
                (key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("ascii")
            ).digest()
        ).decode("ascii")
        if headers.get("sec-websocket-accept") != expected_accept:
            stream.close()
            raise CdpTransportError("CDP WebSocket returned an invalid accept key")
        self._socket = stream

    def close(self) -> None:
        stream, self._socket = self._socket, None
        if stream is not None:
            try:
                _send_frame(stream, 0x8, b"")
            except OSError:
                pass
            stream.close()

    def call(
        self, method: str, params: Mapping[str, Any] | None = None
    ) -> CdpResponse:
        """Send one CDP request and wait for the response with the same ID."""

        with self._lock:
            if self._socket is None:
                self.connect()
            assert self._socket is not None
            request_id = self._next_id
            self._next_id += 1
            payload = json.dumps(
                {"id": request_id, "method": method, "params": dict(params or {})},
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
            _send_frame(self._socket, 0x1, payload)
            while True:
                message = _receive_message(self._socket)
                try:
                    decoded = json.loads(message.decode("utf-8"))
                except (UnicodeError, json.JSONDecodeError) as error:
                    raise CdpTransportError("CDP WebSocket returned invalid JSON") from error
                if not isinstance(decoded, dict) or decoded.get("id") != request_id:
                    continue
                result = decoded.get("result")
                error_value = decoded.get("error")
                return CdpResponse(
                    request_id=request_id,
                    result=dict(result) if isinstance(result, dict) else None,
                    error=dict(error_value) if isinstance(error_value, dict) else None,
                )


def _read_http_headers(stream: socket.socket) -> bytes:
    result = bytearray()
    while b"\r\n\r\n" not in result:
        chunk = stream.recv(4096)
        if not chunk:
            raise CdpTransportError("CDP WebSocket closed during HTTP upgrade")
        result.extend(chunk)
        if len(result) > 64 * 1024:
            raise CdpTransportError("CDP WebSocket upgrade headers are too large")
    return bytes(result).split(b"\r\n\r\n", 1)[0]


def _parse_headers(response: bytes) -> dict[str, str]:
    headers: dict[str, str] = {}
    for line in response.split(b"\r\n")[1:]:
        if b":" not in line:
            continue
        name, value = line.split(b":", 1)
        headers[name.decode("latin-1").strip().lower()] = value.decode("latin-1").strip()
    return headers


def _send_frame(stream: socket.socket, opcode: int, payload: bytes) -> None:
    length = len(payload)
    first = 0x80 | opcode
    mask = os.urandom(4)
    if length < 126:
        header = struct.pack("!BB", first, 0x80 | length)
    elif length <= 0xFFFF:
        header = struct.pack("!BBH", first, 0x80 | 126, length)
    else:
        header = struct.pack("!BBQ", first, 0x80 | 127, length)
    masked = bytes(value ^ mask[index % 4] for index, value in enumerate(payload))
    stream.sendall(header + mask + masked)


def _recv_exact(stream: socket.socket, length: int) -> bytes:
    result = bytearray()
    while len(result) < length:
        chunk = stream.recv(length - len(result))
        if not chunk:
            raise CdpTransportError("CDP WebSocket closed unexpectedly")
        result.extend(chunk)
    return bytes(result)


def _receive_message(stream: socket.socket) -> bytes:
    fragments = bytearray()
    data_opcode: int | None = None
    while True:
        first, second = _recv_exact(stream, 2)
        final = bool(first & 0x80)
        opcode = first & 0x0F
        masked = bool(second & 0x80)
        length = second & 0x7F
        if length == 126:
            length = struct.unpack("!H", _recv_exact(stream, 2))[0]
        elif length == 127:
            length = struct.unpack("!Q", _recv_exact(stream, 8))[0]
        mask = _recv_exact(stream, 4) if masked else b""
        payload = _recv_exact(stream, length)
        if masked:
            payload = bytes(value ^ mask[index % 4] for index, value in enumerate(payload))
        if opcode == 0x8:
            raise CdpTransportError("CDP WebSocket closed")
        if opcode == 0x9:
            _send_frame(stream, 0xA, payload)
            continue
        if opcode == 0xA:
            continue
        if opcode in {0x1, 0x2}:
            data_opcode = opcode
            fragments.extend(payload)
        elif opcode == 0x0 and data_opcode is not None:
            fragments.extend(payload)
        else:
            raise CdpTransportError(f"unsupported CDP WebSocket opcode: {opcode}")
        if final:
            if data_opcode != 0x1:
                raise CdpTransportError("CDP returned a non-text WebSocket message")
            return bytes(fragments)
