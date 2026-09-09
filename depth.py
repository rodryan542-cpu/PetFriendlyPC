"""Gear, combat depth, raid waves, egg-run. Works for every line."""
from __future__ import annotations

import hashlib
import random

GEAR_SLOTS = ("head", "back", "held", "feet")

ATTACHMENTS = (
    {"id": "visor", "name": "Battle Visor", "slot": "head", "cost": 28, "atk": 6, "crit": 4, "blurb": "+6 atk  +crit"},
    {"id": "crown", "name": "Gold Crown", "slot": "head", "cost": 42, "hp": 14, "luck": 6, "blurb": "+14 hp  +luck"},
    {"id": "hornband", "name": "Horn Band", "slot": "head", "cost": 24, "atk": 9, "blurb": "+9 atk"},
    {"id": "cap", "name": "Scout Cap", "slot": "head", "cost": 18, "defe": 5, "xp": 10, "blurb": "+def  +xp"},
    {"id": "helm", "name": "Iron Helm", "slot": "head", "cost": 36, "defe": 10, "hp": 8, "blurb": "+10 def  +hp"},
    {"id": "cape", "name": "Hero Cape", "slot": "back", "cost": 32, "defe": 8, "luck": 5, "blurb": "+def  +luck"},
    {"id": "wings", "name": "Sky Wings", "slot": "back", "cost": 48, "atk": 7, "crit": 8, "blurb": "+atk  +crit"},
    {"id": "pack", "name": "Field Pack", "slot": "back", "cost": 22, "hp": 12, "hatch": 10, "blurb": "+hp  faster hatch"},
    {"id": "cloak", "name": "Night Cloak", "slot": "back", "cost": 30, "defe": 6, "xp": 12, "blurb": "+def  +xp"},
    {"id": "shellp", "name": "Guard Shell", "slot": "back", "cost": 40, "defe": 14, "blurb": "+14 def"},
    {"id": "fangg", "name": "Fang Charm", "slot": "held", "cost": 26, "atk": 11, "blurb": "+11 atk"},
    {"id": "orb", "name": "Pulse Orb", "slot": "held", "cost": 38, "hp": 10, "crit": 8, "blurb": "+hp  +crit"},
    {"id": "badge", "name": "Rank Badge", "slot": "held", "cost": 20, "xp": 14, "luck": 6, "blurb": "+xp  +luck"},
    {"id": "lantern", "name": "Warm Lantern", "slot": "held", "cost": 24, "hatch": 16, "blurb": "hatch much faster"},
    {"id": "luckgem", "name": "Luck Gem", "slot": "held", "cost": 34, "luck": 14, "blurb": "+14 luck"},
    {"id": "boots", "name": "Stride Boots", "slot": "feet", "cost": 22, "atk": 5, "defe": 4, "blurb": "+atk  +def"},
    {"id": "greaves", "name": "Greaves", "slot": "feet", "cost": 30, "defe": 11, "blurb": "+11 def"},
    {"id": "sandals", "name": "Soft Sandals", "slot": "feet", "cost": 16, "hatch": 12, "xp": 6, "blurb": "hatch  +xp"},
    {"id": "magnets", "name": "Coin Magnets", "slot": "feet", "cost": 28, "luck": 10, "atk": 3, "blurb": "+luck  coins"},
    {"id": "claws", "name": "Toe Claws", "slot": "feet", "cost": 26, "atk": 8, "crit": 6, "blurb": "+atk  +crit"},
)
ATTACH_BY_ID = {a["id"]: a for a in ATTACHMENTS}

# attacker type -> defender weak-type extras live on the enemy. this is resist/bonus vs move typ.
TYPE_CHART = {
    "fire": {"ice": 1.4, "leaf": 1.4, "water": 0.7, "dragon": 0.8},
    "ice": {"dragon": 1.4, "plant": 1.3, "fire": 0.7, "water": 0.85},
    "water": {"fire": 1.4, "rock": 1.3, "leaf": 0.75, "shock": 0.85},
    "leaf": {"water": 1.35, "earth": 1.25, "fire": 0.7, "ice": 0.85},
    "shock": {"water": 1.4, "gun": 1.2, "earth": 0.7, "leaf": 0.9},
    "slash": {"leaf": 1.2, "fruit": 1.15, "armor": 0.8, "holy": 0.9},
    "strike": {"slash": 1.15, "gun": 1.1, "curse": 0.9},
    "curse": {"holy": 0.65, "strike": 1.2, "dark": 1.15},
    "holy": {"curse": 1.45, "dark": 1.4, "holy": 0.8},
    "dark": {"holy": 0.7, "curse": 1.2, "leaf": 1.1},
    "gun": {"wing": 1.25, "strike": 0.9, "armor": 0.85},
    "fruit": {"strike": 1.2, "slash": 1.1, "fire": 0.85},
    "wind": {"slash": 1.15, "gun": 1.1, "earth": 0.8},
}

RAID_BOSSES = (
    {"id": "raid_worm", "name": "File Worm", "hp": 220, "atk": 14, "defe": 8, "weak": "fire", "shape": "serpent", "c0": (70, 140, 60), "c1": (30, 70, 30), "lo": 40, "hi": 70, "band": 2},
    {"id": "raid_king", "name": "Street King", "hp": 260, "atk": 16, "defe": 10, "weak": "holy", "shape": "brute", "c0": (160, 50, 40), "c1": (40, 20, 16), "lo": 48, "hi": 80, "band": 3},
    {"id": "raid_void", "name": "Void Shade", "hp": 300, "atk": 18, "defe": 12, "weak": "holy", "shape": "ghost", "c0": (40, 30, 70), "c1": (180, 40, 200), "lo": 56, "hi": 90, "band": 3},
    {"id": "raid_titan", "name": "Raid Titan", "hp": 340, "atk": 20, "defe": 14, "weak": "shock", "shape": "ape", "c0": (120, 110, 90), "c1": (60, 50, 40), "lo": 70, "hi": 110, "band": 3},
)

RUN_OBS = (
    {"id": "rock", "w": 36, "h": 32, "fly": False, "hurt": 1},
    {"id": "spike", "w": 28, "h": 40, "fly": False, "hurt": 1},
    {"id": "crate", "w": 34, "h": 34, "fly": False, "hurt": 1},
    {"id": "log", "w": 48, "h": 22, "fly": False, "hurt": 1},
    {"id": "thorn", "w": 24, "h": 36, "fly": False, "hurt": 1},
    {"id": "bird", "w": 32, "h": 24, "fly": True, "hurt": 1},
    {"id": "drone", "w": 30, "h": 22, "fly": True, "hurt": 1},
    {"id": "fence", "w": 18, "h": 48, "fly": False, "hurt": 1},
)

LEVEL_MAX = 30
INBOX_MAX = 40
GEAR_PER_PAGE = 4


def xp_need(level: int) -> int:
    lv = max(1, min(LEVEL_MAX, int(level)))
    return 18 * lv * (lv + 1)


def gear_of(partner: dict) -> dict:
    g = partner.get("gear") if isinstance(partner.get("gear"), dict) else {}
    return {s: g.get(s) or "" for s in GEAR_SLOTS}


def gear_bonus(partner: dict) -> dict:
    out = {"atk": 0, "defe": 0, "hp": 0, "crit": 0, "luck": 0, "hatch": 0, "xp": 0}
    for slot, aid in gear_of(partner).items():
        a = ATTACH_BY_ID.get(aid)
        if not a or a["slot"] != slot:
            continue
        for k in out:
            out[k] += int(a.get(k) or 0)
    return out


def partner_level(partner: dict) -> int:
    return max(1, min(LEVEL_MAX, int(partner.get("level") or 1)))


def grant_xp(partner: dict, amount: int) -> int:
    """Add XP. Returns levels gained."""
    gained = 0
    bonus = gear_bonus(partner)
    amt = max(0, int(amount * (1.0 + bonus["xp"] / 100.0)))
    partner["xp"] = int(partner.get("xp") or 0) + amt
    lv = partner_level(partner)
    while lv < LEVEL_MAX and int(partner["xp"]) >= xp_need(lv):
        partner["xp"] = int(partner["xp"]) - xp_need(lv)
        lv += 1
        gained += 1
        partner["strength"] = min(99, int(partner.get("strength") or 0) + 2)
    partner["level"] = lv
    return gained


def combat_stats(partner: dict, stage_i: int) -> dict:
    b = gear_bonus(partner)
    lv = partner_level(partner)
    stre = float(partner.get("strength") or 0)
    hp = int(36 + stage_i * 14 + stre * 0.8 + lv * 4 + b["hp"])
    atk = stre * 0.45 + lv * 1.4 + b["atk"]
    defe = stage_i * 2.2 + lv * 0.8 + b["defe"]
    crit = 0.08 + b["crit"] * 0.004
    luck = b["luck"]
    return {"hp": hp, "atk": atk, "defe": defe, "crit": min(0.38, crit), "luck": luck, "level": lv}


def type_mult(move_typ: str, enemy: dict) -> float:
    m = 1.0
    if enemy.get("weak") == move_typ:
        m *= 1.38
    chart = TYPE_CHART.get(move_typ) or {}
    weak = str(enemy.get("weak") or "")
    if weak in chart:
        m *= chart[weak]
    shape = str(enemy.get("shape") or "")
    if shape in chart:
        m *= chart[shape]
    return max(0.55, min(1.85, m))


def roll_hit(move: dict, level: int, stats: dict, enemy: dict, rng: random.Random | None = None) -> dict:
    rng = rng or random
    acc = 0.90 + min(0.08, stats["luck"] * 0.002)
    if rng.random() > acc:
        return {"miss": True, "dmg": 0, "crit": False, "mult": 1.0, "status": ""}
    lv = max(1, min(5, int(level)))
    raw = move["pow"] + (lv - 1) * move.get("grow", 0) + stats["atk"]
    mult = type_mult(str(move.get("typ") or "strike"), enemy)
    crit = rng.random() < stats["crit"]
    if crit:
        mult *= 1.5
    dmg = int(raw * mult - float(enemy.get("defe") or 0) * 0.42 - stats["defe"] * 0.08)
    dmg = max(1, dmg)
    status = ""
    typ = str(move.get("typ") or "")
    if typ == "fire" and rng.random() < 0.18:
        status = "burn"
    elif typ == "ice" and rng.random() < 0.16:
        status = "slow"
    elif typ == "shock" and rng.random() < 0.14:
        status = "stun"
    elif typ == "curse" and rng.random() < 0.12:
        status = "hex"
    return {"miss": False, "dmg": dmg, "crit": crit, "mult": mult, "status": status}


def enemy_hit(enemy: dict, stats: dict, status: str, rng: random.Random | None = None) -> int:
    rng = rng or random
    if status == "stun":
        return 0
    atk = float(enemy.get("atk") or 8)
    if status == "slow":
        atk *= 0.7
    hit = atk - stats["defe"] * 0.12 - stats["level"] * 0.2
    if rng.random() < 0.08:
        hit *= 1.35
    return max(1, int(hit))


def hatch_mult(partner: dict) -> float:
    return 1.0 + gear_bonus(partner)["hatch"] / 100.0


def dirt_count(hygiene: int) -> int:
    h = max(0, min(100, int(hygiene)))
    if h >= 88:
        return 0
    if h >= 70:
        return 10
    if h >= 50:
        return 18
    if h >= 30:
        return 28
    return 40


def dirt_seed(line_id: str, hygiene: int) -> int:
    raw = f"{line_id}:{int(hygiene) // 8}".encode("utf-8")
    return int(hashlib.md5(raw).hexdigest()[:8], 16)


def pick_raid_boss(rng: random.Random | None = None) -> dict:
    rng = rng or random
    return dict(rng.choice(RAID_BOSSES))


def floor_band(floor: int, stage_i: int, strength: float) -> int:
    b = 0
    if stage_i >= 1 or strength >= 10:
        b = 1
    if stage_i >= 2 or strength >= 22 or floor >= 3:
        b = 2
    if stage_i >= 3 or strength >= 40 or floor >= 5:
        b = 3
    return min(3, b + max(0, floor - 1) // 2)
