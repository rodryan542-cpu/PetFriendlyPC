"""Player account: a name plus a friend code. Not tied to a machine."""
from __future__ import annotations

import random

from game_data import new_player_id

CODE_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def normalize_code(raw: str) -> str:
    allowed = set(CODE_CHARS)
    return "".join(c for c in str(raw or "").upper() if c in allowed)[:6]


def new_friend_code() -> str:
    return "".join(random.choice(CODE_CHARS) for _ in range(6))


def ensure_account(save: dict) -> None:
    pid = str(save.get("player_id") or "")
    if len(pid) < 8:
        save["player_id"] = new_player_id()
    code = normalize_code(save.get("friend_code") or "")
    if len(code) != 6:
        save["friend_code"] = new_friend_code()
    else:
        save["friend_code"] = code


def my_code(save: dict) -> str:
    ensure_account(save)
    return str(save.get("friend_code") or "")
