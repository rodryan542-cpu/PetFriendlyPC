"""Border-only key. Eat magenta spill on the silhouette. Do not fill keyed pockets."""
from __future__ import annotations

from pathlib import Path

from PIL import Image
import numpy as np


def is_chroma_key(r: int, g: int, b: int) -> bool:
    return _spill_px(r, g, b)


def is_magenta_bg(r: int, g: int, b: int) -> bool:
    return _spill_px(r, g, b)


def is_key(r: int, g: int, b: int) -> bool:
    return _spill_px(r, g, b)


def _spill_px(r: int, g: int, b: int) -> bool:
    mx = r if r > b else b
    return mx >= 40 and g <= 72 and r >= g + 22 and b >= g + 12 and (r + b) >= 70


def _is_bg(r: int, g: int, b: int, br: int, bg: int, bb: int) -> bool:
    return _spill_px(r, g, b)


def _chroma_mask(r: np.ndarray, g: np.ndarray, b: np.ndarray) -> np.ndarray:
    rd = r.astype(np.int16)
    gd = g.astype(np.int16)
    return (r >= 190) & (g <= 48) & (b >= 150) & ((rd - gd) >= 140)


def _spill_mask(r: np.ndarray, g: np.ndarray, b: np.ndarray) -> np.ndarray:
    rd = r.astype(np.int16)
    gd = g.astype(np.int16)
    bd = b.astype(np.int16)
    mx = np.maximum(rd, bd)
    return (mx >= 40) & (gd <= 72) & (rd >= gd + 22) & (bd >= gd + 12) & ((rd + bd) >= 70)


def _dilate(m: np.ndarray) -> np.ndarray:
    d = m.copy()
    d[1:, :] |= m[:-1, :]
    d[:-1, :] |= m[1:, :]
    d[:, 1:] |= m[:, :-1]
    d[:, :-1] |= m[:, 1:]
    return d


def binary_rgba(im: Image.Image) -> Image.Image:
    arr = np.array(im.convert("RGBA"))
    keep = arr[:, :, 3] >= 16
    arr[:, :, 3] = np.where(keep, 255, 0)
    arr[~keep, 0] = 0
    arr[~keep, 1] = 0
    arr[~keep, 2] = 0
    return Image.fromarray(arr, "RGBA")


def _flood_from_border(walk: np.ndarray) -> np.ndarray:
    seed = np.zeros_like(walk)
    seed[0, :] = walk[0, :]
    seed[-1, :] = walk[-1, :]
    seed[:, 0] = walk[:, 0]
    seed[:, -1] = walk[:, -1]
    last = -1
    while int(seed.sum()) != last:
        last = int(seed.sum())
        nxt = seed
        for _ in range(6):
            d = nxt.copy()
            d[1:, :] |= nxt[:-1, :]
            d[:-1, :] |= nxt[1:, :]
            d[:, 1:] |= nxt[:, :-1]
            d[:, :-1] |= nxt[:, 1:]
            nxt = d & walk
        seed = nxt
    return seed


def clean_rgba(im: Image.Image, crop: bool = True) -> Image.Image:
    arr = np.asarray(im.convert("RGBA")).copy()
    r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
    spill = _spill_mask(r, g, b)
    key = _chroma_mask(r, g, b)
    empty = a < 16
    # Walk in from the frame through empty + magenta fringe. Stop on black outline / real paint.
    bg = _flood_from_border(empty | spill)
    # Hot key pockets (armpits) stay empty. Do not punch red cloth or fill them back in.
    bg |= key
    for _ in range(3):
        extra = (~bg) & (a >= 16) & _dilate(bg) & spill
        if not extra.any():
            break
        bg |= extra
    purple = (g <= 18) & (b >= 10) & (b.astype(np.int16) * 2 >= r.astype(np.int16)) & (r <= 100) & ((r.astype(np.int16) + b.astype(np.int16)) >= 24)
    for _ in range(2):
        extra = (~bg) & (a >= 16) & _dilate(bg) & purple
        if not extra.any():
            break
        bg |= extra
    alpha = (~bg) & (a >= 16)
    arr[:, :, 3] = np.where(alpha, 255, 0)
    gone = arr[:, :, 3] == 0
    arr[gone, 0] = 0
    arr[gone, 1] = 0
    arr[gone, 2] = 0
    out = Image.fromarray(arr, "RGBA")
    if crop:
        box = out.getbbox()
        if box:
            out = out.crop(box)
    return out


def stamp_on_body(im: Image.Image, overlay: Image.Image) -> Image.Image:
    arr = np.array(im.convert("RGBA"))
    over = np.array(overlay.convert("RGBA").resize(im.size, Image.Resampling.NEAREST))
    body = arr[:, :, 3] >= 16
    spec = over[:, :, 3] >= 16
    m = body & spec
    arr[m, 0:3] = over[m, 0:3]
    arr[m, 3] = 255
    gone = arr[:, :, 3] < 16
    arr[gone, 0] = 0
    arr[gone, 1] = 0
    arr[gone, 2] = 0
    arr[gone, 3] = 0
    arr[~gone, 3] = 255
    return Image.fromarray(arr, "RGBA")


def knockout_backdrop(im: Image.Image, crop: bool = True) -> Image.Image:
    """Strip baked checker / solid backdrops. Flood from the frame only."""
    im = im.convert("RGBA")
    if max(im.size) > 720:
        im = im.copy()
        im.thumbnail((720, 720), Image.Resampling.LANCZOS)
    arr = np.asarray(im).copy()
    h, w = arr.shape[:2]
    if h < 8 or w < 8:
        return clean_rgba(im, crop=crop)
    corners = (int(arr[0, 0, 3]), int(arr[0, w - 1, 3]), int(arr[h - 1, 0, 3]), int(arr[h - 1, w - 1, 3]))
    if sum(1 for x in corners if x < 16) >= 3:
        return clean_rgba(im, crop=crop)
    rgb = arr[:, :, :3].astype(np.int16)
    border = np.concatenate((arr[0, :, :3], arr[-1, :, :3], arr[:, 0, :3], arr[:, -1, :3])).astype(np.int16)
    q = (border // 18) * 18
    keys = [tuple(int(v) for v in row) for row in q]
    counts: dict[tuple[int, int, int], int] = {}
    for k in keys:
        counts[k] = counts.get(k, 0) + 1
    top = [np.array(k, dtype=np.int16) for k, _ in sorted(counts.items(), key=lambda kv: -kv[1])[:5]]
    if not top:
        return clean_rgba(im, crop=crop)
    dist = None
    for c in top:
        d = np.abs(rgb - c).sum(axis=2)
        dist = d if dist is None else np.minimum(dist, d)
    lum = (0.30 * rgb[:, :, 0] + 0.59 * rgb[:, :, 1] + 0.11 * rgb[:, :, 2]).astype(np.int16)
    sat = np.maximum(np.maximum(rgb[:, :, 0], rgb[:, :, 1]), rgb[:, :, 2]) - np.minimum(
        np.minimum(rgb[:, :, 0], rgb[:, :, 1]), rgb[:, :, 2]
    )
    walk = (dist <= 42) & (lum >= 28) & ((sat <= 55) | (dist <= 22))
    # Solid black frames (common on generated puff / night sprites).
    walk[:, :] = walk | ((lum <= 18) & (sat <= 28))
    walk[:, :] = walk | (arr[:, :, 3] < 16)
    bg = _flood_from_border(walk)
    arr[bg, 0] = 0
    arr[bg, 1] = 0
    arr[bg, 2] = 0
    arr[bg, 3] = 0
    return clean_rgba(Image.fromarray(arr, "RGBA"), crop=crop)


def cutout(src: Path) -> Image.Image:
    im = Image.open(src).convert("RGBA")
    if max(im.size) > 720:
        im.thumbnail((720, 720), Image.Resampling.NEAREST)
    return knockout_backdrop(im, crop=True)
