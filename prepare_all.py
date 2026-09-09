#!/usr/bin/env python3
from pathlib import Path
import json
from cutout import cutout, is_key

SRC = Path(r"C:\Users\bando\.cursor\projects\c-Users-bando-AppData-Local-Temp-trading-ca\assets")
DEST = Path(__file__).resolve().parent / "sprites"
NEED = [
    "egg_idle_01.png", "egg_idle_02.png", "egg_idle_03.png", "egg_hatch_01.png", "egg_hatch_02.png",
    "botamon_idle_01.png", "botamon_idle_02.png", "botamon_walk_01.png", "botamon_walk_02.png",
    "botamon_eat.png", "botamon_sleep.png",
    "koromon_idle_01.png", "koromon_idle_02.png", "koromon_walk_01.png", "koromon_walk_02.png",
    "koromon_eat.png", "koromon_sleep.png", "koromon_happy.png",
    "agumon_idle_01.png", "agumon_idle_02.png", "agumon_walk_01.png", "agumon_walk_02.png",
    "agumon_walk_03.png", "agumon_walk_04.png", "agumon_eat_01.png", "agumon_eat_02.png",
    "agumon_sleep.png", "agumon_happy.png", "agumon_hungry.png",
]


def leftover(im) -> int:
    n = 0
    for r, g, b, a in im.get_flattened_data() if False else im.getdata():
        if a and is_key(r, g, b):
            n += 1
    return n


def main() -> None:
    DEST.mkdir(exist_ok=True)
    out = {}
    for name in NEED:
        src = SRC / name
        if not src.exists():
            out[name] = "missing"
            continue
        im = cutout(src)
        n = leftover(im)
        if n:
            px = im.load()
            w, h = im.size
            for y in range(h):
                for x in range(w):
                    r, g, b, a = px[x, y]
                    if a and is_key(r, g, b):
                        px[x, y] = (0, 0, 0, 0)
            n = leftover(im)
        im.save(DEST / name)
        out[name] = {"magenta_left": n, "size": list(im.size)}
    (Path(__file__).resolve().parent / "cutout_report.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    bad = {k: v for k, v in out.items() if isinstance(v, dict) and v["magenta_left"]}
    print(json.dumps({"n": len(out), "bad": bad}, indent=2))


if __name__ == "__main__":
    main()
