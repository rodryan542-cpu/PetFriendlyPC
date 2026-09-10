"""Internet pals. Talk by friend code, any network."""
from __future__ import annotations

import json
import queue
import socket
import struct
import threading
import time
from typing import Callable

from account import normalize_code

HOSTS = (("broker.hivemq.com", 1883), ("test.mosquitto.org", 1883))
KEEP = 30
PREFIX = "pfpc/v1"


def _remain(n: int) -> bytes:
    out = bytearray()
    while True:
        b = n % 128
        n //= 128
        if n:
            b |= 128
        out.append(b)
        if not n:
            return bytes(out)


def _utf(s: str) -> bytes:
    raw = s.encode("utf-8")
    return struct.pack("!H", len(raw)) + raw


class PalNet:
    def __init__(self, card_fn: Callable[[], dict]) -> None:
        self.card_fn = card_fn
        self.events: queue.Queue = queue.Queue()
        self.here: dict[str, dict] = {}
        self.ok = False
        self._alive = False
        self._sock: socket.socket | None = None
        self._lock = threading.Lock()
        self._pkt = 1

    def start(self) -> None:
        if self._alive:
            return
        self._alive = True
        threading.Thread(target=self._run, daemon=True).start()

    def stop(self) -> None:
        self._alive = False
        sock = self._sock
        self._sock = None
        if sock:
            try:
                sock.close()
            except OSError:
                pass

    def online(self, code: str) -> dict | None:
        code = normalize_code(code)
        row = self.here.get(code)
        if not row:
            return None
        if time.time() - float(row.get("_at") or 0) > 40:
            return None
        return row

    def watch(self, code: str) -> None:
        code = normalize_code(code)
        if len(code) == 6 and self.ok:
            self._sub(f"{PREFIX}/{code}/here")

    def send(self, code: str, payload: dict) -> bool:
        code = normalize_code(code)
        if len(code) != 6:
            return False
        body = dict(payload)
        me = self.card_fn()
        body.setdefault("from", me.get("code"))
        body.setdefault("from_name", me.get("name"))
        return self._pub(f"{PREFIX}/{code}/in", json.dumps(body, separators=(",", ":")), retain=False)

    def _run(self) -> None:
        while self._alive:
            if self._connect():
                try:
                    self._pump()
                except OSError:
                    pass
            self.ok = False
            self._close()
            time.sleep(8)

    def _connect(self) -> bool:
        me = self.card_fn()
        code = normalize_code(me.get("code") or "")
        cid = "pf" + str(me.get("pid") or "x")[:18]
        for host, port in HOSTS:
            if not self._alive:
                return False
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(12)
            try:
                sock.connect((host, port))
            except OSError:
                sock.close()
                continue
            proto = _utf("MQTT") + bytes([4, 2]) + struct.pack("!H", KEEP) + _utf(cid)
            sock.sendall(bytes([0x10]) + _remain(len(proto)) + proto)
            try:
                hdr = self._read(sock, 2)
                if not hdr or hdr[0] != 0x20:
                    sock.close()
                    continue
                n, extra = self._dec_remain(sock, hdr[1])
                ack = extra + self._read(sock, max(0, n - len(extra)))
                if len(ack) < 2 or ack[1] != 0:
                    sock.close()
                    continue
            except OSError:
                sock.close()
                continue
            sock.settimeout(1.2)
            self._sock = sock
            self.ok = True
            if len(code) == 6:
                self._sub(f"{PREFIX}/{code}/in")
                self._hello(True)
            for other in me.get("watch") or []:
                oc = normalize_code(str(other))
                if len(oc) == 6 and oc != code:
                    self._sub(f"{PREFIX}/{oc}/here")
            return True
        return False

    def _pump(self) -> None:
        last_hello = 0.0
        last_ping = time.time()
        buf = b""
        while self._alive and self._sock:
            now = time.time()
            if now - last_hello > 12:
                self._hello(True)
                last_hello = now
            if now - last_ping > KEEP * 0.6:
                self._raw(bytes([0xC0, 0]))
                last_ping = now
            try:
                chunk = self._sock.recv(4096)
            except TimeoutError:
                continue
            except OSError:
                return
            if not chunk:
                return
            buf += chunk
            while len(buf) >= 2:
                kind = buf[0]
                n, used = self._peek_remain(buf[1:])
                if n < 0 or len(buf) < 1 + used + n:
                    break
                pkt = buf[1 + used : 1 + used + n]
                buf = buf[1 + used + n :]
                self._handle(kind, pkt)

    def _handle(self, kind: int, pkt: bytes) -> None:
        cmd = kind & 0xF0
        if cmd == 0x30:
            if len(pkt) < 2:
                return
            tlen = struct.unpack("!H", pkt[:2])[0]
            topic = pkt[2 : 2 + tlen].decode("utf-8", "replace")
            qos = (kind >> 1) & 0x3
            i = 2 + tlen + (2 if qos else 0)
            try:
                msg = json.loads(pkt[i:].decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return
            if not isinstance(msg, dict):
                return
            me = normalize_code((self.card_fn() or {}).get("code") or "")
            src = normalize_code(str(msg.get("from") or msg.get("code") or ""))
            if src and src == me:
                return
            if msg.get("t") == "hello" and src:
                msg["_at"] = time.time()
                self.here[src] = msg
            self.events.put(msg)
        elif cmd == 0xD0:
            pass

    def _hello(self, on: bool) -> None:
        me = self.card_fn()
        code = normalize_code(me.get("code") or "")
        if len(code) != 6:
            return
        body = {
            "t": "hello",
            "code": code,
            "from": code,
            "from_name": me.get("name") or "Trainer",
            "main": me.get("main") or "",
            "yard": int(me.get("yard") or 0),
            "pals": int(me.get("pals") or 0),
            "on": bool(on),
        }
        self._pub(f"{PREFIX}/{code}/here", json.dumps(body, separators=(",", ":")), retain=True)
        if on:
            self.here[code] = {**body, "_at": time.time()}

    def _sub(self, topic: str) -> None:
        self._pkt = (self._pkt % 65535) + 1
        body = struct.pack("!H", self._pkt) + _utf(topic) + bytes([0])
        self._raw(bytes([0x82]) + _remain(len(body)) + body)

    def _pub(self, topic: str, payload: str, retain: bool) -> bool:
        flags = 0x30 | (1 if retain else 0)
        body = _utf(topic) + payload.encode("utf-8")
        return self._raw(bytes([flags]) + _remain(len(body)) + body)

    def _raw(self, data: bytes) -> bool:
        sock = self._sock
        if not sock:
            return False
        try:
            with self._lock:
                sock.sendall(data)
            return True
        except OSError:
            return False

    def _close(self) -> None:
        sock = self._sock
        self._sock = None
        if sock:
            try:
                sock.close()
            except OSError:
                pass

    @staticmethod
    def _read(sock: socket.socket, n: int) -> bytes:
        out = b""
        while len(out) < n:
            chunk = sock.recv(n - len(out))
            if not chunk:
                raise OSError("closed")
            out += chunk
        return out

    @staticmethod
    def _dec_remain(sock: socket.socket, first: int) -> tuple[int, bytes]:
        mul = 1
        n = first & 127
        extra = b""
        cur = first
        while cur & 128:
            b = sock.recv(1)
            if not b:
                raise OSError("closed")
            extra += b
            cur = b[0]
            n += (cur & 127) * mul * 128
            mul *= 128
        return n, extra

    @staticmethod
    def _peek_remain(buf: bytes) -> tuple[int, int]:
        n = 0
        mul = 1
        for i, b in enumerate(buf[:4]):
            n += (b & 127) * mul
            mul *= 128
            if not (b & 128):
                return n, i + 1
        return -1, 0
