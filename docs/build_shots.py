"""Compose README shots from the real sprites. Run from the repo root."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SPR = ROOT / "sprites"
UI = ROOT / "ui"
OUT = ROOT / "docs"
NAVY = (14, 16, 22, 255)
INK = (236, 228, 210, 255)
DIM = (140, 148, 160, 255)
GOLD = (232, 188, 72, 255)
MINT = (96, 214, 180, 255)
LINE = (40, 48, 62, 255)


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    p = Path(r"C:\Windows\Fonts") / name
    if p.exists():
        return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def load(path: Path) -> Image.Image:
    im = Image.open(path).convert("RGBA")
    return im


def fit_h(im: Image.Image, h: int) -> Image.Image:
    if im.height <= 0:
        return im
    w = max(8, int(im.width * (h / im.height)))
    return im.resize((w, h), Image.Resampling.LANCZOS)


def sheet(w: int, h: int) -> Image.Image:
    im = Image.new("RGBA", (w, h), NAVY)
    d = ImageDraw.Draw(im)
    for x in range(0, w, 32):
        d.line([(x, 0), (x, h)], fill=LINE)
    for y in range(0, h, 32):
        d.line([(0, y), (w, y)], fill=LINE)
    d.rectangle((0, h - 54, w, h), fill=(22, 48, 38, 255))
    d.rectangle((0, 0, 6, h), fill=GOLD)
    d.rectangle((w - 6, 0, w, h), fill=MINT)
    return im


def paste_c(dst: Image.Image, src: Image.Image, cx: int, by: int) -> None:
    dst.paste(src, (cx - src.width // 2, by - src.height), src)


def banner() -> None:
    im = sheet(1280, 420)
    d = ImageDraw.Draw(im)
    d.text((48, 36), "PetFriendlyPC", font=font(48, True), fill=INK)
    d.text((52, 96), "a roommate for monitor 2", font=font(22), fill=DIM)
    d.text((52, 132), "hatch  ·  fight  ·  LAN clan", font=font(18), fill=GOLD)
    pets = [
        SPR / "bunny.png",
        SPR / "frog.png",
        SPR / "cat.png",
        SPR / "puppy.png",
        SPR / "kirby.png",
        SPR / "agumon_master.png",
    ]
    xs = [170, 360, 550, 740, 930, 1120]
    for p, x in zip(pets, xs):
        spr = fit_h(load(p), 210)
        paste_c(im, spr, x, 392)
    im.convert("RGB").save(OUT / "banner.png", quality=92)


def hatch() -> None:
    im = sheet(1280, 420)
    d = ImageDraw.Draw(im)
    d.text((48, 28), "Hatch Lab", font=font(40, True), fill=INK)
    d.text((52, 82), "Six hours on the clock. You can shave it.", font=font(20), fill=DIM)
    egg = fit_h(load(SPR / "egg_agumon.png"), 240)
    paste_c(im, egg, 220, 390)
    tools = [
        (UI / "hatch_warm.png", "Warm"),
        (UI / "hatch_lamp.png", "Lamp"),
        (UI / "hatch_nest.png", "Nest"),
        (UI / "hatch_carry.png", "Carry"),
        (UI / "hatch_comet.png", "Comet"),
    ]
    for i, (p, lab) in enumerate(tools):
        x = 460 + i * 150
        spr = fit_h(load(p), 150)
        paste_c(im, spr, x, 320)
        tw = d.textlength(lab, font=font(16))
        d.text((x - tw / 2, 340), lab, font=font(16), fill=GOLD)
    d.text((460, 372), "Care the shell. Tools cut minutes. Run jumps rocks on the desk.", font=font(16), fill=DIM)
    im.convert("RGB").save(OUT / "hatch.png", quality=92)


def lan() -> None:
    im = sheet(1280, 420)
    d = ImageDraw.Draw(im)
    d.text((48, 28), "LAN multiplayer", font=font(40, True), fill=INK)
    d.text((52, 82), "UDP on your Wi-Fi. No account. No server.", font=font(20), fill=DIM)
    left = fit_h(load(SPR / "agumon_master.png"), 230)
    right = fit_h(load(SPR / "cat.png"), 230)
    paste_c(im, left, 280, 392)
    paste_c(im, right, 1000, 392)
    blast = fit_h(load(UI / "blast_fire.png"), 150)
    paste_c(im, blast, 640, 280)
    d.text((520, 300), "invite  ·  1v1  ·  raid  ·  war", font=font(20, True), fill=GOLD)
    d.text((488, 336), "Same house, two PCs, both running this.", font=font(16), fill=DIM)
    im.convert("RGB").save(OUT / "lan.png", quality=92)


def fight() -> None:
    im = sheet(1280, 420)
    d = ImageDraw.Draw(im)
    d.text((48, 28), "Desktop combat", font=font(40, True), fill=INK)
    d.text((52, 82), "The foe walks in on monitor 2. Moves throw real blasts.", font=font(20), fill=DIM)
    pet = fit_h(load(SPR / "agumon_master.png"), 240)
    foe = fit_h(load(UI / "enemy_numemon.png"), 220)
    paste_c(im, pet, 280, 392)
    paste_c(im, foe, 1000, 392)
    boom = fit_h(load(UI / "blast_boom.png"), 180)
    paste_c(im, boom, 640, 300)
    meat = fit_h(load(UI / "item_meat.png"), 90)
    paste_c(im, meat, 160, 200)
    d.text((430, 360), "137 foes   13 blast types   HP on both walkers", font=font(16), fill=GOLD)
    im.convert("RGB").save(OUT / "fight.png", quality=92)


def social() -> None:
    im = sheet(1280, 640)
    d = ImageDraw.Draw(im)
    d.text((64, 72), "PetFriendlyPC", font=font(64, True), fill=INK)
    d.text((68, 154), "Tamagotchi for your second monitor.", font=font(28), fill=DIM)
    d.text((68, 200), "Hatch · Fight · LAN", font=font(24), fill=GOLD)
    pets = [
        SPR / "bunny.png",
        SPR / "frog.png",
        SPR / "cat.png",
        SPR / "kirby.png",
        SPR / "agumon_master.png",
    ]
    xs = [180, 400, 640, 880, 1100]
    for p, x in zip(pets, xs):
        spr = fit_h(load(p), 280)
        paste_c(im, spr, x, 580)
    im.convert("RGB").save(OUT / "social.png", quality=92)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    banner()
    hatch()
    lan()
    fight()
    social()
    print("wrote", OUT)
