#!/usr/bin/env python3
from pathlib import Path
import json
from PIL import Image
from cutout import is_key

ROOT = Path(__file__).resolve().parent
SPRITES = ROOT / "sprites"


def main() -> None:
    report = json.loads((ROOT / "cutout_report.json").read_text(encoding="utf-8")) if (ROOT / "cutout_report.json").exists() else {}
    leftover = {}
    for p in sorted(SPRITES.glob("*.png")):
        im = Image.open(p).convert("RGBA")
        n = 0
        for pix in im.getdata():
            r, g, b, a = pix
            if a and is_key(r, g, b):
                n += 1
        leftover[p.name] = {"leftover_magenta": n, "size": im.size, "prepare": report.get(p.name)}
    bad = {k: v for k, v in leftover.items() if v["leftover_magenta"] > 0}
    print(json.dumps({"files": len(leftover), "bad": bad, "ok": len(leftover) - len(bad)}, indent=2))


if __name__ == "__main__":
    main()
