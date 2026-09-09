"""Menu sheet. Full-res text. Everything stays inside the frame."""
from __future__ import annotations

import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from catalog_extra import (
    HATCH_PER_PAGE,
    MOVE_PER_PAGE,
    ROSTER_PER_PAGE,
    SHOP_PER_PAGE,
    STARTER_PER_PAGE,
)
from depth import ATTACHMENTS, ATTACH_BY_ID, GEAR_PER_PAGE, GEAR_SLOTS, combat_stats, gear_of, partner_level, xp_need
from game_data import (
    CLAN_CRESTS,
    EGGS,
    ENEMY_BY_ID,
    EGG_PLAY,
    HATCH,
    ITEM_BY_ID,
    ITEMS,
    LINE_NAME,
    LINES,
    LOADOUT_SLOTS,
    MOVE_MAX,
    START_BLURB,
    START_FORM,
    TYPE_COLOR,
    all_moves_for,
    fmt_price,
    fmt_price_short,
    item_blurb,
    line_price,
    move_by_id,
    move_buy_cost,
    move_up_cost,
    owns_line,
    power_of,
    shop_cost,
)

from paths import asset_root

UI = asset_root() / "ui"
PW, PH = 760, 430
SAFE = 16
RIGHT = PW - 16
BOTTOM = PH - 12

INK = (236, 228, 210)
DIM = (150, 142, 128)
GOLD = (232, 188, 72)
GREEN = (96, 214, 118)
RED = (214, 72, 64)
NAVY = (18, 16, 22)
FACE = (32, 30, 38)
FACE2 = (26, 24, 30)
SLOT = (14, 12, 16)
BTN = (52, 46, 58)
BTN_ON = (78, 92, 42)
EDGE = (12, 10, 14)
GOLD_DK = (120, 84, 28)

TABS = (
    ("together", "TEAM"),
    ("shop", "SHOP"),
    ("hatch", "HATCH"),
    ("moves", "MOVES"),
    ("fight", "FIGHT"),
    ("stats", "STATS"),
)


def _font(size: int, mono: bool = False) -> ImageFont.ImageFont:
    name = r"C:\Windows\Fonts\consola.ttf" if mono else r"C:\Windows\Fonts\segoeui.ttf"
    path = Path(name)
    if path.exists():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


F_TITLE = _font(20)
F_BODY = _font(16)
F_BTN = _font(15)
F_SMALL = _font(14)


def _load(name: str) -> Image.Image:
    p = UI / name
    if p.exists():
        return Image.open(p).convert("RGBA")
    return Image.new("RGBA", (8, 8), (0, 0, 0, 0))


def _rect(d, box, c) -> None:
    d.rectangle(box, fill=c)


def _frame(d, box, fill, hi, sh) -> None:
    x0, y0, x1, y1 = box
    x0, y0 = max(4, x0), max(4, y0)
    x1, y1 = min(PW - 4, x1), min(PH - 4, y1)
    if x1 <= x0 or y1 <= y0:
        return
    d.rectangle((x0, y0, x1, y1), fill=fill, outline=EDGE, width=2)
    d.line([(x0 + 2, y0 + 2), (x1 - 3, y0 + 2)], fill=hi)
    d.line([(x0 + 2, y0 + 2), (x0 + 2, y1 - 3)], fill=hi)
    d.line([(x1 - 3, y0 + 2), (x1 - 3, y1 - 3)], fill=sh)
    d.line([(x0 + 2, y1 - 3), (x1 - 3, y1 - 3)], fill=sh)


def _fit(im: Image.Image, mw: int, mh: int, resample=Image.Resampling.NEAREST) -> Image.Image:
    if im.width <= 0 or im.height <= 0:
        return Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    s = min(mw / im.width, mh / im.height)
    nw = max(8, int(im.width * s))
    nh = max(8, int(im.height * s))
    return im.resize((nw, nh), resample)


def _paste(dst, src, xy, box=None) -> None:
    im = src
    if box:
        im = _fit(im, box[0], box[1])
    x, y = int(xy[0]), int(xy[1])
    if x >= PW or y >= PH:
        return
    if x < 0 or y < 0 or x + im.width > PW or y + im.height > PH:
        crop = im.crop((
            max(0, -x),
            max(0, -y),
            im.width - max(0, x + im.width - PW),
            im.height - max(0, y + im.height - PH),
        ))
        dst.paste(crop, (max(0, x), max(0, y)), crop)
        return
    dst.paste(im, (x, y), im)


def _sprite(pet, form: str) -> Image.Image:
    im = pet.forms.get(form)
    if im is None:
        return Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    return im


def _clip(d, xy, text, font, fill, max_w: int) -> None:
    t = str(text or "")
    if max_w <= 8:
        return
    while t and d.textlength(t, font=font) > max_w:
        t = t[:-1]
    if t != str(text or "") and len(t) > 1:
        t = t[:-1] + ".."
    d.text(xy, t, font=font, fill=fill)


def _wrap(d, xy, text, font, fill, max_w: int, lines: int = 2) -> None:
    words = str(text or "").split()
    rows: list[str] = []
    cur = ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= max_w:
            cur = t
        else:
            if cur:
                rows.append(cur)
            cur = w
            if len(rows) >= lines:
                cur = ""
                break
    if cur and len(rows) < lines:
        rows.append(cur)
    x, y = xy
    for i, row in enumerate(rows):
        _clip(d, (x, y + i * 17), row, font, fill, max_w)


class GameUI:
    def __init__(self) -> None:
        self.mode = "together"
        self.hits: list[tuple[str, tuple[int, int, int, int]]] = []
        self.flash = ""
        self.flash_until = 0.0
        self.pick_line = "agumon"
        self.fight: dict | None = None
        self.pvp: dict | None = None
        self.pending_invite: dict | None = None
        self.pending_chal: dict | None = None
        self.crest_i = 0
        self.typing: dict | None = None
        self.sel_peer: str | None = None
        self.shop_page = 0
        self.line_page = 0
        self.hatch_page = 0
        self.hatch_view = "care"
        self.kick_game = None
        self.move_page = 0
        self.roster_page = 0
        self.shop_view = "bag"
        self.fight_view = "wild"
        self.together_view = "team"
        self.gear_page = 0
        self.floor = None

    def say(self, msg: str) -> None:
        self.flash = msg
        self.flash_until = time.time() + 2.4

    def click(self, pet, x: int, y: int) -> str | None:
        for name, (x0, y0, x1, y1) in self.hits:
            if x0 <= x <= x1 and y0 <= y <= y1:
                return name
        return None

    def render(self, pet) -> Image.Image:
        n = Image.new("RGBA", (PW, PH), (0, 0, 0, 0))
        d = ImageDraw.Draw(n)
        self.hits = [("drag", (0, 0, PW - 48, 34))]
        _rect(d, (0, 0, PW, PH), NAVY)
        d.rectangle((0, 0, PW - 1, PH - 1), outline=GOLD, width=3)
        d.rectangle((3, 3, PW - 4, PH - 4), outline=EDGE, width=2)
        _rect(d, (6, 6, PW - 6, 36), (28, 22, 16))
        title = {
            "starter": "CHOOSE MAIN",
            "together": "TEAM",
            "shop": "SHOP",
            "hatch": "HATCH LAB",
            "moves": "DOJO",
            "fight": "ARENA",
            "stats": "STATS",
        }.get(self.mode, "TEAM")
        if self.typing:
            title = self.typing.get("title", "TYPE")
        d.text((14, 10), title, font=F_TITLE, fill=GOLD)
        coins = f"${int(pet.save.get('coins', 0))}"
        tw = d.textlength(coins, font=F_TITLE)
        d.text((PW - 58 - tw, 10), coins, font=F_TITLE, fill=GREEN)
        if time.time() < self.flash_until and self.flash:
            _clip(d, (200, 12), self.flash, F_BODY, INK, 280)
        _frame(d, (PW - 46, 8, PW - 12, 32), (90, 28, 28), (140, 50, 50), (40, 10, 10))
        d.text((PW - 38, 10), "X", font=F_TITLE, fill=INK)
        self.hits.append(("close", (PW - 46, 8, PW - 12, 32)))

        if self.typing:
            self._type(n, d)
        elif self.mode == "starter" or not pet.save.get("player_name"):
            self.mode = "starter"
            self._starter(n, d, pet)
        else:
            self._tabs(d)
            if self.mode == "shop":
                self._shop(n, d, pet)
            elif self.mode == "hatch":
                self._hatch(n, d, pet)
            elif self.mode == "moves":
                self._moves(n, d, pet)
            elif self.mode == "fight":
                self._fight(n, d, pet)
            elif self.mode == "stats":
                self._stats(n, d, pet)
            else:
                self.mode = "together"
                self._together(n, d, pet)
        return n

    def _tabs(self, d) -> None:
        x = 10
        for key, lab in TABS:
            on = self.mode == key
            w = 76
            _frame(d, (x, 42, x + w, 70), BTN_ON if on else BTN, (90, 86, 70), (20, 16, 18))
            tw = d.textlength(lab, font=F_BTN)
            d.text((x + (w - tw) / 2, 48), lab, font=F_BTN, fill=INK)
            self.hits.append((key, (x, 42, x + w, 70)))
            x += w + 6

    def _btn(self, d, box, label, key, on=False) -> None:
        x0, y0, x1, y1 = box
        x0, y0 = max(SAFE - 4, x0), max(36, y0)
        x1, y1 = min(RIGHT + 4, x1), min(BOTTOM, y1)
        if x1 - x0 < 20 or y1 - y0 < 16:
            return
        _frame(d, (x0, y0, x1, y1), BTN_ON if on else BTN, (96, 90, 80), (20, 16, 18))
        _clip(d, (x0 + 4, y0 + (y1 - y0 - 16) / 2), label, F_BTN, INK, x1 - x0 - 8)
        self.hits.append((key, (x0, y0, x1, y1)))

    def _type(self, n, d) -> None:
        t = self.typing or {}
        _clip(d, (16, 48), t.get("prompt", ""), F_BODY, DIM, 720)
        _frame(d, (16, 74, 744, 110), SLOT, GOLD_DK, EDGE)
        lim = 40 if t.get("field") == "chat" else 16
        _clip(d, (24, 82), (t.get("buf") or "_")[:lim], F_TITLE, GREEN, 700)
        keys = "ABCDEFGHIJKLMNOPQRSTUVWXYZ23456789"
        for i, ch in enumerate(keys):
            col, row = i % 11, i // 11
            x0 = 16 + col * 66
            y0 = 118 + row * 50
            self._btn(d, (x0, y0, x0 + 60, y0 + 42), ch, f"key:{ch}")
        self._btn(d, (16, 378, 140, 416), "DEL", "key:del")
        self._btn(d, (152, 378, 300, 416), "SPACE", "key:sp")
        self._btn(d, (312, 378, 500, 416), "OK", "key:ok")
        self._btn(d, (516, 378, 744, 416), "CANCEL", "key:cancel")

    def _starter(self, n, d, pet) -> None:
        name = pet.save.get("player_name") or "???"
        _clip(d, (16, 48), f"Trainer  {name}", F_BODY, INK, 360)
        self._btn(d, (400, 44, 520, 72), "NAME", "name")
        page = int(getattr(self, "line_page", 0) or 0)
        chunk = LINES[page * STARTER_PER_PAGE : page * STARTER_PER_PAGE + STARTER_PER_PAGE]
        _clip(d, (530, 48), f"Pick ONE. The rest cost {fmt_price(line_price(''))}.", F_SMALL, GOLD, 210)
        for i, ln in enumerate(chunk):
            col, row = i % 4, i // 4
            x0 = 16 + col * 184
            y0 = 80 + row * 148
            on = ln["id"] == self.pick_line
            _frame(d, (x0, y0, x0 + 176, y0 + 140), (40, 48, 28) if on else FACE2, GOLD if on else (60, 54, 48), EDGE)
            spr = _fit(_sprite(pet, START_FORM[ln["id"]]), 70, 58)
            _paste(n, spr, (x0 + (176 - spr.width) // 2, y0 + 6))
            _clip(d, (x0 + 8, y0 + 66), LINE_NAME[ln["id"]], F_BODY, GOLD if on else INK, 160)
            _clip(d, (x0 + 8, y0 + 86), ln["tag"], F_SMALL, DIM, 160)
            _wrap(d, (x0 + 8, y0 + 104), START_BLURB.get(ln["id"], ""), F_SMALL, DIM, 160, 2)
            self.hits.append((f"main:{ln['id']}", (x0, y0, x0 + 176, y0 + 140)))
        pages = max(1, (len(LINES) + STARTER_PER_PAGE - 1) // STARTER_PER_PAGE)
        self._btn(d, (16, 380, 200, 416), f"MORE {page + 1}/{pages}", "line_next")
        self._btn(d, (280, 380, 500, 416), "BEGIN", "begin")

    def _together(self, n, d, pet) -> None:
        clan = pet.save.get("clan")
        cur = pet.save.get("current") or pet.save.get("main")
        me = pet.save.get("player_name") or "???"
        p = pet.save["partners"].get(cur) or pet.p()
        pwr = power_of(p, cur)

        _frame(d, (16, 78, 744, 156), FACE, GOLD_DK, EDGE)
        spr = _fit(_sprite(pet, pet.form()), 64, 64)
        _paste(n, spr, (24, 86))
        _clip(d, (100, 84), me, F_TITLE, GOLD, 220)
        _clip(d, (100, 108), f"{LINE_NAME.get(cur, cur)}  {pet.form_label()}", F_BODY, INK, 300)
        _clip(d, (100, 130), f"Lv {partner_level(p)}  Pwr {pwr}  Fd {int(p.get('hunger', 0))}  Md {int(p.get('mood', 0))}  Hy {int(p.get('hygiene', 0))}", F_SMALL, GREEN, 400)
        self._btn(d, (520, 86, 620, 120), "PLAY", "play")
        self._btn(d, (628, 86, 736, 120), "MAIL", "mail_view", on=getattr(self, "together_view", "team") == "mail")
        team = getattr(self, "together_view", "team") != "mail"
        if not team:
            self._mail(n, d, pet)
            return
        if clan:
            _clip(d, (520, 128), f"{clan.get('name', '')}  {clan.get('code', '')}", F_SMALL, INK, 210)
        else:
            _clip(d, (520, 128), "No clan yet", F_SMALL, DIM, 210)

        page = int(getattr(self, "roster_page", 0) or 0)
        chunk = LINES[page * ROSTER_PER_PAGE : page * ROSTER_PER_PAGE + ROSTER_PER_PAGE]
        pages = max(1, (len(LINES) + ROSTER_PER_PAGE - 1) // ROSTER_PER_PAGE)
        _clip(d, (16, 164), f"Owned walk free. Everyone else is {fmt_price(line_price(''))}.", F_BODY, GOLD, 400)
        self._btn(d, (620, 162, 744, 192), f"{page + 1}/{pages}", "roster_next")
        for i, ln in enumerate(chunk):
            col, row = i % 3, i // 3
            x0 = 16 + col * 244
            y0 = 198 + row * 64
            pid = ln["id"]
            pp = pet.save["partners"].get(pid) or {}
            on = pid == cur
            have = owns_line(pet.save, pid)
            _frame(d, (x0, y0, x0 + 236, y0 + 58), (40, 48, 28) if on else FACE2, GOLD if on else GOLD_DK, EDGE)
            form = ln["stages"][max(0, min(int(pp.get("stage_i") or 0), len(ln["stages"]) - 1))]
            spr = _fit(_sprite(pet, form), 46, 46)
            _paste(n, spr, (x0 + 8, y0 + 6))
            _clip(d, (x0 + 62, y0 + 6), LINE_NAME[pid], F_BODY, GOLD if on else INK, 164)
            if have:
                _clip(d, (x0 + 62, y0 + 30), f"{ln['tag']}  st {int(pp.get('stage_i') or 0)}", F_SMALL, DIM, 164)
            else:
                _clip(d, (x0 + 62, y0 + 30), f"BUY {fmt_price(line_price(pid))}", F_SMALL, GOLD, 164)
            self.hits.append((f"swap:{pid}", (x0, y0, x0 + 236, y0 + 58)))

        if not clan:
            self._btn(d, (16, 334, 130, 372), "MAKE", "clan_create")
            self._btn(d, (140, 334, 254, 372), "JOIN", "clan_join")
            crest = CLAN_CRESTS[self.crest_i % len(CLAN_CRESTS)]
            self._btn(d, (264, 334, 380, 372), crest.upper(), "crest")
        else:
            _clip(d, (16, 340), f"{clan.get('name')}  {clan.get('wins', 0)}-{clan.get('losses', 0)}", F_BODY, INK, 300)
            self._btn(d, (320, 334, 420, 372), "LEAVE", "clan_leave")

        peers = pet.net.nearby() if pet.net else []
        if self.sel_peer and not any(p.get("pid") == self.sel_peer for p in peers):
            self.sel_peer = peers[0]["pid"] if peers else None
        if not self.sel_peer and peers:
            self.sel_peer = peers[0]["pid"]
        if not peers:
            _clip(d, (16, 386), "Nobody on the LAN. Same Wi-Fi, same pet.", F_SMALL, DIM, 720)
        else:
            peer = next((x for x in peers if x.get("pid") == self.sel_peer), peers[0])
            _clip(d, (16, 384), f"{peer.get('name', '?')}  {LINE_NAME.get(peer.get('main', ''), '')}", F_SMALL, INK, 360)
            self._btn(d, (400, 378, 520, 414), "FIGHT", f"chal:{peer.get('pid')}")
            if clan:
                self._btn(d, (528, 378, 640, 414), "INVITE", f"inv:{peer.get('pid')}")
                if peer.get("clan_id") and peer.get("clan_id") != clan.get("id"):
                    self._btn(d, (648, 378, 744, 414), "WAR", f"war:{peer.get('pid')}")

    def _mail(self, n, d, pet) -> None:
        inbox = list(pet.save.get("inbox") or [])[-8:]
        _clip(d, (16, 164), "LAN mail. Same Wi-Fi, same pet.", F_BODY, GOLD, 400)
        self._btn(d, (520, 162, 640, 192), "WRITE", "mail_write")
        self._btn(d, (648, 162, 744, 192), "TEAM", "mail_team")
        if not inbox:
            _clip(d, (24, 220), "No messages yet. WRITE sends to everyone nearby.", F_SMALL, DIM, 700)
        else:
            for i, m in enumerate(inbox):
                y = 200 + i * 24
                who = str(m.get("from", "?"))[:12]
                txt = str(m.get("text", ""))[:42]
                _clip(d, (24, y), f"{who}:  {txt}", F_SMALL, INK, 720)
        peers = pet.net.nearby() if pet.net else []
        _clip(d, (16, 396), f"{len(peers)} nearby", F_SMALL, DIM, 300)

    def _shop(self, n, d, pet) -> None:
        gear = getattr(self, "shop_view", "bag") == "gear"
        self._btn(d, (16, 74, 110, 102), "BAG", "shop_bag", on=not gear)
        self._btn(d, (118, 74, 230, 102), "GEAR", "shop_gear", on=gear)
        if gear:
            self._shop_gear(n, d, pet)
            return
        page = int(getattr(self, "shop_page", 0) or 0)
        chunk = ITEMS[page * SHOP_PER_PAGE : page * SHOP_PER_PAGE + SHOP_PER_PAGE]
        pages = max(1, (len(ITEMS) + SHOP_PER_PAGE - 1) // SHOP_PER_PAGE)
        _clip(d, (244, 78), "Bag items. Gear is the other tab.", F_SMALL, DIM, 340)
        self._btn(d, (600, 74, 744, 102), f"{page + 1}/{pages}", "shop_next")
        for i, it in enumerate(chunk):
            x0 = 12 + i * 186
            y0 = 108
            _frame(d, (x0, y0, x0 + 178, y0 + 268), FACE2, GOLD_DK, EDGE)
            icon = _fit(_load(f"item_{it['id']}.png"), 160, 160, Image.Resampling.LANCZOS)
            _paste(n, icon, (x0 + (178 - icon.width) // 2, y0 + 8))
            _clip(d, (x0 + 8, y0 + 172), it["name"], F_BODY, GOLD, 162)
            _clip(d, (x0 + 8, y0 + 194), f"{fmt_price_short(shop_cost(it['cost']))}  {item_blurb(it)}", F_SMALL, INK, 162)
            have = int((pet.save.get("bag") or {}).get(it["id"]) or 0)
            if have:
                _clip(d, (x0 + 8, y0 + 214), f"owned x{have}", F_SMALL, GREEN, 162)
            self._btn(d, (x0 + 8, y0 + 234, x0 + 86, y0 + 260), "BUY", f"buyitem:{it['id']}")
            if have:
                self._btn(d, (x0 + 92, y0 + 234, x0 + 170, y0 + 260), "USE", f"useitem:{it['id']}")
        bag = pet.save.get("bag") or {}
        held = [f"{ITEM_BY_ID.get(k, {}).get('name', k)} x{v}" for k, v in bag.items() if int(v) > 0]
        _clip(d, (16, 384), ("Bag: " + ", ".join(held)) if held else "Bag empty — buy, GO, or win a fight.", F_SMALL, INK, 728)

    def _shop_gear(self, n, d, pet) -> None:
        page = int(getattr(self, "gear_page", 0) or 0)
        pages = max(1, (len(ATTACHMENTS) + GEAR_PER_PAGE - 1) // GEAR_PER_PAGE)
        chunk = ATTACHMENTS[page * GEAR_PER_PAGE : page * GEAR_PER_PAGE + GEAR_PER_PAGE]
        worn = gear_of(pet.p())
        bag = pet.save.get("gear_bag") or {}
        self._btn(d, (600, 74, 744, 102), f"{page + 1}/{pages}", "gear_next")
        _clip(d, (244, 78), "Fits every partner. Equip a slot.", F_SMALL, DIM, 340)
        for i, a in enumerate(chunk):
            x0 = 12 + i * 186
            y0 = 108
            on = worn.get(a["slot"]) == a["id"]
            _frame(d, (x0, y0, x0 + 178, y0 + 268), (40, 48, 28) if on else FACE2, GOLD if on else GOLD_DK, EDGE)
            icon = _fit(_load(f"gear_{a['id']}.png"), 160, 160, Image.Resampling.LANCZOS)
            _paste(n, icon, (x0 + (178 - icon.width) // 2, y0 + 8))
            _clip(d, (x0 + 8, y0 + 172), a["name"], F_BODY, GOLD, 162)
            _clip(d, (x0 + 8, y0 + 194), f"{fmt_price_short(shop_cost(a['cost']))}  {a['slot']}  {a['blurb']}", F_SMALL, INK, 162)
            have = int(bag.get(a["id"]) or 0)
            if have:
                _clip(d, (x0 + 8, y0 + 214), f"owned x{have}", F_SMALL, GREEN, 162)
            self._btn(d, (x0 + 8, y0 + 234, x0 + 86, y0 + 260), "BUY", f"buygear:{a['id']}")
            if have or on:
                self._btn(d, (x0 + 92, y0 + 234, x0 + 170, y0 + 260), "WEAR" if not on else "OFF", f"wear:{a['id']}")
        eq = "  ".join(f"{s}:{ATTACH_BY_ID.get(v, {}).get('name', '—') if v else '—'}" for s, v in worn.items())
        _clip(d, (16, 388), eq[:90], F_SMALL, GREEN, 728)

    def _hatch(self, n, d, pet) -> None:
        p = pet.p()
        ready, txt = pet.evo_status()
        i = p["stage_i"]
        wait = pet._wait_sec(i)
        left = max(0, wait - (time.time() - p["stage_started"]))
        done = 1.0 if wait <= 0 else min(1.0, max(0.0, 1.0 - left / wait))
        _clip(d, (16, 78), f"{pet.form_label()}   {txt}", F_BODY, GREEN if ready else INK, 360)
        _frame(d, (16, 104, 744, 124), SLOT, GOLD_DK, EDGE)
        fill = int(724 * done)
        if fill:
            _rect(d, (18, 106, 18 + fill, 122), (200, 120, 40))
        care = getattr(self, "hatch_view", "care")
        self._btn(d, (390, 74, 488, 102), "CARE", "hatch_care", on=care == "care")
        self._btn(d, (496, 74, 594, 102), "TOOLS", "hatch_tools", on=care == "tools")
        self._btn(d, (602, 74, 700, 102), "RUN", "hatch_run", on=care == "run")
        if care == "run":
            self._hatch_run(n, d, pet, p)
        elif care == "care":
            self._hatch_care(n, d, pet, p)
        else:
            self._hatch_tools(n, d, pet, p)

    def _hatch_care(self, n, d, pet, p) -> None:
        g = getattr(self, "kick_game", None)
        if g and time.time() >= float(g.get("end") or 0):
            self.kick_game = None
            g = None
        _frame(d, (16, 132, 220, 300), FACE, GOLD_DK, EDGE)
        spr = _fit(_sprite(pet, pet.form()), 170, 140)
        _paste(n, spr, (16 + (204 - spr.width) // 2, 148))
        _clip(d, (24, 274), "TAP THE SHELL", F_SMALL, GOLD, 188)
        self.hits.append(("hatch:tap", (16, 132, 220, 300)))

        _frame(d, (16, 308, 220, 336), SLOT, GOLD_DK, EDGE)
        if g:
            span = max(0.2, float(g["end"]) - float(g["start"]))
            t = min(1.0, max(0.0, (time.time() - float(g["start"])) / span))
            lo, hi = float(g["lo"]), float(g["hi"])
            _rect(d, (18 + int(200 * lo), 310, 18 + int(200 * hi), 334), (70, 140, 60))
            mx = 18 + int(200 * t)
            _rect(d, (mx, 310, min(218, mx + 4), 334), GOLD)
        else:
            _clip(d, (24, 312), "Catch the kick", F_SMALL, DIM, 180)
        self._btn(d, (16, 344, 220, 380), "CATCH", "hatch:catch")

        warmth = int(p.get("egg_warmth") or 40)
        kicks = int(p.get("egg_kicks") or 0)
        _clip(d, (16, 388), f"Warm {warmth}   Kicks {kicks}   Taps {int(p.get('egg_taps') or 0)}", F_SMALL, GREEN, 720)

        for i, act in enumerate(EGG_PLAY):
            col, row = i % 5, i // 5
            x0 = 236 + col * 102
            y0 = 132 + row * 126
            cd = float((p.get("cd_egg") or {}).get(act["id"], 0)) - time.time()
            _frame(d, (x0, y0, x0 + 98, y0 + 118), FACE2, GOLD_DK, EDGE)
            _clip(d, (x0 + 6, y0 + 6), act["name"], F_BODY, GOLD, 86)
            _wrap(d, (x0 + 6, y0 + 30), act["desc"], F_SMALL, DIM, 86, 2)
            if cd > 0:
                _clip(d, (x0 + 6, y0 + 82), f"{int(cd)}s", F_SMALL, RED, 86)
            else:
                self._btn(d, (x0 + 6, y0 + 82, x0 + 92, y0 + 110), "DO", f"egg:{act['id']}")

    def _hatch_run(self, n, d, pet, p) -> None:
        _frame(d, (16, 132, 744, 370), FACE2, GOLD_DK, EDGE)
        spr = _fit(_sprite(pet, pet.form()), 140, 140)
        _paste(n, spr, (36, 150))
        _clip(d, (200, 148), "Desktop run", F_TITLE, GOLD, 500)
        _wrap(d, (200, 186), "Rocks and birds slide across monitor 2 on the same floor your egg walks. Click the egg or press Space to jump. Three hits crack the shell. Distance still cuts hatch time.", F_BODY, INK, 520, 4)
        _clip(d, (200, 290), "Space or click the egg. FIGHT on the pad leaves and cashes in.", F_SMALL, DIM, 500)
        self._btn(d, (200, 320, 430, 358), "START RUN", "run_start")
        _clip(d, (16, 388), "Egg only. Hatched partners use RAID on FIGHT.", F_SMALL, GREEN, 720)

    def _hatch_tools(self, n, d, pet, p) -> None:
        page = int(getattr(self, "hatch_page", 0) or 0)
        chunk = HATCH[page * HATCH_PER_PAGE : page * HATCH_PER_PAGE + HATCH_PER_PAGE]
        pages = max(1, (len(HATCH) + HATCH_PER_PAGE - 1) // HATCH_PER_PAGE)
        self._btn(d, (16, 388, 140, 414), f"{page + 1}/{pages}", "hatch_next")
        spr = _fit(_sprite(pet, pet.form()), 88, 88)
        _paste(n, spr, (16, 140))
        _wrap(d, (16, 236), "Warm eggs make tools cut more.", F_SMALL, DIM, 100, 3)
        for ni, h in enumerate(chunk):
            x0 = 126 + ni * 156
            y0 = 132
            _frame(d, (x0, y0, x0 + 148, y0 + 246), FACE2, GOLD_DK, EDGE)
            icon = _fit(_load(f"hatch_{h['id']}.png"), 120, 120, Image.Resampling.LANCZOS)
            _paste(n, icon, (x0 + (148 - icon.width) // 2, y0 + 6))
            _clip(d, (x0 + 8, y0 + 128), h["name"], F_BODY, GOLD, 132)
            _clip(d, (x0 + 8, y0 + 148), f"{fmt_price_short(shop_cost(h['cost']))}  -{h['shave'] // 60} min", F_SMALL, INK, 132)
            _wrap(d, (x0 + 8, y0 + 168), h.get("desc", ""), F_SMALL, DIM, 132, 2)
            cd = float((p.get("cd_hatch") or {}).get(h["id"], 0)) - time.time()
            if cd > 0:
                _clip(d, (x0 + 8, y0 + 200), f"wait {int(cd)}s", F_SMALL, RED, 132)
            self._btn(d, (x0 + 8, y0 + 216, x0 + 140, y0 + 242), "USE", f"hatch:{h['id']}")

    def _moves(self, n, d, pet) -> None:
        p = pet.p()
        owned = p.get("moves") or {}
        load = list(p.get("loadout") or [])
        moves = list(all_moves_for(pet.save["current"]))
        page = int(getattr(self, "move_page", 0) or 0)
        pages = max(1, (len(moves) + MOVE_PER_PAGE - 1) // MOVE_PER_PAGE)
        chunk = moves[page * MOVE_PER_PAGE : page * MOVE_PER_PAGE + MOVE_PER_PAGE]
        _clip(d, (16, 78), "Equip 4. Arena uses these.", F_SMALL, DIM, 400)
        self._btn(d, (600, 74, 744, 104), f"{page + 1}/{pages}", "move_next")
        gap, slot_w = 8, 176
        for i in range(LOADOUT_SLOTS):
            mid = load[i] if i < len(load) else ""
            lab = (move_by_id(pet.save["current"], mid) or {}).get("name", "empty")
            x0 = 16 + i * (slot_w + gap)
            self._btn(d, (x0, 110, x0 + slot_w, 142), lab, f"unequip:{i}", on=bool(mid))
        for ni, m in enumerate(chunk):
            lv = int(owned.get(m["id"], 0))
            col, row = ni % 2, ni // 2
            x0 = 16 + col * 364
            y0 = 152 + row * 118
            _frame(d, (x0, y0, x0 + 356, y0 + 110), FACE2, GOLD_DK, EDGE)
            _paste(n, _fit(_load(f"move_{m['id']}.png"), 80, 80, Image.Resampling.LANCZOS), (x0 + 10, y0 + 14))
            tcol = TYPE_COLOR.get(m["typ"], INK)
            powr = m["pow"] + max(0, lv - 1) * m["grow"]
            _clip(d, (x0 + 100, y0 + 10), m["name"], F_BODY, GOLD, 148)
            _clip(d, (x0 + 100, y0 + 38), f"{m['typ']}  Lv {lv}/{MOVE_MAX}  pow {powr}", F_SMALL, tcol, 168)
            if lv <= 0:
                self._btn(d, (x0 + 230, y0 + 64, x0 + 344, y0 + 100), f"BUY {fmt_price_short(move_buy_cost(m))}", f"buy:{m['id']}")
            elif lv < MOVE_MAX:
                self._btn(d, (x0 + 200, y0 + 64, x0 + 286, y0 + 100), f"UP {fmt_price_short(move_up_cost(m, lv))}", f"up:{m['id']}")
                self._btn(d, (x0 + 294, y0 + 64, x0 + 344, y0 + 100), "EQ", f"eq:{m['id']}")
            else:
                self._btn(d, (x0 + 250, y0 + 64, x0 + 344, y0 + 100), "EQ", f"eq:{m['id']}")

    def _fight(self, n, d, pet) -> None:
        view = getattr(self, "fight_view", "wild")
        if not self.fight and not self.pvp:
            self._btn(d, (16, 74, 130, 102), "WILD", "fight_wild", on=view == "wild")
            self._btn(d, (138, 74, 270, 102), "DUNGEON", "fight_floor", on=view == "floor")
            self._btn(d, (278, 74, 400, 102), "RAID", "fight_raid", on=view == "raid")
        if self.pvp:
            self._pvp(n, d, pet, self.pvp)
            return
        if pet.form() in EGGS:
            _clip(d, (32, 180), "Too small. Hatch first, then fight. Eggs can RUN.", F_TITLE, RED, 680)
            return
        if view == "raid":
            self._raid_lobby(n, d, pet)
            return
        if view == "floor":
            self._floor(n, d, pet)
            return
        if self.fight is None:
            _clip(d, (32, 120), "Wild scrap on monitor 2. The foe walks in on the desktop.", F_BODY, INK, 680)
            _clip(d, (32, 152), "Moves are on the pad. Equip four in DOJO. No battle screen.", F_SMALL, DIM, 680)
            st = combat_stats(pet.p(), pet.p()["stage_i"])
            _clip(d, (32, 184), f"Lv {st['level']}  HP {st['hp']}  ATK {int(st['atk'])}  DEF {int(st['defe'])}  CRIT {int(st['crit']*100)}%", F_BODY, GREEN, 680)
            self._btn(d, (250, 230, 510, 290), "WILD FIGHT", "fight_start")
            return
        f = self.fight
        ene = ENEMY_BY_ID.get(f["eid"], {})
        _frame(d, (24, 80, 250, 220), FACE2, GOLD_DK, EDGE)
        _frame(d, (510, 80, 736, 220), FACE2, GOLD_DK, EDGE)
        spr = _fit(_sprite(pet, pet.form()), 200, 120)
        _paste(n, spr, (24 + (226 - spr.width) // 2, 88))
        es = _fit(_load(f"enemy_{f['eid']}.png"), 200, 120)
        _paste(n, es, (510 + (226 - es.width) // 2, 88))
        _clip(d, (32, 226), pet.form_label(), F_BODY, INK, 210)
        _clip(d, (518, 226), str(ene.get("name", "?")), F_BODY, GOLD, 210)
        self._hp(d, 32, 252, 218, f["php"], f["pmax"], GREEN)
        self._hp(d, 518, 252, 218, f["ehp"], f["emax"], RED)
        _clip(d, (32, 278), f.get("log", ""), F_BODY, INK, 696)
        if f.get("over"):
            self._btn(d, (270, 330, 490, 380), "AGAIN", "fight_start")
            return
        load = [m for m in (pet.p().get("loadout") or []) if m]
        if not load:
            self._btn(d, (250, 330, 510, 384), "STRUGGLE", "use:struggle")
        else:
            for i, mid in enumerate(load[:4]):
                mv = move_by_id(pet.save["current"], mid)
                x0 = 16 + i * 184
                self._btn(d, (x0, 330, x0 + 176, 384), (mv or {}).get("name", mid), f"use:{mid}")

    def _raid_lobby(self, n, d, pet) -> None:
        q = bool(getattr(pet, "raid_queued", False))
        field = getattr(pet, "field_mode", None)
        _clip(d, (32, 120), "Queue on the LAN. The boss walks onto monitor 2 like your pet.", F_BODY, INK, 700)
        _clip(d, (32, 152), "Waves, then a boss. Allies auto-hit. Moves stay on the pad.", F_SMALL, DIM, 700)
        queued = []
        if pet.net:
            queued = [p for p in pet.net.nearby() if p.get("raid")]
        if q:
            queued = [{"name": pet.save.get("player_name") or "YOU"}] + queued
        _clip(d, (32, 188), f"Queued {len(queued)}  " + ", ".join(str(p.get("name", "?"))[:10] for p in queued[:6]), F_BODY, GREEN, 700)
        self._btn(d, (32, 240, 240, 290), "LEAVE Q" if q else "QUEUE", "raid_toggle", on=q)
        self._btn(d, (256, 240, 500, 290), "START RAID", "raid_start")
        if field == "raid":
            _clip(d, (32, 320), "Raid is live on monitor 2.", F_TITLE, GOLD, 680)

    def _floor(self, n, d, pet) -> None:
        fl = getattr(self, "floor", None)
        _clip(d, (32, 120), "Five floors on the desktop. Each foe walks in. HP carries.", F_BODY, INK, 700)
        if not fl:
            self._btn(d, (250, 200, 510, 260), "ENTER DUNGEON", "floor_start")
            return
        _clip(d, (32, 156), f"Floor {int(fl.get('n') or 1)}/5   {fl.get('log', '')}", F_BODY, GOLD, 700)
        self._hp(d, 32, 190, 320, int(fl.get("php") or 0), max(1, int(fl.get("pmax") or 1)), GREEN)
        self._hp(d, 400, 190, 320, int(fl.get("ehp") or 0), max(1, int(fl.get("emax") or 1)), RED)
        _clip(d, (32, 220), f"You  {int(fl.get('php') or 0)}     Foe  {fl.get('ename', '')} {int(fl.get('ehp') or 0)}", F_SMALL, INK, 700)
        if fl.get("over"):
            self._btn(d, (250, 300, 510, 360), "AGAIN", "floor_start")
            return
        if fl.get("clear"):
            self._btn(d, (250, 280, 510, 340), "NEXT FLOOR", "floor_next")
            return
        load = [m for m in (pet.p().get("loadout") or []) if m]
        if not load:
            self._btn(d, (250, 330, 510, 384), "STRUGGLE", "floor:struggle")
        else:
            for i, mid in enumerate(load[:4]):
                mv = move_by_id(pet.save["current"], mid)
                x0 = 16 + i * 184
                self._btn(d, (x0, 330, x0 + 176, 384), (mv or {}).get("name", mid), f"floor:{mid}")

    def _pvp(self, n, d, pet, f: dict) -> None:
        their = f.get("their_main") or "agumon"
        _frame(d, (24, 80, 250, 220), FACE2, GOLD_DK, EDGE)
        _frame(d, (510, 80, 736, 220), FACE2, GOLD_DK, EDGE)
        spr = _fit(_sprite(pet, pet.form()), 200, 120)
        _paste(n, spr, (24 + (226 - spr.width) // 2, 88))
        ts = _fit(_sprite(pet, START_FORM.get(their, their)), 200, 120)
        _paste(n, ts, (510 + (226 - ts.width) // 2, 88))
        _clip(d, (32, 226), (pet.save.get("player_name") or "YOU"), F_BODY, INK, 210)
        _clip(d, (518, 226), str(f.get("their_name", "THEM")), F_BODY, GOLD, 210)
        self._hp(d, 32, 252, 218, f["php"], f["pmax"], GREEN)
        self._hp(d, 518, 252, 218, f["ehp"], f["emax"], RED)
        _clip(d, (32, 278), f.get("log", ""), F_BODY, INK, 696)
        if f.get("over"):
            self._btn(d, (270, 330, 490, 380), "BACK", "pvp_end")
            return
        if f.get("wait"):
            _clip(d, (220, 340), "Waiting on them...", F_TITLE, GOLD, 320)
            return
        load = [m for m in (pet.p().get("loadout") or []) if m]
        if not load:
            self._btn(d, (250, 330, 510, 384), "STRUGGLE", "pvp:struggle")
        else:
            for i, mid in enumerate(load[:4]):
                mv = move_by_id(pet.save["current"], mid)
                x0 = 16 + i * 184
                self._btn(d, (x0, 330, x0 + 176, 384), (mv or {}).get("name", mid), f"pvp:{mid}")

    def _hp(self, d, x, y, w, cur, mx, col) -> None:
        _frame(d, (x, y, x + w, y + 18), SLOT, GOLD_DK, EDGE)
        if mx:
            fw = max(1, int((w - 4) * max(0, cur) / mx))
            _rect(d, (x + 2, y + 2, min(x + w - 2, x + 2 + fw), y + 16), col)

    def _stats(self, n, d, pet) -> None:
        st = pet.save.get("stats") or {}
        cur = pet.save.get("current") or pet.save.get("main")
        p = pet.save["partners"].get(cur) or pet.p()
        rows = (
            ("Name", pet.save.get("player_name") or "—"),
            ("Out now", LINE_NAME.get(cur, cur)),
            ("Level", f"{partner_level(p)}  xp {int(p.get('xp') or 0)}/{xp_need(partner_level(p))}"),
            ("Power", str(power_of(p, cur))),
            ("Fights", f"{st.get('wins', 0)}-{st.get('losses', 0)}"),
            ("Wars", f"{st.get('wars_won', 0)}-{st.get('wars_lost', 0)}"),
            ("Raids", f"{st.get('raids', 0)}"),
            ("Hatches", str(st.get("hatches", 0))),
            ("Coins earned", f"${st.get('coins_earned', 0)}"),
            ("Streak", str(pet.save.get("streak", 0))),
        )
        for i, (k, v) in enumerate(rows):
            y = 78 + i * 28
            _clip(d, (24, y), k, F_BODY, DIM, 180)
            _clip(d, (210, y), str(v), F_TITLE, INK, 240)
        _frame(d, (480, 84, 736, 340), FACE2, GOLD_DK, EDGE)
        spr = _fit(_sprite(pet, pet.form()), 230, 230)
        _paste(n, spr, (480 + (256 - spr.width) // 2, 100))
        self._btn(d, (24, 376, 170, 414), "NAME", "name")
        self._btn(d, (186, 376, 330, 414), "PLAY", "play")
