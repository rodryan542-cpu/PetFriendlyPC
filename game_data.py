"""Catalogs: moves, enemies, hatch tools, clan defaults. Data only."""
from __future__ import annotations

import random
import uuid

from catalog_extra import (
    EXTRA_BLURB,
    EXTRA_ENEMIES,
    EXTRA_ITEMS,
    EXTRA_LINES,
    EXTRA_MOVES,
    EXTRA_NAMES,
)
from more_roster import (
    MORE_BLURB,
    MORE_ENEMIES,
    MORE_ITEMS,
    MORE_LINES,
    MORE_MOVES,
    MORE_NAMES,
)

LINES = (
    {"id": "agumon", "tag": "DIGIMON", "stages": ("egg_agumon", "botamon", "koromon", "agumon", "greymon")},
    {"id": "gabumon", "tag": "DIGIMON", "stages": ("egg_gabumon", "gabumon", "garurumon")},
    {"id": "luffy", "tag": "ONE PIECE", "stages": ("fruit_gomu", "luffy", "luffy_g2", "luffy_g3", "luffy_g4", "luffy2")},
    {"id": "zoro", "tag": "ONE PIECE", "stages": ("egg_zoro", "zoro", "zoro2")},
    {"id": "yuji", "tag": "JJK", "stages": ("egg_yuji", "yuji", "yuji2")},
    {"id": "gojo", "tag": "JJK", "stages": ("egg_gojo", "gojo", "gojo2")},
    {"id": "chief", "tag": "HALO", "stages": ("cryo", "chief", "chief_ar", "chief_kit")},
    {"id": "arbiter", "tag": "HALO", "stages": ("egg_arbiter", "arbiter", "arbiter2")},
) + EXTRA_LINES + MORE_LINES
LINE_BY_ID = {ln["id"]: ln for ln in LINES}
LINE_NAME = {
    "agumon": "Agumon",
    "gabumon": "Gabumon",
    "luffy": "Luffy",
    "zoro": "Zoro",
    "yuji": "Yuji",
    "gojo": "Gojo",
    "chief": "Chief",
    "arbiter": "Arbiter",
    **EXTRA_NAMES,
    **MORE_NAMES,
}
START_FORM = {ln["id"]: ln["stages"][0] for ln in LINES}
LINE_PRICE = 2_500_000
PRICE_MULT = 50
UP_GROW = 2.4


def owned_list(save: dict) -> list[str]:
    raw = save.get("owned")
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for x in raw:
        s = str(x)
        if s in LINE_BY_ID and s not in out:
            out.append(s)
    return out


def owns_line(save: dict, pid: str) -> bool:
    return pid in owned_list(save)


def line_price(_pid: str) -> int:
    return LINE_PRICE


def shop_cost(n: int) -> int:
    try:
        v = int(n or 0)
    except (TypeError, ValueError):
        return 0
    if v <= 0:
        return 0
    return v * PRICE_MULT


def move_buy_cost(mv: dict) -> int:
    return shop_cost(mv.get("buy") or 12) * 2


def move_up_cost(mv: dict, lv: int) -> int:
    base = shop_cost(mv.get("up") or 10)
    step = max(1, int(lv))
    return int(base * (UP_GROW ** step))


def fmt_price(n: int) -> str:
    return f"${int(n):,}"


def fmt_price_short(n: int) -> str:
    n = int(n)
    if n >= 1_000_000:
        x = n / 1_000_000
        return f"${x:.1f}M" if x < 10 else f"${x:.0f}M"
    if n >= 10_000:
        return f"${n // 1000}k"
    if n >= 1000:
        return f"${n / 1000:.1f}k"
    return f"${n}"


START_BLURB = {
    "agumon": "Fire. Teeth. File Island dirt.",
    "gabumon": "Blue fur. A pelt that bites back.",
    "luffy": "Gomu Gomu. Stretch or starve.",
    "zoro": "Three blades. Gets lost on purpose.",
    "yuji": "A vessel. Fists first.",
    "gojo": "Six Eyes. Unlimited smug.",
    "chief": "Cryo to rifle. Finish the fight.",
    "arbiter": "Sangheili honor. Energy blade.",
    **EXTRA_BLURB,
    **MORE_BLURB,
}

MOVE_MAX = 5
LOADOUT_SLOTS = 4

# buy = first purchase, up = cost to raise one level, pow = base, grow = per level
MOVES = {
    "agumon": (
        {"id": "pepper", "name": "Pepper Breath", "typ": "fire", "buy": 16, "up": 12, "pow": 14, "grow": 5},
        {"id": "claw", "name": "Baby Claw", "typ": "slash", "buy": 12, "up": 10, "pow": 10, "grow": 4},
        {"id": "bite", "name": "Sharp Bite", "typ": "slash", "buy": 18, "up": 12, "pow": 15, "grow": 5},
        {"id": "tail", "name": "Tail Whip", "typ": "strike", "buy": 14, "up": 11, "pow": 12, "grow": 4},
        {"id": "spitfire", "name": "Spitfire", "typ": "fire", "buy": 28, "up": 16, "pow": 20, "grow": 6},
        {"id": "inferno", "name": "Baby Inferno", "typ": "fire", "buy": 36, "up": 18, "pow": 24, "grow": 6},
        {"id": "nova", "name": "Nova Blast", "typ": "fire", "buy": 48, "up": 22, "pow": 28, "grow": 7},
        {"id": "mega_flame", "name": "Mega Flame", "typ": "fire", "buy": 62, "up": 26, "pow": 34, "grow": 8},
    ),
    "gabumon": (
        {"id": "blue_fire", "name": "Blue Blaster", "typ": "ice", "buy": 16, "up": 12, "pow": 14, "grow": 5},
        {"id": "horn", "name": "Horn Attack", "typ": "strike", "buy": 12, "up": 10, "pow": 11, "grow": 4},
        {"id": "pelt", "name": "Pelt Slash", "typ": "slash", "buy": 18, "up": 12, "pow": 15, "grow": 5},
        {"id": "freeze", "name": "Frost Fang", "typ": "ice", "buy": 22, "up": 14, "pow": 17, "grow": 5},
        {"id": "howl", "name": "Howling", "typ": "ice", "buy": 26, "up": 16, "pow": 18, "grow": 6},
        {"id": "blizzard", "name": "Little Blizzard", "typ": "ice", "buy": 38, "up": 18, "pow": 24, "grow": 6},
        {"id": "garuru", "name": "Garuru Fang", "typ": "slash", "buy": 46, "up": 22, "pow": 27, "grow": 7},
        {"id": "moon", "name": "Moon Howl", "typ": "ice", "buy": 60, "up": 26, "pow": 33, "grow": 8},
    ),
    "luffy": (
        {"id": "pistol", "name": "Gum-Gum Pistol", "typ": "fruit", "buy": 16, "up": 12, "pow": 13, "grow": 5},
        {"id": "whip", "name": "Gum-Gum Whip", "typ": "fruit", "buy": 18, "up": 12, "pow": 14, "grow": 5},
        {"id": "balloon", "name": "Balloon", "typ": "strike", "buy": 14, "up": 11, "pow": 11, "grow": 4},
        {"id": "gatling", "name": "Gatling", "typ": "strike", "buy": 22, "up": 14, "pow": 17, "grow": 5},
        {"id": "bazooka", "name": "Bazooka", "typ": "fruit", "buy": 30, "up": 18, "pow": 22, "grow": 6},
        {"id": "red_hawk", "name": "Red Hawk", "typ": "fire", "buy": 42, "up": 20, "pow": 26, "grow": 7},
        {"id": "kong", "name": "Kong Gun", "typ": "fruit", "buy": 50, "up": 24, "pow": 30, "grow": 7},
        {"id": "bajrang", "name": "Bajrang Gun", "typ": "fruit", "buy": 70, "up": 28, "pow": 38, "grow": 8},
    ),
    "zoro": (
        {"id": "onetwo", "name": "One-Two", "typ": "slash", "buy": 14, "up": 11, "pow": 12, "grow": 4},
        {"id": "hawk", "name": "Hawk Wave", "typ": "slash", "buy": 18, "up": 12, "pow": 15, "grow": 5},
        {"id": "oni", "name": "Oni Giri", "typ": "slash", "buy": 24, "up": 15, "pow": 19, "grow": 6},
        {"id": "lion", "name": "Lion Song", "typ": "slash", "buy": 28, "up": 16, "pow": 21, "grow": 6},
        {"id": "tatsumaki", "name": "Tatsumaki", "typ": "slash", "buy": 32, "up": 18, "pow": 23, "grow": 6},
        {"id": "three_k", "name": "Three Thousand", "typ": "slash", "buy": 44, "up": 20, "pow": 27, "grow": 7},
        {"id": "ashura", "name": "Ashura", "typ": "slash", "buy": 52, "up": 24, "pow": 31, "grow": 8},
        {"id": "dragon", "name": "Dragon Twister", "typ": "slash", "buy": 66, "up": 28, "pow": 36, "grow": 8},
    ),
    "yuji": (
        {"id": "divergent", "name": "Divergent Fist", "typ": "strike", "buy": 16, "up": 12, "pow": 14, "grow": 5},
        {"id": "kick", "name": "Knee Spike", "typ": "strike", "buy": 14, "up": 11, "pow": 12, "grow": 4},
        {"id": "manji", "name": "Manji Kick", "typ": "strike", "buy": 20, "up": 13, "pow": 16, "grow": 5},
        {"id": "dismantle", "name": "Dismantle", "typ": "slash", "buy": 26, "up": 16, "pow": 20, "grow": 6},
        {"id": "cleave", "name": "Cleave", "typ": "slash", "buy": 34, "up": 18, "pow": 24, "grow": 6},
        {"id": "soul", "name": "Soul Punch", "typ": "curse", "buy": 40, "up": 20, "pow": 26, "grow": 7},
        {"id": "black", "name": "Black Flash", "typ": "curse", "buy": 54, "up": 26, "pow": 32, "grow": 8},
        {"id": "shrine", "name": "Malevolent Shrine", "typ": "curse", "buy": 72, "up": 30, "pow": 38, "grow": 8},
    ),
    "gojo": (
        {"id": "repel", "name": "Repel", "typ": "curse", "buy": 18, "up": 13, "pow": 13, "grow": 5},
        {"id": "snap", "name": "Snap", "typ": "strike", "buy": 16, "up": 12, "pow": 14, "grow": 5},
        {"id": "infinity", "name": "Infinity", "typ": "curse", "buy": 24, "up": 15, "pow": 12, "grow": 6},
        {"id": "blue", "name": "Cursed Blue", "typ": "curse", "buy": 28, "up": 17, "pow": 21, "grow": 6},
        {"id": "red", "name": "Cursed Red", "typ": "fire", "buy": 36, "up": 20, "pow": 25, "grow": 7},
        {"id": "six", "name": "Six Eyes Cut", "typ": "slash", "buy": 44, "up": 22, "pow": 27, "grow": 7},
        {"id": "hollow", "name": "Hollow Purple", "typ": "curse", "buy": 58, "up": 28, "pow": 34, "grow": 8},
        {"id": "domain", "name": "Unlimited Void", "typ": "curse", "buy": 80, "up": 32, "pow": 40, "grow": 9},
    ),
    "chief": (
        {"id": "mag", "name": "Magnum", "typ": "gun", "buy": 16, "up": 12, "pow": 13, "grow": 5},
        {"id": "melee", "name": "Rifle Bash", "typ": "strike", "buy": 12, "up": 10, "pow": 11, "grow": 4},
        {"id": "ar", "name": "MA40 Burst", "typ": "gun", "buy": 24, "up": 15, "pow": 18, "grow": 6},
        {"id": "shotgun", "name": "Bulldog", "typ": "gun", "buy": 28, "up": 16, "pow": 20, "grow": 6},
        {"id": "grenade", "name": "Frag", "typ": "fire", "buy": 30, "up": 17, "pow": 22, "grow": 6},
        {"id": "sniper", "name": "SRS99", "typ": "gun", "buy": 42, "up": 20, "pow": 26, "grow": 7},
        {"id": "spartan", "name": "Spartan Charge", "typ": "strike", "buy": 48, "up": 22, "pow": 28, "grow": 7},
        {"id": "laser", "name": "Spartan Laser", "typ": "fire", "buy": 68, "up": 28, "pow": 36, "grow": 8},
    ),
    "arbiter": (
        {"id": "plasma", "name": "Plasma Pistol", "typ": "shock", "buy": 16, "up": 12, "pow": 13, "grow": 5},
        {"id": "needler", "name": "Needler", "typ": "gun", "buy": 18, "up": 13, "pow": 15, "grow": 5},
        {"id": "rifle", "name": "Plasma Rifle", "typ": "shock", "buy": 24, "up": 15, "pow": 18, "grow": 6},
        {"id": "carbine", "name": "Carbine", "typ": "gun", "buy": 28, "up": 16, "pow": 20, "grow": 6},
        {"id": "blade", "name": "Energy Sword", "typ": "slash", "buy": 34, "up": 20, "pow": 26, "grow": 7},
        {"id": "hammer", "name": "Gravity Hammer", "typ": "strike", "buy": 46, "up": 22, "pow": 29, "grow": 7},
        {"id": "zealot", "name": "Zealot Rush", "typ": "slash", "buy": 50, "up": 24, "pow": 30, "grow": 8},
        {"id": "honor", "name": "Honor Duel", "typ": "slash", "buy": 64, "up": 28, "pow": 35, "grow": 8},
    ),
}
MOVES = {**MOVES, **EXTRA_MOVES, **MORE_MOVES}

HATCH = (
    {"id": "warm", "name": "Warm", "cost": 8, "cd": 180, "shave": 12 * 60, "desc": "Hands on the shell. 12 min gone."},
    {"id": "lullaby", "name": "Lullaby", "cost": 10, "cd": 240, "shave": 14 * 60, "desc": "Sing it along. 14 min."},
    {"id": "pulse", "name": "Pulse", "cost": 12, "cd": 300, "shave": 16 * 60, "desc": "A jolt. 16 min + a bit of strength."},
    {"id": "spicy", "name": "Spicy Rub", "cost": 14, "cd": 360, "shave": 18 * 60, "desc": "Heat in the shell. 18 min."},
    {"id": "lamp", "name": "Heat Lamp", "cost": 18, "cd": 480, "shave": 28 * 60, "desc": "Bake minutes off. 28 min."},
    {"id": "carry", "name": "Carry", "cost": 0, "cd": 360, "shave": 8 * 60, "desc": "Walk with it. Free. 8 min."},
    {"id": "candy", "name": "Rare Candy", "cost": 40, "cd": 120, "shave": 30 * 60, "desc": "Chew a half hour off."},
    {"id": "incubate", "name": "Incubate", "cost": 35, "cd": 900, "shave": 50 * 60, "desc": "Lock it in. 50 min."},
    {"id": "nest", "name": "Warm Nest", "cost": 48, "cd": 720, "shave": 70 * 60, "desc": "Tuck it in. 70 min."},
    {"id": "comet", "name": "Comet Chew", "cost": 80, "cd": 180, "shave": 90 * 60, "desc": "Eat an hour and a half."},
)

EGG_PLAY = (
    {"id": "roll", "name": "ROLL", "cd": 40, "desc": "Luck or a kick."},
    {"id": "talk", "name": "TALK", "cd": 50, "desc": "Tell it a secret."},
    {"id": "turn", "name": "TURN", "cd": 25, "desc": "No flat spots."},
    {"id": "listen", "name": "LISTEN", "cd": 35, "desc": "Hear the shell."},
    {"id": "wish", "name": "WISH", "cd": 90, "desc": "Ask it for luck."},
    {"id": "window", "name": "LOOK", "cd": 55, "desc": "Watch the world."},
    {"id": "pat", "name": "PAT", "cd": 20, "desc": "Warm little pats."},
    {"id": "peek", "name": "PEEK", "cd": 45, "desc": "Crack peek."},
    {"id": "rock", "name": "ROCK", "cd": 30, "desc": "Rock it to sleep."},
    {"id": "snack", "name": "SNACK", "cd": 35, "desc": "A crumb. Yum."},
)
EGG_PLAY_BY_ID = {x["id"]: x for x in EGG_PLAY}

TALK_LINES = (
    "You are brave.",
    "I will wait.",
    "Kick if you hear me.",
    "The world is loud. Sleep.",
    "I named you already.",
    "Just a little longer.",
    "I saved you a snack.",
    "The sun is on your shell.",
    "Dream of running.",
    "I am right here.",
)

# bag items. kind: food play heal train hatch luck map flee chip
ITEMS = (
    {"id": "meat", "name": "Meat", "cost": 10, "kind": "food", "hunger": 22, "mood": 2},
    {"id": "onigiri", "name": "Onigiri", "cost": 11, "kind": "food", "hunger": 18, "mood": 4},
    {"id": "ration", "name": "MRE", "cost": 14, "kind": "food", "hunger": 28, "mood": 0},
    {"id": "cola", "name": "Gear Cola", "cost": 16, "kind": "food", "hunger": 10, "mood": 18},
    {"id": "fruit", "name": "Odd Fruit", "cost": 18, "kind": "food", "hunger": 16, "mood": 14},
    {"id": "deluxe", "name": "Deluxe Steak", "cost": 22, "kind": "food", "hunger": 40, "mood": 8},
    {"id": "sake", "name": "Party Bottle", "cost": 19, "kind": "play", "mood": 30, "hygiene": -8},
    {"id": "toy", "name": "Squeaky Toy", "cost": 12, "kind": "play", "mood": 25},
    {"id": "ball", "name": "Ball", "cost": 16, "kind": "play", "mood": 18, "str": 1},
    {"id": "cards", "name": "Card Pack", "cost": 20, "kind": "gamble"},
    {"id": "soap", "name": "Soap", "cost": 8, "kind": "heal", "hygiene": 50},
    {"id": "med", "name": "Medkit", "cost": 15, "kind": "heal", "hygiene": 100, "clear_poop": True, "mood": 8},
    {"id": "protein", "name": "Protein", "cost": 18, "kind": "train", "str": 5, "hunger": -4},
    {"id": "weights", "name": "Dumbbell", "cost": 28, "kind": "train", "str": 8, "hunger": -6},
    {"id": "chip", "name": "Skill Chip", "cost": 35, "kind": "chip"},
    {"id": "charm", "name": "Lucky Charm", "cost": 24, "kind": "luck"},
    {"id": "map", "name": "Worn Map", "cost": 20, "kind": "map"},
    {"id": "bomb", "name": "Smoke Bomb", "cost": 12, "kind": "flee"},
    {"id": "candy_bag", "name": "Rare Candy", "cost": 40, "kind": "hatch", "shave": 30 * 60},
    {"id": "clock", "name": "Time Chew", "cost": 70, "kind": "hatch", "shave": 60 * 60},
) + EXTRA_ITEMS + MORE_ITEMS
ITEM_BY_ID = {it["id"]: it for it in ITEMS}
FOODS = tuple(it for it in ITEMS if it["kind"] == "food")

# band 0 = early, 3 = late. weak is a move typ.
ENEMIES = (
    # DIGIMON 12
    {"id": "numemon", "name": "Numemon", "tag": "DIGIMON", "hp": 26, "atk": 6, "defe": 2, "lo": 7, "hi": 12, "weak": "fire", "band": 0, "shape": "slug", "c0": (80, 140, 70), "c1": (40, 70, 35)},
    {"id": "gazimon", "name": "Gazimon", "tag": "DIGIMON", "hp": 28, "atk": 8, "defe": 3, "lo": 8, "hi": 13, "weak": "ice", "band": 0, "shape": "beast", "c0": (40, 36, 48), "c1": (20, 18, 24)},
    {"id": "vegiemon", "name": "Vegiemon", "tag": "DIGIMON", "hp": 30, "atk": 7, "defe": 4, "lo": 8, "hi": 14, "weak": "fire", "band": 0, "shape": "plant", "c0": (70, 160, 60), "c1": (40, 90, 30)},
    {"id": "bakemon", "name": "Bakemon", "tag": "DIGIMON", "hp": 24, "atk": 9, "defe": 2, "lo": 9, "hi": 15, "weak": "holy", "band": 0, "shape": "ghost", "c0": (36, 36, 44), "c1": (16, 16, 20)},
    {"id": "kuwagamon", "name": "Kuwagamon", "tag": "DIGIMON", "hp": 36, "atk": 11, "defe": 5, "lo": 11, "hi": 18, "weak": "fire", "band": 1, "shape": "beetle", "c0": (160, 50, 50), "c1": (90, 24, 24)},
    {"id": "meramon", "name": "Meramon", "tag": "DIGIMON", "hp": 34, "atk": 13, "defe": 3, "lo": 12, "hi": 19, "weak": "ice", "band": 1, "shape": "flame", "c0": (230, 90, 30), "c1": (160, 40, 10)},
    {"id": "ogremon", "name": "Ogremon", "tag": "DIGIMON", "hp": 42, "atk": 14, "defe": 6, "lo": 13, "hi": 20, "weak": "curse", "band": 1, "shape": "brute", "c0": (70, 130, 70), "c1": (30, 70, 30)},
    {"id": "kokatori", "name": "Kokatorimon", "tag": "DIGIMON", "hp": 38, "atk": 12, "defe": 5, "lo": 12, "hi": 19, "weak": "slash", "band": 1, "shape": "bird", "c0": (200, 80, 70), "c1": (120, 40, 36)},
    {"id": "seadramon", "name": "Seadramon", "tag": "DIGIMON", "hp": 48, "atk": 15, "defe": 7, "lo": 16, "hi": 24, "weak": "shock", "band": 2, "shape": "serpent", "c0": (50, 120, 180), "c1": (20, 60, 110)},
    {"id": "tyrannomon", "name": "Tyrannomon", "tag": "DIGIMON", "hp": 52, "atk": 16, "defe": 8, "lo": 17, "hi": 26, "weak": "ice", "band": 2, "shape": "dino", "c0": (200, 70, 50), "c1": (120, 30, 24)},
    {"id": "devimon", "name": "Devimon", "tag": "DIGIMON", "hp": 56, "atk": 18, "defe": 8, "lo": 20, "hi": 30, "weak": "holy", "band": 3, "shape": "wing", "c0": (48, 36, 70), "c1": (20, 14, 36)},
    {"id": "etemon", "name": "Etemon", "tag": "DIGIMON", "hp": 58, "atk": 17, "defe": 9, "lo": 22, "hi": 32, "weak": "slash", "band": 3, "shape": "ape", "c0": (80, 56, 40), "c1": (40, 26, 18)},
    # ONE PIECE 12
    {"id": "marine", "name": "Marine", "tag": "ONE PIECE", "hp": 26, "atk": 7, "defe": 3, "lo": 7, "hi": 12, "weak": "fruit", "band": 0, "shape": "soldier", "c0": (40, 80, 160), "c1": (20, 40, 90)},
    {"id": "krieg", "name": "Krieg Thug", "tag": "ONE PIECE", "hp": 30, "atk": 8, "defe": 4, "lo": 8, "hi": 14, "weak": "fire", "band": 0, "shape": "brute", "c0": (90, 90, 70), "c1": (50, 50, 36)},
    {"id": "fishman", "name": "Fish-Man", "tag": "ONE PIECE", "hp": 32, "atk": 9, "defe": 4, "lo": 9, "hi": 15, "weak": "shock", "band": 0, "shape": "fish", "c0": (50, 130, 140), "c1": (20, 70, 80)},
    {"id": "buggy", "name": "Buggy Crew", "tag": "ONE PIECE", "hp": 28, "atk": 8, "defe": 2, "lo": 10, "hi": 16, "weak": "slash", "band": 0, "shape": "clown", "c0": (200, 50, 50), "c1": (120, 20, 20)},
    {"id": "seaking", "name": "Sea King", "tag": "ONE PIECE", "hp": 44, "atk": 12, "defe": 6, "lo": 13, "hi": 20, "weak": "shock", "band": 1, "shape": "serpent", "c0": (40, 90, 70), "c1": (16, 50, 40)},
    {"id": "arlong", "name": "Arlong", "tag": "ONE PIECE", "hp": 40, "atk": 14, "defe": 5, "lo": 14, "hi": 21, "weak": "fruit", "band": 1, "shape": "fish", "c0": (40, 150, 130), "c1": (16, 80, 70)},
    {"id": "smoker", "name": "Smoke Unit", "tag": "ONE PIECE", "hp": 38, "atk": 13, "defe": 6, "lo": 13, "hi": 20, "weak": "fruit", "band": 1, "shape": "soldier", "c0": (90, 90, 96), "c1": (40, 40, 46)},
    {"id": "wapol", "name": "Wapol Guard", "tag": "ONE PIECE", "hp": 42, "atk": 11, "defe": 8, "lo": 12, "hi": 19, "weak": "slash", "band": 1, "shape": "brute", "c0": (160, 60, 90), "c1": (90, 30, 50)},
    {"id": "cipher", "name": "CP9 Agent", "tag": "ONE PIECE", "hp": 48, "atk": 16, "defe": 7, "lo": 17, "hi": 26, "weak": "curse", "band": 2, "shape": "agent", "c0": (30, 30, 36), "c1": (12, 12, 16)},
    {"id": "pacifista", "name": "Pacifista", "tag": "ONE PIECE", "hp": 60, "atk": 17, "defe": 10, "lo": 20, "hi": 30, "weak": "shock", "band": 2, "shape": "armor", "c0": (200, 170, 80), "c1": (120, 100, 40)},
    {"id": "enel", "name": "Enel Drone", "tag": "ONE PIECE", "hp": 46, "atk": 18, "defe": 6, "lo": 18, "hi": 28, "weak": "strike", "band": 3, "shape": "drone", "c0": (220, 200, 80), "c1": (140, 120, 30)},
    {"id": "admiral", "name": "Vice Admiral", "tag": "ONE PIECE", "hp": 62, "atk": 19, "defe": 9, "lo": 22, "hi": 34, "weak": "fruit", "band": 3, "shape": "soldier", "c0": (30, 60, 130), "c1": (12, 28, 70)},
    # JJK 12
    {"id": "flyhead", "name": "Fly Head", "tag": "JJK", "hp": 22, "atk": 7, "defe": 1, "lo": 7, "hi": 12, "weak": "strike", "band": 0, "shape": "fly", "c0": (90, 110, 70), "c1": (40, 50, 30)},
    {"id": "curse_s", "name": "Low Curse", "tag": "JJK", "hp": 26, "atk": 8, "defe": 2, "lo": 8, "hi": 13, "weak": "curse", "band": 0, "shape": "ghost", "c0": (70, 50, 90), "c1": (30, 20, 44)},
    {"id": "transfig", "name": "Transfigured", "tag": "JJK", "hp": 30, "atk": 9, "defe": 3, "lo": 9, "hi": 15, "weak": "slash", "band": 0, "shape": "blob", "c0": (180, 140, 130), "c1": (110, 70, 70)},
    {"id": "hopper", "name": "Grasshopper", "tag": "JJK", "hp": 32, "atk": 10, "defe": 3, "lo": 10, "hi": 16, "weak": "fire", "band": 0, "shape": "beetle", "c0": (90, 140, 50), "c1": (40, 70, 20)},
    {"id": "shiki", "name": "Shikigami", "tag": "JJK", "hp": 36, "atk": 12, "defe": 4, "lo": 12, "hi": 18, "weak": "holy", "band": 1, "shape": "beast", "c0": (200, 190, 170), "c1": (120, 110, 90)},
    {"id": "finger", "name": "Finger Bearer", "tag": "JJK", "hp": 44, "atk": 14, "defe": 6, "lo": 14, "hi": 22, "weak": "curse", "band": 1, "shape": "skull", "c0": (90, 80, 70), "c1": (40, 34, 28)},
    {"id": "grade1", "name": "Grade 1 Curse", "tag": "JJK", "hp": 48, "atk": 15, "defe": 7, "lo": 16, "hi": 24, "weak": "slash", "band": 1, "shape": "wing", "c0": (60, 40, 70), "c1": (24, 14, 36)},
    {"id": "patch", "name": "Patchwork", "tag": "JJK", "hp": 40, "atk": 16, "defe": 5, "lo": 15, "hi": 23, "weak": "fire", "band": 1, "shape": "clown", "c0": (200, 80, 90), "c1": (90, 30, 40)},
    {"id": "rainbow", "name": "Rainbow Dragon", "tag": "JJK", "hp": 54, "atk": 16, "defe": 8, "lo": 18, "hi": 28, "weak": "shock", "band": 2, "shape": "serpent", "c0": (80, 180, 200), "c1": (30, 90, 120)},
    {"id": "sprout", "name": "Forest Sprout", "tag": "JJK", "hp": 50, "atk": 15, "defe": 9, "lo": 17, "hi": 26, "weak": "fire", "band": 2, "shape": "plant", "c0": (50, 140, 80), "c1": (20, 70, 40)},
    {"id": "disaster", "name": "Disaster Shade", "tag": "JJK", "hp": 58, "atk": 19, "defe": 8, "lo": 21, "hi": 32, "weak": "holy", "band": 3, "shape": "flame", "c0": (160, 40, 200), "c1": (70, 10, 100)},
    {"id": "wheel", "name": "Divine Wheel", "tag": "JJK", "hp": 64, "atk": 20, "defe": 10, "lo": 24, "hi": 36, "weak": "strike", "band": 3, "shape": "drone", "c0": (200, 180, 120), "c1": (120, 90, 40)},
    # HALO 12
    {"id": "grunt", "name": "Grunt", "tag": "HALO", "hp": 24, "atk": 6, "defe": 2, "lo": 7, "hi": 12, "weak": "fire", "band": 0, "shape": "grunt", "c0": (230, 140, 40), "c1": (140, 70, 16)},
    {"id": "grunt_h", "name": "Grunt Heavy", "tag": "HALO", "hp": 30, "atk": 8, "defe": 4, "lo": 9, "hi": 14, "weak": "shock", "band": 0, "shape": "grunt", "c0": (80, 90, 200), "c1": (30, 36, 110)},
    {"id": "jackal", "name": "Jackal", "tag": "HALO", "hp": 26, "atk": 9, "defe": 6, "lo": 8, "hi": 14, "weak": "strike", "band": 0, "shape": "bird", "c0": (200, 170, 70), "c1": (120, 90, 30)},
    {"id": "drone", "name": "Drone", "tag": "HALO", "hp": 22, "atk": 10, "defe": 2, "lo": 9, "hi": 15, "weak": "gun", "band": 0, "shape": "fly", "c0": (70, 90, 50), "c1": (30, 44, 20)},
    {"id": "elite", "name": "Elite", "tag": "HALO", "hp": 40, "atk": 13, "defe": 6, "lo": 13, "hi": 20, "weak": "gun", "band": 1, "shape": "elite", "c0": (40, 160, 90), "c1": (16, 80, 44)},
    {"id": "jackal_s", "name": "Jackal Sniper", "tag": "HALO", "hp": 28, "atk": 16, "defe": 4, "lo": 14, "hi": 21, "weak": "strike", "band": 1, "shape": "bird", "c0": (180, 60, 50), "c1": (90, 24, 20)},
    {"id": "brute", "name": "Brute", "tag": "HALO", "hp": 48, "atk": 15, "defe": 7, "lo": 15, "hi": 23, "weak": "slash", "band": 1, "shape": "ape", "c0": (140, 70, 40), "c1": (70, 30, 16)},
    {"id": "flood", "name": "Flood Pod", "tag": "HALO", "hp": 36, "atk": 14, "defe": 3, "lo": 14, "hi": 22, "weak": "fire", "band": 1, "shape": "blob", "c0": (180, 200, 70), "c1": (90, 110, 30)},
    {"id": "hunter", "name": "Hunter", "tag": "HALO", "hp": 70, "atk": 16, "defe": 12, "lo": 18, "hi": 28, "weak": "shock", "band": 2, "shape": "armor", "c0": (60, 90, 50), "c1": (24, 44, 20)},
    {"id": "sentinel", "name": "Sentinel", "tag": "HALO", "hp": 42, "atk": 15, "defe": 9, "lo": 16, "hi": 25, "weak": "gun", "band": 2, "shape": "drone", "c0": (220, 200, 90), "c1": (140, 120, 30)},
    {"id": "zealot", "name": "Elite Zealot", "tag": "HALO", "hp": 54, "atk": 18, "defe": 8, "lo": 20, "hi": 30, "weak": "gun", "band": 3, "shape": "elite", "c0": (200, 160, 40), "c1": (110, 80, 16)},
    {"id": "chiefbrute", "name": "Chieftain", "tag": "HALO", "hp": 66, "atk": 20, "defe": 10, "lo": 24, "hi": 36, "weak": "slash", "band": 3, "shape": "ape", "c0": (180, 90, 30), "c1": (90, 36, 10)},
) + EXTRA_ENEMIES + MORE_ENEMIES
ENEMY_BY_ID = {e["id"]: e for e in ENEMIES}

TYPE_COLOR = {
    "fire": (230, 90, 40),
    "ice": (90, 180, 230),
    "slash": (200, 200, 210),
    "strike": (220, 160, 70),
    "curse": (160, 70, 210),
    "gun": (90, 110, 90),
    "fruit": (230, 80, 90),
    "holy": (230, 220, 120),
    "dark": (70, 50, 90),
    "shock": (80, 200, 230),
    "water": (50, 130, 210),
    "wind": (160, 220, 180),
    "leaf": (70, 170, 70),
}

FOE_BLAST = {
    "flame": "fire",
    "plant": "leaf",
    "ghost": "curse",
    "serpent": "water",
    "dino": "fire",
    "wing": "wind",
    "beetle": "leaf",
    "bird": "wind",
    "fish": "water",
    "skull": "dark",
    "grunt": "gun",
    "soldier": "gun",
    "armor": "strike",
    "drone": "shock",
    "fly": "wind",
    "blob": "curse",
    "ape": "strike",
    "brute": "strike",
    "agent": "dark",
    "clown": "curse",
    "slug": "leaf",
    "beast": "slash",
    "elite": "holy",
}


def blast_typ_for_enemy(e: dict) -> str:
    return FOE_BLAST.get(str((e or {}).get("shape") or ""), "strike")

EGGS = frozenset(ln["stages"][0] for ln in LINES)


def is_egg_form(form: str) -> bool:
    return form in EGGS

CLAN_CRESTS = ("fang", "sun", "blade", "eye", "ring", "wave")

NET_PORT = 47832
NET_MAGIC = "DGP1"


def item_blurb(it: dict) -> str:
    kind = it.get("kind")
    if kind == "food":
        return f"+{int(it.get('hunger') or 0)}fd +{int(it.get('mood') or 0)}md"
    if kind == "play":
        extra = f" +{int(it['str'])}str" if it.get("str") else ""
        return f"+{int(it.get('mood') or 20)}md{extra}"
    if kind == "heal":
        return "full clean" if it.get("clear_poop") else f"+{int(it.get('hygiene') or 0)} wash"
    if kind == "train":
        return f"+{int(it.get('str') or 4)} str"
    if kind == "hatch":
        return f"-{int(it.get('shave') or 0) // 60}m evo"
    if kind == "gamble":
        return "coins gamble"
    if kind == "chip":
        return "next hit +"
    if kind == "luck":
        return "luckier GO"
    if kind == "map":
        return "safer GO"
    if kind == "flee":
        return "skip hurt"
    return kind or "item"


def move_by_id(line_id: str, mid: str) -> dict | None:
    for m in MOVES.get(line_id, ()):
        if m["id"] == mid:
            return m
    return None


def all_moves_for(line_id: str) -> tuple:
    return MOVES.get(line_id, ())


def move_damage(move: dict, level: int, strength: float, enemy: dict) -> int:
    lv = max(1, min(MOVE_MAX, int(level)))
    raw = move["pow"] + (lv - 1) * move["grow"] + strength * 0.35
    if enemy.get("weak") == move["typ"]:
        raw *= 1.35
    dmg = int(raw - enemy.get("defe", 0) * 0.45)
    return max(1, dmg)


def player_hp(stage_i: int, strength: float) -> int:
    return int(36 + stage_i * 14 + strength * 0.8)


def pick_enemy(tag: str, stage_i: int, strength: float) -> dict:
    band = 0
    if stage_i >= 3 or strength >= 40:
        band = 3
    elif stage_i >= 2 or strength >= 22:
        band = 2
    elif stage_i >= 1 or strength >= 10:
        band = 1
    pool = [e for e in ENEMIES if e["tag"] == tag and e["band"] <= band]
    if not pool:
        pool = [e for e in ENEMIES if e["tag"] == tag]
    return dict(random.choice(pool))


def new_player_id() -> str:
    return str(uuid.uuid4())


def new_clan(leader_id: str, leader_name: str, main: str, name: str, crest: str) -> dict:
    code = "".join(random.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(5))
    return {
        "id": str(uuid.uuid4()),
        "code": code,
        "name": name[:16],
        "crest": crest if crest in CLAN_CRESTS else "fang",
        "leader": leader_id,
        "members": [
            {"id": leader_id, "name": leader_name, "main": main, "power": 0},
        ],
        "wins": 0,
        "losses": 0,
    }


def power_of(partner: dict, line_id: str) -> int:
    mv = sum(int(v) for v in (partner.get("moves") or {}).values())
    return int(
        partner.get("stage_i", 0) * 18
        + partner.get("strength", 0) * 2
        + mv * 7
        + partner.get("mood", 0) * 0.08
        + partner.get("level", 1) * 3
    )


def default_stats() -> dict:
    return {
        "wins": 0,
        "losses": 0,
        "wars_won": 0,
        "wars_lost": 0,
        "hatches": 0,
        "coins_earned": 0,
        "pets": 0,
        "minutes": 0,
        "play_started": 0.0,
        "raids": 0,
    }


def blank_partner() -> dict:
    return {
        "stage_i": 0,
        "hunger": 70,
        "mood": 70,
        "strength": 0,
        "hygiene": 80,
        "poop": False,
        "sleeping": False,
        "feeds": 0,
        "trains": 0,
        "stage_started": 0.0,
        "poop_at": 0.0,
        "cd_feed": 0.0,
        "cd_train": 0.0,
        "cd_play": 0.0,
        "cd_shower": 0.0,
        "moves": {},
        "loadout": [],
        "cd_hatch": {},
    }
