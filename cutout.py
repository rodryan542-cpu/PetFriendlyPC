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
    h, w = walk.shape
    seen = np.zeros((h, w), dtype=bool)
    st: list[tuple[int, int]] = []
    for x in range(w):
        st.append((0, x))
        st.append((h - 1, x))
    for y in range(h):
        st.append((y, 0))
        st.append((y, w - 1))
    while st:
        y, x = st.pop()
        if y < 0 or x < 0 or y >= h or x >= w or seen[y, x]:
            continue
        seen[y, x] = True
        if not walk[y, x]:
            continue
        st.extend(((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)))
    return seen & walk


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


def cutout(src: Path) -> Image.Image:
    im = Image.open(src).convert("RGBA")
    if max(im.size) > 720:
        im.thumbnail((720, 720), Image.Resampling.NEAREST)
    return clean_rgba(im, crop=True)
