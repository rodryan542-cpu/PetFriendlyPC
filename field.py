"""Second-monitor battleground: egg run + raid. Pixel, full width of DISPLAY2."""
from __future__ import annotations

import random
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from depth import RUN_OBS, combat_stats
from game_data import ENEMY_BY_ID, LINE_NAME, move_by_id, pick_enemy

from paths import asset_root

UI = asset_root() / "ui"
FIELD_W, FIELD_H = 1920, 700
GROUND_Y = 560
RUN_X = 220


def _font(size: int):
    p = Path(r"C:\Windows\Fonts\segoeui.ttf")
    if p.exists():
        return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


F_BIG = _font(28)
F_MID = _font(18)
F_SM = _font(14)


def _load(name: str) -> Image.Image:
    path = UI / name
    if path.exists():
        return Image.open(path).convert("RGBA")
    return Image.new("RGBA", (32, 32), (0, 0, 0, 0))


def _fit(im: Image.Image, w: int, h: int) -> Image.Image:
    if im.width <= 0 or im.height <= 0:
        return im
    s = min(w / im.width, h / im.height)
    nw, nh = max(8, int(im.width * s)), max(8, int(im.height * s))
    return im.resize((nw, nh), Image.Resampling.NEAREST)


def new_run() -> dict:
    return {
        "kind": "run",
        "t": 0.0,
        "scroll": 0.0,
        "speed": 240.0,
        "y": 0.0,
        "vy": 0.0,
        "ground": True,
        "lives": 3,
        "dist": 0.0,
        "ifr": 0.0,
        "obs": [],
        "spawn": 1.1,
        "alive": True,
        "over": False,
        "score": 0,
    }


def new_raid(boss: dict, members: list, seed: int) -> dict:
    rng = random.Random(seed)
    waves = []
    for i in range(3):
        tag_pool = list({m.get("tag") or "DIGIMON" for m in members}) or ["DIGIMON"]
        waves.append({"band": min(3, i + 1), "tag": rng.choice(tag_pool)})
    return {
        "kind": "raid",
        "seed": seed,
        "boss": dict(boss),
        "members": members[:4],
        "wave": 0,
        "waves": waves,
        "enemy": None,
        "ehp": 0,
        "emax": 1,
        "php": 1,
        "pmax": 1,
        "status": "",
        "log": "RAID START",
        "over": False,
        "won": False,
        "t": 0.0,
        "ally_cd": 0.0,
        "hits": [],
    }


def tick_run(st: dict, dt: float, jump: bool) -> None:
    if st.get("over"):
        return
    st["t"] += dt
    st["ifr"] = max(0.0, float(st["ifr"]) - dt)
    st["speed"] = min(640.0, 240.0 + st["dist"] * 0.085 + st["t"] * 6.0)
    if jump and st["ground"] and st["alive"]:
        st["vy"] = -640.0
        st["ground"] = False
    st["vy"] += 1750.0 * dt
    st["y"] += st["vy"] * dt
    if st["y"] >= 0:
        st["y"] = 0.0
        st["vy"] = 0.0
        st["ground"] = True
    st["scroll"] += st["speed"] * dt
    st["dist"] += st["speed"] * dt * 0.08
    st["spawn"] -= dt
    if st["spawn"] <= 0 and st["alive"]:
        gap = max(0.55, 1.35 - st["t"] * 0.025)
        st["spawn"] = gap
        spec = random.choice(RUN_OBS)
        fly = bool(spec["fly"]) and random.random() < 0.7
        st["obs"].append(
            {
                "id": spec["id"],
                "x": FIELD_W + 40,
                "y": (GROUND_Y - 90 - random.randint(0, 50)) if fly else GROUND_Y,
                "w": spec["w"],
                "h": spec["h"],
                "fly": fly,
            }
        )
    keep = []
    egg = (RUN_X, GROUND_Y - 10 + int(st["y"]), 44, 52)
    for o in st["obs"]:
        o["x"] -= st["speed"] * dt
        if o["x"] + o["w"] < -20:
            continue
        keep.append(o)
        if st["alive"] and st["ifr"] <= 0 and _overlap(egg, (o["x"], o["y"] - o["h"], o["w"], o["h"])):
            st["lives"] -= 1
            st["ifr"] = 0.85
            st["vy"] = -220
            st["ground"] = False
            if st["lives"] <= 0:
                st["alive"] = False
                st["over"] = True
                st["score"] = int(st["dist"])
    st["obs"] = keep


def _overlap(a, b) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by


def render_run(pet, st: dict) -> Image.Image:
    im = Image.new("RGBA", (FIELD_W, FIELD_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    sky_top, sky_bot = (24, 40, 70), (80, 140, 190)
    for y in range(FIELD_H):
        t = y / max(1, FIELD_H)
        c = tuple(int(sky_top[i] * (1 - t) + sky_bot[i] * t) for i in range(3))
        d.line((0, y, FIELD_W, y), fill=c)
    hill = _load("run_hill.png")
    cloud = _load("run_cloud.png")
    ground = _load("run_ground.png")
    hs = int(st["scroll"] * 0.35)
    cs = int(st["scroll"] * 0.2)
    for x in range(-((hs) % max(1, hill.width)) - hill.width, FIELD_W + 80, max(40, hill.width)):
        im.paste(hill, (x, GROUND_Y - hill.height - 8), hill)
    for i in range(6):
        cx = int((i * 340 - cs) % (FIELD_W + 200) - 80)
        im.paste(cloud, (cx, 40 + (i % 3) * 36), cloud)
    gw = max(16, ground.width)
    g0 = -int(st["scroll"]) % gw
    for x in range(g0 - gw, FIELD_W + gw, gw):
        im.paste(ground, (x, GROUND_Y), ground)
        im.paste(ground, (x, GROUND_Y + ground.height), ground)
    d.rectangle((0, GROUND_Y + 32, FIELD_W, FIELD_H), fill=(40, 30, 22))
    for o in st["obs"]:
        spr = _fit(_load(f"run_{o['id']}.png"), o["w"] + 8, o["h"] + 8)
        im.paste(spr, (int(o["x"]), int(o["y"] - spr.height)), spr)
    body = pet.body(110)
    squash = 1.0
    if not st["ground"]:
        squash = 0.88
        body = body.rotate(-12, expand=True, resample=Image.Resampling.NEAREST)
    nh = max(8, int(body.height * squash))
    body = body.resize((body.width, nh), Image.Resampling.NEAREST)
    ex = RUN_X - body.width // 2
    ey = GROUND_Y - body.height + 8 + int(st["y"])
    if st["ifr"] > 0 and int(st["t"] * 20) % 2 == 0:
        pass
    else:
        im.paste(body, (ex, ey), body)
    d.text((24, 16), "EGG RUN", font=F_BIG, fill=(232, 188, 72))
    d.text((24, 52), f"Dist {int(st['dist'])}   Speed {int(st['speed'])}", font=F_MID, fill=(236, 228, 210))
    lives = "♥ " * max(0, int(st["lives"]))
    d.text((24, 82), lives or "OUT", font=F_MID, fill=(214, 72, 64))
    d.rectangle((FIELD_W - 160, 16, FIELD_W - 24, 56), outline=(232, 188, 72), width=2)
    d.text((FIELD_W - 148, 24), "LEAVE", font=F_MID, fill=(236, 228, 210))
    if st.get("over"):
        d.rectangle((660, 240, 1260, 420), fill=(18, 16, 22), outline=(232, 188, 72), width=3)
        d.text((700, 270), "SHELL CRACKED", font=F_BIG, fill=(232, 188, 72))
        d.text((700, 320), f"Distance {int(st['dist'])}   Hatch time cut on LEAVE", font=F_MID, fill=(236, 228, 210))
        d.text((700, 360), "Click LEAVE to cash in.", font=F_SM, fill=(150, 142, 128))
    else:
        d.text((24, FIELD_H - 40), "Click or Space to jump. It gets faster. Don't cheap the landing.", font=F_SM, fill=(200, 200, 180))
    return im


def run_hits() -> list:
    return [("field_leave", (FIELD_W - 160, 16, FIELD_W - 24, 56)), ("field_jump", (0, 80, FIELD_W, FIELD_H))]


def raid_hits(st: dict, pet) -> list:
    hits = [("field_leave", (FIELD_W - 160, 16, FIELD_W - 24, 56))]
    if st.get("over"):
        return hits
    load = [m for m in (pet.p().get("loadout") or []) if m][:4]
    if not load:
        hits.append(("raid:struggle", (860, 620, 1060, 680)))
    else:
        for i, mid in enumerate(load):
            x0 = 40 + i * 280
            hits.append((f"raid:{mid}", (x0, 620, x0 + 260, 680)))
    return hits


def start_raid_wave(pet, st: dict) -> None:
    stats = combat_stats(pet.p(), pet.p()["stage_i"])
    st["php"] = stats["hp"]
    st["pmax"] = stats["hp"]
    if st["wave"] >= 3:
        b = st["boss"]
        st["enemy"] = dict(b)
        st["ehp"] = int(b["hp"])
        st["emax"] = int(b["hp"])
        st["log"] = f"BOSS  {b['name'].upper()}"
        return
    spec = st["waves"][st["wave"]]
    e = pick_enemy(spec["tag"], spec["band"], pet.p().get("strength") or 0)
    e["hp"] = int(e["hp"] * (1.15 + st["wave"] * 0.2))
    st["enemy"] = e
    st["ehp"] = int(e["hp"])
    st["emax"] = int(e["hp"])
    st["log"] = f"WAVE {st['wave'] + 1}  {e['name'].upper()}"


def render_raid(pet, st: dict) -> Image.Image:
    im = Image.new("RGBA", (FIELD_W, FIELD_H), (18, 16, 26, 255))
    d = ImageDraw.Draw(im)
    sky = _load("raid_sky.png")
    floor = _load("raid_floor.png")
    if sky.width > 1:
        for y in range(0, 360, sky.height):
            for x in range(0, FIELD_W, sky.width):
                im.paste(sky, (x, y))
    if floor.width > 1:
        for y in range(360, FIELD_H, floor.height):
            for x in range(0, FIELD_W, floor.width):
                im.paste(floor, (x, y))
    d.rectangle((0, 0, FIELD_W, 70), fill=(12, 10, 16))
    d.text((24, 16), "RAID GROUND", font=F_BIG, fill=(232, 188, 72))
    d.text((320, 22), st.get("log", ""), font=F_MID, fill=(236, 228, 210))
    d.rectangle((FIELD_W - 160, 16, FIELD_W - 24, 56), outline=(232, 188, 72), width=2)
    d.text((FIELD_W - 148, 24), "LEAVE", font=F_MID, fill=(236, 228, 210))
    body = _fit(pet.body(160), 180, 180)
    im.paste(body, (160, 340), body)
    d.text((160, 520), pet.save.get("player_name") or "YOU", font=F_MID, fill=(96, 214, 118))
    php, pmax = int(st.get("php") or 1), max(1, int(st.get("pmax") or 1))
    d.rectangle((160, 548, 420, 568), outline=(232, 188, 72))
    d.rectangle((162, 550, 162 + int(256 * php / pmax), 566), fill=(96, 214, 118))
    d.text((160, 572), f"HP {php}/{pmax}  Lv {combat_stats(pet.p(), pet.p()['stage_i'])['level']}", font=F_SM, fill=(236, 228, 210))
    for i, m in enumerate(st.get("members") or []):
        if m.get("pid") == pet.save.get("player_id"):
            continue
        d.text((40, 90 + i * 28), f"ALLY {m.get('name', '?')}  {LINE_NAME.get(m.get('main', ''), '')}", font=F_SM, fill=(180, 220, 255))
    ene = st.get("enemy") or {}
    spr_name = f"boss_{ene.get('id')}.png" if str(ene.get("id") or "").startswith("raid_") else f"enemy_{ene.get('id')}.png"
    es = _fit(_load(spr_name), 220, 220)
    im.paste(es, (FIELD_W - 420, 300), es)
    d.text((FIELD_W - 420, 520), str(ene.get("name", "FOE")), font=F_MID, fill=(214, 72, 64))
    ehp, emax = int(st.get("ehp") or 0), max(1, int(st.get("emax") or 1))
    d.rectangle((FIELD_W - 420, 548, FIELD_W - 160, 568), outline=(232, 188, 72))
    d.rectangle((FIELD_W - 418, 550, FIELD_W - 418 + int(256 * ehp / emax), 566), fill=(214, 72, 64))
    wave_lab = "BOSS" if st.get("wave", 0) >= 3 else f"WAVE {int(st.get('wave') or 0) + 1}/3"
    d.text((FIELD_W - 420, 572), f"{wave_lab}  {ehp}/{emax}", font=F_SM, fill=(236, 228, 210))
    if st.get("over"):
        msg = "RAID CLEAR" if st.get("won") else "RAID WIPE"
        d.rectangle((700, 240, 1220, 400), fill=(12, 10, 16), outline=(232, 188, 72), width=3)
        d.text((740, 280), msg, font=F_BIG, fill=(232, 188, 72))
        d.text((740, 330), st.get("log", ""), font=F_MID, fill=(236, 228, 210))
        return im
    load = [m for m in (pet.p().get("loadout") or []) if m][:4]
    if not load:
        d.rectangle((860, 620, 1060, 680), fill=(52, 46, 58), outline=(232, 188, 72), width=2)
        d.text((900, 636), "STRUGGLE", font=F_MID, fill=(236, 228, 210))
    else:
        for i, mid in enumerate(load):
            mv = move_by_id(pet.save["current"], mid)
            x0 = 40 + i * 280
            d.rectangle((x0, 620, x0 + 260, 680), fill=(52, 46, 58), outline=(232, 188, 72), width=2)
            d.text((x0 + 16, 636), (mv or {}).get("name", mid)[:16], font=F_MID, fill=(236, 228, 210))
    return im
