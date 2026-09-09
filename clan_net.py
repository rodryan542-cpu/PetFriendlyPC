"""LAN presence, invites, wars, 1v1. UDP on the local subnet."""
from __future__ import annotations

import json
import queue
import socket
import threading
import time
from typing import Callable

from game_data import NET_MAGIC, NET_PORT

BUDDIES = ("192.168.1.230", "192.168.1.86", "127.0.0.1")


class ClanNet:
    def __init__(self, presence_fn: Callable[[], dict]) -> None:
        self.presence_fn = presence_fn
        self.peers: dict[str, dict] = {}
        self.events: queue.Queue = queue.Queue()
        self._sock: socket.socket | None = None
        self._alive = False
        self.port = NET_PORT

    def start(self) -> None:
        if self._alive:
            return
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("", NET_PORT))
            self.port = NET_PORT
        except OSError:
            sock.bind(("", 0))
            self.port = int(sock.getsockname()[1])
        sock.settimeout(0.4)
        self._sock = sock
        self._alive = True
        threading.Thread(target=self._listen, daemon=True).start()
        threading.Thread(target=self._beacon, daemon=True).start()

    def stop(self) -> None:
        self._alive = False
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None

    def nearby(self) -> list[dict]:
        now = time.time()
        dead = [k for k, p in self.peers.items() if now - p.get("_at", 0) > 10]
        for k in dead:
            self.peers.pop(k, None)
        me = self.presence_fn().get("pid")
        return [p for p in self.peers.values() if p.get("pid") != me]

    def send_to(self, ip: str, payload: dict, port: int | None = None) -> None:
        if not self._sock or not ip:
            return
        raw = (NET_MAGIC + json.dumps(payload, separators=(",", ":"))).encode("utf-8")
        dest = port or NET_PORT
        try:
            self._sock.sendto(raw, (ip, int(dest)))
        except OSError:
            pass

    def send_peer(self, peer: dict, payload: dict) -> None:
        self.send_to(peer.get("ip", ""), payload, peer.get("port") or NET_PORT)

    def invite(self, peer: dict, clan: dict, from_name: str, from_pid: str) -> None:
        self.send_peer(
            peer,
            {
                "t": "invite",
                "to": peer["pid"],
                "from_pid": from_pid,
                "from_name": from_name,
                "clan": {
                    "id": clan["id"],
                    "code": clan["code"],
                    "name": clan["name"],
                    "crest": clan["crest"],
                    "leader": clan["leader"],
                },
            },
        )

    def reply_invite(self, ip: str, to_pid: str, ok: bool, member: dict | None, port: int | None = None) -> None:
        self.send_to(ip, {"t": "accept" if ok else "decline", "to": to_pid, "member": member}, port)

    def challenge(self, peer: dict, snap: dict) -> None:
        body = dict(snap)
        body["t"] = "chal"
        body["to"] = peer["pid"]
        self.send_peer(peer, body)

    def chal_reply(self, peer: dict, ok: bool, snap: dict) -> None:
        body = dict(snap)
        body["t"] = "chal_ok" if ok else "chal_no"
        body["to"] = peer.get("pid") or peer.get("from_pid")
        self.send_peer(peer, body)

    def pvp_act(self, peer: dict, mid: str, dmg: int, name: str) -> None:
        self.send_peer(peer, {"t": "pvp_act", "to": peer.get("pid"), "mid": mid, "dmg": dmg, "name": name})

    def chat(self, text: str, from_name: str, from_pid: str) -> None:
        self._broadcast({"t": "chat", "from_name": from_name, "from_pid": from_pid, "text": text[:40]})

    def raid_q(self, queued: bool, from_name: str, from_pid: str, power: int) -> None:
        self._broadcast({"t": "raid_q", "queued": bool(queued), "from_name": from_name, "from_pid": from_pid, "power": int(power)})

    def raid_go(self, seed: int, boss_id: str, members: list) -> None:
        self._broadcast({"t": "raid_go", "seed": int(seed), "boss": boss_id, "members": members[:4]})

    def raid_hit(self, dmg: int, name: str, from_pid: str, ehp: int, wave: int) -> None:
        self._broadcast({"t": "raid_hit", "dmg": int(dmg), "name": name, "from_pid": from_pid, "ehp": int(ehp), "wave": int(wave)})

    def raid_over(self, won: bool, loot: int) -> None:
        self._broadcast({"t": "raid_over", "won": bool(won), "loot": int(loot)})

    def war(self, ip: str, to_pid: str, my_power: int, clan_name: str, seed: int, port: int | None = None) -> None:
        self.send_to(ip, {"t": "war", "to": to_pid, "power": my_power, "clan": clan_name, "seed": seed}, port)

    def war_result(self, ip: str, to_pid: str, we_won: bool, seed: int, port: int | None = None) -> None:
        self.send_to(ip, {"t": "war_ack", "to": to_pid, "won": we_won, "seed": seed}, port)

    def _broadcast(self, payload: dict) -> None:
        if not self._sock:
            return
        raw = (NET_MAGIC + json.dumps(payload, separators=(",", ":"))).encode("utf-8")
        for dest in ("255.255.255.255", "192.168.1.255"):
            try:
                self._sock.sendto(raw, (dest, NET_PORT))
            except OSError:
                pass
        known = {p.get("ip") for p in self.peers.values() if p.get("ip")}
        for ip in set(BUDDIES) | known:
            if not ip:
                continue
            try:
                self._sock.sendto(raw, (ip, NET_PORT))
            except OSError:
                pass

    def _beacon(self) -> None:
        while self._alive:
            body = dict(self.presence_fn())
            body["t"] = "hello"
            body["port"] = self.port
            self._broadcast(body)
            time.sleep(1.2)

    def _listen(self) -> None:
        while self._alive and self._sock:
            try:
                data, addr = self._sock.recvfrom(4096)
            except (TimeoutError, OSError):
                continue
            if not data.startswith(NET_MAGIC.encode("utf-8")):
                continue
            try:
                msg = json.loads(data[len(NET_MAGIC) :].decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            if not isinstance(msg, dict):
                continue
            me = self.presence_fn().get("pid")
            kind = msg.get("t")
            if kind == "hello":
                pid = msg.get("pid")
                if not pid or pid == me:
                    continue
                msg["ip"] = addr[0]
                msg["port"] = int(msg.get("port") or addr[1] or NET_PORT)
                msg["_at"] = time.time()
                self.peers[pid] = msg
                continue
            if msg.get("to") not in (None, me):
                continue
            msg["ip"] = addr[0]
            msg["port"] = int(msg.get("port") or addr[1] or NET_PORT)
            self.events.put(msg)
