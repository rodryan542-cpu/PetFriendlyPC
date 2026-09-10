"""Yard upgrades and friend book. Persist on save."""
from __future__ import annotations

import time

from account import normalize_code
from game_data import shop_cost

YARD_SLOTS = ("house", "bed", "tree", "shower", "bowl", "lamp", "fence", "pond", "toy")
YARD_PER_PAGE = 6
YARD_MAX = 5
CHEER_CD = 3 * 60
SNACK_CD = 2 * 60
HUNT_CD = 5 * 60
YARD_TINTS = (
    (255, 255, 255),
    (120, 170, 230),
    (230, 130, 180),
    (230, 190, 60),
)
BOND_TITLES = (
    (0, "STRANGER"),
    (1, "PAL"),
    (4, "BUDDY"),
    (8, "BESTIE"),
    (14, "RIDE OR DIE"),
)
VISIT_CD = 8 * 60
GIFT_CD = 4 * 60
GIFT_COINS = 400

YARD = {
    "house": (
        {"tier": 1, "name": "Crate Den", "cost": 40, "blurb": "A box. Hunger slows a bit."},
        {"tier": 2, "name": "Dog House", "cost": 180, "blurb": "Classic roof. Sleeps easier."},
        {"tier": 3, "name": "Cottage", "cost": 600, "blurb": "Real walls. Hunger barely moves."},
        {"tier": 4, "name": "Villa", "cost": 2400, "blurb": "A home. They stop looking lost."},
        {"tier": 5, "name": "Manor", "cost": 7200, "blurb": "A whole house. Hunger almost sleeps."},
    ),
    "bed": (
        {"tier": 1, "name": "Rag Pile", "cost": 28, "blurb": "Better than dirt."},
        {"tier": 2, "name": "Cushion", "cost": 140, "blurb": "Sleep heals mood."},
        {"tier": 3, "name": "Nest", "cost": 480, "blurb": "Deep sleep. Wake clean."},
        {"tier": 4, "name": "Canopy", "cost": 1800, "blurb": "Dreams that refill them."},
        {"tier": 5, "name": "Cloud Bed", "cost": 5600, "blurb": "Sleep like they own the sky."},
    ),
    "tree": (
        {"tier": 1, "name": "Sprout", "cost": 24, "blurb": "A stick with hope."},
        {"tier": 2, "name": "Sapling", "cost": 120, "blurb": "GO finds more coins."},
        {"tier": 3, "name": "Oak", "cost": 520, "blurb": "Shade and luck."},
        {"tier": 4, "name": "Sakura", "cost": 2000, "blurb": "Petals. Streets pay out."},
        {"tier": 5, "name": "World Tree", "cost": 6400, "blurb": "Coins fall when they walk."},
    ),
    "shower": (
        {"tier": 1, "name": "Bucket", "cost": 32, "blurb": "Dump water. It counts."},
        {"tier": 2, "name": "Hose", "cost": 150, "blurb": "Wash feels better."},
        {"tier": 3, "name": "Stall", "cost": 540, "blurb": "No more overwash."},
        {"tier": 4, "name": "Spa", "cost": 2100, "blurb": "Steam. Mood and shine."},
        {"tier": 5, "name": "Hot Spring", "cost": 6800, "blurb": "Wash becomes a party."},
    ),
    "bowl": (
        {"tier": 1, "name": "Tin Bowl", "cost": 20, "blurb": "Food sits. They eat more."},
        {"tier": 2, "name": "Dish", "cost": 110, "blurb": "Bigger scoops."},
        {"tier": 3, "name": "Stand", "cost": 400, "blurb": "No more stuffing as fast."},
        {"tier": 4, "name": "Fountain", "cost": 1600, "blurb": "Always a snack waiting."},
        {"tier": 5, "name": "Feast Table", "cost": 5200, "blurb": "Every meal lands bigger."},
    ),
    "lamp": (
        {"tier": 1, "name": "Candle", "cost": 22, "blurb": "A little light."},
        {"tier": 2, "name": "Lantern", "cost": 130, "blurb": "Mood drains slower."},
        {"tier": 3, "name": "Post", "cost": 460, "blurb": "The yard stays awake."},
        {"tier": 4, "name": "Neon", "cost": 1700, "blurb": "Night looks like a stage."},
        {"tier": 5, "name": "Constellation", "cost": 6000, "blurb": "Mood barely moves."},
    ),
    "fence": (
        {"tier": 1, "name": "Stick Fence", "cost": 26, "blurb": "A line in the dirt."},
        {"tier": 2, "name": "Picket", "cost": 140, "blurb": "A real yard. Luck ticks up."},
        {"tier": 3, "name": "Stone Wall", "cost": 500, "blurb": "Safe. Hunger holds."},
        {"tier": 4, "name": "Iron Gate", "cost": 1900, "blurb": "Nobody walks off with coins."},
        {"tier": 5, "name": "Bastion", "cost": 6200, "blurb": "The yard is a keep."},
    ),
    "pond": (
        {"tier": 1, "name": "Puddle", "cost": 24, "blurb": "They splash. A little clean."},
        {"tier": 2, "name": "Basin", "cost": 130, "blurb": "Wash hits harder."},
        {"tier": 3, "name": "Koi Pond", "cost": 520, "blurb": "Hygiene holds longer."},
        {"tier": 4, "name": "Spring", "cost": 2000, "blurb": "The water does half the work."},
        {"tier": 5, "name": "Lagoon", "cost": 6500, "blurb": "They come back shining."},
    ),
    "toy": (
        {"tier": 1, "name": "Stick Toy", "cost": 18, "blurb": "Something to chew."},
        {"tier": 2, "name": "Ball Bin", "cost": 120, "blurb": "Mood holds a bit."},
        {"tier": 3, "name": "Play Set", "cost": 460, "blurb": "Play hits harder."},
        {"tier": 4, "name": "Arcade", "cost": 1800, "blurb": "They stay happier."},
        {"tier": 5, "name": "Fairground", "cost": 5800, "blurb": "The yard is a party."},
    ),
}


def empty_yard() -> dict:
    return {s: 0 for s in YARD_SLOTS}


def empty_tints() -> dict:
    return {s: 0 for s in YARD_SLOTS}


def merge_yard(raw) -> dict:
    out = empty_yard()
    if isinstance(raw, dict):
        for s in YARD_SLOTS:
            try:
                out[s] = max(0, min(YARD_MAX, int(raw.get(s) or 0)))
            except (TypeError, ValueError):
                out[s] = 0
    return out


def merge_tints(raw) -> dict:
    out = empty_tints()
    if isinstance(raw, dict):
        for s in YARD_SLOTS:
            try:
                out[s] = max(0, min(3, int(raw.get(s) or 0)))
            except (TypeError, ValueError):
                out[s] = 0
    return out


def merge_friends(raw) -> list:
    out = []
    if not isinstance(raw, list):
        return out
    seen = set()
    for row in raw:
        if not isinstance(row, dict):
            continue
        code = normalize_code(row.get("code") or row.get("id") or "")
        key = code if len(code) == 6 else str(row.get("id") or "")
        if len(key) < 6 or key in seen:
            continue
        seen.add(key)
        out.append(
            {
                "id": key,
                "code": code if len(code) == 6 else "",
                "name": str(row.get("name") or "Trainer")[:16],
                "main": str(row.get("main") or ""),
                "since": float(row.get("since") or 0),
                "bond": max(0, min(99, int(row.get("bond") or 0))),
                "last_visit": float(row.get("last_visit") or 0),
                "last_gift": float(row.get("last_gift") or 0),
                "last_cheer": float(row.get("last_cheer") or 0),
                "last_snack": float(row.get("last_snack") or 0),
                "last_hunt": float(row.get("last_hunt") or 0),
            }
        )
    return out[:24]


def yard_tier(save: dict, slot: str) -> int:
    y = save.get("yard") if isinstance(save.get("yard"), dict) else {}
    try:
        return max(0, min(YARD_MAX, int(y.get(slot) or 0)))
    except (TypeError, ValueError):
        return 0


def yard_tint(save: dict, slot: str) -> int:
    t = save.get("yard_tint") if isinstance(save.get("yard_tint"), dict) else {}
    try:
        return max(0, min(3, int(t.get(slot) or 0)))
    except (TypeError, ValueError):
        return 0


def yard_item(slot: str, tier: int) -> dict | None:
    pack = YARD.get(slot) or ()
    for it in pack:
        if int(it["tier"]) == int(tier):
            return it
    return None


def next_yard(save: dict, slot: str) -> dict | None:
    return yard_item(slot, yard_tier(save, slot) + 1)


def yard_score(save: dict) -> int:
    y = save.get("yard") if isinstance(save.get("yard"), dict) else {}
    return sum(max(0, int(y.get(s) or 0)) for s in YARD_SLOTS)


def cycle_tint(save: dict, slot: str) -> None:
    if slot not in YARD_SLOTS:
        return
    tints = save.setdefault("yard_tint", empty_tints())
    tints[slot] = (int(tints.get(slot) or 0) + 1) % 4


def buy_yard(save: dict, slot: str) -> str:
    nxt = next_yard(save, slot)
    if not nxt:
        return "MAXED"
    price = shop_cost(nxt["cost"])
    if int(save.get("coins") or 0) < price:
        return "BROKE"
    save["coins"] = int(save.get("coins") or 0) - price
    yard = save.setdefault("yard", empty_yard())
    yard[slot] = int(nxt["tier"])
    return ""


def yard_bonus(save: dict) -> dict:
    h = yard_tier(save, "house")
    b = yard_tier(save, "bed")
    t = yard_tier(save, "tree")
    s = yard_tier(save, "shower")
    o = yard_tier(save, "bowl")
    l = yard_tier(save, "lamp")
    f = yard_tier(save, "fence")
    p = yard_tier(save, "pond")
    y = yard_tier(save, "toy")
    return {
        "hunger": h * 7 + f * 3,
        "sleep": b + (1 if h >= 2 else 0) + (1 if b >= 5 else 0),
        "wash": s * 3 + p * 2,
        "no_overwash": s >= 3,
        "feed": o * 4,
        "no_overfed": o >= 3,
        "coins": t * 2 + (2 if t >= 5 else 0),
        "mood_hold": l * 8 + y * 6,
        "luck": t + l + f,
        "play": y * 3,
    }


def tint_rgba(im, slot_tint: int):
    if slot_tint <= 0 or im.mode != "RGBA":
        return im
    r, g, b = YARD_TINTS[slot_tint]
    out = im.copy()
    px = out.load()
    w, h = out.size
    for y in range(h):
        for x in range(w):
            pr, pg, pb, pa = px[x, y]
            if pa < 16:
                continue
            px[x, y] = ((pr * r) // 255, (pg * g) // 255, (pb * b) // 255, pa)
    return out


def friend_of(save: dict, pid: str) -> dict | None:
    want = normalize_code(pid) or str(pid or "")
    for f in save.get("friends") or []:
        if f.get("id") == want or f.get("code") == want or f.get("id") == pid:
            return f
    return None


def is_friend(save: dict, pid: str) -> bool:
    return friend_of(save, pid) is not None


def upsert_friend(save: dict, card: dict) -> dict:
    pals = save.setdefault("friends", [])
    code = normalize_code(card.get("code") or card.get("from") or card.get("id") or "")
    pid = code if len(code) == 6 else str(card.get("id") or "")
    now = time.time()
    hit = friend_of(save, pid)
    if hit:
        if card.get("name") or card.get("from_name"):
            hit["name"] = str(card.get("name") or card.get("from_name") or hit.get("name") or "Trainer")[:16]
        if card.get("main"):
            hit["main"] = str(card["main"])
        if code:
            hit["code"] = code
            hit["id"] = code
        return hit
    if len(pid) < 6:
        return {"id": "", "name": "", "code": ""}
    row = {
        "id": pid,
        "code": code,
        "name": str(card.get("name") or card.get("from_name") or "Trainer")[:16],
        "main": str(card.get("main") or ""),
        "since": now,
        "bond": 1,
        "last_visit": 0.0,
        "last_gift": 0.0,
        "last_cheer": 0.0,
        "last_snack": 0.0,
        "last_hunt": 0.0,
    }
    pals.append(row)
    save["friends"] = pals[:24]
    return row


def drop_friend(save: dict, pid: str) -> None:
    want = normalize_code(pid) or str(pid or "")
    save["friends"] = [f for f in (save.get("friends") or []) if f.get("id") != want and f.get("code") != want]


def add_bond(save: dict, pid: str, n: int = 1) -> None:
    hit = friend_of(save, pid)
    if hit:
        hit["bond"] = min(99, int(hit.get("bond") or 0) + n)


def bond_title(n: int) -> str:
    lab = "STRANGER"
    for need, name in BOND_TITLES:
        if int(n) >= need:
            lab = name
    return lab


def online_map(peers: list) -> dict:
    return {p.get("pid"): p for p in peers if p.get("pid")}
