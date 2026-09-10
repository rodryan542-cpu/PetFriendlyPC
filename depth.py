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
from wave4 import WAVE4_BOSSES, WAVE4_GEAR

ATTACHMENTS = ATTACHMENTS + WAVE4_GEAR
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
    {"id": "raid_worm", "name": "File Worm", "hp": 280, "atk": 22, "defe": 12, "weak": "fire", "shape": "serpent", "c0": (70, 140, 60), "c1": (30, 70, 30), "lo": 40, "hi": 70, "band": 2},
    {"id": "raid_king", "name": "Street King", "hp": 340, "atk": 26, "defe": 16, "weak": "holy", "shape": "brute", "c0": (160, 50, 40), "c1": (40, 20, 16), "lo": 48, "hi": 80, "band": 3},
    {"id": "raid_void", "name": "Void Shade", "hp": 390, "atk": 28, "defe": 18, "weak": "holy", "shape": "ghost", "c0": (40, 30, 70), "c1": (180, 40, 200), "lo": 56, "hi": 90, "band": 3},
    {"id": "raid_titan", "name": "Raid Titan", "hp": 460, "atk": 32, "defe": 20, "weak": "shock", "shape": "ape", "c0": (120, 110, 90), "c1": (60, 50, 40), "lo": 70, "hi": 110, "band": 3},
) + WAVE4_BOSSES
HEAT_MAX = 5
INTENTS = ("jab", "smash", "guard", "hex", "heal")
SHAPE_RESIST = {
    "armor": {"slash": 0.58, "strike": 0.78, "gun": 0.72, "shock": 1.4, "fire": 1.15},
    "ghost": {"strike": 0.48, "slash": 0.68, "holy": 1.55, "curse": 0.82, "dark": 0.7},
    "slug": {"fire": 1.5, "slash": 0.82, "water": 0.68, "ice": 0.8},
    "beast": {"fire": 1.2, "ice": 0.75, "slash": 0.88, "fruit": 1.15},
    "flame": {"fire": 0.45, "water": 1.5, "ice": 1.35, "leaf": 0.7},
    "plant": {"fire": 1.5, "leaf": 0.55, "water": 0.72, "ice": 1.2},
    "serpent": {"fire": 1.25, "ice": 0.7, "shock": 1.3, "water": 0.75},
    "dino": {"fire": 0.8, "ice": 1.25, "slash": 0.85, "strike": 0.9},
    "wing": {"gun": 1.3, "wind": 0.65, "shock": 1.2, "slash": 0.85},
    "beetle": {"fire": 1.35, "slash": 0.7, "strike": 0.8, "leaf": 0.75},
    "bird": {"gun": 1.25, "wind": 0.7, "strike": 1.15, "ice": 1.1},
    "fish": {"shock": 1.5, "water": 0.55, "fire": 0.75, "leaf": 1.15},
    "skull": {"holy": 1.5, "curse": 0.7, "dark": 0.65, "strike": 0.85},
    "grunt": {"fire": 1.2, "gun": 0.8, "shock": 1.15, "strike": 0.9},
    "soldier": {"gun": 0.75, "slash": 1.2, "fruit": 1.15, "strike": 0.85},
    "drone": {"shock": 0.6, "gun": 1.25, "water": 1.2, "strike": 0.9},
    "fly": {"wind": 0.7, "gun": 1.3, "ice": 1.2, "strike": 1.1},
    "blob": {"slash": 0.55, "fire": 1.4, "curse": 0.8, "strike": 0.75},
    "ape": {"slash": 1.2, "strike": 0.8, "fire": 1.1, "holy": 1.15},
    "brute": {"holy": 1.35, "strike": 0.78, "slash": 0.85, "curse": 0.9},
    "agent": {"curse": 1.3, "dark": 0.7, "strike": 0.85, "holy": 1.2},
    "clown": {"fire": 1.3, "curse": 0.75, "slash": 1.15, "holy": 1.1},
    "elite": {"gun": 0.7, "holy": 0.8, "shock": 1.25, "slash": 1.15},
}
WEAK_RESIST = {
    "fire": "water",
    "water": "fire",
    "ice": "fire",
    "leaf": "fire",
    "shock": "earth",
    "holy": "curse",
    "curse": "holy",
    "dark": "holy",
    "slash": "strike",
    "strike": "slash",
    "gun": "strike",
    "fruit": "fire",
    "wind": "earth",
}

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


def resist_map(enemy: dict) -> dict:
    r = dict(SHAPE_RESIST.get(str(enemy.get("shape") or ""), {}))
    weak = str(enemy.get("weak") or "")
    opp = WEAK_RESIST.get(weak)
    if opp:
        r.setdefault(opp, 0.7)
    extra = enemy.get("resist")
    if isinstance(extra, dict):
        for k, v in extra.items():
            try:
                r[str(k)] = float(v)
            except (TypeError, ValueError):
                continue
    r.pop("", None)
    return r


def type_mult(move_typ: str, enemy: dict) -> float:
    m = 1.0
    if enemy.get("weak") == move_typ:
        m *= 1.55
    chart = TYPE_CHART.get(move_typ) or {}
    weak = str(enemy.get("weak") or "")
    if weak in chart:
        m *= chart[weak]
    shape = str(enemy.get("shape") or "")
    if shape in chart:
        m *= chart[shape]
    r = resist_map(enemy)
    m *= float(r.get(move_typ) or 1.0)
    return max(0.38, min(2.2, m))


def heat_cost(move: dict) -> int:
    p = int((move or {}).get("pow") or 8)
    if p >= 30:
        return 3
    if p >= 20:
        return 2
    return 1


def scale_foe(e: dict, partner: dict, hp_mult: float = 1.0) -> dict:
    st = combat_stats(partner, int(partner.get("stage_i") or 0))
    band = int(e.get("band") or 0)
    out = dict(e)
    hp = float(e.get("hp") or 26)
    atk = float(e.get("atk") or 8)
    defe = float(e.get("defe") or 3)
    raid = str(e.get("id") or "").startswith("raid_")
    pwr = float(st["atk"]) + st["level"] * 1.2
    if raid:
        out["hp"] = max(40, int((hp * 1.15 + st["level"] * 5 + st["hp"] * 0.2 + pwr * 1.1) * hp_mult))
        out["atk"] = max(8, int(atk * 1.18 + st["atk"] * 0.18 + band * 1.4))
        out["defe"] = max(4, int(defe * 1.18 + st["level"] * 0.45 + band * 1.0 + pwr * 0.18))
    else:
        out["hp"] = max(16, int((hp * 1.38 + st["level"] * 2.4 + band * 8 + pwr * (0.85 + band * 0.5)) * hp_mult))
        out["atk"] = max(5, int(atk * (1.02 + band * 0.06) + band * 1.35 + st["level"] * 0.28 + st["atk"] * 0.12))
        out["defe"] = max(2, int(defe * 1.2 + band * 1.2 + st["level"] * 0.4 + pwr * 0.2))
    out["resist"] = resist_map(out)
    return out


def roll_intent(foe: dict, rng: random.Random | None = None, last: str = "") -> str:
    rng = rng or random
    band = int(foe.get("band") or 0)
    hp = max(1, int(foe.get("hp") or 1))
    ehp = int(foe.get("_ehp") or hp)
    low = ehp / hp <= 0.38
    w = {"jab": 38, "smash": 18 + band * 5, "guard": 16, "hex": 8 + band * 3, "heal": (14 if low else 4) + (6 if band >= 2 else 0)}
    if last == "smash":
        w["smash"] = max(4, w["smash"] - 12)
        w["jab"] += 8
    if last == "heal":
        w["heal"] = 2
    names, weights = zip(*w.items())
    pick = rng.choices(list(names), weights=list(weights), k=1)[0]
    return pick if pick in INTENTS else "jab"


def seed_battle(st: dict, foe: dict, rng: random.Random | None = None) -> None:
    rng = rng or random
    st["foe"] = foe
    st["eid"] = foe.get("id")
    st["ename"] = foe.get("name")
    st["ehp"] = int(foe.get("hp") or 1)
    st["emax"] = int(foe.get("hp") or 1)
    st["status"] = ""
    st["pstatus"] = ""
    st["focus"] = 0
    st["heat"] = 0
    st["combo_typ"] = ""
    st["combo_n"] = 0
    foe["_ehp"] = st["ehp"]
    st["intent"] = roll_intent(foe, rng)
    st["guarding"] = False


def intent_label(st: dict) -> str:
    return str(st.get("intent") or "jab").upper()


def roll_hit(move: dict, level: int, stats: dict, enemy: dict, rng: random.Random | None = None) -> dict:
    rng = rng or random
    acc = 0.88 + min(0.08, stats["luck"] * 0.002)
    if str(stats.get("_pstatus") or "") == "hex":
        acc -= 0.08
    if rng.random() > acc:
        return {"miss": True, "dmg": 0, "crit": False, "mult": 1.0, "status": ""}
    lv = max(1, min(5, int(level)))
    raw = move["pow"] + (lv - 1) * move.get("grow", 0) + stats["atk"] * 0.82
    if str(stats.get("_pstatus") or "") == "slow":
        raw *= 0.8
    mult = type_mult(str(move.get("typ") or "strike"), enemy)
    crit_p = stats["crit"]
    if str(stats.get("_pstatus") or "") == "hex":
        crit_p *= 0.35
        mult = 1.0 + (mult - 1.0) * 0.45
    crit = rng.random() < crit_p
    if crit:
        mult *= 1.5
    dmg = int(raw * mult - float(enemy.get("defe") or 0) * 0.62 - stats["defe"] * 0.05)
    dmg = max(int(raw * mult * 0.24), dmg)
    dmg = max(1, dmg)
    status = ""
    typ = str(move.get("typ") or "")
    if typ == "fire" and rng.random() < 0.22:
        status = "burn"
    elif typ == "ice" and rng.random() < 0.2:
        status = "slow"
    elif typ == "shock" and rng.random() < 0.16:
        status = "stun"
    elif typ == "curse" and rng.random() < 0.16:
        status = "hex"
    return {"miss": False, "dmg": dmg, "crit": crit, "mult": mult, "status": status}


def enemy_hit(enemy: dict, stats: dict, status: str, rng: random.Random | None = None) -> int:
    rng = rng or random
    if status == "stun":
        return 0
    atk = float(enemy.get("atk") or 8)
    if status == "slow":
        atk *= 0.7
    hit = atk * 1.22 - stats["defe"] * 0.2 - stats["level"] * 0.12
    if rng.random() < 0.1:
        hit *= 1.4
    return max(2, int(hit))


def _foe_payload(enemy: dict, stats: dict, intent: str, status: str, guarding: bool, rng: random.Random) -> dict:
    if status == "stun":
        return {"dmg": 0, "heal": 0, "pstatus": "", "riposte": 0, "tag": "STUNNED"}
    atk = float(enemy.get("atk") or 8)
    if status == "slow":
        atk *= 0.7
    if status == "hex":
        atk *= 0.88
    if intent == "heal":
        return {"dmg": 0, "heal": max(8, int(float(enemy.get("hp") or 30) * 0.14) + 4), "pstatus": "", "riposte": 0, "tag": "HEAL"}
    if intent == "guard":
        poke = max(1, int(atk * 0.32 - stats["defe"] * 0.1))
        return {"dmg": poke, "heal": 0, "pstatus": "", "riposte": 0, "tag": "BRACE"}
    if intent == "smash":
        hit = atk * 1.75 - stats["defe"] * 0.16
        tag = "SMASH"
    elif intent == "hex":
        hit = atk * 0.8 - stats["defe"] * 0.16
        tag = "HEX"
    else:
        hit = atk * 0.88 - stats["defe"] * 0.24
        tag = "JAB"
    if rng.random() < 0.08:
        hit *= 1.32
        tag += "!"
    if guarding:
        if intent == "smash":
            hit *= 0.22
            rip = max(6, int(atk * 0.45))
            return {"dmg": max(1, int(hit)), "heal": 0, "pstatus": "", "riposte": rip, "tag": "BLOCK SMASH"}
        if intent == "jab":
            hit *= 0.55
        elif intent == "hex":
            hit *= 0.4
        else:
            hit *= 0.45
    dmg = max(1, int(hit))
    pstatus = ""
    if intent == "hex":
        pstatus = rng.choice(("burn", "slow", "hex"))
    elif intent == "smash" and rng.random() < 0.12:
        pstatus = "slow"
    return {"dmg": dmg, "heal": 0, "pstatus": pstatus, "riposte": 0, "tag": tag}


def play_turn(st: dict, action: str, move: dict | None, level: int, stats: dict, rng: random.Random | None = None, dmg_mult: float = 1.0) -> dict:
    rng = rng or random
    foe = st.get("foe") or {}
    intent = str(st.get("intent") or "jab")
    action = str(action or "move")
    if action == "move":
        mv = move or {"name": "Struggle", "typ": "strike", "pow": 8, "grow": 0}
        cost = heat_cost(mv)
        heat = int(st.get("heat") or 0)
        if cost >= 2 and heat + cost > HEAT_MAX:
            return {"blocked": True, "log": "TOO HOT  GUARD OR FOCUS", "killed": False, "wiped": False, "dmg": 0, "dmg_in": 0, "crit": False, "miss": False, "typ": str(mv.get("typ") or "strike")}
        stats = dict(stats)
        stats["_pstatus"] = str(st.get("pstatus") or "")
        hit = roll_hit(mv, level, stats, foe, rng)
        dmg = 0
        miss = bool(hit["miss"])
        crit = bool(hit.get("crit"))
        if not miss:
            dmg = max(1, int(hit["dmg"] * dmg_mult))
            if int(st.get("focus") or 0):
                dmg = int(dmg * 1.6)
            if intent == "guard":
                dmg = max(1, int(dmg * (0.72 if foe.get("weak") == mv.get("typ") else 0.46)))
            typ = str(mv.get("typ") or "strike")
            if typ and typ == str(st.get("combo_typ") or ""):
                st["combo_n"] = min(4, int(st.get("combo_n") or 1) + 1)
            else:
                st["combo_n"] = 1
                st["combo_typ"] = typ
            dmg = int(dmg * (1.0 + 0.11 * (int(st["combo_n"]) - 1)))
            if foe.get("weak") == typ:
                dmg = int(dmg * 1.1)
            st["ehp"] = max(0, int(st.get("ehp") or 0) - dmg)
            if hit.get("status"):
                st["status"] = hit["status"]
            tag = " CRIT" if crit else ""
            if hit.get("status"):
                tag += f" {hit['status'].upper()}"
            you = f"{str(mv.get('name') or 'HIT').upper()} {dmg}{tag}"
        else:
            st["combo_n"] = 0
            st["combo_typ"] = ""
            you = f"{str(mv.get('name') or 'HIT').upper()} MISS"
        st["focus"] = 0
        st["heat"] = min(HEAT_MAX, heat + cost)
        typ = str(mv.get("typ") or "strike")
    elif action == "guard":
        miss = False
        crit = False
        dmg = 0
        typ = "strike"
        you = "GUARD"
        st["guarding"] = True
        st["heat"] = max(0, int(st.get("heat") or 0) - 2)
        st["combo_n"] = 0
        st["combo_typ"] = ""
    elif action == "focus":
        miss = False
        crit = False
        dmg = 0
        typ = "strike"
        you = "FOCUS"
        st["focus"] = 1
        st["heat"] = max(0, int(st.get("heat") or 0) - 1)
        st["combo_n"] = 0
        st["combo_typ"] = ""
    else:
        return {"blocked": True, "log": "NO ACT", "killed": False, "wiped": False, "dmg": 0, "dmg_in": 0, "crit": False, "miss": False, "typ": "strike"}

    if str(st.get("status") or "") == "burn" and int(st.get("ehp") or 0) > 0:
        burn = 5
        st["ehp"] = max(0, int(st["ehp"]) - burn)
        you += f"  BURN {burn}"

    killed = int(st.get("ehp") or 0) <= 0
    dmg_in = 0
    counter_typ = "strike"
    if killed:
        st["heat"] = max(0, int(st.get("heat") or 0) - 1)
        st["guarding"] = False
        st["log"] = you
        return {"blocked": False, "log": you, "killed": True, "wiped": False, "dmg": dmg, "dmg_in": 0, "crit": crit, "miss": miss, "typ": typ, "counter": None}

    guarding = bool(st.get("guarding"))
    payload = _foe_payload(foe, stats, intent, str(st.get("status") or ""), guarding, rng)
    if action == "focus":
        payload["dmg"] = int(payload["dmg"] * 1.08)

    if payload["heal"]:
        cap = int(st.get("emax") or foe.get("hp") or 1)
        st["ehp"] = min(cap, int(st.get("ehp") or 0) + int(payload["heal"]))
        them = f"{payload['tag']} +{int(payload['heal'])}"
    else:
        dmg_in = int(payload["dmg"] or 0)
        if dmg_in > 0:
            st["php"] = max(0, int(st.get("php") or 0) - dmg_in)
        them = f"{payload['tag']} {dmg_in}"
        if payload.get("pstatus"):
            st["pstatus"] = payload["pstatus"]
            them += f" {payload['pstatus'].upper()}"
        if payload.get("riposte"):
            rip = int(payload["riposte"])
            st["ehp"] = max(0, int(st["ehp"]) - rip)
            them += f"  RIPOSTE {rip}"
            dmg += rip
            if int(st["ehp"]) <= 0:
                killed = True

    if str(st.get("pstatus") or "") == "burn" and int(st.get("php") or 0) > 0 and not killed:
        pb = 4
        st["php"] = max(0, int(st["php"]) - pb)
        them += f"  YOU BURN {pb}"

    wiped = int(st.get("php") or 0) <= 0
    st["heat"] = max(0, int(st.get("heat") or 0) - 1)
    st["guarding"] = False
    foe["_ehp"] = int(st.get("ehp") or 0)
    if not killed and not wiped:
        st["intent"] = roll_intent(foe, rng, last=intent)
    nxt = intent_label(st)
    st["log"] = f"{you}  /  {them}  next {nxt}"
    return {
        "blocked": False,
        "log": st["log"],
        "killed": killed,
        "wiped": wiped,
        "dmg": dmg,
        "dmg_in": dmg_in,
        "crit": crit,
        "miss": miss,
        "typ": typ,
        "counter": None if dmg_in <= 0 else {"dmg": dmg_in, "label": str(foe.get("name") or "HIT")},
    }


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
