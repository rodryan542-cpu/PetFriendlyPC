#!/usr/bin/env python3
"""Desktop pet. Character walks alone. HUD stays put."""
from __future__ import annotations

import json
import math
import queue
import random
import sys
import time
import uuid
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import numpy as np
import tkinter as tk
from tkinter import messagebox
import ctypes
from ctypes import wintypes

from art import build_all
from paths import asset_root, save_dir
from clan_net import ClanNet
from cutout import binary_rgba, clean_rgba, cutout, stamp_on_body
from catalog_extra import EXTRA_FOES, EXTRA_FORMS, EXTRA_LABELS, EXTRA_PLACES, PICK_PER_PAGE
from depth import ATTACHMENTS, RUN_OBS, combat_stats, dirt_count, gear_of, grant_xp, hatch_mult, pick_raid_boss, roll_hit, enemy_hit
from field import new_raid, new_run, start_raid_wave
from game_data import (
    FOODS,
    ITEMS,
    LINE_BY_ID,
    LINE_NAME,
    LINES,
    default_stats,
    fmt_price,
    fmt_price_short,
    is_egg_form,
    line_price,
    move_by_id,
    new_player_id,
    owned_list,
    owns_line,
    power_of,
    shop_cost,
)
from handlers import give_item, handle, net_event
from panels import PW, PH, GameUI

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    user32.SetProcessDPIAware()

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
ULW_ALPHA = 2
AC_SRC_OVER = 0
AC_SRC_ALPHA = 1


class BLENDFUNCTION(ctypes.Structure):
    _fields_ = [
        ("BlendOp", ctypes.c_byte),
        ("BlendFlags", ctypes.c_byte),
        ("SourceConstantAlpha", ctypes.c_byte),
        ("AlphaFormat", ctypes.c_byte),
    ]


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class SIZE(ctypes.Structure):
    _fields_ = [("cx", ctypes.c_long), ("cy", ctypes.c_long)]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", wintypes.DWORD * 3)]


def hwnd_of(win) -> int:
    win.update_idletasks()
    hwnd = user32.GetParent(win.winfo_id())
    return int(hwnd or win.winfo_id())


def make_layered(hwnd: int) -> None:
    style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED)


def update_layered(hwnd: int, im: Image.Image, x: int, y: int) -> None:
    im = im.convert("RGBA")
    w, h = im.size
    src = np.asarray(im)
    a = src[:, :, 3].astype(np.uint16)
    bgra = np.empty((h, w, 4), dtype=np.uint8)
    bgra[:, :, 0] = (src[:, :, 2].astype(np.uint16) * a // 255).astype(np.uint8)
    bgra[:, :, 1] = (src[:, :, 1].astype(np.uint16) * a // 255).astype(np.uint8)
    bgra[:, :, 2] = (src[:, :, 0].astype(np.uint16) * a // 255).astype(np.uint8)
    bgra[:, :, 3] = src[:, :, 3]
    raw = np.ascontiguousarray(bgra).tobytes()
    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = w
    bmi.bmiHeader.biHeight = -h
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = 0
    hdc_screen = user32.GetDC(0)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
    bits = ctypes.c_void_p()
    hbmp = gdi32.CreateDIBSection(hdc_screen, ctypes.byref(bmi), 0, ctypes.byref(bits), None, 0)
    ctypes.memmove(bits, raw, len(raw))
    old = gdi32.SelectObject(hdc_mem, hbmp)
    blend = BLENDFUNCTION(AC_SRC_OVER, 0, 255, AC_SRC_ALPHA)
    dest = POINT(int(x), int(y))
    srcpt = POINT(0, 0)
    size = SIZE(w, h)
    user32.UpdateLayeredWindow(
        hwnd,
        hdc_screen,
        ctypes.byref(dest),
        ctypes.byref(size),
        hdc_mem,
        ctypes.byref(srcpt),
        0,
        ctypes.byref(blend),
        ULW_ALPHA,
    )
    gdi32.SelectObject(hdc_mem, old)
    gdi32.DeleteObject(hbmp)
    gdi32.DeleteDC(hdc_mem)
    user32.ReleaseDC(0, hdc_screen)

ROOT = save_dir()
ASSETS = asset_root()
SRC = Path(r"C:\Users\bando\.cursor\projects\c-Users-bando-AppData-Local-Temp-trading-ca\assets")
SPRITES = ASSETS / "sprites"
UI = ASSETS / "ui"
STATE_PATH = ROOT / "state.json"
MON2 = (1920, 0, 1920, 1080)

PET_W = 300
PET_H = 230
HUD_W = 284
HUD_H = 166
PROP_W = 96
PROP_H = 96
PROP_N = 3
KEY = (0, 253, 253)
KEY_HEX = "#00fdfd"

FORMS = {
    "egg_agumon": "egg_agumon.png",
    "egg_gabumon": "egg_gabumon.png",
    "egg_zoro": "egg_zoro.png",
    "egg_yuji": "egg_yuji.png",
    "egg_gojo": "egg_gojo.png",
    "egg_arbiter": "egg_arbiter.png",
    "fruit_gomu": "fruit_gomu.png",
    "cryo": "cryo_pod.png",
    "botamon": "botamon_master.png",
    "koromon": "koromon_master.png",
    "agumon": "agumon_master.png",
    "greymon": "greymon_master.png",
    "gabumon": "gabumon_master.png",
    "garurumon": "garurumon_master.png",
    "luffy": "luffy_master.png",
    "luffy_g2": "luffy_g2.png",
    "luffy_g3": "luffy_g3.png",
    "luffy_g4": "luffy_g4.png",
    "luffy2": "luffy2_master.png",
    "zoro": "zoro_master.png",
    "zoro2": "zoro2_master.png",
    "yuji": "yuji_master.png",
    "yuji2": "yuji2_master.png",
    "gojo": "gojo_master.png",
    "gojo2": "gojo2_master.png",
    "chief": "chief_master.png",
    "chief_ar": "chief_ar.png",
    "chief_kit": "chief_kit.png",
    "chief2": "chief2_master.png",
    "arbiter": "arbiter_master.png",
    "arbiter2": "arbiter2_master.png",
}
FORMS.update(EXTRA_FORMS)
LABEL = {
    "egg_agumon": "Agu Egg",
    "egg_gabumon": "Gabu Egg",
    "egg_zoro": "Zoro Egg",
    "egg_yuji": "Yuji Egg",
    "egg_gojo": "Gojo Egg",
    "egg_arbiter": "Elite Egg",
    "fruit_gomu": "Gomu Fruit",
    "cryo": "Cryo Pod",
    "botamon": "Botamon",
    "koromon": "Koromon",
    "agumon": "Agumon",
    "greymon": "Greymon",
    "gabumon": "Gabumon",
    "garurumon": "Garurumon",
    "luffy": "Luffy",
    "luffy_g2": "Gear 2",
    "luffy_g3": "Gear 3",
    "luffy_g4": "Gear 4",
    "luffy2": "Gear 5",
    "zoro": "Zoro",
    "zoro2": "Zoro+",
    "yuji": "Yuji",
    "yuji2": "Yuji+",
    "gojo": "Gojo",
    "gojo2": "Gojo+",
    "chief": "Chief",
    "chief_ar": "Chief AR",
    "chief_kit": "Chief Kit",
    "chief2": "Chief+",
    "arbiter": "Arbiter",
    "arbiter2": "Arbiter+",
}
LABEL.update(EXTRA_LABELS)

WAIT_SEC = (6 * 3600, 12 * 3600, 18 * 3600, 36 * 3600, 72 * 3600)
NEED_STR = (8, 16, 28, 50, 80)
NEED_FEED = (6, 12, 20, 36, 60)
NEED_TRAIN = (3, 8, 14, 24, 40)
CD_TRAIN = 8 * 60
CD_PLAY = 2 * 60

HELP = (
    "MENU opens the pixel house. Pick a MAIN on first boot.\n"
    "HATCH LAB — Warm, lamp, pulse, incubate, carry, candy. They cut real minutes.\n"
    "MOVES — buy, equip three, upgrade to 5. Arena uses the loadout.\n"
    "ARENA — 100+ foes. Type advantage. Struggle if you bought nothing.\n"
    "SWAP pages through 24 partners. SHOP has a bag of 40 items.\n"
    "CLAN — create one, invite anyone on the LAN running this, or type their code. War.\n"
    "GO / FEED / WASH still live on the pad. Drag the pad. They walk alone."
)

QUESTS = (
    {"id": "feed3", "kind": "feed", "need": 3, "reward": 18, "label": "Feed 3 times"},
    {"id": "win1", "kind": "win", "need": 1, "reward": 22, "label": "Win a fight"},
    {"id": "go2", "kind": "go", "need": 2, "reward": 20, "label": "Explore twice"},
    {"id": "train2", "kind": "train", "need": 2, "reward": 16, "label": "Train twice"},
    {"id": "pet5", "kind": "pet", "need": 5, "reward": 14, "label": "Pet them 5x"},
    {"id": "wash1", "kind": "wash", "need": 1, "reward": 10, "label": "Give a wash"},
    {"id": "win3", "kind": "win", "need": 3, "reward": 40, "label": "Win 3 fights"},
    {"id": "shop1", "kind": "shop", "need": 1, "reward": 12, "label": "Buy 1 shop item"},
    {"id": "shop3", "kind": "shop", "need": 3, "reward": 22, "label": "Buy 3 items"},
    {"id": "item2", "kind": "item", "need": 2, "reward": 16, "label": "Use 2 items"},
    {"id": "learn1", "kind": "learn", "need": 1, "reward": 18, "label": "Learn a move"},
    {"id": "tap8", "kind": "eggtap", "need": 8, "reward": 14, "label": "Tap the egg 8x"},
    {"id": "roll2", "kind": "eggroll", "need": 2, "reward": 16, "label": "Roll the egg twice"},
    {"id": "catch1", "kind": "eggcatch", "need": 1, "reward": 18, "label": "Catch a kick"},
    {"id": "wish1", "kind": "eggwish", "need": 1, "reward": 14, "label": "Make a wish"},
)

FOES = {
    "DIGIMON": ("Numemon", "Kuwagamon", "Devimon", "Ogremon", "Seadramon"),
    "ONE PIECE": ("Marine", "Sea King", "Buggy", "Arlong", "Pacifista"),
    "JJK": ("Fly Head", "Cursed Spirit", "Finger Bearer", "Shikigami"),
    "HALO": ("Grunt", "Jackal", "Elite", "Brute", "Hunter"),
}

PLACES = {
    "DIGIMON": ("File Island", "Server Desert", "Infinity Mtn"),
    "ONE PIECE": ("East Blue", "Alabasta", "Skypiea"),
    "JJK": ("Shibuya", "Jujutsu High", "Yasohachi"),
    "HALO": ("Halo Ring", "New Mombasa", "High Charity"),
}
FOES.update(EXTRA_FOES)
PLACES.update(EXTRA_PLACES)

SHOP = (
    ("meat", "MEAT", shop_cost(10)),
    ("toy", "TOY", shop_cost(12)),
    ("med", "MED", shop_cost(15)),
    ("gym", "GYM", shop_cost(8)),
    ("candy", "CANDY", shop_cost(40)),
)


def new_quest(exclude: str | None = None) -> dict:
    pool = [dict(q) for q in QUESTS if q["id"] != exclude]
    q = random.choice(pool)
    q["have"] = 0
    return q

BODY = (28, 30, 34)
BODY_HI = (58, 62, 68)
BODY_SH = (10, 10, 12)
LCD = (8, 16, 10)
LCD_FG = (90, 210, 110)
LCD_DIM = (40, 88, 52)
BTN = (40, 44, 50)
BTN_HI = (88, 94, 102)
BTN_SH = (12, 12, 14)
INK = (220, 224, 228)


def line_of(pid: str) -> dict:
    return LINE_BY_ID[pid]


def blank(pid: str) -> dict:
    now = time.time()
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
        "stage_started": now,
        "poop_at": 0.0,
        "cd_feed": 0.0,
        "cd_train": 0.0,
        "cd_play": 0.0,
        "cd_shower": 0.0,
        "moves": {},
        "loadout": [],
        "cd_hatch": {},
        "cd_egg": {},
        "egg_warmth": 40,
        "egg_kicks": 0,
        "egg_taps": 0,
        "xp": 0,
        "level": 1,
        "gear": {"head": "", "back": "", "held": "", "feet": ""},
    }


def default_state() -> dict:
    return {
        "current": "agumon",
        "main": "agumon",
        "player_id": new_player_id(),
        "player_name": "",
        "coins": 0,
        "streak": 0,
        "quest": new_quest(),
        "clan": None,
        "stats": default_stats(),
        "bag": {},
        "buffs": {},
        "pantry_i": 0,
        "inbox": [],
        "gear_bag": {},
        "owned": [],
        "partners": {ln["id"]: blank(ln["id"]) for ln in LINES},
    }


def load_state() -> dict:
    st = default_state()
    if not STATE_PATH.exists():
        return st
    try:
        raw = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return st
    if not isinstance(raw, dict):
        return st
    partners = raw.get("partners") or {}
    for ln in LINES:
        pid = ln["id"]
        p = blank(pid)
        old = partners.get(pid)
        if isinstance(old, dict):
            for k in p:
                if k in old:
                    p[k] = old[k]
            if "stage" in old and old["stage"] in ln["stages"]:
                p["stage_i"] = ln["stages"].index(old["stage"])
        p["stage_i"] = max(0, min(int(p["stage_i"]), len(ln["stages"]) - 1))
        st["partners"][pid] = p
    cur = raw.get("current")
    st["current"] = cur if cur in LINE_BY_ID else "agumon"
    try:
        st["coins"] = max(0, int(raw.get("coins") or 0))
    except (TypeError, ValueError):
        st["coins"] = 0
    q = raw.get("quest")
    if isinstance(q, dict) and q.get("id") and q.get("kind") and q.get("label"):
        q.setdefault("have", 0)
        q.setdefault("need", 1)
        q.setdefault("reward", 10)
        st["quest"] = q
    else:
        st["quest"] = new_quest()
    try:
        st["streak"] = max(0, int(raw.get("streak") or 0))
    except (TypeError, ValueError):
        st["streak"] = 0
    bag = raw.get("bag")
    st["bag"] = {str(k): int(v) for k, v in bag.items() if int(v) > 0} if isinstance(bag, dict) else {}
    buffs = raw.get("buffs")
    st["buffs"] = dict(buffs) if isinstance(buffs, dict) else {}
    if not raw.get("got_starter"):
        st["coins"] = max(st["coins"], 25)
        st["got_starter"] = True
    else:
        st["got_starter"] = True
    pid = raw.get("player_id")
    st["player_id"] = pid if isinstance(pid, str) and len(pid) > 8 else new_player_id()
    name = raw.get("player_name")
    st["player_name"] = name[:16] if isinstance(name, str) else ""
    main = raw.get("main")
    st["main"] = main if main in LINE_BY_ID else st["current"]
    clan = raw.get("clan")
    st["clan"] = clan if isinstance(clan, dict) and clan.get("id") else None
    stats = raw.get("stats")
    st["stats"] = default_stats()
    if isinstance(stats, dict):
        for k in st["stats"]:
            if k in stats:
                st["stats"][k] = stats[k]
    try:
        st["pantry_i"] = max(0, int(raw.get("pantry_i") or 0))
    except (TypeError, ValueError):
        st["pantry_i"] = 0
    for pid, p in st["partners"].items():
        if not isinstance(p.get("moves"), dict):
            p["moves"] = {}
        if not isinstance(p.get("loadout"), list):
            p["loadout"] = []
        if not isinstance(p.get("cd_hatch"), dict):
            p["cd_hatch"] = {}
        if not isinstance(p.get("cd_egg"), dict):
            p["cd_egg"] = {}
        p["egg_warmth"] = max(0, min(100, int(p.get("egg_warmth") or 40)))
        p["egg_kicks"] = max(0, int(p.get("egg_kicks") or 0))
        p["egg_taps"] = max(0, int(p.get("egg_taps") or 0))
        if not isinstance(p.get("gear"), dict):
            p["gear"] = {"head": "", "back": "", "held": "", "feet": ""}
        p["level"] = max(1, min(30, int(p.get("level") or 1)))
        p["xp"] = max(0, int(p.get("xp") or 0))
    inbox = raw.get("inbox")
    st["inbox"] = inbox[-40:] if isinstance(inbox, list) else []
    gb = raw.get("gear_bag")
    st["gear_bag"] = {str(k): int(v) for k, v in gb.items() if int(v) > 0} if isinstance(gb, dict) else {}
    owned = owned_list({"owned": raw.get("owned")})
    if owned:
        st["owned"] = owned
    elif st.get("player_name"):
        main = st["main"] if st["main"] in LINE_BY_ID else st["current"]
        st["owned"] = [main] if main in LINE_BY_ID else []
    else:
        st["owned"] = []
    if st.get("player_name") and st["main"] in LINE_BY_ID and st["main"] not in st["owned"]:
        st["owned"].insert(0, st["main"])
    if st["owned"] and st["current"] not in st["owned"]:
        st["current"] = st["owned"][0]
    return st


def save_state(st: dict) -> None:
    STATE_PATH.write_text(json.dumps(st, indent=2), encoding="utf-8")


def prepare(name: str) -> Path:
    dest = SPRITES / name
    src = SRC / name
    if not src.exists():
        return dest
    SPRITES.mkdir(parents=True, exist_ok=True)
    cutout(src).save(dest)
    return dest


def harden(im: Image.Image) -> Image.Image:
    return clean_rgba(im, crop=True)


def load_rgba(name: str) -> Image.Image:
    path = SPRITES / name
    if not path.exists():
        path = prepare(name)
    if path.exists():
        return harden(Image.open(path))
    return Image.new("RGBA", (64, 64), (0, 0, 0, 0))


def load_ui(name: str) -> Image.Image:
    path = UI / name
    if path.exists():
        return binary_rgba(Image.open(path).convert("RGBA"))
    return Image.new("RGBA", (32, 32), (0, 0, 0, 0))


def fit_h(im: Image.Image, h: int) -> Image.Image:
    if im.height <= 0:
        return im
    nw = max(8, int(im.width * (h / im.height)))
    return im.resize((nw, h), Image.Resampling.NEAREST)


def key_fill(im: Image.Image) -> Image.Image:
    arr = np.array(im)
    empty = arr[:, :, 3] == 0
    arr[empty, 0] = KEY[0]
    arr[empty, 1] = KEY[1]
    arr[empty, 2] = KEY[2]
    arr[empty, 3] = 255
    return Image.fromarray(arr, "RGBA")


def font(size: int, mono: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    path = Path(r"C:\Windows\Fonts\consola.ttf" if mono else r"C:\Windows\Fonts\segoeui.ttf")
    if path.exists():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def bevel(draw: ImageDraw.ImageDraw, box, face, hi, sh) -> None:
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=face)
    draw.line([(x0, y0), (x1 - 1, y0)], fill=hi)
    draw.line([(x0, y0), (x0, y1 - 1)], fill=hi)
    draw.line([(x1 - 1, y0), (x1 - 1, y1 - 1)], fill=sh)
    draw.line([(x0, y1 - 1), (x1, y1 - 1)], fill=sh)


def _overlap_box(a, b) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by


def fmt_left(sec: float) -> str:
    sec = max(0, int(sec))
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    if h >= 24:
        d, h = divmod(h, 24)
        return f"{d}d {h}h"
    if h:
        return f"{h}h {m:02d}m"
    return f"{m:02d}m {s:02d}s"


class DigimonPet:
    def __init__(self) -> None:
        if not getattr(sys, "frozen", False):
            build_all()
        SPRITES.mkdir(parents=True, exist_ok=True)
        needed = list(FORMS.values()) + ["prop_bed.png", "food_meat.png", "poop.png"]
        for n in needed:
            if not (SPRITES / n).exists() and (SRC / n).exists():
                prepare(n)
        self.forms = {k: load_rgba(v) for k, v in FORMS.items()}
        self.bed = load_rgba("prop_bed.png")
        self.poop_im = load_rgba("poop.png")
        self.meat_im = load_rgba("food_meat.png")
        self.food_ims = {}
        for it in FOODS:
            path = UI / f"food_{it['id']}.png"
            if path.exists():
                self.food_ims[it["id"]] = binary_rgba(Image.open(path).convert("RGBA"))
        if "meat" not in self.food_ims:
            self.food_ims["meat"] = self.meat_im
        self.gear_ims = {}
        for a in ATTACHMENTS:
            path = UI / f"gear_{a['id']}.png"
            if path.exists():
                self.gear_ims[a["id"]] = binary_rgba(Image.open(path).convert("RGBA"))
        self.dirt_ims = {}
        for key in ("light", "mid", "heavy"):
            path = UI / f"dirt_{key}.png"
            if path.exists():
                self.dirt_ims[key] = binary_rgba(Image.open(path).convert("RGBA"))
        self.obs_ims = {}
        for spec in RUN_OBS:
            path = UI / f"run_{spec['id']}.png"
            if path.exists():
                self.obs_ims[spec["id"]] = binary_rgba(Image.open(path).convert("RGBA"))
        self.eat_id = "meat"
        self.save = load_state()
        self.anim = "idle"
        self.facing = 1
        self.anim_until = 0.0
        self.next_ai = time.time() + 6
        self.last_tick = time.time()
        self.hunger_acc = 0.0
        self._pet_pos = (-1, -1)
        self.pet_hwnd = 0
        self.hud_hwnd = 0
        self.panel_hwnd = 0
        self.panel_open = False
        self.sheet_vis = 0.0
        self.ui = GameUI()
        self.net = None
        self.picker = False
        self.pick_page = 0
        self.shop_open = False
        self.showering = False
        self.exploring = False
        self.fighting = False
        self.fx: list[dict] = []
        self._foe = ""
        self._place = ""
        self.hits: list[tuple[str, tuple[int, int, int, int]]] = []
        self.lcd_flash = ""
        self.lcd_until = 0.0
        self.f_lcd = font(13, True)
        self.f_tiny = font(11, True)
        self.f_btn = font(11, True)

        mx, my, mw, mh = MON2
        self.hud_x = float(mx + (mw - HUD_W) // 2)
        self.hud_y = float(my + mh - HUD_H - 10)
        self.x = float(mx + 380)
        self.y = float(self.hud_y - PET_H - 4)
        self.dragging = False
        self._grab = (0.0, 0.0)

        self.root = tk.Tk()
        self._chrome(self.root)
        self.root.geometry(f"{PET_W}x{PET_H}+{int(self.x)}+{int(self.y)}")
        self.root.bind("<Button-1>", self.on_pet_click)
        self.root.bind("<Button-3>", self.on_right)

        self.hud = tk.Toplevel(self.root)
        self._chrome(self.hud)
        self.hud.geometry(f"{HUD_W}x{HUD_H}+{int(self.hud_x)}+{int(self.hud_y)}")
        self.hud.bind("<Button-1>", self.on_hud_down)
        self.hud.bind("<B1-Motion>", self.on_hud_drag)
        self.hud.bind("<ButtonRelease-1>", self.on_up)
        self.hud.bind("<Button-3>", self.on_right)

        self.panel_x = float(self.hud_x + (HUD_W - PW) / 2)
        self.panel_y = float(self.hud_y)
        self.panel = tk.Toplevel(self.root)
        self._chrome(self.panel)
        self.panel.geometry(f"{PW}x{PH}+{int(self.panel_x)}+{int(self.panel_y)}")
        self.panel.bind("<Button-1>", self.on_panel_down)
        self.panel.bind("<B1-Motion>", self.on_panel_drag)
        self.panel.bind("<ButtonRelease-1>", self.on_up)

        self.field_mode = None
        self.field_state = None
        self.field_jump = False
        self.raid_queued = False
        self.combat_over_at = 0.0
        self.air = 0.0
        self.air_v = 0.0
        self.foe_on = False
        self.foe_src = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        self.foe_name = ""
        self.foe_x = float(mx + mw - PET_W - 24)
        self.foe_y = float(self.hud_y - PET_H - 4)
        self.foe_facing = -1
        self.foe_hwnd = 0
        self.prop_hwnds: list[int] = []
        self.props: list = []
        self.foe = tk.Toplevel(self.root)
        self._chrome(self.foe)
        self.foe.geometry(f"{PET_W}x{PET_H}+{-4000}+{-4000}")
        for _ in range(PROP_N):
            win = tk.Toplevel(self.root)
            self._chrome(win)
            win.geometry(f"{PROP_W}x{PROP_H}+{-4000}+{-4000}")
            self.props.append(win)

        self.menu = tk.Menu(self.root, tearoff=0)
        by_tag: dict[str, list] = {}
        for ln in LINES:
            by_tag.setdefault(ln["tag"], []).append(ln)
        for tag, rows in by_tag.items():
            sub = tk.Menu(self.menu, tearoff=0)
            for ln in rows:
                sub.add_command(label=LINE_NAME[ln["id"]], command=lambda x=ln["id"]: self.set_partner(x))
            self.menu.add_cascade(label=tag, menu=sub)
        self.menu.add_command(label="Shop", command=lambda: self.open_panel("shop"))
        self.menu.add_command(label="Hatch lab", command=lambda: self.open_panel("hatch"))
        self.menu.add_command(label="Moves", command=lambda: self.open_panel("moves"))
        self.menu.add_command(label="Arena", command=lambda: self.open_panel("fight"))
        self.menu.add_command(label="Clan", command=lambda: self.open_panel("clan"))
        self.menu.add_command(label="Stats", command=lambda: self.open_panel("stats"))
        self.menu.add_command(label="How to play", command=self.show_help)
        self.menu.add_command(label="Quit", command=self.quit)

        self.root.update_idletasks()
        self.hud.update_idletasks()
        self.panel.update_idletasks()
        self.foe.update_idletasks()
        for win in self.props:
            win.update_idletasks()
        self.pet_hwnd = hwnd_of(self.root)
        self.hud_hwnd = hwnd_of(self.hud)
        self.panel_hwnd = hwnd_of(self.panel)
        self.foe_hwnd = hwnd_of(self.foe)
        self.prop_hwnds = [hwnd_of(win) for win in self.props]
        make_layered(self.pet_hwnd)
        make_layered(self.hud_hwnd)
        make_layered(self.panel_hwnd)
        make_layered(self.foe_hwnd)
        for hwnd in self.prop_hwnds:
            make_layered(hwnd)
        self.root.bind("<space>", self.on_field_space)
        self.hud.bind("<space>", self.on_field_space)
        self.net = ClanNet(self.presence)
        self.net.start()
        if not self.save.get("player_name"):
            self.ui.mode = "starter"
            self.panel_open = True
        else:
            self.ui.mode = "together"
        self.redraw()
        self.root.after(33, self.loop)

    def _chrome(self, win: tk.Tk | tk.Toplevel) -> None:
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(bg="black")

    def p(self) -> dict:
        return self.save["partners"][self.save["current"]]

    def ln(self) -> dict:
        return line_of(self.save["current"])

    def form(self) -> str:
        stages = self.ln()["stages"]
        i = max(0, min(self.p()["stage_i"], len(stages) - 1))
        return stages[i]

    def form_label(self) -> str:
        return LABEL[self.form()]

    def _wait_sec(self, i: int) -> float:
        return float(WAIT_SEC[min(max(0, i), len(WAIT_SEC) - 1)])

    def presence(self) -> dict:
        clan = self.save.get("clan") or {}
        main = self.save.get("main") or self.save.get("current")
        p = self.save["partners"].get(main) or self.p()
        return {
            "pid": self.save.get("player_id"),
            "name": self.save.get("player_name") or "Trainer",
            "main": main,
            "power": power_of(p, main),
            "clan_id": clan.get("id"),
            "clan_name": clan.get("name"),
            "clan_code": clan.get("code"),
            "wins": int((self.save.get("stats") or {}).get("wins") or 0),
            "hp": int(36 + p.get("stage_i", 0) * 14 + p.get("strength", 0) * 0.8),
            "str": int(p.get("strength") or 0),
            "form": self.form() if main == self.save.get("current") else None,
            "raid": bool(getattr(self, "raid_queued", False)),
        }

    def ask_text(self, title: str, prompt: str, default: str = "") -> str:
        win = tk.Toplevel(self.root)
        win.title(title)
        win.attributes("-topmost", True)
        mx, my, mw, mh = MON2
        win.geometry(f"340x110+{mx + 400}+{my + 280}")
        tk.Label(win, text=prompt).pack(pady=6)
        var = tk.StringVar(value=default)
        entry = tk.Entry(win, textvariable=var, width=28)
        entry.pack()
        entry.focus_set()
        out = {"v": ""}

        def ok(_e=None):
            out["v"] = var.get().strip()
            win.destroy()

        tk.Button(win, text="OK", command=ok).pack(pady=6)
        win.bind("<Return>", ok)
        self.root.wait_window(win)
        return out["v"]

    def open_panel(self, mode: str) -> None:
        if mode == "hub":
            mode = "together"
        if mode == "menu":
            mode = "starter" if not self.save.get("player_name") else "together"
        self.ui.mode = mode
        self.panel_open = True
        self.shop_open = False
        self.picker = False

    def persist(self) -> None:
        save_state(self.save)

    def quit(self) -> None:
        self.persist()
        if self.net:
            self.net.stop()
        self.root.destroy()

    def hit(self, x: int, y: int) -> str | None:
        for name, (x0, y0, x1, y1) in self.hits:
            if x0 <= x <= x1 and y0 <= y <= y1:
                return name
        return None

    def toggle_shop(self) -> None:
        self.open_panel("shop")

    def flash(self, msg: str) -> None:
        self.lcd_flash = msg
        self.lcd_until = time.time() + 2.4

    def pop(self, text: str, color: tuple[int, int, int] = (255, 220, 80), kind: str = "text") -> None:
        self.fx.append(
            {
                "text": text,
                "x": PET_W // 2 + random.randint(-36, 28),
                "y": 70 + random.randint(-16, 20),
                "born": time.time(),
                "color": color,
                "vy": -48 - random.randint(0, 18),
                "kind": kind,
            }
        )

    def quest_tick(self, kind: str, n: int = 1) -> None:
        q = self.save.get("quest")
        if not isinstance(q, dict) or q.get("kind") != kind:
            return
        q["have"] = int(q.get("have") or 0) + n
        need = max(1, int(q.get("need") or 1))
        if q["have"] >= need:
            reward = max(1, int(q.get("reward") or 10))
            self.save["coins"] = int(self.save.get("coins", 0)) + reward
            self.flash(f"QUEST +${reward}")
            self.pop(f"QUEST +${reward}", (120, 255, 150))
            self.save["quest"] = new_quest(exclude=str(q.get("id")))
        else:
            self.save["quest"] = q
        self.persist()

    def on_pet_click(self, _e) -> None:
        if self.field_mode == "run":
            self.field_jump = True
            return
        self.play()

    def on_hud_down(self, e) -> None:
        action = self.hit(e.x, e.y)
        if action == "drag" or action is None:
            self.dragging = True
            self._grab = (e.x_root - self.hud_x, e.y_root - self.hud_y)
            return
        self.dragging = False
        if action == "feed":
            self.feed()
        elif action == "train":
            self.train()
        elif action == "play":
            self.play()
        elif action == "fight":
            if self.field_mode:
                self.close_field()
            else:
                handle(self, "fight_start")
        elif action == "menu":
            if self.panel_open and self.ui.mode in ("together", "starter"):
                self.panel_open = False
            else:
                self.open_panel("together")
        elif action == "hatch":
            if self.panel_open and self.ui.mode == "hatch":
                self.panel_open = False
            else:
                self.open_panel("hatch")
        elif action == "go":
            self.explore()
        elif action == "bed":
            self.toggle_sleep()
        elif action == "shower":
            self.do_shower()
        elif action == "evo":
            self.evolve()
        elif action == "swap":
            self.picker = not self.picker
            self.shop_open = False
        elif action == "shop":
            self.toggle_shop()
        elif action == "help":
            self.show_help()
        elif action == "toast_yes":
            handle(self, "toast_yes")
        elif action == "toast_no":
            handle(self, "toast_no")
        elif action and action.startswith("atk:"):
            self._combat_atk(action.split(":", 1)[1])
        elif action and action.startswith("pick:"):
            self.set_partner(action.split(":", 1)[1])
            self.picker = False
        elif action == "pick_next":
            handle(self, "pick_next")
        elif action and action.startswith("buy:"):
            self.buy(action.split(":", 1)[1])

    def on_hud_drag(self, e) -> None:
        if not self.dragging:
            return
        mx, my, mw, mh = MON2
        self.hud_x = min(max(e.x_root - self._grab[0], mx + 8), mx + mw - HUD_W - 8)
        self.hud_y = min(max(e.y_root - self._grab[1], my + 8), my + mh - HUD_H - 8)
        self.hud.geometry(f"{HUD_W}x{HUD_H}+{int(self.hud_x)}+{int(self.hud_y)}")
        self._dock_sheet()

    def on_panel_down(self, e) -> None:
        if not self.panel_open:
            return
        action = self.ui.click(self, e.x, e.y)
        if action == "drag" or action is None:
            self.dragging = True
            self._grab = (e.x_root - self.hud_x, e.y_root - self.hud_y)
            return
        self.dragging = False
        handle(self, action)

    def on_panel_drag(self, e) -> None:
        if not self.dragging:
            return
        self.on_hud_drag(e)

    def _dock_sheet(self) -> None:
        mx, my, mw, mh = MON2
        self.panel_x = min(max(self.hud_x + (HUD_W - PW) / 2, mx + 8), mx + mw - PW - 8)
        if self.hud_y - PH >= my + 8:
            self.panel_y = self.hud_y - PH * self.sheet_vis
        else:
            self.panel_y = self.hud_y + HUD_H * self.sheet_vis

    def on_up(self, _e) -> None:
        self.dragging = False

    def on_right(self, e) -> None:
        self.menu.tk_popup(e.x_root, e.y_root)

    def evo_status(self) -> tuple[bool, str]:
        p = self.p()
        stages = self.ln()["stages"]
        i = p["stage_i"]
        if i >= len(stages) - 1:
            return False, "MAX"
        wait = WAIT_SEC[min(i, len(WAIT_SEC) - 1)]
        left = wait - (time.time() - p["stage_started"])
        need_s = NEED_STR[min(i, len(NEED_STR) - 1)]
        need_f = NEED_FEED[min(i, len(NEED_FEED) - 1)]
        need_t = NEED_TRAIN[min(i, len(NEED_TRAIN) - 1)]
        if left > 0:
            return False, fmt_left(left)
        missing = []
        if p["feeds"] < need_f:
            missing.append(f"Fd {p['feeds']}/{need_f}")
        if p["trains"] < need_t:
            missing.append(f"Tr {p['trains']}/{need_t}")
        if p["strength"] < need_s:
            missing.append(f"Str {int(p['strength'])}/{need_s}")
        if p["hygiene"] < 35:
            missing.append("Wash")
        if missing:
            return False, " ".join(missing[:2])
        return True, "READY"

    def body(self, h: int) -> Image.Image:
        im = fit_h(self.forms[self.form()].copy(), h)
        if self.facing < 0:
            im = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        return self._with_gear_dirt(im)

    def _with_gear_dirt(self, im: Image.Image) -> Image.Image:
        p = self.p()
        w, h = im.size
        gear = gear_of(p)
        back = gear.get("back") or ""
        if back and back in self.gear_ims:
            g = fit_h(self.gear_ims[back].copy(), max(18, h // 3))
            im.paste(g, (max(0, w // 2 - g.width // 2 - 8), max(0, h // 3 - 4)), g)
        head = gear.get("head") or ""
        if head and head in self.gear_ims:
            g = fit_h(self.gear_ims[head].copy(), max(16, h // 4))
            im.paste(g, (max(0, w // 2 - g.width // 2), 2), g)
        held = gear.get("held") or ""
        if held and held in self.gear_ims:
            g = fit_h(self.gear_ims[held].copy(), max(14, h // 5))
            hx = w - g.width - 2 if self.facing >= 0 else 2
            im.paste(g, (hx, h // 2), g)
        feet = gear.get("feet") or ""
        if feet and feet in self.gear_ims:
            g = fit_h(self.gear_ims[feet].copy(), max(12, h // 6))
            im.paste(g, (max(0, w // 2 - g.width // 2), h - g.height - 2), g)
        n = dirt_count(int(p.get("hygiene") or 80))
        if n:
            key = "heavy" if n >= 28 else ("mid" if n >= 18 else "light")
            sheet = self.dirt_ims.get(key)
            if sheet:
                dirt = sheet.resize((w, h), Image.Resampling.NEAREST)
                im = stamp_on_body(im, dirt)
        return binary_rgba(im)

    def render_pet(self) -> Image.Image:
        canvas = Image.new("RGBA", (PET_W, PET_H), (0, 0, 0, 0))
        p = self.p()
        t = time.time()
        anim = self.anim
        if p["sleeping"]:
            anim = "sleep"
        if self.showering:
            anim = "shower"

        if anim == "sleep":
            self._draw_bed(canvas)
        elif anim == "shower":
            self._draw_shower(canvas, t)
        else:
            im = self.body(150)
            bob = 0.0
            rot = 0.0
            shake = 0
            squash = 1.0
            if anim == "idle":
                squash = 1.0 + 0.02 * math.sin(t * 2.6)
            elif anim == "hungry":
                squash = 1.0 + 0.014 * math.sin(t * 2.0)
            elif anim == "walk":
                bob = abs(math.sin(t * 8.2)) * 8
                rot = math.sin(t * 8.2) * 3.0
            elif anim in ("happy", "play", "evo"):
                bob = abs(math.sin(t * 10.0)) * 14
            elif anim == "train":
                shake = int(math.sin(t * 18.0) * 5)
                bob = abs(math.sin(t * 11.0)) * 5
            elif anim == "eat":
                squash = 1.04 + 0.03 * math.sin(t * 12.0)
            if rot:
                im = im.rotate(rot, expand=True, resample=Image.Resampling.NEAREST)
            nh = max(8, int(im.height * squash))
            im = im.resize((im.width, nh), Image.Resampling.NEAREST)
            x = (PET_W - im.width) // 2 + shake
            y = PET_H - im.height - 6 - int(bob)
            canvas.paste(im, (x, y), im)
            if anim == "eat":
                food = self.food_ims.get(getattr(self, "eat_id", "meat")) or self.meat_im
                m = fit_h(food.copy(), 28)
                canvas.paste(m, (x + im.width - 8, y + im.height // 3), m)
            if p["poop"]:
                po = fit_h(self.poop_im.copy(), 26)
                canvas.paste(po, (12, PET_H - po.height - 2), po)
        self._draw_fx(canvas, t)
        return canvas

    def _draw_fx(self, canvas: Image.Image, t: float) -> None:
        keep: list[dict] = []
        d = ImageDraw.Draw(canvas)
        for f in self.fx:
            age = t - float(f["born"])
            if age > 1.7:
                continue
            fade = max(0, min(255, int(255 * (1.0 - age / 1.7))))
            x = int(f["x"])
            y = int(f["y"] + float(f["vy"]) * age)
            col = tuple(f["color"]) + (fade,)
            if f.get("kind") == "heart":
                d.text((x, y), "♥", font=self.f_lcd, fill=col)
            else:
                d.text((x, y), str(f["text"]), font=self.f_tiny, fill=col)
            keep.append(f)
        self.fx = keep

    def _draw_bed(self, canvas: Image.Image) -> None:
        bed = fit_h(self.bed.copy(), 150)
        bx = (PET_W - bed.width) // 2
        by = PET_H - bed.height + 8
        canvas.paste(bed, (bx, by), bed)
        body = fit_h(self.forms[self.form()].copy(), 118)
        recline = body.rotate(86, expand=True, resample=Image.Resampling.NEAREST)
        lx = bx + 28
        ly = by + 22
        canvas.paste(recline, (lx, ly), recline)

    def _draw_shower(self, canvas: Image.Image, t: float) -> None:
        d = ImageDraw.Draw(canvas)
        cx = PET_W // 2
        d.ellipse((cx - 48, PET_H - 22, cx + 48, PET_H - 4), fill=(70, 78, 86), outline=(40, 44, 48))
        d.rectangle((cx + 40, 20, cx + 46, PET_H - 24), fill=(150, 156, 164), outline=(60, 64, 70))
        d.rectangle((cx - 8, 16, cx + 46, 22), fill=(150, 156, 164), outline=(60, 64, 70))
        d.ellipse((cx - 22, 8, cx + 16, 30), fill=(188, 194, 202), outline=(60, 64, 70))
        im = self.body(140)
        im = im.resize((im.width, max(8, int(im.height * (1.0 + 0.02 * math.sin(t * 9))))), Image.Resampling.NEAREST)
        x = cx - im.width // 2 - 8
        y = PET_H - im.height - 14
        canvas.paste(im, (x, y), im)
        for i in range(40):
            wx = cx - 16 + (i * 2) % 30 + int(math.sin(t * 12 + i) * 2)
            wy = 30 + int((t * 110 + i * 11) % 140)
            if wy < PET_H - 18:
                d.point((wx, wy), fill=(230, 240, 248))
                d.point((wx, wy + 1), fill=(170, 210, 235))

    def render_hud(self) -> Image.Image:
        hud = Image.new("RGBA", (HUD_W, HUD_H), (0, 0, 0, 0))
        d = ImageDraw.Draw(hud)
        bevel(d, (0, 0, HUD_W, HUD_H), BODY, BODY_HI, BODY_SH)
        bevel(d, (6, 6, HUD_W - 6, 72), LCD, (4, 10, 6), (20, 48, 24))

        p = self.p()
        name = LABEL[self.form()]
        tag = self.ln()["tag"]
        ready, evo_txt = self.evo_status()
        q = self.save.get("quest") if isinstance(self.save.get("quest"), dict) else {}
        toast = None
        if self.ui.pending_chal:
            toast = f"FIGHT {self.ui.pending_chal.get('from_name', '?')}"
        elif self.ui.pending_invite:
            toast = f"CLAN {self.ui.pending_invite.get('from_name', '?')}"
        if toast:
            d.text((14, 14), toast[:20].upper(), font=self.f_lcd, fill=(220, 210, 80))
            d.text((14, 36), "ON THE PAD", font=self.f_tiny, fill=LCD_DIM)
            bevel(d, (168, 28, 214, 52), (40, 70, 40), BTN_HI, BTN_SH)
            bevel(d, (220, 28, 266, 52), (70, 30, 30), BTN_HI, BTN_SH)
            d.text((176, 34), "YES", font=self.f_btn, fill=INK)
            d.text((228, 34), "NO", font=self.f_btn, fill=INK)
        elif time.time() < self.lcd_until and self.lcd_flash:
            d.text((14, 26), self.lcd_flash[:24], font=self.f_lcd, fill=LCD_FG)
        else:
            d.text((14, 10), name, font=self.f_lcd, fill=LCD_FG)
            tw = d.textlength(tag, font=self.f_tiny)
            d.text((HUD_W - 12 - tw, 12), tag, font=self.f_tiny, fill=LCD_DIM)

            def meter(label: str, val: float, y: int):
                d.text((14, y), label, font=self.f_tiny, fill=LCD_DIM)
                x0, x1, by = 40, 156, y + 4
                d.rectangle((x0, by, x1, by + 5), fill=(4, 10, 6))
                fill = int((x1 - x0) * max(0, min(100, val)) / 100)
                if fill:
                    d.rectangle((x0, by, x0 + fill, by + 5), fill=LCD_FG)

            meter("FD", p["hunger"], 28)
            meter("MD", p["mood"], 40)
            extra = "DIRT" if int(p.get("hygiene") or 80) < 50 else ("POOP" if p["poop"] else ("ZZZ" if p["sleeping"] else evo_txt))
            col = (220, 210, 70) if ready else LCD_DIM
            streak = int(self.save.get("streak") or 0)
            st_txt = f"ST {int(p['strength']):02d}" + (f" x{streak}" if streak >= 2 else "")
            d.text((164, 28), st_txt, font=self.f_tiny, fill=LCD_FG)
            d.text((164, 40), f"${int(self.save.get('coins', 0))} {extra[:6]}", font=self.f_tiny, fill=col)
            d.text((164, 52), f"HY {int(p.get('hygiene') or 0)} Lv{int(p.get('level') or 1)}", font=self.f_tiny, fill=LCD_DIM)
            qline = f"Q {q.get('label', '—')} {int(q.get('have') or 0)}/{int(q.get('need') or 1)}"
            d.text((14, 54), qline[:22], font=self.f_tiny, fill=(70, 190, 100))

        self.hits = []
        if toast:
            self.hits.append(("toast_yes", (168, 28, 214, 52)))
            self.hits.append(("toast_no", (220, 28, 266, 52)))
        self.hits.append(("swap", (8, 8, 150, 26)))
        self.hits.append(("drag", (0, 0, HUD_W, 72)))
        if self.picker:
            gap, bw, bh = 4, 64, 24
            page = int(getattr(self, "pick_page", 0) or 0)
            chunk = LINES[page * PICK_PER_PAGE : page * PICK_PER_PAGE + PICK_PER_PAGE]
            for i, ln in enumerate(chunk):
                col, row = i % 3, i // 3
                x0 = 8 + col * (bw + gap)
                y0 = 78 + row * (bh + 4)
                on = ln["id"] == self.save["current"]
                have = owns_line(self.save, ln["id"])
                face = (70, 86, 52) if on else BTN
                bevel(d, (x0, y0, x0 + bw, y0 + bh), face, BTN_HI, BTN_SH)
                lab = LINE_NAME[ln["id"]][:8] if have else fmt_price_short(line_price(ln["id"]))
                d.text((x0 + 6, y0 + 5), lab, font=self.f_btn, fill=INK if have else (220, 210, 80))
                self.hits.append((f"pick:{ln['id']}", (x0, y0, x0 + bw, y0 + bh)))
            x0, y0 = 8 + 3 * (bw + gap), 78
            bevel(d, (x0, y0, x0 + bw, y0 + bh), (70, 86, 52), BTN_HI, BTN_SH)
            pages = max(1, (len(LINES) + PICK_PER_PAGE - 1) // PICK_PER_PAGE)
            d.text((x0 + 8, y0 + 5), f"{page + 1}/{pages}", font=self.f_btn, fill=INK)
            self.hits.append(("pick_next", (x0, y0, x0 + bw, y0 + bh)))
        elif self.shop_open:
            gap, bw, bh = 4, 64, 24
            for i, (key, label, price) in enumerate(SHOP):
                col, row = i % 3, i // 3
                x0 = 8 + col * (bw + gap)
                y0 = 78 + row * (bh + 4)
                bevel(d, (x0, y0, x0 + bw, y0 + bh), (52, 58, 44), BTN_HI, BTN_SH)
                d.text((x0 + 5, y0 + 5), f"{label}{fmt_price_short(price)}", font=self.f_tiny, fill=INK)
                self.hits.append((f"buy:{key}", (x0, y0, x0 + bw, y0 + bh)))
            x0, y0 = 8 + 2 * (bw + gap), 78 + (bh + 4)
            bevel(d, (x0, y0, x0 + bw, y0 + bh), BTN, BTN_HI, BTN_SH)
            tw = d.textlength("BACK", font=self.f_btn)
            d.text((x0 + (bw - tw) / 2, y0 + 4), "BACK", font=self.f_btn, fill=INK)
            self.hits.append(("shop", (x0, y0, x0 + bw, y0 + bh)))
        else:
            if self.field_mode == "run":
                row1 = (("fight", "LEAVE"), ("hatch", "HATCH"), ("menu", "MENU"), ("help", "HELP"))
                row2 = (("go", "GO"), ("shop", "SHOP"), ("swap", "SWAP"), ("evo", "EVO"))
                row3 = (("bed", "BED"), ("shower", "WASH"), ("feed", "FEED"), ("train", "TRN"))
            elif self._combat_live():
                moves = self._hud_moves()
                row1 = [(f"atk:{mid}", lab) for mid, lab in moves]
                while len(row1) < 4:
                    row1.append(("atk:struggle", "STRUG"))
                row1 = row1[:4]
                row2 = (("fight", "FLEE"), ("shop", "SHOP"), ("hatch", "HATCH"), ("menu", "MENU"))
                row3 = (("bed", "BED"), ("shower", "WASH"), ("swap", "SWAP"), ("help", "HELP"))
            else:
                row1 = (("feed", "FEED"), ("train", "TRN"), ("fight", "FIGHT"), ("evo", "EVO"))
                row2 = (("go", "GO"), ("shop", "SHOP"), ("hatch", "HATCH"), ("menu", "MENU"))
                row3 = (("bed", "BED"), ("shower", "WASH"), ("swap", "SWAP"), ("help", "HELP"))
            gap, bw, bh = 4, 64, 20
            for r, items in enumerate((row1, row2, row3)):
                y0 = 78 + r * (bh + 4)
                for c, (key, label) in enumerate(items):
                    x0 = 8 + c * (bw + gap)
                    face = (70, 86, 52) if key in ("shop", "menu", "hatch", "fight") else BTN
                    bevel(d, (x0, y0, x0 + bw, y0 + bh), face, BTN_HI, BTN_SH)
                    tw = d.textlength(label, font=self.f_btn)
                    d.text((x0 + (bw - tw) / 2, y0 + 3), label, font=self.f_btn, fill=INK)
                    self.hits.append((key, (x0, y0, x0 + bw, y0 + bh)))
        return hud

    def redraw(self) -> None:
        if self.pet_hwnd:
            update_layered(self.pet_hwnd, self.render_pet(), int(self.x), int(self.y))
        if self.hud_hwnd:
            update_layered(self.hud_hwnd, self.render_hud(), int(self.hud_x), int(self.hud_y))
        if self.panel_hwnd:
            self._dock_sheet()
            if self.sheet_vis > 0.02:
                update_layered(self.panel_hwnd, self.ui.render(self), int(self.panel_x), int(self.panel_y))
            else:
                blank = Image.new("RGBA", (PW, PH), (0, 0, 0, 0))
                update_layered(self.panel_hwnd, blank, -4000, -4000)
        self._blit_foe()
        self._blit_props()

    def set_anim(self, name: str, hold: float = 0.0) -> None:
        self.anim = name
        self.anim_until = time.time() + hold if hold else 0.0
        self.redraw()

    def busy(self) -> bool:
        return self.p()["sleeping"] or self.showering or self.exploring or bool(self.field_mode)

    def _combat_live(self) -> bool:
        if self.field_mode == "run":
            return False
        if self.field_mode == "raid" and self.field_state and not self.field_state.get("over"):
            return True
        if self.field_mode == "floor":
            fl = getattr(self.ui, "floor", None)
            return bool(fl) and not fl.get("over")
        if self.ui.fight and not self.ui.fight.get("over"):
            return True
        return False

    def _hud_moves(self) -> list[tuple[str, str]]:
        load = [m for m in (self.p().get("loadout") or []) if m][:4]
        if not load:
            return [("struggle", "STRUG")]
        out = []
        for mid in load:
            mv = move_by_id(self.save["current"], mid)
            out.append((mid, ((mv or {}).get("name") or mid)[:6].upper()))
        return out

    def _combat_atk(self, mid: str) -> None:
        if not self._combat_live():
            return
        if self.field_mode == "raid":
            self.raid_move(mid)
        elif self.field_mode == "floor":
            handle(self, f"floor:{mid}")
        else:
            handle(self, f"use:{mid}")
        self.set_anim("train", 0.45)

    def begin_desktop_fight(self, kind: str, enemy: dict, boss: bool = False) -> None:
        self.panel_open = False
        self.field_mode = kind
        self.fighting = False
        eid = str(enemy.get("id") or "")
        path = UI / (f"boss_{eid}.png" if boss or eid.startswith("raid_") else f"enemy_{eid}.png")
        if not path.exists():
            path = UI / f"enemy_{eid}.png"
        if path.exists():
            im = binary_rgba(Image.open(path).convert("RGBA"))
        else:
            im = Image.new("RGBA", (48, 48), (180, 50, 40, 255))
        self.foe_src = im
        mx, _, mw, _ = MON2
        self.foe_on = True
        self.foe_x = float(mx + mw - PET_W - 28)
        self.foe_y = float(self.hud_y - PET_H - 4)
        self.foe_facing = -1
        self.foe_name = str(enemy.get("name") or "FOE")
        self.combat_over_at = 0.0
        self.flash(f"VS {self.foe_name.upper()[:16]}")

    def render_foe(self) -> Image.Image:
        canvas = Image.new("RGBA", (PET_W, PET_H), (0, 0, 0, 0))
        if not self.foe_on:
            return canvas
        im = fit_h(self.foe_src.copy(), 150)
        if self.foe_facing < 0:
            im = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        t = time.time()
        bob = abs(math.sin(t * 8.2)) * 8
        rot = math.sin(t * 8.2) * 3.0
        im = im.rotate(rot, expand=True, resample=Image.Resampling.NEAREST)
        x = (PET_W - im.width) // 2
        y = PET_H - im.height - 6 - int(bob)
        canvas.paste(im, (x, y), im)
        return canvas

    def _blit_foe(self) -> None:
        if not self.foe_hwnd:
            return
        if not self.foe_on:
            blank = Image.new("RGBA", (PET_W, PET_H), (0, 0, 0, 0))
            update_layered(self.foe_hwnd, blank, -4000, -4000)
            return
        update_layered(self.foe_hwnd, self.render_foe(), int(self.foe_x), int(self.foe_y))

    def _blit_props(self) -> None:
        obs = []
        if self.field_mode == "run" and self.field_state:
            obs = list(self.field_state.get("obs") or [])[:PROP_N]
        mx, _, mw, _ = MON2
        floor = self.hud_y - PET_H - 4
        for i, hwnd in enumerate(self.prop_hwnds):
            if i >= len(obs):
                blank = Image.new("RGBA", (PROP_W, PROP_H), (0, 0, 0, 0))
                update_layered(hwnd, blank, -4000, -4000)
                continue
            o = obs[i]
            spr = self.obs_ims.get(o.get("id"))
            canvas = Image.new("RGBA", (PROP_W, PROP_H), (0, 0, 0, 0))
            if spr:
                im = spr.copy()
                s = min(PROP_W / max(1, im.width), PROP_H / max(1, im.height))
                im = im.resize((max(8, int(im.width * s)), max(8, int(im.height * s))), Image.Resampling.NEAREST)
                canvas.paste(im, ((PROP_W - im.width) // 2, PROP_H - im.height), im)
            px = mx + int(o["x"])
            py = int(floor + PET_H - PROP_H - (72 if o.get("fly") else 0))
            update_layered(hwnd, canvas, px, py)

    def _tick_foe(self, dt: float) -> None:
        if not self.foe_on:
            return
        self.foe_y = self.hud_y - PET_H - 4
        gap = 170
        dx = (self.x + PET_W / 2) - (self.foe_x + PET_W / 2)
        if abs(dx) > gap:
            self.foe_facing = 1 if dx > 0 else -1
            self.foe_x += 88 * dt * self.foe_facing
        if self.field_mode in ("wild", "floor", "raid"):
            self.facing = 1 if self.foe_x > self.x else -1

    def _tick_run(self, dt: float) -> None:
        st = self.field_state
        if not st or st.get("over"):
            return
        mx, _, mw, _ = MON2
        st["t"] = float(st.get("t") or 0) + dt
        st["ifr"] = max(0.0, float(st.get("ifr") or 0) - dt)
        st["speed"] = min(640.0, 240.0 + float(st.get("dist") or 0) * 0.085 + st["t"] * 6.0)
        jump = self.field_jump
        self.field_jump = False
        if jump and self.air <= 0 and st.get("alive"):
            self.air_v = 640.0
        st["scroll"] = float(st.get("scroll") or 0) + st["speed"] * dt
        st["dist"] = float(st.get("dist") or 0) + st["speed"] * dt * 0.08
        st["spawn"] = float(st.get("spawn") or 0) - dt
        if st["spawn"] <= 0 and st.get("alive"):
            gap = max(0.55, 1.35 - st["t"] * 0.025)
            st["spawn"] = gap
            spec = random.choice(RUN_OBS)
            fly = bool(spec["fly"]) and random.random() < 0.7
            st.setdefault("obs", []).append(
                {"id": spec["id"], "x": float(mw + 40), "w": spec["w"], "h": spec["h"], "fly": fly}
            )
        keep = []
        hitbox = (self.x + 70, self.y + 40, 160, 150)
        floor = self.hud_y - PET_H - 4
        for o in st.get("obs") or []:
            o["x"] = float(o["x"]) - st["speed"] * dt
            if o["x"] + o["w"] < -40:
                continue
            keep.append(o)
            if not st.get("alive") or float(st.get("ifr") or 0) > 0:
                continue
            ox = mx + o["x"]
            oy = floor + PET_H - (o["h"] + 8) - (72 if o.get("fly") else 0)
            if _overlap_box(hitbox, (ox, oy, o["w"], o["h"])):
                st["lives"] = int(st.get("lives") or 3) - 1
                st["ifr"] = 0.85
                self.air_v = 220.0
                self.pop("OUCH", (255, 90, 90))
                self.flash(f"HIT {int(st['lives'])}")
                if int(st["lives"]) <= 0:
                    st["alive"] = False
                    st["over"] = True
                    st["score"] = int(st["dist"])
                    self.combat_over_at = time.time()
                    self.flash("SHELL CRACKED")
        st["obs"] = keep
        lives = int(st.get("lives") or 0)
        self.lcd_flash = f"RUN {int(st['dist'])}  {lives}HP"
        self.lcd_until = time.time() + 0.2

    def _hide_walkers(self) -> None:
        self.foe_on = False
        if self.field_state and isinstance(self.field_state, dict):
            self.field_state["obs"] = []

    def _cd(self, key: str, seconds: int, label: str) -> bool:
        left = self.p()[key] - time.time()
        if left > 0:
            self.flash(f"{label} {fmt_left(left)}")
            return True
        return False

    def feed(self) -> None:
        if self.busy():
            return
        foods = FOODS or ({"id": "meat", "name": "Meat", "hunger": 12, "mood": 2},)
        i = int(self.save.get("pantry_i") or 0) % len(foods)
        it = foods[i]
        self.save["pantry_i"] = i + 1
        self.eat_id = it["id"]
        p = self.p()
        stuffed = p["hunger"] >= 86
        p["hunger"] = min(100, p["hunger"] + int(it.get("hunger") or 12))
        p["mood"] = min(100, p["mood"] + int(it.get("mood") or 2))
        p["feeds"] += 1
        p["poop_at"] = time.time() + 90
        if stuffed:
            p["mood"] = max(0, p["mood"] - 10)
            p["hygiene"] = max(0, p["hygiene"] - 8)
            self.flash("OVERFED")
            self.pop("BLEH", (255, 140, 90))
        else:
            self.flash(it["name"].upper())
            self.pop("YUM", (255, 200, 90))
        self.quest_tick("feed")
        self.persist()
        self.set_anim("eat", 1.6)

    def train(self) -> None:
        if self.busy():
            return
        if self._cd("cd_train", CD_TRAIN, "TRAIN CD"):
            return
        p = self.p()
        if p["hunger"] < 20:
            self.flash("TOO HUNGRY")
            self.set_anim("hungry", 1.2)
            return
        p["hunger"] = max(0, p["hunger"] - 6)
        p["strength"] = min(99, p["strength"] + 2)
        p["mood"] = min(100, p["mood"] + 3)
        p["hygiene"] = max(0, p["hygiene"] - 4)
        p["trains"] += 1
        p["cd_train"] = time.time() + CD_TRAIN
        self.pop("+STR", (120, 220, 255))
        self.quest_tick("train")
        self.persist()
        self.set_anim("train", 1.5)

    def play(self) -> None:
        if self.busy():
            return
        if is_egg_form(self.form()):
            handle(self, "hatch:tap")
            return
        p = self.p()
        p["mood"] = min(100, p["mood"] + 10)
        p["hunger"] = max(0, p["hunger"] - 2)
        if random.random() < 0.18:
            n = random.randint(1, 4)
            self.save["coins"] = int(self.save.get("coins", 0)) + n
            self.pop(f"+${n}", (255, 220, 70))
        for _ in range(4):
            self.pop("♥", (255, 90, 130), kind="heart")
        self.quest_tick("pet")
        self.persist()
        self.set_anim("happy", 1.2)

    def explore(self) -> None:
        if self.busy():
            return
        if is_egg_form(self.form()):
            self.open_panel("hatch")
            self.ui.hatch_view = "care"
            handle(self, "egg:window")
            return
        self.exploring = True
        self.facing = 1 if random.random() < 0.5 else -1
        self._place = random.choice(PLACES.get(self.ln()["tag"], ("the wild",)))
        self.flash(f"GO {self._place.upper()[:16]}")
        self.set_anim("walk", 6.5)
        self.root.after(2200, self._street_coin)
        self.root.after(6500, self._end_explore)

    def _street_coin(self) -> None:
        if self.anim != "walk":
            return
        n = random.randint(1, 3)
        self.save["coins"] = int(self.save.get("coins", 0)) + n
        self.pop(f"+${n}", (255, 220, 70))
        self.persist()

    def _end_explore(self) -> None:
        self.exploring = False
        p = self.p()
        place = self._place or "the wild"
        buffs = self.save.setdefault("buffs", {})
        weights = [
            ("stash", 22),
            ("feast", 16),
            ("gym", 12),
            ("merchant", 14),
            ("shrine", 10),
            ("party", 8),
            ("jackpot", 6),
            ("ambush", 12),
        ]
        if int(buffs.get("map") or 0) > 0:
            buffs["map"] -= 1
            weights = [(k, w) for k, w in weights if k != "ambush"] + [("stash", 10)]
        bag = [k for k, w in weights for _ in range(w)]
        kind = random.choice(bag)
        if int(buffs.get("luck") or 0) > 0:
            extra = random.randint(6, 14)
            self.save["coins"] = int(self.save.get("coins", 0)) + extra
            buffs["luck"] -= 1
            self.pop(f"LUCK +${extra}", (255, 220, 70))
        if kind == "stash":
            n = random.randint(10, 22)
            self.save["coins"] = int(self.save.get("coins", 0)) + n
            self.flash(f"{place.upper()[:10]} +${n}")
            self.pop(f"+${n}", (255, 220, 70))
            self.set_anim("happy", 1.2)
        elif kind == "feast":
            it = random.choice(FOODS) if FOODS else {"id": "meat", "name": "Meat"}
            self.eat_id = it["id"]
            p["hunger"] = min(100, p["hunger"] + 22)
            p["mood"] = min(100, p["mood"] + 6)
            self.flash(f"{it['name'].upper()[:8]} @ {place.upper()[:6]}")
            self.pop("YUM", (255, 200, 90))
            self.set_anim("eat", 1.4)
        elif kind == "gym":
            p["strength"] = min(99, p["strength"] + 3)
            p["trains"] = int(p.get("trains") or 0) + 1
            self.flash(f"TRAIN @ {place.upper()[:8]}")
            self.pop("+STR", (140, 220, 255))
            self.set_anim("train", 1.2)
        elif kind == "merchant":
            drop = random.choice(ITEMS)
            give_item(self, drop["id"], 1)
            self.save["coins"] = int(self.save.get("coins", 0)) + 5
            self.flash(f"BOUGHT {drop['name'].upper()[:10]}")
            self.pop(drop["name"].upper(), (180, 220, 255))
            self.set_anim("happy", 1.0)
        elif kind == "shrine":
            p["stage_started"] = float(p["stage_started"]) - 12 * 60
            p["mood"] = min(100, p["mood"] + 8)
            self.flash("SHRINE -12 MIN")
            self.pop("-12m", (255, 180, 80))
            self.set_anim("evo", 0.8)
        elif kind == "party":
            p["mood"] = min(100, p["mood"] + 20)
            p["hygiene"] = max(0, p["hygiene"] - 6)
            self.save["coins"] = int(self.save.get("coins", 0)) + 8
            self.flash(f"PARTY @ {place.upper()[:8]}")
            self.pop("PARTY", (255, 120, 200))
            self.set_anim("happy", 1.4)
        elif kind == "jackpot":
            n = random.randint(28, 48)
            self.save["coins"] = int(self.save.get("coins", 0)) + n
            drop = random.choice(ITEMS)
            give_item(self, drop["id"], 1)
            self.flash(f"JACKPOT +${n}")
            self.pop(f"+${n}", (255, 220, 70))
            self.set_anim("happy", 1.4)
        else:
            if int(buffs.get("flee") or 0) > 0:
                buffs["flee"] -= 1
                self.flash("SMOKE ESCAPE")
                self.pop("POOF", (200, 200, 220))
                self.set_anim("happy", 0.8)
            else:
                p["mood"] = max(0, p["mood"] - 8)
                p["hygiene"] = max(0, p["hygiene"] - 6)
                p["hunger"] = max(0, p["hunger"] - 4)
                self.flash(f"AMBUSH @ {place.upper()[:8]}")
                self.pop("OUCH", (255, 90, 90))
                self.set_anim("hungry", 1.2)
        if kind not in ("merchant", "jackpot") and random.random() < 0.28:
            drop = random.choice(ITEMS)
            give_item(self, drop["id"], 1)
            self.pop(drop["name"].upper(), (180, 220, 255))
        p["hunger"] = max(0, p["hunger"] - 4)
        self.quest_tick("go")
        self.persist()

    def fight(self) -> None:
        if self.busy():
            return
        if is_egg_form(self.form()):
            self.flash("TOO SMALL")
            return
        p = self.p()
        if p["hunger"] < 16:
            self.flash("TOO HUNGRY")
            return
        self.fighting = True
        self._foe = random.choice(FOES.get(self.ln()["tag"], ("Rival",)))
        self.flash(f"VS {self._foe.upper()}")
        self.pop("FIGHT", (255, 80, 80))
        self.set_anim("train", 2.0)
        self.root.after(2000, self._end_fight)

    def _end_fight(self) -> None:
        self.fighting = False
        p = self.p()
        foe = self._foe or "Rival"
        chance = 0.38 + min(0.45, p["strength"] / 120)
        p["hunger"] = max(0, p["hunger"] - 8)
        p["hygiene"] = max(0, p["hygiene"] - 5)
        if random.random() < chance:
            loot = random.randint(6, 16)
            self.save["streak"] = int(self.save.get("streak") or 0) + 1
            streak = int(self.save["streak"])
            if streak >= 3:
                loot += 6 + streak
            self.save["coins"] = int(self.save.get("coins", 0)) + loot
            p["strength"] = min(99, p["strength"] + 3)
            p["mood"] = min(100, p["mood"] + 8)
            p["trains"] += 1
            tag = f"WIN x{streak}" if streak >= 2 else f"BEAT {foe.upper()[:8]}"
            self.flash(f"{tag} +${loot}")
            self.pop(f"+${loot}", (255, 220, 70))
            self.pop("WIN", (120, 255, 140))
            self.quest_tick("win")
            self.set_anim("happy", 1.2)
        else:
            self.save["streak"] = 0
            p["mood"] = max(0, p["mood"] - 12)
            self.flash(f"{foe.upper()[:10]} WINS")
            self.pop("LOST", (255, 90, 90))
            self.set_anim("hungry", 1.2)
        self.persist()

    def toggle_sleep(self) -> None:
        if self.showering:
            return
        p = self.p()
        p["sleeping"] = not p["sleeping"]
        self.persist()
        self.set_anim("sleep" if p["sleeping"] else "idle")

    def do_shower(self) -> None:
        if self.p()["sleeping"]:
            return
        p = self.p()
        over = p["hygiene"] >= 88
        p["hygiene"] = 100
        p["poop"] = False
        if over:
            p["mood"] = max(0, p["mood"] - 8)
            p["strength"] = max(0, p["strength"] - 1)
            self.flash("OVERWASH")
            self.pop("BRR", (160, 200, 255))
        else:
            p["mood"] = min(100, p["mood"] + 4)
            self.pop("SPLASH", (140, 210, 255))
        self.quest_tick("wash")
        self.persist()
        self.showering = True
        self.set_anim("shower", 2.4)
        self.root.after(2400, self._end_shower)

    def _end_shower(self) -> None:
        self.showering = False
        self.set_anim("idle")

    def evolve(self) -> None:
        if self.busy():
            return
        ready, txt = self.evo_status()
        if not ready:
            self.flash(f"EVO {txt}")
            return
        p = self.p()
        p["stage_i"] += 1
        p["stage_started"] = time.time()
        p["feeds"] = 0
        p["trains"] = 0
        self.persist()
        self.set_anim("evo", 2.0)
        self.flash(f"EVOLVED {LABEL[self.form()].upper()}")
        self.pop("EVO!", (180, 255, 120))

    def buy(self, item: str) -> None:
        catalog = {k: (label, price) for k, label, price in SHOP}
        if item not in catalog:
            return
        label, price = catalog[item]
        coins = int(self.save.get("coins", 0))
        if coins < price:
            self.flash("BROKE")
            self.pop("BROKE", (255, 90, 90))
            return
        if self.busy() and item != "med":
            return
        p = self.p()
        self.save["coins"] = coins - price
        if item == "meat":
            self.eat_id = "meat"
            stuffed = p["hunger"] >= 86
            p["hunger"] = min(100, p["hunger"] + 22)
            p["feeds"] += 1
            p["poop_at"] = time.time() + 90
            if stuffed:
                p["mood"] = max(0, p["mood"] - 8)
                self.flash("OVERFED")
            else:
                self.flash("ATE MEAT")
                self.pop("YUM", (255, 200, 90))
            self.quest_tick("feed")
            self.set_anim("eat", 1.6)
        elif item == "toy":
            p["mood"] = min(100, p["mood"] + 25)
            self.flash("NEW TOY")
            for _ in range(3):
                self.pop("♥", (255, 90, 130), kind="heart")
            self.set_anim("happy", 1.4)
        elif item == "med":
            p["hygiene"] = 100
            p["poop"] = False
            p["mood"] = min(100, p["mood"] + 8)
            self.flash("PATCHED UP")
            self.pop("OK", (140, 255, 180))
            self.quest_tick("wash")
            self.set_anim("happy", 1.0)
        elif item == "gym":
            if p["hunger"] < 16:
                self.save["coins"] = coins
                self.flash("TOO HUNGRY")
                return
            p["hunger"] = max(0, p["hunger"] - 5)
            p["strength"] = min(99, p["strength"] + 4)
            p["trains"] += 1
            self.flash("GYM +STR")
            self.pop("+STR", (120, 220, 255))
            self.quest_tick("train")
            self.set_anim("train", 1.5)
        elif item == "candy":
            p["stage_started"] = float(p["stage_started"]) - 30 * 60
            self.flash("EVO -30 MIN")
            self.pop("CANDY", (255, 160, 255))
            self.set_anim("evo", 1.2)
        self.shop_open = False
        self.quest_tick("shop")
        self.persist()

    def set_partner(self, name: str) -> None:
        if name not in LINE_BY_ID:
            return
        if not owns_line(self.save, name):
            cost = line_price(name)
            coins = int(self.save.get("coins") or 0)
            if coins < cost:
                self.flash(f"NEED {fmt_price(cost)}")
                self.pop("BROKE", (255, 90, 90))
                self.ui.say(f"NEED {fmt_price(cost)}")
                return
            self.save["coins"] = coins - cost
            owned = owned_list(self.save)
            owned.append(name)
            self.save["owned"] = owned
            st = self.save.setdefault("stats", {})
            st["pets"] = len(owned)
            self.pop(f"BUY {fmt_price(cost)}", (255, 220, 70))
            self.flash(f"OWN {LINE_NAME[name].upper()}")
        self.save["current"] = name
        self.persist()
        self.picker = False
        self.shop_open = False
        self.ui.move_page = 0
        self.pop(LINE_NAME[name].upper(), (180, 220, 255))
        self.set_anim("happy", 0.7)

    def show_help(self) -> None:
        messagebox.showinfo("Desktop pet", HELP, parent=self.hud)

    def on_field_space(self, _e=None) -> None:
        if self.field_mode == "run":
            self.field_jump = True

    def start_run(self) -> None:
        if not is_egg_form(self.form()):
            self.flash("EGG ONLY")
            self.ui.say("EGG ONLY")
            return
        self.panel_open = False
        self.field_mode = "run"
        self.field_state = new_run()
        self.field_jump = False
        self.air = 0.0
        self.air_v = 0.0
        self.foe_on = False
        self.ui.say("JUMP")
        self.flash("JUMP")

    def start_raid(self) -> None:
        if is_egg_form(self.form()):
            self.flash("TOO SMALL")
            return
        p = self.p()
        if p["hunger"] < 16:
            self.flash("TOO HUNGRY")
            return
        members = [
            {
                "pid": self.save.get("player_id"),
                "name": self.save.get("player_name") or "You",
                "main": self.save.get("current"),
                "tag": self.ln()["tag"],
                "power": power_of(p, self.save["current"]),
            }
        ]
        if self.net:
            for peer in self.net.nearby():
                if peer.get("raid") or getattr(self, "raid_queued", False):
                    members.append(
                        {
                            "pid": peer.get("pid"),
                            "name": peer.get("name") or "Ally",
                            "main": peer.get("main"),
                            "tag": (LINE_BY_ID.get(peer.get("main") or "") or {}).get("tag") or "DIGIMON",
                            "power": int(peer.get("power") or 10),
                        }
                    )
        members = members[:4]
        seed = random.randint(1, 1_000_000)
        boss = pick_raid_boss(random.Random(seed))
        if self.net:
            self.net.raid_go(seed, boss["id"], members)
        self._begin_raid(boss, members, seed)

    def join_raid(self, ev: dict) -> None:
        from depth import RAID_BOSSES
        boss = next((dict(b) for b in RAID_BOSSES if b["id"] == ev.get("boss")), None)
        if not boss:
            boss = pick_raid_boss()
        members = list(ev.get("members") or [])
        self._begin_raid(boss, members, int(ev.get("seed") or 1))

    def _begin_raid(self, boss: dict, members: list, seed: int) -> None:
        self.panel_open = False
        self.raid_queued = False
        self.field_mode = "raid"
        self.field_state = new_raid(boss, members, seed)
        start_raid_wave(self, self.field_state)
        e = (self.field_state or {}).get("enemy") or boss
        self.begin_desktop_fight("raid", e, boss=str(e.get("id") or "").startswith("raid_"))
        self.ui.say("RAID")
        self.flash("RAID")

    def raid_move(self, mid: str) -> None:
        st = self.field_state
        if not st or st.get("kind") != "raid" or st.get("over"):
            return
        p = self.p()
        e = st.get("enemy") or {}
        if mid == "struggle":
            mv = {"name": "Struggle", "typ": "strike", "pow": 8, "grow": 0}
            lv = 1
        else:
            from game_data import move_by_id
            mv = move_by_id(self.save["current"], mid)
            lv = int((p.get("moves") or {}).get(mid, 0))
            if not mv or lv <= 0:
                self.flash("NO MOVE")
                return
        stats = combat_stats(p, p["stage_i"])
        hit = roll_hit(mv, lv, stats, e)
        p["hunger"] = max(0, p["hunger"] - 2)
        if hit["miss"]:
            st["log"] = "MISS"
        else:
            st["ehp"] = max(0, int(st["ehp"]) - hit["dmg"])
            if hit["status"]:
                st["status"] = hit["status"]
            st["log"] = f"{mv['name'].upper()} {hit['dmg']}" + (" CRIT" if hit["crit"] else "")
            self.pop(str(hit["dmg"]), (255, 220, 80))
            if self.net:
                self.net.raid_hit(hit["dmg"], self.save.get("player_name") or "You", self.save.get("player_id") or "", st["ehp"], st.get("wave") or 0)
        self._raid_after_hit(stats)

    def _raid_after_hit(self, stats: dict) -> None:
        st = self.field_state
        if not st:
            return
        e = st.get("enemy") or {}
        if int(st.get("ehp") or 0) <= 0:
            st["wave"] = int(st.get("wave") or 0) + 1
            if st["wave"] > 3:
                self._raid_finish(True)
                return
            start_raid_wave(self, st)
            e = st.get("enemy") or {}
            self.begin_desktop_fight("raid", e, boss=str(e.get("id") or "").startswith("raid_"))
            return
        dmg_in = enemy_hit(e, stats, st.get("status") or "")
        st["php"] = max(0, int(st["php"]) - dmg_in)
        if st["php"] <= 0:
            self._raid_finish(False)

    def _raid_finish(self, won: bool) -> None:
        st = self.field_state
        if not st:
            return
        st["over"] = True
        st["won"] = won
        p = self.p()
        stats = self.save.setdefault("stats", {})
        if won:
            loot = random.randint(int(st["boss"].get("lo") or 40), int(st["boss"].get("hi") or 80))
            self.save["coins"] = int(self.save.get("coins", 0)) + loot
            grant_xp(p, 40)
            stats["raids"] = int(stats.get("raids") or 0) + 1
            stats["wins"] = int(stats.get("wins") or 0) + 1
            stats["coins_earned"] = int(stats.get("coins_earned") or 0) + loot
            bag = self.save.setdefault("gear_bag", {})
            drop = random.choice(ATTACHMENTS)
            bag[drop["id"]] = int(bag.get(drop["id"]) or 0) + 1
            st["log"] = f"CLEAR  +${loot}  {drop['name']}"
            self.quest_tick("win")
            self.flash(f"RAID +${loot}")
        else:
            stats["losses"] = int(stats.get("losses") or 0) + 1
            st["log"] = "WIPE"
            self.flash("RAID WIPE")
        if self.net:
            self.net.raid_over(won, int(self.save.get("coins") or 0))
        self.combat_over_at = time.time()
        self.persist()

    def close_field(self) -> None:
        st = self.field_state
        if self.field_mode == "run" and st:
            dist = int(st.get("dist") or 0)
            shave = max(30, int(dist * 2.4 * hatch_mult(self.p())))
            self.p()["stage_started"] = float(self.p()["stage_started"]) - shave
            coins = dist // 35
            self.save["coins"] = int(self.save.get("coins", 0)) + coins
            self.flash(f"RUN -{shave // 60}m +${coins}")
            self.ui.say(f"RUN -{shave // 60} MIN")
            self.persist()
        self.field_mode = None
        self.field_state = None
        self.field_jump = False
        self.air = 0.0
        self.air_v = 0.0
        self.foe_on = False
        if getattr(self.ui, "fight", None):
            self.ui.fight = None
        if getattr(self.ui, "floor", None):
            self.ui.floor = None

    def think(self) -> None:
        p = self.p()
        if p["sleeping"] or self.showering or time.time() < self.anim_until:
            return
        mood = p["mood"]
        if p["hunger"] < 22:
            self.set_anim("hungry")
            self.next_ai = time.time() + 8
            return
        walk_odds = 0.28 if mood < 30 else (0.62 if mood > 75 else 0.45)
        if random.random() < walk_odds:
            self.set_anim("walk")
            self.next_ai = time.time() + random.uniform(5.0, 8.0)
            if random.random() < 0.22:
                self.root.after(1800, self._street_coin)
        else:
            self.set_anim("idle")
            self.next_ai = time.time() + random.uniform(6.0, 12.0)

    def move(self, dt: float) -> None:
        mx, my, mw, mh = MON2
        if self.anim == "walk" and not self.p()["sleeping"] and not self.showering:
            mood = self.p()["mood"]
            speed = 78 if self.exploring else (20 + mood * 0.24)
            if mood < 30:
                speed *= 0.55
            self.x += speed * dt * self.facing
        floor = self.hud_y - PET_H - 4
        if self.field_mode == "run":
            self.air_v -= 1750.0 * dt
            self.air += self.air_v * dt
            if self.air < 0:
                self.air = 0.0
                self.air_v = 0.0
            self.y = floor - self.air
        else:
            self.air = 0.0
            self.air_v = 0.0
            self.y = floor
        if self.x < mx + 16:
            self.x = mx + 16
            self.facing = 1
        if self.x > mx + mw - PET_W - 16:
            self.x = mx + mw - PET_W - 16
            self.facing = -1
        pos = (int(self.x), int(self.y))
        if pos != self._pet_pos:
            self._pet_pos = pos
            self.root.geometry(f"{PET_W}x{PET_H}+{pos[0]}+{pos[1]}")

    def loop(self) -> None:
        now = time.time()
        dt = min(0.05, now - self.last_tick)
        self.last_tick = now
        p = self.p()
        if p["poop_at"] and now >= p["poop_at"]:
            p["poop"] = True
            p["poop_at"] = 0
            p["mood"] = max(0, p["mood"] - 6)
            p["hygiene"] = max(0, p["hygiene"] - 10)
            self.persist()
        drain = 0.45 if p["sleeping"] else 1.1
        self.hunger_acc += dt * drain
        if self.hunger_acc >= 18:
            p["hunger"] = max(0, p["hunger"] - 1)
            if not p["sleeping"]:
                p["mood"] = max(0, p["mood"] - 1)
                p["hygiene"] = max(0, p["hygiene"] - 1)
            if p["poop"]:
                p["mood"] = max(0, p["mood"] - 1)
            if p["sleeping"]:
                p["mood"] = min(100, p["mood"] + 1)
            self.hunger_acc = 0
            self.persist()
        if self.net:
            while True:
                try:
                    ev = self.net.events.get_nowait()
                except queue.Empty:
                    break
                net_event(self, ev)
        if self.field_mode == "run" and self.field_state:
            self._tick_run(dt)
        elif self.field_mode == "raid" and self.field_state and not self.field_state.get("over"):
            st = self.field_state
            st["t"] = float(st.get("t") or 0) + dt
            st["ally_cd"] = float(st.get("ally_cd") or 0) - dt
            if st["ally_cd"] <= 0:
                st["ally_cd"] = 1.5
                extra = 0
                for m in st.get("members") or []:
                    if m.get("pid") != self.save.get("player_id"):
                        extra += max(2, int(m.get("power") or 10) // 8)
                if extra:
                    st["ehp"] = max(0, int(st["ehp"]) - extra)
                    st["log"] = f"ALLIES {extra}"
                    if int(st["ehp"]) <= 0:
                        self._raid_after_hit(combat_stats(self.p(), self.p()["stage_i"]))
        fl = getattr(self.ui, "floor", None)
        if self.field_mode == "floor" and fl and fl.get("clear") and not fl.get("over"):
            if self.combat_over_at and now - self.combat_over_at > 1.1:
                handle(self, "floor_next")
                self.combat_over_at = 0.0
        if self.combat_over_at and now - self.combat_over_at > 2.2:
            if self.field_mode in ("wild", "raid") or (self.field_mode == "floor" and fl and fl.get("over")):
                self.close_field()
            elif self.field_mode == "run" and self.field_state and self.field_state.get("over"):
                self.close_field()
        self._tick_foe(dt)
        want = 1.0 if self.panel_open else 0.0
        self.sheet_vis += (want - self.sheet_vis) * min(1.0, dt * 10)
        if abs(self.sheet_vis - want) < 0.012:
            self.sheet_vis = want
        if now >= self.anim_until:
            if p["sleeping"]:
                self.anim = "sleep"
            elif self.showering:
                self.anim = "shower"
            elif now >= self.next_ai:
                self.think()
        self.move(dt)
        self.redraw()
        self.root.after(33, self.loop)

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    try:
        DigimonPet().run()
    except KeyboardInterrupt:
        sys.exit(0)
