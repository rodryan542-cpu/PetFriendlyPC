"""True pixel-art PNGs. Drawn at native res, scaled with NEAREST only."""
from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw

from catalog_extra import GEN_FORMS
from depth import ATTACHMENTS, RAID_BOSSES, RUN_OBS
from game_data import CLAN_CRESTS, ENEMIES, HATCH, ITEMS, MOVES, TYPE_COLOR

from paths import asset_root

SPRITES = asset_root() / "sprites"

UI = asset_root() / "ui"
RW, RH = 320, 180  # room native
EW, EH = 48, 48  # enemy / icon native


def _new(w: int, h: int, c=(0, 0, 0, 255)) -> Image.Image:
    return Image.new("RGBA", (w, h), c)


def _px(im: Image.Image, x: int, y: int, c) -> None:
    if 0 <= x < im.width and 0 <= y < im.height:
        if len(c) == 3:
            c = (*c, 255)
        im.putpixel((x, y), c)


def _rect(im: Image.Image, x0: int, y0: int, x1: int, y1: int, c) -> None:
    for y in range(y0, y1):
        for x in range(x0, x1):
            _px(im, x, y, c)


def _hline(im: Image.Image, x0: int, x1: int, y: int, c) -> None:
    for x in range(x0, x1):
        _px(im, x, y, c)


def _vline(im: Image.Image, x: int, y0: int, y1: int, c) -> None:
    for y in range(y0, y1):
        _px(im, x, y, c)


def _box(im: Image.Image, x0: int, y0: int, x1: int, y1: int, fill, hi, sh, ink=(8, 8, 10)) -> None:
    _rect(im, x0, y0, x1, y1, fill)
    _hline(im, x0, x1, y0, hi)
    _vline(im, x0, y0, y1, hi)
    _hline(im, x0, x1, y1 - 1, sh)
    _vline(im, x1 - 1, y0, y1, sh)
    _hline(im, x0, x1, y0 - 1, ink) if y0 > 0 else None
    _vline(im, x0 - 1, y0, y1, ink) if x0 > 0 else None


def _disc(im: Image.Image, cx: int, cy: int, r: int, c) -> None:
    r2 = r * r
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            if (x - cx) * (x - cx) + (y - cy) * (y - cy) <= r2:
                _px(im, x, y, c)


def _dither(im: Image.Image, x0: int, y0: int, x1: int, y1: int, a, b) -> None:
    for y in range(y0, y1):
        for x in range(x0, x1):
            _px(im, x, y, a if (x + y) % 2 == 0 else b)


def _outline(im: Image.Image, ink=(10, 10, 12, 255)) -> None:
    px = im.load()
    w, h = im.size
    mark = []
    for y in range(h):
        for x in range(w):
            a = px[x, y][3]
            if a < 16:
                continue
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nx, ny = x + dx, y + dy
                if nx < 0 or ny < 0 or nx >= w or ny >= h or px[nx, ny][3] < 16:
                    mark.append((x, y))
                    break
    for x, y in mark:
        px[x, y] = ink


def scale_nn(im: Image.Image, k: int) -> Image.Image:
    return im.resize((im.width * k, im.height * k), Image.Resampling.NEAREST)


def _floor_check(im: Image.Image, y0: int, a, b, cell=8) -> None:
    for y in range(y0, im.height):
        for x in range(im.width):
            cx, cy = x // cell, (y - y0) // cell
            _px(im, x, y, a if (cx + cy) % 2 == 0 else b)


def _brick_wall(im: Image.Image, y1: int, c0, c1, mortar) -> None:
    for y in range(y1):
        row = y // 6
        shift = 4 if row % 2 else 0
        for x in range(im.width):
            if y % 6 == 5:
                _px(im, x, y, mortar)
            elif (x + shift) % 10 == 9:
                _px(im, x, y, mortar)
            else:
                _px(im, x, y, c0 if ((x + shift) // 10 + row) % 2 == 0 else c1)


def _planks(im: Image.Image, y0: int, c0, c1, line) -> None:
    for y in range(y0, im.height):
        band = ((y - y0) // 5) % 2
        for x in range(im.width):
            _px(im, x, y, c0 if band == 0 else c1)
            if (y - y0) % 5 == 4:
                _px(im, x, y, line)
            if x % 28 == 0:
                _px(im, x, y, line)


def _torch(im: Image.Image, x: int, y: int) -> None:
    _rect(im, x, y + 6, x + 3, y + 18, (70, 46, 28))
    _disc(im, x + 1, y + 4, 3, (230, 120, 30))
    _disc(im, x + 1, y + 3, 2, (255, 210, 70))
    _px(im, x + 1, y + 1, (255, 250, 200))


def room_starter() -> Image.Image:
    im = _new(RW, RH, (18, 16, 22, 255))
    _brick_wall(im, 96, (48, 36, 52), (38, 28, 42), (22, 16, 24))
    _rect(im, 0, 70, RW, 96, (28, 22, 34))
    for i in range(6):
        _rect(im, 20 + i * 52, 18, 52 + i * 52, 70, (14, 18, 28))
        _rect(im, 22 + i * 52, 20, 50 + i * 52, 68, (40, 70, 90))
        _dither(im, 22 + i * 52, 20, 50 + i * 52, 68, (40, 70, 90), (28, 52, 70))
    _floor_check(im, 96, (62, 48, 40), (50, 38, 32), 10)
    for i in range(8):
        col, row = i % 4, i // 4
        x = 28 + col * 74
        y = 102 + row * 34
        _box(im, x, y + 10, x + 28, y + 18, (90, 70, 48), (140, 110, 70), (50, 36, 24))
        _rect(im, x + 6, y + 4, x + 22, y + 11, (120, 92, 60))
        _rect(im, x + 10, y, x + 18, y + 5, (160, 130, 80))
        _px(im, x + 13, y - 2, (255, 220, 120))
    _torch(im, 8, 40)
    _torch(im, 309, 40)
    return im


def room_hatch() -> Image.Image:
    im = _new(RW, RH, (12, 10, 14, 255))
    _brick_wall(im, 88, (36, 32, 40), (28, 24, 32), (16, 14, 18))
    _rect(im, 0, 88, RW, RH, (24, 22, 26))
    for x in range(0, RW, 8):
        _vline(im, x, 88, RH, (18, 16, 20))
    for y in range(88, RH, 8):
        _hline(im, 0, RW, y, (18, 16, 20))
    # incubators
    for i, ox in enumerate((24, 124, 224)):
        _box(im, ox, 48, ox + 72, 120, (48, 52, 58), (90, 96, 104), (24, 26, 30))
        _rect(im, ox + 8, 56, ox + 64, 100, (80, 40, 16))
        _dither(im, ox + 8, 56, ox + 64, 100, (80, 40, 16), (120, 60, 20))
        _rect(im, ox + 20, 64, ox + 52, 92, (255, 160, 40))
        _disc(im, ox + 36, 78, 8, (255, 210, 80))
        _rect(im, ox + 28, 36, ox + 44, 48, (70, 74, 80))
        _disc(im, ox + 36, 34, 6, (255, 90, 30) if i == 1 else (200, 60, 20))
        _rect(im, ox + 8, 108, ox + 64, 116, (30, 32, 36))
    _rect(im, 0, 140, RW, 148, (40, 36, 30))
    _torch(im, 6, 20)
    _torch(im, 311, 20)
    return im


def room_arena() -> Image.Image:
    im = _new(RW, RH, (20, 14, 16, 255))
    _brick_wall(im, 78, (70, 42, 38), (54, 30, 28), (28, 16, 16))
    _rect(im, 0, 78, RW, RH, (90, 70, 52))
    for y in range(78, RH, 6):
        _hline(im, 0, RW, y, (70, 52, 38))
    for x in range(40, 280, 18):
        if x % 36 == 4:
            _rect(im, x, 100, x + 3, 118, (50, 36, 28))
    _box(im, 18, 118, 118, 156, (120, 88, 60), (170, 130, 80), (70, 48, 32))
    _box(im, 202, 118, 302, 156, (120, 88, 60), (170, 130, 80), (70, 48, 32))
    _rect(im, 130, 132, 190, 148, (60, 44, 32))
    _torch(im, 30, 28)
    _torch(im, 287, 28)
    _disc(im, 160, 40, 10, (40, 20, 18))
    return im


def room_clan() -> Image.Image:
    im = _new(RW, RH, (16, 18, 20, 255))
    _brick_wall(im, 86, (42, 48, 52), (32, 36, 40), (18, 20, 22))
    _rect(im, 48, 16, 272, 70, (20, 28, 24))
    _dither(im, 52, 20, 268, 66, (28, 44, 36), (20, 32, 28))
    _floor_check(im, 86, (70, 56, 40), (56, 44, 32), 8)
    _box(im, 36, 108, 284, 142, (86, 58, 34), (130, 90, 50), (48, 30, 18))
    for i in range(6):
        _rect(im, 50 + i * 38, 100, 62 + i * 38, 108, (50, 34, 22))
    _rect(im, 20, 30, 40, 86, (90, 30, 30))
    _rect(im, 280, 30, 300, 86, (30, 70, 90))
    _torch(im, 10, 24)
    _torch(im, 307, 24)
    return im


def room_dojo() -> Image.Image:
    im = _new(RW, RH, (28, 20, 16, 255))
    _rect(im, 0, 0, RW, 80, (48, 28, 22))
    for x in range(16, RW, 40):
        _rect(im, x, 8, x + 6, 80, (70, 40, 28))
        _rect(im, x + 1, 10, x + 5, 78, (24, 16, 14))
    _planks(im, 80, (150, 104, 62), (132, 90, 52), (90, 60, 36))
    _rect(im, 12, 40, 36, 80, (70, 48, 32))
    _rect(im, 16, 44, 32, 76, (40, 28, 20))
    _hline(im, 16, 32, 52, (180, 180, 190))
    _hline(im, 16, 32, 60, (180, 180, 190))
    _rect(im, 284, 40, 308, 80, (70, 48, 32))
    _disc(im, 40, 28, 5, (220, 80, 50))
    _disc(im, 280, 28, 5, (220, 80, 50))
    return im


def room_hub() -> Image.Image:
    im = _new(RW, RH, (22, 24, 28, 255))
    _brick_wall(im, 70, (34, 38, 44), (26, 28, 32), (14, 14, 16))
    _floor_check(im, 70, (40, 44, 50), (30, 32, 36), 8)
    _box(im, 20, 88, 100, 150, (48, 36, 28), (90, 70, 48), (24, 16, 12))
    _box(im, 120, 88, 200, 150, (28, 40, 36), (50, 80, 70), (12, 20, 16))
    _box(im, 220, 88, 300, 150, (40, 32, 48), (80, 60, 90), (20, 14, 24))
    _torch(im, 8, 18)
    _torch(im, 309, 18)
    return im


def _shade(c0, c1, t: float):
    return tuple(int(a + (b - a) * t) for a, b in zip(c0, c1))


def enemy_sprite(shape: str, c0, c1) -> Image.Image:
    im = _new(EW, EH, (0, 0, 0, 0))
    hi = _shade(c0, (255, 255, 255), 0.28)
    eye = (20, 16, 14)
    glow = (255, 230, 80)

    def body_blob(cx, cy, rx, ry):
        for y in range(cy - ry, cy + ry + 1):
            for x in range(cx - rx, cx + rx + 1):
                nx = (x - cx) / max(1, rx)
                ny = (y - cy) / max(1, ry)
                if nx * nx + ny * ny <= 1:
                    _px(im, x, y, hi if ny < -0.2 else (c0 if ny < 0.45 else c1))

    if shape == "slug":
        body_blob(24, 30, 16, 10)
        _rect(im, 8, 26, 14, 34, c1)
        _px(im, 30, 26, glow)
        _px(im, 34, 26, glow)
    elif shape == "beast":
        body_blob(24, 28, 12, 11)
        _rect(im, 10, 16, 16, 24, c0)
        _rect(im, 32, 16, 38, 24, c0)
        _rect(im, 16, 36, 20, 46, c1)
        _rect(im, 28, 36, 32, 46, c1)
        _px(im, 20, 26, glow)
        _px(im, 28, 26, glow)
    elif shape == "plant":
        _rect(im, 22, 28, 26, 44, (60, 40, 24))
        body_blob(24, 22, 12, 10)
        _rect(im, 8, 18, 16, 24, c0)
        _rect(im, 32, 16, 42, 22, c1)
    elif shape == "ghost":
        body_blob(24, 24, 12, 14)
        for x in range(14, 36, 4):
            _rect(im, x, 36, x + 3, 42, c1)
        _px(im, 20, 22, (255, 255, 255))
        _px(im, 28, 22, (255, 255, 255))
        _px(im, 20, 23, eye)
        _px(im, 28, 23, eye)
    elif shape == "beetle":
        body_blob(24, 28, 14, 10)
        _rect(im, 8, 14, 14, 28, c1)
        _rect(im, 34, 14, 40, 28, c1)
        _rect(im, 22, 12, 26, 20, hi)
        _px(im, 20, 26, glow)
        _px(im, 28, 26, glow)
    elif shape == "flame":
        body_blob(24, 30, 10, 12)
        _disc(im, 24, 16, 7, hi)
        _disc(im, 24, 12, 4, (255, 230, 80))
        _px(im, 20, 28, eye)
        _px(im, 28, 28, eye)
    elif shape == "brute":
        body_blob(24, 26, 13, 12)
        _rect(im, 12, 36, 18, 46, c1)
        _rect(im, 30, 36, 36, 46, c1)
        _rect(im, 8, 22, 14, 30, c0)
        _rect(im, 34, 20, 42, 32, (90, 70, 40))
        _px(im, 20, 22, glow)
        _px(im, 28, 22, glow)
    elif shape == "bird":
        body_blob(24, 26, 11, 9)
        _rect(im, 8, 20, 16, 28, c1)
        _rect(im, 32, 20, 42, 26, c0)
        _rect(im, 22, 34, 26, 44, c1)
        _px(im, 20, 24, glow)
    elif shape == "serpent":
        body_blob(18, 30, 8, 8)
        body_blob(28, 24, 8, 7)
        body_blob(36, 18, 7, 6)
        _px(im, 38, 16, glow)
        _rect(im, 40, 16, 46, 18, hi)
    elif shape == "dino":
        body_blob(22, 28, 12, 10)
        _rect(im, 30, 16, 42, 24, c0)
        _rect(im, 14, 36, 18, 46, c1)
        _rect(im, 26, 36, 30, 46, c1)
        _rect(im, 8, 20, 14, 28, c1)
        _px(im, 36, 18, glow)
    elif shape == "wing":
        body_blob(24, 28, 10, 12)
        _rect(im, 6, 16, 16, 30, c1)
        _rect(im, 32, 16, 42, 30, c1)
        _px(im, 20, 24, glow)
        _px(im, 28, 24, glow)
    elif shape == "ape":
        body_blob(24, 26, 12, 11)
        _disc(im, 24, 16, 7, hi)
        _rect(im, 12, 34, 18, 46, c1)
        _rect(im, 30, 34, 36, 46, c1)
        _px(im, 21, 15, eye)
        _px(im, 27, 15, eye)
    elif shape == "soldier":
        _rect(im, 18, 18, 30, 36, c0)
        _rect(im, 20, 10, 28, 18, hi)
        _rect(im, 16, 36, 22, 46, c1)
        _rect(im, 26, 36, 32, 46, c1)
        _rect(im, 28, 22, 40, 26, (180, 180, 80))
        _px(im, 22, 14, eye)
        _px(im, 26, 14, eye)
    elif shape == "fish":
        body_blob(24, 26, 14, 8)
        _rect(im, 6, 22, 12, 30, c1)
        _rect(im, 34, 20, 40, 24, hi)
        _px(im, 32, 24, glow)
    elif shape == "clown":
        body_blob(24, 28, 11, 11)
        _disc(im, 24, 16, 8, (230, 80, 80))
        _rect(im, 16, 12, 32, 16, (20, 20, 24))
        _px(im, 20, 26, (20, 20, 24))
        _px(im, 28, 26, (20, 20, 24))
    elif shape == "agent":
        _rect(im, 18, 16, 30, 36, (24, 24, 28))
        _rect(im, 20, 10, 28, 16, (16, 16, 18))
        _rect(im, 16, 36, 22, 46, (20, 20, 24))
        _rect(im, 26, 36, 32, 46, (20, 20, 24))
        _hline(im, 20, 28, 14, (200, 40, 40))
    elif shape == "armor":
        _rect(im, 14, 12, 34, 40, c0)
        _rect(im, 16, 14, 32, 22, hi)
        _rect(im, 12, 38, 20, 46, c1)
        _rect(im, 28, 38, 36, 46, c1)
        _rect(im, 32, 18, 44, 28, (80, 90, 70))
        _px(im, 20, 18, glow)
        _px(im, 26, 18, glow)
    elif shape == "drone":
        body_blob(24, 24, 12, 8)
        _rect(im, 10, 22, 16, 26, c1)
        _rect(im, 32, 22, 38, 26, c1)
        _disc(im, 24, 24, 3, glow)
    elif shape == "fly":
        body_blob(24, 28, 8, 7)
        _rect(im, 12, 16, 20, 24, (200, 200, 180))
        _rect(im, 28, 16, 36, 24, (200, 200, 180))
        _px(im, 22, 26, glow)
        _px(im, 26, 26, glow)
    elif shape == "blob":
        body_blob(24, 28, 14, 12)
        _px(im, 18, 24, eye)
        _px(im, 28, 26, eye)
        _px(im, 22, 32, c1)
    elif shape == "skull":
        _disc(im, 24, 22, 10, hi)
        _rect(im, 18, 30, 30, 38, c0)
        _px(im, 20, 20, eye)
        _px(im, 28, 20, eye)
        _rect(im, 22, 26, 26, 28, (10, 10, 12))
    elif shape == "grunt":
        body_blob(24, 30, 11, 10)
        _rect(im, 18, 14, 30, 24, (200, 160, 60))
        _rect(im, 20, 10, 28, 16, c0)
        _px(im, 22, 18, eye)
        _px(im, 26, 18, eye)
    elif shape == "elite":
        _rect(im, 18, 16, 30, 36, c0)
        _rect(im, 16, 8, 32, 18, hi)
        _rect(im, 20, 4, 28, 10, c1)
        _rect(im, 16, 36, 22, 46, c1)
        _rect(im, 26, 36, 32, 46, c1)
        _rect(im, 30, 22, 42, 26, (80, 220, 180))
        _px(im, 20, 12, glow)
        _px(im, 26, 12, glow)
    else:
        body_blob(24, 26, 12, 12)
        _px(im, 20, 24, glow)
        _px(im, 28, 24, glow)
    _outline(im)
    return im


def tint_shape(im: Image.Image, c0, c1) -> Image.Image:
    import numpy as np

    arr = np.array(im.convert("RGBA"))
    r = arr[:, :, 0].astype(np.float32)
    g = arr[:, :, 1].astype(np.float32)
    b = arr[:, :, 2].astype(np.float32)
    a = arr[:, :, 3]
    lum = 0.30 * r + 0.59 * g + 0.11 * b
    glow = (r > 200) & (g > 170) & (b < 140)
    outline = lum < 40
    keep = (a < 16) | outline | glow
    t = np.clip((lum - 40.0) / 175.0, 0.0, 1.0)
    nr = c1[0] + (c0[0] - c1[0]) * t
    ng = c1[1] + (c0[1] - c1[1]) * t
    nb = c1[2] + (c0[2] - c1[2]) * t
    nr = nr * 0.72 + r * 0.28
    ng = ng * 0.72 + g * 0.28
    nb = nb * 0.72 + b * 0.28
    m = (~keep) & (a >= 16)
    out = arr.copy()
    out[m, 0] = np.clip(nr[m], 0, 255).astype(np.uint8)
    out[m, 1] = np.clip(ng[m], 0, 255).astype(np.uint8)
    out[m, 2] = np.clip(nb[m], 0, 255).astype(np.uint8)
    gone = out[:, :, 3] < 16
    out[gone, 0:3] = 0
    out[gone, 3] = 0
    out[~gone, 3] = 255
    return Image.fromarray(out, "RGBA")


def _enemy_png(shape: str, c0, c1) -> Image.Image:
    tmpl = UI / f"shape_{shape}.png"
    if tmpl.exists() and tmpl.stat().st_size >= 8000:
        return tint_shape(Image.open(tmpl), c0, c1)
    return scale_nn(enemy_sprite(shape, c0, c1), 3)


def move_icon(typ: str) -> Image.Image:
    im = _new(32, 32, (0, 0, 0, 0))
    c = TYPE_COLOR.get(typ, (200, 200, 200))
    hi = _shade(c, (255, 255, 255), 0.35)
    _rect(im, 4, 4, 28, 28, (18, 18, 22))
    if typ == "fire":
        _disc(im, 16, 18, 7, c)
        _disc(im, 16, 12, 5, hi)
        _px(im, 16, 8, (255, 240, 160))
    elif typ == "ice":
        for i in range(6):
            _hline(im, 16 - i, 16 + i + 1, 10 + i, hi)
        _rect(im, 14, 16, 18, 26, c)
    elif typ == "slash":
        _hline(im, 6, 26, 10, hi)
        _hline(im, 8, 24, 14, c)
        _hline(im, 10, 22, 18, hi)
    elif typ == "strike":
        _disc(im, 16, 16, 7, c)
        _rect(im, 8, 14, 24, 18, hi)
    elif typ == "curse":
        _disc(im, 16, 16, 8, c)
        _px(im, 13, 14, (10, 10, 12))
        _px(im, 19, 14, (10, 10, 12))
        _rect(im, 14, 20, 18, 22, (10, 10, 12))
    elif typ == "gun":
        _rect(im, 6, 14, 24, 18, c)
        _rect(im, 20, 12, 26, 20, hi)
        _rect(im, 8, 18, 12, 24, (40, 40, 40))
    elif typ == "fruit":
        _disc(im, 16, 18, 8, c)
        _rect(im, 15, 8, 17, 12, (40, 120, 40))
        _px(im, 18, 10, (40, 140, 50))
    elif typ == "holy":
        _rect(im, 14, 8, 18, 24, hi)
        _rect(im, 8, 14, 24, 18, hi)
    elif typ == "shock":
        _px(im, 18, 8, hi)
        for i, y in enumerate(range(10, 24, 2)):
            x = 18 - (i % 2) * 6
            _hline(im, x, x + 6, y, c)
    elif typ == "water":
        _disc(im, 16, 18, 6, c)
        _disc(im, 12, 12, 3, hi)
        _disc(im, 20, 10, 2, hi)
    elif typ == "wind":
        _hline(im, 6, 24, 12, hi)
        _hline(im, 8, 26, 16, c)
        _hline(im, 6, 22, 20, hi)
    elif typ == "leaf":
        _disc(im, 16, 16, 7, c)
        _rect(im, 15, 8, 17, 16, (40, 90, 30))
    else:
        _disc(im, 16, 16, 8, c)
    _outline(im)
    return im


def hatch_icon(hid: str) -> Image.Image:
    im = _new(32, 32, (0, 0, 0, 0))
    _rect(im, 3, 3, 29, 29, (22, 20, 26))
    if hid == "warm":
        _disc(im, 16, 18, 7, (230, 140, 70))
        _disc(im, 12, 16, 3, (255, 200, 120))
    elif hid == "lamp":
        _rect(im, 14, 8, 18, 14, (80, 80, 90))
        _disc(im, 16, 20, 6, (255, 160, 40))
    elif hid == "pulse":
        _rect(im, 8, 14, 24, 18, (80, 200, 230))
        _rect(im, 14, 8, 18, 24, (80, 200, 230))
    elif hid == "incubate":
        _box(im, 8, 10, 24, 26, (50, 54, 60), (90, 96, 104), (24, 26, 30))
        _rect(im, 11, 13, 21, 22, (255, 140, 40))
    elif hid == "carry":
        _rect(im, 10, 16, 22, 24, (90, 70, 48))
        _disc(im, 16, 14, 5, (230, 210, 160))
    elif hid == "candy":
        _rect(im, 10, 12, 22, 22, (230, 80, 180))
        _rect(im, 12, 10, 20, 12, (255, 160, 210))
    elif hid == "lullaby":
        _disc(im, 16, 16, 6, (180, 140, 220))
        _px(im, 22, 10, (255, 230, 80))
        _px(im, 24, 8, (255, 230, 80))
    elif hid == "spicy":
        _disc(im, 16, 18, 6, (220, 60, 30))
        _px(im, 16, 8, (255, 180, 40))
    elif hid == "nest":
        _rect(im, 8, 18, 24, 26, (140, 90, 40))
        _disc(im, 16, 16, 5, (230, 210, 140))
    elif hid == "comet":
        _disc(im, 18, 14, 5, (80, 200, 255))
        _rect(im, 8, 18, 16, 22, (255, 200, 80))
    else:
        _disc(im, 16, 16, 7, (200, 200, 80))
    _outline(im)
    return im


def crest_icon(name: str) -> Image.Image:
    im = _new(32, 32, (0, 0, 0, 0))
    _rect(im, 4, 4, 28, 28, (28, 24, 20))
    gold = (220, 180, 70)
    if name == "fang":
        _rect(im, 10, 10, 14, 22, gold)
        _rect(im, 18, 10, 22, 22, gold)
        _px(im, 12, 22, (255, 255, 220))
        _px(im, 20, 22, (255, 255, 220))
    elif name == "sun":
        _disc(im, 16, 16, 7, gold)
        for a in range(0, 32, 4):
            _px(im, 16 + (a % 7) - 3, 6, gold)
    elif name == "blade":
        _rect(im, 14, 6, 18, 24, (200, 200, 210))
        _rect(im, 10, 22, 22, 26, gold)
    elif name == "eye":
        _disc(im, 16, 16, 8, (220, 220, 230))
        _disc(im, 16, 16, 3, (20, 80, 90))
    elif name == "ring":
        _disc(im, 16, 16, 8, gold)
        _disc(im, 16, 16, 4, (28, 24, 20))
    else:
        for i in range(8):
            _hline(im, 8, 24 - abs(i - 4), 12 + i, (70, 140, 200))
    _outline(im)
    return im


def _keep_png(dest: Path, maker) -> Image.Image:
    if dest.exists() and dest.stat().st_size >= 8000:
        return Image.open(dest).convert("RGBA")
    im = maker()
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest)
    return im


def build_all() -> Path:
    UI.mkdir(parents=True, exist_ok=True)
    rooms = {
        "room_starter": room_starter,
        "room_hatch": room_hatch,
        "room_arena": room_arena,
        "room_clan": room_clan,
        "room_dojo": room_dojo,
        "room_hub": room_hub,
    }
    for name, fn in rooms.items():
        scale_nn(fn(), 3).save(UI / f"{name}.png")
    seen_types = set()
    for pack in MOVES.values():
        for m in pack:
            seen_types.add(m["typ"])
            scale_nn(move_icon(m["typ"]), 2).save(UI / f"move_{m['id']}.png")
    for typ in seen_types:
        scale_nn(move_icon(typ), 2).save(UI / f"type_{typ}.png")
    for e in ENEMIES:
        _enemy_png(e["shape"], e["c0"], e["c1"]).save(UI / f"enemy_{e['id']}.png")
    for h in HATCH:
        _keep_png(UI / f"hatch_{h['id']}.png", lambda hid=h["id"]: scale_nn(hatch_icon(hid), 3))
    for c in CLAN_CRESTS:
        scale_nn(crest_icon(c), 2).save(UI / f"crest_{c}.png")
    for it in ITEMS:
        item = _keep_png(UI / f"item_{it['id']}.png", lambda iid=it["id"], k=it["kind"]: scale_nn(item_icon(iid, k), 3))
        if it["kind"] == "food":
            food = _keep_png(UI / f"food_{it['id']}.png", lambda im=item: im.copy())
            food.save(SPRITES / f"food_{it['id']}.png")
    for a in ATTACHMENTS:
        _keep_png(UI / f"gear_{a['id']}.png", lambda aid=a["id"], slot=a["slot"]: scale_nn(attach_sprite(aid, slot), 3))
    for typ in TYPE_COLOR:
        _keep_png(UI / f"blast_{typ}.png", lambda t=typ: scale_nn(move_icon(t), 5))
    _keep_png(UI / "blast_boom.png", lambda: scale_nn(move_icon("fire"), 5))
    for spec in RUN_OBS:
        scale_nn(run_obs_sprite(spec["id"]), 2).save(UI / f"run_{spec['id']}.png")
    scale_nn(run_ground(), 2).save(UI / "run_ground.png")
    scale_nn(run_cloud(), 2).save(UI / "run_cloud.png")
    scale_nn(run_hill(), 2).save(UI / "run_hill.png")
    for name, fn in (("dirt_light", lambda: dirt_sheet(10)), ("dirt_mid", lambda: dirt_sheet(18)), ("dirt_heavy", lambda: dirt_sheet(32))):
        scale_nn(fn(), 2).save(UI / f"{name}.png")
    scale_nn(raid_tile(), 3).save(UI / "raid_floor.png")
    scale_nn(raid_sky(), 3).save(UI / "raid_sky.png")
    for b in RAID_BOSSES:
        _enemy_png(b["shape"], b["c0"], b["c1"]).save(UI / f"boss_{b['id']}.png")
    build_pets()
    return UI


def _mark(im, cx, cy, mark, c):
    if mark == "bolt":
        _hline(im, cx - 1, cx + 3, cy - 3, c)
        _hline(im, cx - 2, cx + 1, cy, c)
        _px(im, cx, cy + 2, c)
    elif mark == "flame":
        _disc(im, cx, cy, 2, (255, 160, 40))
        _px(im, cx, cy - 3, (255, 230, 80))
    elif mark == "sword":
        _rect(im, cx, cy - 4, cx + 2, cy + 3, (200, 200, 210))
        _rect(im, cx - 2, cy + 2, cx + 4, cy + 4, (180, 140, 50))
    elif mark == "hat":
        _rect(im, cx - 3, cy - 2, cx + 4, cy, c)
        _rect(im, cx - 1, cy - 4, cx + 2, cy - 2, c)
    elif mark == "ring":
        _disc(im, cx, cy, 3, (240, 200, 50))
        _disc(im, cx, cy, 1, (0, 0, 0, 0))
    elif mark == "star":
        _px(im, cx, cy - 2, c)
        _hline(im, cx - 2, cx + 3, cy, c)
        _px(im, cx, cy + 2, c)
    elif mark == "leaf":
        _disc(im, cx, cy, 2, (50, 150, 60))
    elif mark == "check":
        _px(im, cx, cy, c)
        _px(im, cx + 1, cy + 1, (20, 20, 24))
        _px(im, cx + 2, cy, c)
    elif mark == "hole":
        _px(im, cx, cy, (180, 140, 40))
        _px(im, cx + 2, cy + 1, (180, 140, 40))
    elif mark == "web":
        _hline(im, cx - 2, cx + 3, cy, c)
        _vline(im, cx, cy - 2, cy + 3, c)
    elif mark == "paw":
        _disc(im, cx, cy, 2, c)
        _px(im, cx - 2, cy - 2, c)
        _px(im, cx + 2, cy - 2, c)
    elif mark == "eye":
        _disc(im, cx, cy, 2, (240, 230, 180))
        _px(im, cx, cy, (20, 16, 14))
    elif mark == "wing":
        _rect(im, cx - 4, cy - 1, cx, cy + 2, c)
        _rect(im, cx + 1, cy - 1, cx + 5, cy + 2, c)
    else:
        _px(im, cx, cy, c)


def pet_sprite(kind: str, c0, c1, stage: int = 0, mark: str = "dot") -> Image.Image:
    im = _new(96, 96, (0, 0, 0, 0))
    hi = _shade(c0, (255, 255, 255), 0.28)
    eye = (20, 16, 14)
    glow = (255, 230, 80)
    s = 0.72 + 0.14 * max(0, min(2, stage))

    def blob(cx, cy, rx, ry, col=None):
        rx, ry = max(3, int(rx * s)), max(3, int(ry * s))
        for y in range(cy - ry, cy + ry + 1):
            for x in range(cx - rx, cx + rx + 1):
                nx = (x - cx) / max(1, rx)
                ny = (y - cy) / max(1, ry)
                if nx * nx + ny * ny <= 1:
                    use = col or (hi if ny < -0.25 else (c0 if ny < 0.4 else c1))
                    _px(im, x, y, use)

    cx, cy = 48, 52
    if kind == "egg":
        blob(48, 50, 18, 24, None)
        _disc(im, 42, 42, 4, hi)
        _mark(im, 48, 50, mark, c1)
    elif kind == "mouse":
        blob(cx, cy, 16, 14)
        blob(cx - 12, 34, 5, 6, c0)
        blob(cx + 12, 34, 5, 6, c0)
        blob(cx + 18, cy + 6, 7, 4, c1)
        _disc(im, cx - 7, cy + 2, 3, (220, 50, 50))
        _disc(im, cx + 7, cy + 2, 3, (220, 50, 50))
        _px(im, cx - 5, cy - 2, eye)
        _px(im, cx + 5, cy - 2, eye)
        _mark(im, cx + 18, cy + 2, mark, glow)
    elif kind == "lizard":
        blob(cx, cy + 4, 14, 12)
        blob(cx + 14, cy - 8, 8, 6, c0)
        blob(cx - 10, cy + 14, 4, 6, c1)
        blob(cx + 6, cy + 14, 4, 6, c1)
        _disc(im, cx + 18, cy - 16, 4, (255, 140, 30))
        _px(im, cx + 16, cy - 10, eye)
        if stage >= 2:
            _rect(im, cx - 22, cy - 4, cx - 8, cy + 4, c1)
            _rect(im, cx + 8, cy - 6, cx + 24, cy + 2, c1)
    elif kind == "hero":
        _rect(im, cx - 8, cy - 4, cx + 8, cy + 16, c0)
        _rect(im, cx - 7, cy - 16, cx + 7, cy - 4, (230, 190, 140))
        _rect(im, cx - 10, cy - 18, cx + 10, cy - 12, c0)
        _rect(im, cx + 8, cy - 2, cx + 22, cy + 2, (200, 200, 210))
        _rect(im, cx - 10, cy + 16, cx - 2, cy + 26, c1)
        _rect(im, cx + 2, cy + 16, cx + 10, cy + 26, c1)
        _px(im, cx - 3, cy - 10, eye)
        _px(im, cx + 3, cy - 10, eye)
    elif kind == "plumber":
        _rect(im, cx - 8, cy, cx + 8, cy + 16, c1)
        _rect(im, cx - 6, cy - 12, cx + 6, cy, (230, 180, 130))
        _rect(im, cx - 10, cy - 16, cx + 10, cy - 10, c0)
        _rect(im, cx - 4, cy - 20, cx + 6, cy - 16, c0)
        _rect(im, cx - 10, cy + 16, cx - 2, cy + 26, (40, 40, 48))
        _rect(im, cx + 2, cy + 16, cx + 10, cy + 26, (40, 40, 48))
        _px(im, cx - 3, cy - 8, eye)
        _px(im, cx + 3, cy - 8, eye)
        _rect(im, cx - 5, cy - 4, cx + 5, cy - 2, (120, 50, 20))
    elif kind == "hedgehog":
        blob(cx, cy, 15, 13)
        for i in range(-3, 4):
            _rect(im, cx + i * 4 - 2, cy - 16, cx + i * 4 + 2, cy - 4, c0)
        _rect(im, cx - 10, cy + 14, cx - 2, cy + 22, c1)
        _rect(im, cx + 2, cy + 14, cx + 10, cy + 22, c1)
        _px(im, cx - 5, cy - 2, eye)
        _px(im, cx + 5, cy - 2, eye)
        _rect(im, cx - 2, cy + 4, cx + 3, cy + 6, (240, 200, 50))
    elif kind == "puff":
        blob(cx, cy, 20, 18)
        _rect(im, cx - 10, cy + 14, cx - 2, cy + 22, (220, 80, 110))
        _rect(im, cx + 2, cy + 14, cx + 10, cy + 22, (220, 80, 110))
        _disc(im, cx - 6, cy - 2, 3, (20, 16, 16))
        _disc(im, cx + 6, cy - 2, 3, (20, 16, 16))
        _rect(im, cx - 4, cy + 6, cx + 5, cy + 8, (180, 40, 80))
        _mark(im, cx + 14, cy - 12, mark, glow)
    elif kind == "ninja":
        _rect(im, cx - 8, cy, cx + 8, cy + 16, c0)
        _rect(im, cx - 7, cy - 14, cx + 7, cy, (230, 190, 140))
        _rect(im, cx - 8, cy - 8, cx + 8, cy - 4, c1)
        _rect(im, cx - 10, cy + 16, cx - 2, cy + 26, (40, 40, 48))
        _rect(im, cx + 2, cy + 16, cx + 10, cy + 26, (40, 40, 48))
        _px(im, cx - 3, cy - 10, eye)
        _px(im, cx + 3, cy - 10, eye)
        _px(im, cx - 6, cy - 2, (80, 40, 20))
        _px(im, cx + 6, cy - 2, (80, 40, 20))
        _mark(im, cx, cy - 16, mark, (50, 160, 70))
    elif kind == "saiya":
        _rect(im, cx - 8, cy, cx + 8, cy + 16, c0)
        _rect(im, cx - 7, cy - 12, cx + 7, cy, (230, 180, 130))
        for i in range(-3, 4):
            _rect(im, cx + i * 3, cy - 22, cx + i * 3 + 2, cy - 10, c1)
        _rect(im, cx - 10, cy + 16, cx - 2, cy + 26, (40, 40, 160))
        _rect(im, cx + 2, cy + 16, cx + 10, cy + 26, (40, 40, 160))
        _px(im, cx - 3, cy - 8, eye)
        _px(im, cx + 3, cy - 8, eye)
        _rect(im, cx - 4, cy + 2, cx + 5, cy + 6, (40, 70, 180))
    elif kind == "slayer":
        _rect(im, cx - 8, cy, cx + 8, cy + 16, c0)
        _rect(im, cx - 7, cy - 14, cx + 7, cy, (210, 170, 130))
        for y in range(cy - 2, cy + 14, 4):
            for x in range(cx - 8, cx + 8, 4):
                if ((x + y) // 4) % 2 == 0:
                    _rect(im, x, y, x + 4, y + 4, (20, 20, 24) if y < cy + 6 else (180, 40, 40))
        _rect(im, cx - 6, cy - 20, cx + 6, cy - 14, (20, 20, 24))
        _rect(im, cx - 10, cy + 16, cx - 2, cy + 26, (40, 30, 28))
        _rect(im, cx + 2, cy + 16, cx + 10, cy + 26, (40, 30, 28))
        _px(im, cx - 3, cy - 10, eye)
        _px(im, cx + 3, cy - 10, eye)
        _rect(im, cx + 10, cy - 2, cx + 22, cy + 2, (180, 180, 190))
    elif kind == "sponge":
        _rect(im, cx - 14, cy - 12, cx + 14, cy + 16, c0)
        for hx, hy in ((-8, -6), (4, -4), (-4, 4), (8, 2), (0, -2)):
            _disc(im, cx + hx, cy + hy, 2, (200, 160, 40))
        _rect(im, cx - 14, cy + 10, cx + 14, cy + 18, c1)
        _rect(im, cx - 10, cy + 18, cx - 2, cy + 26, (40, 40, 48))
        _rect(im, cx + 2, cy + 18, cx + 10, cy + 26, (40, 40, 48))
        _px(im, cx - 6, cy - 4, eye)
        _px(im, cx + 6, cy - 4, eye)
        _rect(im, cx - 4, cy + 2, cx + 5, cy + 4, (180, 40, 40))
    elif kind == "spider":
        _rect(im, cx - 8, cy - 2, cx + 8, cy + 14, c0)
        _rect(im, cx - 6, cy - 14, cx + 6, cy - 2, c1)
        for i, ox in enumerate((-16, -12, 10, 14)):
            _rect(im, cx + ox, cy + (i % 2) * 6, cx + ox + 4, cy + 16, c1)
        _rect(im, cx - 10, cy + 14, cx - 2, cy + 24, c1)
        _rect(im, cx + 2, cy + 14, cx + 10, cy + 24, c1)
        _px(im, cx - 3, cy - 8, glow)
        _px(im, cx + 3, cy - 8, glow)
        _hline(im, cx - 4, cx + 5, cy, (20, 16, 16))
        _vline(im, cx, cy - 6, cy + 6, (20, 16, 16))
    elif kind == "cat":
        blob(cx, cy, 14, 12)
        _rect(im, cx - 12, 32, cx - 6, 42, c0)
        _rect(im, cx + 6, 32, cx + 12, 42, c0)
        blob(cx + 16, cy + 4, 8, 5, c1)
        _px(im, cx - 5, cy - 2, glow)
        _px(im, cx + 5, cy - 2, glow)
        _rect(im, cx - 2, cy + 4, cx + 3, cy + 6, (20, 16, 14))
        _rect(im, cx - 8, cy + 14, cx - 3, cy + 24, c1)
        _rect(im, cx + 3, cy + 14, cx + 8, cy + 24, c1)
    elif kind == "dog":
        blob(cx, cy, 15, 13)
        _rect(im, cx - 16, 38, cx - 8, 50, c1)
        _rect(im, cx + 8, 38, cx + 16, 50, c1)
        blob(cx + 14, cy + 8, 7, 4, c0)
        _px(im, cx - 5, cy - 2, eye)
        _px(im, cx + 5, cy - 2, eye)
        _disc(im, cx, cy + 4, 2, (40, 24, 16))
        _rect(im, cx - 8, cy + 14, cx - 3, cy + 24, c1)
        _rect(im, cx + 3, cy + 14, cx + 8, cy + 24, c1)
    elif kind == "fox":
        blob(cx, cy, 14, 12)
        _rect(im, cx - 12, 30, cx - 6, 42, c0)
        _rect(im, cx + 6, 30, cx + 12, 42, c0)
        blob(cx, cy + 4, 8, 6, c1)
        blob(cx + 16, cy + 2, 9, 5, c0)
        _px(im, cx - 5, cy - 2, eye)
        _px(im, cx + 5, cy - 2, eye)
        _rect(im, cx - 8, cy + 14, cx - 3, cy + 24, c1)
        _rect(im, cx + 3, cy + 14, cx + 8, cy + 24, c1)
    elif kind == "owl":
        blob(cx, cy, 16, 14)
        _disc(im, cx - 6, cy - 2, 6, c1)
        _disc(im, cx + 6, cy - 2, 6, c1)
        _disc(im, cx - 6, cy - 2, 2, eye)
        _disc(im, cx + 6, cy - 2, 2, eye)
        _rect(im, cx - 2, cy + 4, cx + 3, cy + 8, (220, 160, 40))
        _rect(im, cx - 16, cy, cx - 6, cy + 8, c1)
        _rect(im, cx + 6, cy, cx + 16, cy + 8, c1)
        _rect(im, cx - 4, cy + 16, cx + 5, cy + 24, c1)
    elif kind == "dragon":
        blob(cx, cy, 16, 13)
        blob(cx + 14, cy - 8, 9, 7, c0)
        _rect(im, cx - 20, cy - 4, cx - 6, cy + 4, c1)
        _rect(im, cx + 6, cy - 2, cx + 22, cy + 6, c1)
        _disc(im, cx + 20, cy - 14, 4, (255, 140, 30))
        _px(im, cx + 16, cy - 10, glow)
        _rect(im, cx - 8, cy + 14, cx - 2, cy + 26, c1)
        _rect(im, cx + 4, cy + 14, cx + 10, cy + 26, c1)
        if stage >= 2:
            _rect(im, cx - 4, cy - 20, cx + 4, cy - 10, (220, 60, 40))
    elif kind == "turtle":
        blob(cx - 2, cy + 6, 16, 13, c1)
        for ox, oy in ((-8, -2), (0, -4), (8, -2), (-6, 4), (6, 4)):
            _rect(im, cx + ox - 2, cy + oy, cx + ox + 3, cy + oy + 3, hi)
        blob(cx + 16, cy - 6, 9, 8, c0)
        _rect(im, cx - 10, cy + 16, cx - 4, cy + 26, c0)
        _rect(im, cx + 2, cy + 16, cx + 8, cy + 26, c0)
        _rect(im, cx - 20, cy + 6, cx - 12, cy + 10, c0)
        _px(im, cx + 18, cy - 8, eye)
        _rect(im, cx + 20, cy - 4, cx + 24, cy - 2, (40, 40, 48))
        if stage >= 2:
            _rect(im, cx - 8, cy, cx - 4, cy + 8, (180, 180, 190))
            _rect(im, cx + 6, cy, cx + 10, cy + 8, (180, 180, 190))
        _mark(im, cx, cy + 4, mark, glow)
    elif kind == "yoshi":
        blob(cx, cy + 4, 15, 14, c0)
        blob(cx + 16, cy - 8, 10, 8, c0)
        _rect(im, cx - 6, cy + 2, cx + 10, cy + 12, c1)
        _rect(im, cx - 10, cy + 16, cx - 2, cy + 28, (230, 70, 70))
        _rect(im, cx + 4, cy + 16, cx + 12, cy + 28, (230, 70, 70))
        _disc(im, cx + 22, cy - 6, 3, (230, 70, 70))
        _px(im, cx + 18, cy - 10, eye)
        _rect(im, cx - 4, 28, cx + 2, 40, c0)
        _mark(im, cx - 12, cy - 8, mark, glow)
    elif kind == "deku":
        _rect(im, cx - 8, cy, cx + 8, cy + 16, c1)
        _rect(im, cx - 7, cy - 14, cx + 7, cy, (230, 190, 140))
        for i in range(-4, 5):
            _rect(im, cx + i * 2, cy - 22, cx + i * 2 + 2, cy - 12, c0)
        _rect(im, cx - 10, cy + 16, cx - 2, cy + 26, (40, 40, 48))
        _rect(im, cx + 2, cy + 16, cx + 10, cy + 26, (40, 40, 48))
        _px(im, cx - 3, cy - 8, eye)
        _px(im, cx + 3, cy - 8, eye)
        _rect(im, cx - 4, cy + 4, cx + 5, cy + 8, (200, 40, 40))
        _mark(im, cx + 12, cy - 2, mark, glow)
    elif kind == "bleach":
        _rect(im, cx - 10, cy, cx + 10, cy + 18, c1)
        _rect(im, cx - 7, cy - 12, cx + 7, cy, (230, 190, 140))
        for i in range(-5, 6):
            _rect(im, cx + i * 3 - 1, cy - 26, cx + i * 3 + 2, cy - 10, c0)
        _rect(im, cx - 10, cy + 18, cx - 2, cy + 26, (20, 20, 24))
        _rect(im, cx + 2, cy + 18, cx + 10, cy + 26, (20, 20, 24))
        _rect(im, cx + 10, cy - 16, cx + 14, cy + 10, (200, 200, 210))
        _rect(im, cx + 8, cy - 18, cx + 16, cy - 14, (230, 230, 236))
        _px(im, cx - 3, cy - 8, eye)
        _px(im, cx + 3, cy - 8, glow)
        _mark(im, cx + 12, cy - 22, mark, glow)
    elif kind == "vegeta":
        _rect(im, cx - 8, cy, cx + 8, cy + 16, c0)
        _rect(im, cx - 7, cy - 12, cx + 7, cy, (230, 180, 130))
        for i in range(-3, 4):
            _rect(im, cx + i * 3, cy - 22, cx + i * 3 + 2, cy - 10, (20, 18, 22))
        _rect(im, cx - 10, cy + 16, cx - 2, cy + 26, (230, 200, 50))
        _rect(im, cx + 2, cy + 16, cx + 10, cy + 26, (230, 200, 50))
        _rect(im, cx - 4, cy + 2, cx + 5, cy + 8, (230, 200, 50))
        _px(im, cx - 3, cy - 8, eye)
        _px(im, cx + 3, cy - 8, eye)
        if stage >= 2:
            _rect(im, cx - 6, cy - 4, cx + 7, cy, (160, 40, 90))
        _mark(im, cx, cy - 16, mark, glow)
    elif kind == "bunny":
        blob(cx, cy + 4, 13, 12)
        _rect(im, cx - 10, 22, cx - 4, 46, c0)
        _rect(im, cx + 4, 22, cx + 10, 46, c0)
        _rect(im, cx - 8, 26, cx - 6, 40, c1)
        _rect(im, cx + 6, 26, cx + 8, 40, c1)
        _px(im, cx - 4, cy, eye)
        _px(im, cx + 4, cy, eye)
        _disc(im, cx, cy + 4, 2, (230, 140, 160))
        _rect(im, cx - 8, cy + 16, cx - 3, cy + 26, c1)
        _rect(im, cx + 3, cy + 16, cx + 8, cy + 26, c1)
        _mark(im, cx + 14, cy - 6, mark, glow)
    elif kind == "frog":
        blob(cx, cy + 6, 16, 12)
        _disc(im, cx - 8, cy - 4, 6, c0)
        _disc(im, cx + 8, cy - 4, 6, c0)
        _disc(im, cx - 8, cy - 4, 2, eye)
        _disc(im, cx + 8, cy - 4, 2, eye)
        _rect(im, cx - 4, cy + 8, cx + 5, cy + 10, (40, 90, 40))
        _rect(im, cx - 10, cy + 16, cx - 4, cy + 24, c1)
        _rect(im, cx + 4, cy + 16, cx + 10, cy + 24, c1)
        _mark(im, cx, cy + 2, mark, glow)
    elif kind == "cook":
        _rect(im, cx - 8, cy, cx + 8, cy + 16, c1)
        _rect(im, cx - 7, cy - 14, cx + 7, cy, (230, 190, 140))
        for i in range(-3, 5):
            _rect(im, cx + i * 2, cy - 22, cx + i * 2 + 2, cy - 12, c0)
        _rect(im, cx - 8, cy - 8, cx + 2, cy - 6, (40, 30, 24))
        _rect(im, cx - 10, cy + 16, cx - 2, cy + 26, (40, 40, 48))
        _rect(im, cx + 2, cy + 16, cx + 10, cy + 26, (40, 40, 48))
        _px(im, cx - 3, cy - 10, eye)
        _px(im, cx + 3, cy - 10, eye)
        _rect(im, cx + 10, cy + 4, cx + 18, cy + 8, (230, 180, 50))
        _mark(im, cx + 14, cy - 4, mark, glow)
    else:
        blob(cx, cy, 14, 14)
        _px(im, cx - 4, cy - 2, glow)
        _px(im, cx + 4, cy - 2, glow)
    _outline(im)
    return im


def build_pets() -> None:
    SPRITES.mkdir(parents=True, exist_ok=True)
    for spec in GEN_FORMS:
        dest = SPRITES / f"{spec['id']}.png"
        # Hand-drawn / generated portraits are much larger than the 2KB blobs.
        if dest.exists() and dest.stat().st_size >= 8000:
            continue
        scale_nn(
            pet_sprite(spec["kind"], spec["c0"], spec["c1"], spec.get("stage", 0), spec.get("mark", "dot")),
            5,
        ).save(dest)


def food_sprite(iid: str) -> Image.Image:
    im = _new(32, 32, (0, 0, 0, 0))
    if iid == "meat":
        _disc(im, 16, 18, 8, (190, 60, 40))
        _disc(im, 14, 16, 3, (230, 120, 80))
        _rect(im, 22, 12, 28, 16, (230, 220, 200))
    elif iid == "deluxe":
        _disc(im, 16, 18, 9, (160, 40, 30))
        _disc(im, 13, 15, 4, (230, 140, 70))
        _rect(im, 8, 10, 24, 13, (80, 40, 24))
        _rect(im, 24, 14, 30, 18, (230, 220, 200))
    elif iid == "onigiri":
        _rect(im, 10, 18, 22, 26, (40, 40, 44))
        for i in range(8):
            _hline(im, 16 - i, 16 + i + 1, 10 + i, (240, 236, 220))
    elif iid == "ration":
        _rect(im, 7, 10, 25, 24, (90, 70, 40))
        _rect(im, 9, 12, 23, 16, (200, 180, 80))
        _rect(im, 10, 18, 22, 22, (40, 36, 30))
    elif iid in ("cola", "soda"):
        can = (200, 40, 50) if iid == "cola" else (40, 90, 180)
        _rect(im, 11, 8, 21, 26, can)
        _rect(im, 12, 6, 20, 9, (200, 200, 210))
        _rect(im, 13, 12, 19, 16, (240, 240, 250))
    elif iid == "fruit":
        _disc(im, 16, 18, 8, (160, 50, 180))
        _rect(im, 15, 8, 17, 12, (40, 120, 40))
        _px(im, 19, 10, (50, 150, 50))
    elif iid == "berry":
        _disc(im, 12, 18, 5, (200, 40, 50))
        _disc(im, 20, 16, 5, (180, 30, 50))
        _disc(im, 16, 22, 4, (220, 60, 70))
        _rect(im, 15, 8, 17, 12, (40, 120, 40))
    elif iid == "ramen":
        _disc(im, 16, 20, 9, (80, 50, 30))
        _disc(im, 16, 18, 7, (230, 180, 70))
        _hline(im, 10, 22, 16, (240, 210, 120))
        _hline(im, 11, 21, 18, (240, 210, 120))
        _rect(im, 20, 10, 22, 20, (180, 180, 190))
    elif iid == "patty":
        _disc(im, 16, 14, 7, (230, 180, 80))
        _rect(im, 9, 16, 23, 20, (120, 60, 30))
        _rect(im, 10, 18, 22, 20, (50, 140, 50))
        _disc(im, 16, 22, 7, (200, 140, 50))
    elif iid == "chili":
        _rect(im, 6, 16, 26, 22, (230, 180, 90))
        _rect(im, 8, 14, 24, 18, (140, 70, 30))
        _rect(im, 10, 12, 22, 16, (200, 50, 30))
    elif iid == "pizza":
        _rect(im, 8, 10, 24, 26, (230, 180, 60))
        _px(im, 8, 10, (0, 0, 0, 0))
        _px(im, 24, 10, (0, 0, 0, 0))
        _disc(im, 14, 16, 2, (200, 40, 40))
        _disc(im, 18, 20, 2, (200, 40, 40))
        _disc(im, 16, 22, 2, (50, 140, 50))
    elif iid == "fish":
        _disc(im, 18, 16, 7, (90, 160, 200))
        _rect(im, 6, 12, 12, 20, (70, 130, 180))
        _px(im, 22, 14, (20, 16, 14))
        _rect(im, 20, 20, 24, 24, (230, 140, 70))
    elif iid == "honey":
        _rect(im, 10, 12, 22, 26, (220, 160, 40))
        _rect(im, 12, 8, 20, 12, (180, 180, 190))
        _rect(im, 12, 16, 20, 22, (240, 200, 70))
    elif iid == "treat":
        _disc(im, 16, 16, 8, (210, 150, 70))
        _disc(im, 16, 16, 3, (180, 110, 50))
        _rect(im, 14, 8, 18, 12, (210, 150, 70))
        _rect(im, 14, 20, 18, 24, (210, 150, 70))
    elif iid == "apple":
        _disc(im, 16, 18, 8, (200, 40, 40))
        _rect(im, 15, 8, 17, 12, (80, 50, 30))
        _px(im, 19, 10, (50, 150, 50))
        _disc(im, 12, 16, 2, (230, 90, 80))
    elif iid == "bread":
        _disc(im, 16, 18, 8, (210, 160, 80))
        _rect(im, 8, 16, 24, 24, (190, 140, 60))
        _px(im, 12, 14, (230, 200, 140))
        _px(im, 18, 16, (230, 200, 140))
    elif iid == "sushi":
        _rect(im, 8, 16, 24, 24, (240, 236, 220))
        _rect(im, 8, 12, 24, 18, (230, 90, 70))
        _rect(im, 10, 14, 22, 16, (40, 40, 44))
    elif iid == "curry":
        _disc(im, 16, 20, 9, (80, 50, 30))
        _disc(im, 16, 18, 7, (210, 110, 40))
        _disc(im, 13, 16, 2, (240, 200, 80))
        _rect(im, 20, 10, 22, 18, (200, 200, 210))
    elif iid == "milk":
        _rect(im, 11, 10, 21, 26, (240, 240, 246))
        _rect(im, 12, 6, 20, 10, (200, 200, 210))
        _rect(im, 13, 14, 19, 22, (230, 230, 236))
    elif iid == "cookie":
        _disc(im, 16, 16, 8, (180, 110, 50))
        _px(im, 12, 14, (80, 40, 24))
        _px(im, 18, 18, (80, 40, 24))
        _px(im, 16, 12, (80, 40, 24))
        _px(im, 14, 20, (80, 40, 24))
    elif iid == "peach":
        _disc(im, 14, 18, 7, (240, 140, 150))
        _disc(im, 18, 18, 7, (230, 120, 130))
        _rect(im, 15, 8, 17, 12, (80, 50, 30))
        _px(im, 20, 10, (50, 150, 50))
    elif iid == "taco":
        _disc(im, 16, 18, 9, (230, 180, 70))
        _rect(im, 8, 18, 24, 26, (0, 0, 0, 0))
        _rect(im, 10, 14, 22, 20, (80, 140, 50))
        _rect(im, 12, 16, 20, 18, (180, 70, 30))
    else:
        _disc(im, 16, 18, 7, (200, 80, 50))
        _rect(im, 12, 10, 20, 14, (80, 50, 30))
    _outline(im)
    return im


def item_icon(iid: str, kind: str) -> Image.Image:
    im = _new(32, 32, (0, 0, 0, 0))
    _rect(im, 3, 3, 29, 29, (22, 20, 26))
    if kind == "food":
        food = food_sprite(iid)
        im.paste(food, (0, 0), food)
        return im
    elif kind == "play":
        _disc(im, 16, 16, 7, (230, 90, 130))
        _px(im, 13, 14, (20, 16, 16))
        _px(im, 19, 14, (20, 16, 16))
    elif kind == "heal":
        _rect(im, 14, 8, 18, 24, (230, 230, 230))
        _rect(im, 8, 14, 24, 18, (200, 40, 40))
    elif kind == "train":
        _rect(im, 8, 14, 24, 18, (90, 90, 100))
        _disc(im, 10, 16, 3, (60, 60, 70))
        _disc(im, 22, 16, 3, (60, 60, 70))
    elif kind == "hatch":
        _rect(im, 10, 12, 22, 22, (230, 80, 180))
    elif kind == "gamble":
        _rect(im, 8, 10, 24, 22, (40, 100, 180))
        _px(im, 16, 16, (255, 220, 70))
    elif kind == "chip":
        _rect(im, 10, 10, 22, 22, (40, 180, 90))
        _rect(im, 13, 13, 19, 19, (200, 255, 180))
    elif kind == "luck":
        _disc(im, 16, 16, 7, (220, 180, 50))
    elif kind == "map":
        _rect(im, 8, 10, 24, 22, (210, 190, 120))
        _hline(im, 10, 22, 16, (80, 50, 30))
    elif kind == "flee":
        _disc(im, 16, 16, 7, (80, 80, 90))
        _px(im, 16, 16, (200, 200, 210))
    else:
        _disc(im, 16, 16, 6, (180, 180, 80))
    _outline(im)
    return im


def attach_sprite(aid: str, slot: str) -> Image.Image:
    im = _new(48, 48, (0, 0, 0, 0))
    gold, iron, red, cloth, gem = (220, 180, 50), (140, 140, 150), (180, 40, 40), (40, 70, 160), (80, 200, 230)
    if aid == "visor":
        _rect(im, 10, 18, 38, 26, (20, 22, 28))
        _rect(im, 14, 20, 34, 24, (40, 180, 220))
        _px(im, 16, 21, (200, 255, 255))
    elif aid == "crown":
        _rect(im, 12, 22, 36, 30, gold)
        for x in (14, 22, 30):
            _rect(im, x, 14, x + 4, 22, gold)
        _px(im, 24, 12, red)
    elif aid == "hornband":
        _rect(im, 14, 22, 34, 28, (90, 50, 30))
        _rect(im, 10, 10, 16, 24, (230, 220, 200))
        _rect(im, 32, 10, 38, 24, (230, 220, 200))
    elif aid == "cap":
        _rect(im, 12, 18, 36, 28, (40, 90, 50))
        _rect(im, 8, 24, 40, 28, (40, 90, 50))
        _rect(im, 20, 12, 28, 18, (40, 90, 50))
    elif aid == "helm":
        _rect(im, 12, 14, 36, 32, iron)
        _rect(im, 16, 20, 32, 26, (20, 20, 24))
        _rect(im, 20, 10, 28, 14, iron)
    elif aid == "cape":
        _rect(im, 16, 10, 32, 16, red)
        for y in range(16, 42):
            _hline(im, 12 + (y - 16) // 6, 36 - (y - 16) // 6, y, red if y % 2 == 0 else (140, 30, 30))
    elif aid == "wings":
        for i in range(6):
            _rect(im, 6, 12 + i * 4, 18 - i, 16 + i * 4, (230, 230, 240))
            _rect(im, 30 + i, 12 + i * 4, 42, 16 + i * 4, (230, 230, 240))
        _rect(im, 20, 20, 28, 28, (200, 180, 60))
    elif aid == "pack":
        _rect(im, 14, 14, 34, 36, (90, 70, 40))
        _rect(im, 16, 16, 32, 22, (70, 50, 30))
        _rect(im, 18, 24, 30, 32, (50, 90, 50))
    elif aid == "cloak":
        _rect(im, 14, 8, 34, 16, (30, 24, 40))
        for y in range(16, 42):
            _hline(im, 10, 38, y, (24, 18, 32) if y % 3 else (40, 30, 50))
    elif aid == "shellp":
        _disc(im, 24, 24, 14, (70, 140, 90))
        _disc(im, 24, 24, 8, (50, 100, 70))
        _px(im, 18, 18, (180, 220, 160))
    elif aid == "fangg":
        _rect(im, 20, 8, 28, 28, (230, 230, 236))
        _rect(im, 22, 28, 26, 40, (180, 140, 50))
        _px(im, 24, 10, (200, 200, 210))
    elif aid == "orb":
        _disc(im, 24, 24, 10, gem)
        _disc(im, 20, 20, 3, (220, 255, 255))
        _rect(im, 22, 34, 26, 42, iron)
    elif aid == "badge":
        _disc(im, 24, 22, 10, gold)
        _rect(im, 20, 18, 28, 26, (40, 70, 160))
        _px(im, 24, 22, gold)
    elif aid == "lantern":
        _rect(im, 18, 10, 30, 16, iron)
        _rect(im, 16, 16, 32, 34, (255, 180, 40))
        _rect(im, 20, 34, 28, 40, (80, 50, 30))
        _px(im, 24, 20, (255, 240, 160))
    elif aid == "luckgem":
        _rect(im, 18, 12, 30, 36, (180, 50, 200))
        _px(im, 24, 16, (255, 200, 255))
        _px(im, 22, 24, (240, 180, 255))
    elif aid == "boots":
        _rect(im, 10, 24, 22, 40, (80, 50, 30))
        _rect(im, 26, 24, 38, 40, (80, 50, 30))
        _rect(im, 8, 36, 22, 42, (40, 30, 24))
        _rect(im, 26, 36, 40, 42, (40, 30, 24))
    elif aid == "greaves":
        _rect(im, 12, 16, 22, 40, iron)
        _rect(im, 26, 16, 36, 40, iron)
        _rect(im, 14, 20, 20, 24, (200, 200, 210))
    elif aid == "sandals":
        _rect(im, 10, 32, 22, 38, (180, 140, 70))
        _rect(im, 26, 32, 38, 38, (180, 140, 70))
        _vline(im, 16, 22, 32, (120, 80, 40))
        _vline(im, 32, 22, 32, (120, 80, 40))
    elif aid == "magnets":
        _rect(im, 10, 22, 20, 40, red)
        _rect(im, 28, 22, 38, 40, cloth)
        _rect(im, 12, 34, 18, 38, iron)
        _rect(im, 30, 34, 36, 38, iron)
    elif aid == "claws":
        _rect(im, 10, 28, 20, 38, (40, 30, 24))
        _rect(im, 28, 28, 38, 38, (40, 30, 24))
        for x in (12, 16, 30, 34):
            _rect(im, x, 18, x + 2, 28, (230, 230, 220))
    else:
        _disc(im, 24, 24, 8, gold)
    _outline(im)
    return im


def run_obs_sprite(oid: str) -> Image.Image:
    im = _new(32, 32, (0, 0, 0, 0))
    if oid == "rock":
        _disc(im, 16, 20, 10, (110, 100, 90))
        _disc(im, 12, 16, 4, (140, 130, 120))
        _rect(im, 6, 24, 26, 30, (70, 64, 56))
    elif oid == "spike":
        for i, x in enumerate((8, 16, 24)):
            h = 18 + (i % 2) * 6
            for y in range(h):
                w = max(1, 5 - y // 4)
                _hline(im, x - w, x + w, 30 - y, (180, 180, 190) if y < 4 else (90, 90, 100))
    elif oid == "crate":
        _rect(im, 6, 8, 26, 28, (160, 110, 50))
        _hline(im, 6, 26, 18, (90, 60, 30))
        _vline(im, 16, 8, 28, (90, 60, 30))
        _rect(im, 6, 8, 26, 10, (200, 160, 80))
    elif oid == "log":
        _rect(im, 2, 16, 30, 26, (120, 80, 40))
        _disc(im, 4, 21, 5, (160, 110, 60))
        _disc(im, 28, 21, 5, (90, 60, 30))
        _px(im, 12, 18, (80, 50, 24))
    elif oid == "thorn":
        _rect(im, 14, 18, 18, 30, (50, 120, 50))
        _px(im, 10, 16, (40, 90, 40))
        _px(im, 20, 14, (40, 90, 40))
        _px(im, 16, 10, (200, 40, 40))
        _px(im, 12, 12, (200, 40, 40))
        _px(im, 22, 12, (200, 40, 40))
    elif oid == "bird":
        _disc(im, 16, 16, 6, (40, 40, 48))
        _rect(im, 6, 14, 12, 18, (30, 30, 36))
        _rect(im, 20, 12, 28, 16, (30, 30, 36))
        _px(im, 20, 14, (255, 200, 40))
        _px(im, 14, 14, (255, 255, 255))
    elif oid == "drone":
        _rect(im, 8, 14, 24, 22, (80, 80, 90))
        _rect(im, 4, 16, 8, 20, (200, 200, 210))
        _rect(im, 24, 16, 28, 20, (200, 200, 210))
        _disc(im, 16, 18, 2, (80, 220, 120))
    else:
        _rect(im, 14, 6, 18, 30, (120, 90, 50))
        _rect(im, 8, 6, 24, 12, (90, 70, 40))
    _outline(im)
    return im


def run_ground() -> Image.Image:
    im = _new(32, 16, (0, 0, 0, 0))
    _rect(im, 0, 0, 32, 16, (70, 120, 50))
    _hline(im, 0, 32, 0, (160, 200, 90))
    for x in range(0, 32, 8):
        _rect(im, x, 6, x + 7, 16, (90, 70, 40) if (x // 8) % 2 == 0 else (70, 54, 30))
    return im


def run_cloud() -> Image.Image:
    im = _new(48, 20, (0, 0, 0, 0))
    _disc(im, 16, 12, 8, (230, 230, 240))
    _disc(im, 28, 10, 9, (230, 230, 240))
    _disc(im, 38, 12, 6, (210, 214, 230))
    return im


def run_hill() -> Image.Image:
    im = _new(64, 24, (0, 0, 0, 0))
    for y in range(24):
        w = 8 + y * 2
        _hline(im, 32 - w // 2, 32 + w // 2, y, (40, 80, 50) if y > 8 else (50, 100, 60))
    return im


def dirt_sheet(n: int) -> Image.Image:
    im = _new(48, 48, (0, 0, 0, 0))
    rng = random.Random(n * 17 + 9)
    cols = ((70, 50, 30, 255), (50, 36, 22, 255), (90, 70, 40, 255), (30, 24, 16, 255))
    for _ in range(n):
        x, y = rng.randint(6, 42), rng.randint(10, 42)
        c = cols[rng.randint(0, 3)]
        _px(im, x, y, c)
        if rng.random() < 0.5:
            _px(im, x + 1, y, cols[rng.randint(0, 3)])
    return im


def raid_tile() -> Image.Image:
    im = _new(32, 32, (36, 32, 40, 255))
    _dither(im, 0, 0, 32, 32, (40, 36, 44), (28, 24, 32))
    _hline(im, 0, 32, 0, (70, 60, 40))
    _vline(im, 0, 0, 32, (20, 16, 18))
    return im


def raid_sky() -> Image.Image:
    im = _new(32, 32, (18, 16, 28, 255))
    for y in range(32):
        c = (18 + y // 4, 16 + y // 6, 36 + y // 3)
        _hline(im, 0, 32, y, c)
    _px(im, 8, 6, (220, 220, 180))
    _px(im, 22, 12, (220, 220, 180))
    _px(im, 16, 4, (180, 180, 140))
    return im


if __name__ == "__main__":
    p = build_all()
    print("wrote", p, "files", len(list(p.glob('*.png'))))
