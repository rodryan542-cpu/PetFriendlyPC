"""Panel actions: hatch, moves, fights, clans. Called from the pet."""
from __future__ import annotations

import random
import time

from catalog_extra import (
    HATCH_PER_PAGE,
    MOVE_PER_PAGE,
    PICK_PER_PAGE,
    ROSTER_PER_PAGE,
    SHOP_PER_PAGE,
    STARTER_PER_PAGE,
)
from depth import (
    ATTACH_BY_ID,
    ATTACHMENTS,
    GEAR_PER_PAGE,
    GEAR_SLOTS,
    INBOX_MAX,
    combat_stats,
    floor_band,
    grant_xp,
    hatch_mult,
    pick_raid_boss,
    roll_hit,
    enemy_hit,
    gear_bonus,
)
from game_data import (
    CLAN_CRESTS,
    EGGS,
    EGG_PLAY_BY_ID,
    ENEMY_BY_ID,
    FOODS,
    HATCH,
    ITEM_BY_ID,
    ITEMS,
    LINE_BY_ID,
    LINES,
    LOADOUT_SLOTS,
    MOVE_MAX,
    owns_line,
    TALK_LINES,
    all_moves_for,
    move_by_id,
    move_buy_cost,
    move_damage,
    move_up_cost,
    new_clan,
    pick_enemy,
    player_hp,
    power_of,
    shop_cost,
)


def handle(pet, action: str) -> None:
    if action in (None, "drag"):
        return
    if action == "close":
        pet.panel_open = False
        return
    if action == "hub":
        pet.ui.mode = "hub"
        pet.ui.fight = None
        return
    if action in ("hatch", "moves", "fight", "together", "stats", "clan", "shop"):
        pet.ui.mode = "together" if action == "clan" else action
        return
    if action == "shop_next":
        n = max(1, (len(ITEMS) + SHOP_PER_PAGE - 1) // SHOP_PER_PAGE)
        pet.ui.shop_page = (int(getattr(pet.ui, "shop_page", 0) or 0) + 1) % n
        return
    if action == "line_next":
        n = max(1, (len(LINES) + STARTER_PER_PAGE - 1) // STARTER_PER_PAGE)
        pet.ui.line_page = (int(getattr(pet.ui, "line_page", 0) or 0) + 1) % n
        return
    if action == "pick_next":
        n = max(1, (len(LINES) + PICK_PER_PAGE - 1) // PICK_PER_PAGE)
        pet.pick_page = (int(getattr(pet, "pick_page", 0) or 0) + 1) % n
        return
    if action == "hatch_next":
        n = max(1, (len(HATCH) + HATCH_PER_PAGE - 1) // HATCH_PER_PAGE)
        pet.ui.hatch_page = (int(getattr(pet.ui, "hatch_page", 0) or 0) + 1) % n
        return
    if action == "hatch_care":
        pet.ui.hatch_view = "care"
        return
    if action == "hatch_tools":
        pet.ui.hatch_view = "tools"
        return
    if action == "hatch:tap":
        _egg_tap(pet)
        return
    if action == "hatch:catch":
        _egg_catch(pet)
        return
    if action.startswith("egg:"):
        _egg_play(pet, action.split(":", 1)[1])
        return
    if action == "move_next":
        n = max(1, (len(all_moves_for(pet.save["current"])) + MOVE_PER_PAGE - 1) // MOVE_PER_PAGE)
        pet.ui.move_page = (int(getattr(pet.ui, "move_page", 0) or 0) + 1) % n
        return
    if action == "roster_next":
        n = max(1, (len(LINES) + ROSTER_PER_PAGE - 1) // ROSTER_PER_PAGE)
        pet.ui.roster_page = (int(getattr(pet.ui, "roster_page", 0) or 0) + 1) % n
        return
    if action.startswith("swap:"):
        pid = action.split(":", 1)[1]
        pet.set_partner(pid)
        if owns_line(pet.save, pid):
            pet.panel_open = True
            pet.ui.mode = "together"
        return
    if action == "play":
        pet.play()
        pet.ui.say("PLAY")
        return
    if action == "go":
        pet.explore()
        return
    if action.startswith("buyitem:"):
        _buy_item(pet, action.split(":", 1)[1])
        return
    if action.startswith("useitem:"):
        _use_item(pet, action.split(":", 1)[1])
        return
    if action.startswith("sel:"):
        pet.ui.sel_peer = action.split(":", 1)[1]
        return
    if action.startswith("chal:"):
        _challenge(pet, action.split(":", 1)[1])
        return
    if action.startswith("pvp:"):
        _pvp_use(pet, action.split(":", 1)[1])
        return
    if action == "pvp_end":
        pet.ui.pvp = None
        pet.ui.mode = "together"
        return
    if action == "toast_yes":
        if pet.ui.pending_chal:
            _chal_yes(pet)
        else:
            _invite_yes(pet)
        return
    if action == "toast_no":
        if pet.ui.pending_chal:
            _chal_no(pet)
        elif pet.ui.pending_invite and pet.net:
            inv = pet.ui.pending_invite
            pet.net.reply_invite(inv.get("ip", ""), inv.get("from_pid", ""), False, None, inv.get("port"))
            pet.ui.pending_invite = None
            pet.ui.say("DECLINED")
        return
    if action == "swap":
        pet.picker = True
        pet.panel_open = False
        return
    if action == "name":
        pet.ui.typing = {"title": "NAME", "prompt": "What do they call you?", "buf": pet.save.get("player_name") or "", "field": "player_name"}
        return
    if action.startswith("key:"):
        _key(pet, action.split(":", 1)[1])
        return
    if action.startswith("main:"):
        pet.ui.pick_line = action.split(":", 1)[1]
        return
    if action == "begin":
        _begin(pet)
        return
    if action.startswith("hatch:"):
        _hatch(pet, action.split(":", 1)[1])
        return
    if action.startswith("buy:"):
        _buy_move(pet, action.split(":", 1)[1])
        return
    if action.startswith("up:"):
        _up_move(pet, action.split(":", 1)[1])
        return
    if action.startswith("eq:"):
        _equip(pet, action.split(":", 1)[1])
        return
    if action.startswith("unequip:"):
        _unequip(pet, int(action.split(":", 1)[1]))
        return
    if action == "fight_start":
        _fight_start(pet)
        return
    if action.startswith("use:"):
        _fight_use(pet, action.split(":", 1)[1])
        return
    if action == "crest":
        pet.ui.crest_i = (pet.ui.crest_i + 1) % len(CLAN_CRESTS)
        return
    if action == "clan_create":
        _clan_create(pet)
        return
    if action == "clan_join":
        _clan_join(pet)
        return
    if action == "clan_leave":
        pet.save["clan"] = None
        pet.persist()
        pet.ui.say("LEFT CLAN")
        return
    if action.startswith("inv:"):
        _invite(pet, action.split(":", 1)[1])
        return
    if action.startswith("war:"):
        _war(pet, action.split(":", 1)[1])
        return
    if action == "invite_yes":
        _invite_yes(pet)
        return
    if action == "invite_no":
        if pet.ui.pending_invite and pet.net:
            inv = pet.ui.pending_invite
            pet.net.reply_invite(inv.get("ip", ""), inv.get("from_pid", ""), False, None)
        pet.ui.pending_invite = None
        pet.ui.say("DECLINED")
        return
    if action == "shop_bag":
        pet.ui.shop_view = "bag"
        return
    if action == "shop_gear":
        pet.ui.shop_view = "gear"
        return
    if action == "gear_next":
        n = max(1, (len(ATTACHMENTS) + GEAR_PER_PAGE - 1) // GEAR_PER_PAGE)
        pet.ui.gear_page = (int(getattr(pet.ui, "gear_page", 0) or 0) + 1) % n
        return
    if action.startswith("buygear:"):
        _buy_gear(pet, action.split(":", 1)[1])
        return
    if action.startswith("wear:"):
        _wear_gear(pet, action.split(":", 1)[1])
        return
    if action == "mail_view":
        pet.ui.together_view = "mail"
        pet.ui.mode = "together"
        return
    if action == "mail_team":
        pet.ui.together_view = "team"
        return
    if action == "mail_write":
        pet.ui.typing = {"title": "MAIL", "prompt": "Message the LAN", "buf": "", "field": "chat"}
        return
    if action == "hatch_run":
        pet.ui.hatch_view = "run"
        return
    if action == "run_start":
        pet.start_run()
        return
    if action == "fight_wild":
        pet.ui.fight_view = "wild"
        pet.ui.fight = None
        return
    if action == "fight_floor":
        pet.ui.fight_view = "floor"
        return
    if action == "fight_raid":
        pet.ui.fight_view = "raid"
        return
    if action == "raid_toggle":
        _raid_toggle(pet)
        return
    if action == "raid_start":
        pet.start_raid()
        return
    if action == "floor_start":
        _floor_start(pet)
        return
    if action == "floor_next":
        _floor_next(pet)
        return
    if action.startswith("floor:"):
        _floor_use(pet, action.split(":", 1)[1])
        return
    if action.startswith("raid:"):
        pet.raid_move(action.split(":", 1)[1])
        return
    if action == "field_leave":
        pet.close_field()
        return
    if action == "field_jump":
        pet.field_jump = True
        return


def _key(pet, ch: str) -> None:
    t = pet.ui.typing
    if not t:
        return
    buf = str(t.get("buf") or "")
    lim = 40 if t.get("field") == "chat" else 16
    if ch == "del":
        t["buf"] = buf[:-1]
        return
    if ch == "sp":
        t["buf"] = (buf + " ")[:lim]
        return
    if ch == "cancel":
        pet.ui.typing = None
        return
    if ch == "ok":
        field = t.get("field")
        val = buf.strip()[:lim]
        pet.ui.typing = None
        if field == "player_name":
            if not val:
                pet.ui.say("NEED A NAME")
                return
            pet.save["player_name"] = val[:16]
            pet.persist()
            pet.ui.say(val.upper())
        elif field == "clan_name":
            _clan_create_named(pet, val[:16])
        elif field == "clan_code":
            _clan_join_code(pet, val[:16])
        elif field == "chat":
            _send_chat(pet, val)
        return
    if len(ch) == 1:
        t["buf"] = (buf + ch)[:lim]


def _begin(pet) -> None:
    if not pet.save.get("player_name"):
        pet.ui.typing = {"title": "NAME", "prompt": "What do they call you?", "buf": "", "field": "player_name"}
        pet.ui.say("NEED A NAME")
        return
    pid = pet.ui.pick_line
    if pid not in LINE_BY_ID:
        return
    pet.save["main"] = pid
    pet.save["current"] = pid
    pet.save["owned"] = [pid]
    st = pet.save.setdefault("stats", {})
    st["pets"] = 1
    pet.persist()
    pet.ui.mode = "together"
    pet.panel_open = True
    pet.set_anim("happy", 1.0)
    pet.flash(f"MAIN {pid.upper()}")


def _hatch(pet, hid: str) -> None:
    h = next((x for x in HATCH if x["id"] == hid), None)
    if not h:
        return
    p = pet.p()
    cds = p.setdefault("cd_hatch", {})
    left = float(cds.get(hid, 0)) - time.time()
    if left > 0:
        pet.ui.say(f"WAIT {int(left)}s")
        return
    coins = int(pet.save.get("coins", 0))
    if coins < shop_cost(h["cost"]):
        pet.ui.say("BROKE")
        pet.pop("BROKE", (255, 90, 90))
        return
    pet.save["coins"] = coins - shop_cost(h["cost"])
    warmth = max(0, min(100, int(p.get("egg_warmth") or 40)))
    shave = int(h["shave"] * (1.0 + 0.2 * (warmth / 100.0)))
    p["stage_started"] = float(p["stage_started"]) - shave
    cds[hid] = time.time() + h["cd"]
    if hid == "pulse":
        p["strength"] = min(99, p["strength"] + 1)
    if hid == "spicy":
        p["mood"] = min(100, p["mood"] + 6)
    if hid in ("warm", "lamp", "nest"):
        p["egg_warmth"] = min(100, warmth + 8)
    st = pet.save.setdefault("stats", {})
    st["hatches"] = int(st.get("hatches") or 0) + 1
    pet.persist()
    pet.ui.say(f"-{shave // 60} MIN")
    pet.pop(f"-{shave // 60}m", (255, 180, 80))
    pet.set_anim("evo", 0.8)


def _egg_cd(pet, key: str, seconds: int) -> bool:
    p = pet.p()
    cds = p.setdefault("cd_egg", {})
    left = float(cds.get(key, 0)) - time.time()
    if left > 0:
        pet.ui.say(f"WAIT {int(left)}s")
        return True
    cds[key] = time.time() + seconds
    return False


def _shave(pet, sec: int) -> int:
    p = pet.p()
    warmth = max(0, min(100, int(p.get("egg_warmth") or 40)))
    got = max(30, int(sec * (1.0 + 0.15 * (warmth / 100.0)) * hatch_mult(p)))
    p["stage_started"] = float(p["stage_started"]) - got
    return got


def _egg_tap(pet) -> None:
    g = getattr(pet.ui, "kick_game", None)
    if g and time.time() < float(g.get("end") or 0):
        _egg_catch_resolve(pet)
        return
    p = pet.p()
    now = time.time()
    combo_until = float(p.get("egg_combo_until") or 0)
    combo = int(p.get("egg_combo") or 0)
    if now < combo_until:
        combo += 1
    else:
        combo = 1
    p["egg_combo"] = combo
    p["egg_combo_until"] = now + 1.4
    p["egg_taps"] = int(p.get("egg_taps") or 0) + 1
    p["egg_warmth"] = min(100, int(p.get("egg_warmth") or 40) + 1)
    p["mood"] = min(100, p["mood"] + 2)
    pet.quest_tick("eggtap")
    pet.quest_tick("pet")
    if combo > 0 and combo % 5 == 0:
        p["egg_kicks"] = int(p.get("egg_kicks") or 0) + 1
        got = _shave(pet, 90 + combo * 8)
        pet.ui.say(f"KICK x{combo}  -{got // 60}m")
        pet.pop("KICK", (255, 180, 80))
        pet.set_anim("evo", 0.5)
    else:
        pet.ui.say(f"TAP x{combo}")
        pet.pop("♥", (255, 90, 130), kind="heart")
        pet.set_anim("happy", 0.4)
    pet.persist()


def _egg_catch(pet) -> None:
    g = getattr(pet.ui, "kick_game", None)
    if g and time.time() < float(g.get("end") or 0):
        _egg_catch_resolve(pet)
        return
    if _egg_cd(pet, "catch", 20):
        return
    pet.ui.kick_game = {
        "start": time.time(),
        "end": time.time() + 2.3,
        "lo": 0.58,
        "hi": 0.84,
    }
    pet.ui.say("TAP THE KICK")


def _egg_catch_resolve(pet) -> None:
    g = getattr(pet.ui, "kick_game", None)
    pet.ui.kick_game = None
    if not g:
        return
    span = max(0.2, float(g["end"]) - float(g["start"]))
    t = (time.time() - float(g["start"])) / span
    p = pet.p()
    if float(g["lo"]) <= t <= float(g["hi"]):
        p["egg_kicks"] = int(p.get("egg_kicks") or 0) + 1
        p["egg_warmth"] = min(100, int(p.get("egg_warmth") or 40) + 6)
        p["mood"] = min(100, p["mood"] + 8)
        got = _shave(pet, 6 * 60)
        n = random.randint(1, 4)
        pet.save["coins"] = int(pet.save.get("coins", 0)) + n
        pet.ui.say(f"CAUGHT  -{got // 60}m  +${n}")
        pet.pop("KICK!", (255, 200, 70))
        pet.quest_tick("eggcatch")
        pet.set_anim("evo", 0.7)
    elif t < float(g["lo"]):
        pet.ui.say("TOO SOON")
        pet.pop("...", (180, 180, 180))
    else:
        pet.ui.say("TOO LATE")
        pet.pop("...", (180, 180, 180))
    pet.persist()


def _egg_play(pet, kind: str) -> None:
    spec = EGG_PLAY_BY_ID.get(kind)
    if not spec:
        return
    if _egg_cd(pet, kind, int(spec["cd"])):
        return
    p = pet.p()
    if kind == "roll":
        roll = random.random()
        if roll < 0.18:
            p["mood"] = max(0, p["mood"] - 4)
            pet.ui.say("DIZZY EGG")
            pet.pop("WHOA", (200, 160, 80))
        elif roll < 0.45:
            n = random.randint(2, 6)
            pet.save["coins"] = int(pet.save.get("coins", 0)) + n
            pet.ui.say(f"NEST COIN +${n}")
            pet.pop(f"+${n}", (255, 220, 70))
        elif roll < 0.78:
            p["egg_kicks"] = int(p.get("egg_kicks") or 0) + 1
            got = _shave(pet, 4 * 60)
            pet.ui.say(f"IT KICKED  -{got // 60}m")
            pet.pop("KICK", (255, 180, 80))
        else:
            got = _shave(pet, 9 * 60)
            p["egg_warmth"] = min(100, int(p.get("egg_warmth") or 40) + 8)
            pet.ui.say(f"LUCKY ROLL  -{got // 60}m")
            pet.pop("LUCK", (120, 255, 150))
        pet.quest_tick("eggroll")
        pet.set_anim("happy", 0.8)
    elif kind == "talk":
        line = random.choice(TALK_LINES)
        p["mood"] = min(100, p["mood"] + 10)
        p["egg_warmth"] = min(100, int(p.get("egg_warmth") or 40) + 4)
        got = _shave(pet, 3 * 60)
        pet.ui.say(line.upper()[:22])
        pet.pop("...", (180, 220, 255))
        pet.set_anim("happy", 0.7)
    elif kind == "turn":
        p["egg_warmth"] = min(100, int(p.get("egg_warmth") or 40) + 10)
        p["hygiene"] = min(100, p["hygiene"] + 6)
        got = _shave(pet, 2 * 60)
        pet.ui.say(f"TURNED  -{got // 60}m")
        pet.pop("TURN", (200, 200, 120))
        pet.set_anim("idle", 0.4)
    elif kind == "listen":
        roll = random.random()
        if roll < 0.4:
            p["egg_kicks"] = int(p.get("egg_kicks") or 0) + 1
            got = _shave(pet, 5 * 60)
            p["strength"] = min(99, p["strength"] + 1)
            pet.ui.say("IT MOVED")
            pet.pop("THUMP", (255, 180, 80))
        elif roll < 0.75:
            pet.ui.say("THUMP  THUMP")
            pet.pop("♥", (255, 90, 130), kind="heart")
        else:
            p["mood"] = min(100, p["mood"] + 6)
            pet.ui.say("SLEEPY HUM")
            pet.pop("ZZZ", (180, 180, 220))
        pet.set_anim("happy", 0.6)
    elif kind == "wish":
        roll = random.random()
        if roll < 0.35:
            got = _shave(pet, 12 * 60)
            pet.ui.say(f"WISH  -{got // 60}m")
            pet.pop("WISH", (255, 220, 80))
        elif roll < 0.6:
            n = random.randint(6, 14)
            pet.save["coins"] = int(pet.save.get("coins", 0)) + n
            pet.ui.say(f"WISH +${n}")
            pet.pop(f"+${n}", (255, 220, 70))
        elif roll < 0.8:
            drop = random.choice(ITEMS)
            give_item(pet, drop["id"], 1)
            pet.ui.say(f"WISH {drop['name'].upper()[:12]}")
            pet.pop(drop["name"].upper(), (180, 220, 255))
        else:
            p["mood"] = min(100, p["mood"] + 16)
            p["egg_warmth"] = min(100, int(p.get("egg_warmth") or 40) + 12)
            pet.ui.say("THE EGG GLOWS")
            pet.pop("GLOW", (255, 240, 160))
        pet.quest_tick("eggwish")
        pet.set_anim("evo", 0.8)
    elif kind == "window":
        roll = random.random()
        if roll < 0.28:
            n = random.randint(3, 8)
            pet.save["coins"] = int(pet.save.get("coins", 0)) + n
            pet.ui.say(f"BIRD DROPPED +${n}")
            pet.pop(f"+${n}", (255, 220, 70))
        elif roll < 0.5:
            p["mood"] = min(100, p["mood"] + 12)
            pet.ui.say("RAIN ON THE GLASS")
            pet.pop("RAIN", (120, 180, 255))
        elif roll < 0.72:
            got = _shave(pet, 3 * 60)
            pet.ui.say(f"SUN WARM  -{got // 60}m")
            p["egg_warmth"] = min(100, int(p.get("egg_warmth") or 40) + 6)
            pet.pop("SUN", (255, 200, 80))
        else:
            pet.ui.say("A FACE IN THE GLASS")
            pet.pop("...", (200, 200, 210))
            p["mood"] = min(100, p["mood"] + 6)
        pet.quest_tick("go")
        pet.set_anim("happy", 0.8)
    elif kind == "pat":
        p["mood"] = min(100, p["mood"] + 8)
        p["egg_warmth"] = min(100, int(p.get("egg_warmth") or 40) + 8)
        got = _shave(pet, 90)
        pet.ui.say(f"PAT  -{got // 60}m")
        pet.pop("♥", (255, 90, 130), kind="heart")
        pet.set_anim("happy", 0.5)
    elif kind == "peek":
        roll = random.random()
        if roll < 0.4:
            p["egg_kicks"] = int(p.get("egg_kicks") or 0) + 1
            got = _shave(pet, 5 * 60)
            pet.ui.say(f"EYE IN THE CRACK  -{got // 60}m")
            pet.pop("PEEK", (255, 200, 80))
        elif roll < 0.7:
            n = random.randint(2, 7)
            pet.save["coins"] = int(pet.save.get("coins", 0)) + n
            pet.ui.say(f"SHINY CRACK +${n}")
            pet.pop(f"+${n}", (255, 220, 70))
        else:
            p["mood"] = min(100, p["mood"] + 10)
            pet.ui.say("IT BLINKED")
            pet.pop("...", (180, 220, 255))
        pet.set_anim("evo", 0.6)
    elif kind == "rock":
        p["egg_warmth"] = min(100, int(p.get("egg_warmth") or 40) + 12)
        p["mood"] = min(100, p["mood"] + 6)
        got = _shave(pet, 4 * 60)
        pet.ui.say(f"ROCK-A-BYE  -{got // 60}m")
        pet.pop("ZZZ", (180, 180, 220))
        pet.set_anim("idle", 0.8)
    elif kind == "snack":
        it = random.choice(FOODS) if FOODS else {"id": "meat", "name": "Meat", "hunger": 8, "mood": 4}
        pet.eat_id = it["id"]
        p["hunger"] = min(100, p["hunger"] + int(it.get("hunger") or 8) // 2)
        p["mood"] = min(100, p["mood"] + 6)
        p["egg_warmth"] = min(100, int(p.get("egg_warmth") or 40) + 5)
        got = _shave(pet, 2 * 60)
        pet.ui.say(f"CRUMB {it['name'].upper()[:10]}")
        pet.pop("YUM", (255, 200, 90))
        pet.set_anim("eat", 1.2)
        pet.quest_tick("feed")
    pet.persist()


def _buy_move(pet, mid: str) -> None:
    mv = move_by_id(pet.save["current"], mid)
    if not mv:
        return
    p = pet.p()
    owned = p.setdefault("moves", {})
    if mid in owned:
        return
    coins = int(pet.save.get("coins", 0))
    price = move_buy_cost(mv)
    if coins < price:
        pet.ui.say("BROKE")
        return
    pet.save["coins"] = coins - price
    owned[mid] = 1
    load = p.setdefault("loadout", [])
    if len([x for x in load if x]) < LOADOUT_SLOTS:
        load.append(mid)
        p["loadout"] = [x for x in load if x][:LOADOUT_SLOTS]
    pet.persist()
    pet.ui.say(f"LEARNED {mv['name'].upper()}")
    pet.pop(mv["name"].upper(), (180, 220, 255))
    pet.quest_tick("learn")
    pet.set_anim("train", 1.0)


def _up_move(pet, mid: str) -> None:
    mv = move_by_id(pet.save["current"], mid)
    if not mv:
        return
    p = pet.p()
    owned = p.setdefault("moves", {})
    lv = int(owned.get(mid, 0))
    if lv <= 0 or lv >= MOVE_MAX:
        return
    coins = int(pet.save.get("coins", 0))
    price = move_up_cost(mv, lv)
    if coins < price:
        pet.ui.say("BROKE")
        return
    pet.save["coins"] = coins - price
    owned[mid] = lv + 1
    pet.persist()
    pet.ui.say(f"{mv['name'].upper()} LV{lv + 1}")
    pet.pop(f"LV{lv + 1}", (255, 220, 80))
    pet.set_anim("train", 0.8)


def _equip(pet, mid: str) -> None:
    p = pet.p()
    if mid not in (p.get("moves") or {}):
        return
    load = [x for x in (p.get("loadout") or []) if x and x != mid]
    if len(load) >= LOADOUT_SLOTS:
        load = load[1:]
    load.append(mid)
    p["loadout"] = load
    pet.persist()
    pet.ui.say("EQUIPPED")


def _unequip(pet, slot: int) -> None:
    p = pet.p()
    load = list(p.get("loadout") or [])
    while len(load) < LOADOUT_SLOTS:
        load.append("")
    if 0 <= slot < len(load):
        load[slot] = ""
    p["loadout"] = [x for x in load if x]
    pet.persist()


def _fight_start(pet) -> None:
    if pet.form() in EGGS:
        pet.ui.say("TOO SMALL")
        return
    p = pet.p()
    if p["hunger"] < 16:
        pet.ui.say("TOO HUNGRY")
        return
    st = combat_stats(p, p["stage_i"])
    e = pick_enemy(pet.ln()["tag"], p["stage_i"], p["strength"])
    pet.ui.fight = {
        "eid": e["id"],
        "php": st["hp"],
        "ehp": int(e["hp"]),
        "pmax": st["hp"],
        "emax": int(e["hp"]),
        "over": False,
        "status": "",
        "log": f"VS {e['name'].upper()}  weak {e.get('weak', '-')}",
    }
    pet.ui.say(f"VS {e['name'].upper()}")
    pet.panel_open = False
    pet.begin_desktop_fight("wild", e)
    pet.set_anim("train", 0.6)


def _fight_use(pet, mid: str) -> None:
    f = pet.ui.fight
    if not f or f.get("over"):
        return
    p = pet.p()
    e = ENEMY_BY_ID.get(f["eid"])
    if not e:
        return
    if mid == "struggle":
        mv = {"name": "Struggle", "typ": "strike", "pow": 8, "grow": 0}
        lv = 1
    else:
        mv = move_by_id(pet.save["current"], mid)
        lv = int((p.get("moves") or {}).get(mid, 0))
        if not mv or lv <= 0:
            pet.ui.say("NO MOVE")
            return
    stats = combat_stats(p, p["stage_i"])
    hit = roll_hit(mv, lv, stats, e)
    buffs = pet.save.setdefault("buffs", {})
    if int(buffs.get("chip") or 0) > 0 and not hit["miss"]:
        hit["dmg"] = int(hit["dmg"] * 1.28)
        buffs["chip"] -= 1
    p["hunger"] = max(0, p["hunger"] - 3)
    if hit["miss"]:
        f["log"] = f"{mv['name'].upper()}  MISS"
        pet.pop("MISS", (180, 180, 180))
    else:
        f["ehp"] = max(0, f["ehp"] - hit["dmg"])
        tag = " CRIT" if hit["crit"] else ""
        if hit["status"]:
            f["status"] = hit["status"]
            tag += f" {hit['status'].upper()}"
        f["log"] = f"{mv['name'].upper()}  {hit['dmg']}{tag}"
        pet.pop(str(hit["dmg"]), (255, 220, 80) if not hit["crit"] else (255, 80, 80))
    if f["ehp"] <= 0:
        _fight_win(pet, e)
        return
    if f.get("status") == "burn":
        f["ehp"] = max(0, f["ehp"] - 3)
    dmg_in = enemy_hit(e, stats, f.get("status") or "")
    if dmg_in <= 0:
        f["log"] += "  STUNNED"
    else:
        f["php"] = max(0, f["php"] - dmg_in)
        f["log"] += f"  /  {e['name']} {dmg_in}"
    if f["php"] <= 0:
        _fight_lose(pet, e)
        return
    pet.persist()


def _fight_win(pet, e: dict) -> None:
    f = pet.ui.fight
    f["over"] = True
    loot = random.randint(int(e["lo"]), int(e["hi"]))
    pet.save["streak"] = int(pet.save.get("streak") or 0) + 1
    streak = int(pet.save["streak"])
    if streak >= 3:
        loot += 4 + streak
    pet.save["coins"] = int(pet.save.get("coins", 0)) + loot
    p = pet.p()
    p["strength"] = min(99, p["strength"] + 2)
    p["mood"] = min(100, p["mood"] + 8)
    p["trains"] += 1
    gained = grant_xp(p, 12 + int(e.get("hi") or 10))
    st = pet.save.setdefault("stats", {})
    st["wins"] = int(st.get("wins") or 0) + 1
    st["coins_earned"] = int(st.get("coins_earned") or 0) + loot
    f["log"] = f"WIN  {e['name'].upper()}  +${loot}"
    pet.ui.say(f"WIN +${loot}")
    pet.pop(f"+${loot}", (120, 255, 140))
    pet.quest_tick("win")
    if gained:
        pet.ui.say(f"LV UP {p['level']}")
        pet.pop("LV UP", (180, 255, 120))
    if random.random() < 0.55:
        drop = random.choice(ITEMS)
        give_item(pet, drop["id"], 1)
        f["log"] = f"WIN  +${loot}  {drop['name']}"
        pet.ui.say(f"LOOT {drop['name'].upper()}")
        pet.pop(drop["name"].upper(), (180, 220, 255))
    pet.set_anim("happy", 1.2)
    pet.combat_over_at = time.time()
    pet.persist()


def _fight_lose(pet, e: dict) -> None:
    f = pet.ui.fight
    f["over"] = True
    pet.save["streak"] = 0
    p = pet.p()
    p["mood"] = max(0, p["mood"] - 12)
    st = pet.save.setdefault("stats", {})
    st["losses"] = int(st.get("losses") or 0) + 1
    f["log"] = f"{e['name'].upper()}  WINS"
    pet.ui.say("LOST")
    pet.pop("LOST", (255, 90, 90))
    pet.set_anim("hungry", 1.2)
    pet.combat_over_at = time.time()
    pet.persist()


def _clan_create(pet) -> None:
    if pet.save.get("clan"):
        return
    pet.ui.typing = {"title": "CLAN", "prompt": "Name the clan", "buf": "", "field": "clan_name"}


def _clan_create_named(pet, name: str) -> None:
    if not name:
        pet.ui.say("NEED A NAME")
        return
    trainer = pet.save.get("player_name") or "Trainer"
    main = pet.save.get("main") or pet.save.get("current")
    crest = CLAN_CRESTS[pet.ui.crest_i % len(CLAN_CRESTS)]
    clan = new_clan(pet.save["player_id"], trainer, main, name, crest)
    clan["members"][0]["power"] = power_of(pet.p(), main)
    pet.save["clan"] = clan
    pet.persist()
    pet.ui.say(f"CLAN {clan['code']}")


def _clan_join(pet) -> None:
    pet.ui.typing = {"title": "JOIN", "prompt": "5-letter clan code", "buf": "", "field": "clan_code"}


def _clan_join_code(pet, code: str) -> None:
    if not code:
        return
    code = code.strip().upper()
    peers = pet.net.nearby() if pet.net else []
    hit = next((p for p in peers if str(p.get("clan_code", "")).upper() == code), None)
    if not hit:
        pet.ui.say("NO HOST WITH THAT CODE")
        return
    member = _me_member(pet)
    pet.net.send_to(hit["ip"], {"t": "join", "to": hit["pid"], "code": code, "member": member})
    pet.ui.say("JOIN SENT")


def _me_member(pet) -> dict:
    main = pet.save.get("main") or pet.save.get("current")
    return {
        "id": pet.save["player_id"],
        "name": pet.save.get("player_name") or "Trainer",
        "main": main,
        "power": power_of(pet.save["partners"][main], main),
    }


def _invite(pet, pid: str) -> None:
    clan = pet.save.get("clan")
    if not clan or not pet.net:
        pet.ui.say("MAKE A CLAN")
        return
    peer = next((p for p in pet.net.nearby() if p.get("pid") == pid), None)
    if not peer:
        pet.ui.say("THEY LEFT")
        return
    pet.net.invite(peer, clan, pet.save.get("player_name") or "Trainer", pet.save["player_id"])
    pet.ui.say("INVITE SENT")


def _invite_yes(pet) -> None:
    inv = pet.ui.pending_invite
    if not inv:
        return
    clan = dict(inv.get("clan") or {})
    if not clan.get("id"):
        pet.ui.pending_invite = None
        return
    member = _me_member(pet)
    clan["members"] = [member]
    pet.save["clan"] = {
        "id": clan["id"],
        "code": clan.get("code", ""),
        "name": clan.get("name", "Clan"),
        "crest": clan.get("crest", "fang"),
        "leader": clan.get("leader", ""),
        "members": [member],
        "wins": 0,
        "losses": 0,
    }
    if pet.net:
        pet.net.reply_invite(inv.get("ip", ""), inv.get("from_pid", ""), True, member, inv.get("port"))
    pet.ui.pending_invite = None
    pet.persist()
    pet.ui.say(f"JOINED {clan.get('name', '').upper()}")


def _war(pet, pid: str) -> None:
    clan = pet.save.get("clan")
    if not clan or not pet.net:
        return
    peer = next((p for p in pet.net.nearby() if p.get("pid") == pid), None)
    if not peer:
        pet.ui.say("THEY LEFT")
        return
    my_p = sum(int(m.get("power") or 0) for m in clan.get("members") or [])
    seed = random.randint(1, 1_000_000)
    pet.net.war(peer["ip"], pid, my_p, clan.get("name", ""), seed)
    their = int(peer.get("power") or 10)
    won = _war_roll(my_p, their, seed)
    _apply_war(pet, won)
    pet.net.war_result(peer["ip"], pid, not won, seed)


def _war_roll(a: int, b: int, seed: int) -> bool:
    rng = random.Random(seed)
    return a * rng.uniform(0.87, 1.13) >= b * rng.uniform(0.87, 1.13)


def _apply_war(pet, won: bool) -> None:
    clan = pet.save.get("clan")
    st = pet.save.setdefault("stats", {})
    if won:
        clan["wins"] = int(clan.get("wins") or 0) + 1
        st["wars_won"] = int(st.get("wars_won") or 0) + 1
        loot = 20
        pet.save["coins"] = int(pet.save.get("coins", 0)) + loot
        st["coins_earned"] = int(st.get("coins_earned") or 0) + loot
        pet.ui.say(f"WAR WIN +${loot}")
        pet.pop("WAR WIN", (120, 255, 140))
    else:
        clan["losses"] = int(clan.get("losses") or 0) + 1
        st["wars_lost"] = int(st.get("wars_lost") or 0) + 1
        pet.ui.say("WAR LOST")
        pet.pop("WAR LOST", (255, 90, 90))
    pet.persist()


def _combat_snap(pet) -> dict:
    main = pet.save.get("main") or pet.save.get("current")
    p = pet.save["partners"].get(main) or pet.p()
    return {
        "from_pid": pet.save["player_id"],
        "from_name": pet.save.get("player_name") or "Trainer",
        "main": main,
        "form": pet.form(),
        "hp": player_hp(p["stage_i"], p["strength"]),
        "str": int(p["strength"]),
        "power": power_of(p, main),
        "moves": dict(p.get("moves") or {}),
        "loadout": list(p.get("loadout") or []),
    }


def _peer_by_id(pet, pid: str) -> dict | None:
    if not pet.net:
        return None
    return next((p for p in pet.net.nearby() if p.get("pid") == pid), None)


def _challenge(pet, pid: str) -> None:
    if pet.form() in EGGS:
        pet.ui.say("TOO SMALL")
        return
    peer = _peer_by_id(pet, pid)
    if not peer or not pet.net:
        pet.ui.say("THEY LEFT")
        return
    pet.net.challenge(peer, _combat_snap(pet))
    pet.ui.say("CHALLENGE SENT")
    pet.flash("CHALLENGE SENT")


def _chal_yes(pet) -> None:
    ev = pet.ui.pending_chal
    if not ev or not pet.net:
        return
    snap = _combat_snap(pet)
    peer = {"ip": ev.get("ip"), "port": ev.get("port"), "pid": ev.get("from_pid")}
    pet.net.chal_reply(peer, True, snap)
    pet.ui.pvp = _pvp_state(pet, ev, host=False)
    pet.ui.pending_chal = None
    pet.ui.mode = "fight"
    pet.panel_open = True
    pet.ui.say("FIGHT ON")


def _chal_no(pet) -> None:
    ev = pet.ui.pending_chal
    if ev and pet.net:
        pet.net.chal_reply({"ip": ev.get("ip"), "port": ev.get("port"), "pid": ev.get("from_pid")}, False, {})
    pet.ui.pending_chal = None
    pet.ui.say("NO FIGHT")


def _pvp_state(pet, their: dict, host: bool) -> dict:
    me = _combat_snap(pet)
    return {
        "host": host,
        "peer_ip": their.get("ip"),
        "peer_port": their.get("port"),
        "peer_pid": their.get("from_pid") or their.get("pid"),
        "their_name": their.get("from_name") or their.get("name") or "THEM",
        "their_main": their.get("main") or "agumon",
        "php": me["hp"],
        "pmax": me["hp"],
        "ehp": int(their.get("hp") or 36),
        "emax": int(their.get("hp") or 36),
        "their_str": int(their.get("str") or 0),
        "over": False,
        "wait": False,
        "log": f"VS {str(their.get('from_name') or their.get('name') or 'THEM').upper()}",
    }


def _pvp_use(pet, mid: str) -> None:
    f = pet.ui.pvp
    if not f or f.get("over") or f.get("wait"):
        return
    p = pet.p()
    if mid == "struggle":
        name, dmg = "STRUGGLE", max(2, 6 + int(p["strength"] * 0.2))
    else:
        mv = move_by_id(pet.save["current"], mid)
        lv = int((p.get("moves") or {}).get(mid, 0))
        if not mv or lv <= 0:
            pet.ui.say("NO MOVE")
            return
        dummy = {"defe": 3, "weak": ""}
        dmg = move_damage(mv, lv, p["strength"], dummy)
        name = mv["name"]
    f["ehp"] = max(0, f["ehp"] - dmg)
    f["log"] = f"{name.upper()} {dmg}"
    f["wait"] = True
    if pet.net:
        pet.net.pvp_act(
            {"ip": f.get("peer_ip"), "port": f.get("peer_port"), "pid": f.get("peer_pid")},
            mid,
            dmg,
            name,
        )
    if f["ehp"] <= 0:
        _pvp_finish(pet, True)
        return
    pet.set_anim("train", 0.4)


def _pvp_finish(pet, won: bool) -> None:
    f = pet.ui.pvp
    if not f:
        return
    f["over"] = True
    f["wait"] = False
    st = pet.save.setdefault("stats", {})
    if won:
        loot = 18
        pet.save["coins"] = int(pet.save.get("coins", 0)) + loot
        pet.save["streak"] = int(pet.save.get("streak") or 0) + 1
        st["wins"] = int(st.get("wins") or 0) + 1
        st["coins_earned"] = int(st.get("coins_earned") or 0) + loot
        f["log"] = f"YOU WIN  +${loot}"
        pet.ui.say(f"WIN +${loot}")
        pet.pop(f"+${loot}", (120, 255, 140))
        pet.quest_tick("win")
        pet.set_anim("happy", 1.0)
    else:
        pet.save["streak"] = 0
        st["losses"] = int(st.get("losses") or 0) + 1
        f["log"] = "YOU LOSE"
        pet.ui.say("LOST")
        pet.pop("LOST", (255, 90, 90))
        pet.set_anim("hungry", 1.0)
    pet.persist()


def net_event(pet, ev: dict) -> None:
    kind = ev.get("t")
    if kind == "invite":
        pet.ui.pending_invite = ev
        pet.flash(f"CLAN {ev.get('from_name', '?')}")
        pet.ui.say("CLAN INVITE")
        return
    if kind == "chal":
        pet.ui.pending_chal = ev
        pet.flash(f"FIGHT {ev.get('from_name', '?')}")
        pet.ui.say("CHALLENGE")
        return
    if kind == "chal_ok":
        pet.ui.pvp = _pvp_state(pet, ev, host=True)
        pet.ui.mode = "fight"
        pet.panel_open = True
        pet.ui.say("THEY ACCEPTED")
        return
    if kind == "chal_no":
        pet.ui.say("THEY SAID NO")
        pet.flash("NO FIGHT")
        return
    if kind == "pvp_act":
        f = pet.ui.pvp
        if not f or f.get("over"):
            return
        dmg = int(ev.get("dmg") or 1)
        f["php"] = max(0, f["php"] - dmg)
        f["wait"] = False
        f["log"] = f"{str(ev.get('name', 'HIT')).upper()} {dmg} ON YOU"
        if f["php"] <= 0:
            _pvp_finish(pet, False)
        return
    if kind == "join":
        clan = pet.save.get("clan")
        if not clan or str(ev.get("code", "")).upper() != str(clan.get("code", "")).upper():
            return
        _add_member(pet, ev.get("member"))
        return
    if kind == "accept":
        _add_member(pet, ev.get("member"))
        pet.ui.say("THEY JOINED")
        return
    if kind == "decline":
        pet.ui.say("INVITE NO")
        return
    if kind == "war":
        clan = pet.save.get("clan")
        if not clan:
            return
        my_p = sum(int(m.get("power") or 0) for m in clan.get("members") or [])
        their = int(ev.get("power") or 10)
        won = _war_roll(my_p, their, int(ev.get("seed") or 1))
        _apply_war(pet, won)
        if pet.net:
            pet.net.war_result(ev.get("ip", ""), ev.get("from_pid") or ev.get("pid") or "", not won, int(ev.get("seed") or 1))
        return
    if kind == "war_ack":
        return
    if kind == "chat":
        if ev.get("from_pid") == pet.save.get("player_id"):
            return
        _push_mail(pet, str(ev.get("from_name") or "?"), str(ev.get("text") or ""))
        pet.flash(f"MAIL {ev.get('from_name', '?')}")
        return
    if kind == "raid_q":
        return
    if kind == "raid_go":
        if getattr(pet, "field_mode", None) == "raid":
            return
        pet.join_raid(ev)
        return
    if kind == "raid_hit":
        st = getattr(pet, "field_state", None)
        if not st or st.get("kind") != "raid" or st.get("over"):
            return
        if ev.get("from_pid") == pet.save.get("player_id"):
            return
        st["ehp"] = min(int(st.get("ehp") or 0), int(ev.get("ehp") or st.get("ehp") or 0))
        st["log"] = f"{str(ev.get('name', 'ALLY')).upper()}  {int(ev.get('dmg') or 0)}"
        return
    if kind == "raid_over":
        st = getattr(pet, "field_state", None)
        if st and st.get("kind") == "raid" and not st.get("over"):
            st["over"] = True
            st["won"] = bool(ev.get("won"))
            st["log"] = "RAID CLEAR" if ev.get("won") else "RAID WIPE"
        return


def give_item(pet, iid: str, n: int = 1) -> None:
    bag = pet.save.setdefault("bag", {})
    bag[iid] = int(bag.get(iid) or 0) + n


def _buy_item(pet, iid: str) -> None:
    it = ITEM_BY_ID.get(iid)
    if not it:
        return
    coins = int(pet.save.get("coins", 0))
    price = shop_cost(it["cost"])
    if coins < price:
        pet.ui.say("BROKE")
        pet.pop("BROKE", (255, 90, 90))
        return
    pet.save["coins"] = coins - price
    give_item(pet, iid, 1)
    pet.quest_tick("shop")
    pet.persist()
    pet.ui.say(f"GOT {it['name'].upper()}")
    pet.pop(it["name"].upper(), (255, 220, 80))


def _use_item(pet, iid: str) -> None:
    it = ITEM_BY_ID.get(iid)
    bag = pet.save.setdefault("bag", {})
    if not it or int(bag.get(iid) or 0) <= 0:
        pet.ui.say("NONE LEFT")
        return
    bag[iid] = int(bag[iid]) - 1
    if bag[iid] <= 0:
        bag.pop(iid, None)
    p = pet.p()
    kind = it["kind"]
    buffs = pet.save.setdefault("buffs", {})
    if kind == "food":
        stuffed = p["hunger"] >= 86
        p["hunger"] = min(100, p["hunger"] + int(it.get("hunger") or 0))
        p["mood"] = min(100, p["mood"] + int(it.get("mood") or 0))
        p["feeds"] += 1
        p["poop_at"] = time.time() + 90
        pet.eat_id = iid
        if stuffed:
            p["mood"] = max(0, p["mood"] - 8)
            pet.ui.say("OVERFED")
        else:
            pet.ui.say(f"ATE {it['name'].upper()}")
            pet.set_anim("eat", 1.4)
        pet.quest_tick("feed")
    elif kind == "play":
        p["mood"] = min(100, p["mood"] + int(it.get("mood") or 20))
        p["strength"] = min(99, p["strength"] + int(it.get("str") or 0))
        if it.get("hygiene"):
            p["hygiene"] = max(0, min(100, p["hygiene"] + int(it["hygiene"])))
        pet.ui.say(it["name"].upper())
        pet.set_anim("happy", 1.2)
        pet.quest_tick("pet")
    elif kind == "heal":
        p["hygiene"] = min(100, p["hygiene"] + int(it.get("hygiene") or 40))
        if it.get("clear_poop"):
            p["poop"] = False
            p["hygiene"] = 100
        p["mood"] = min(100, p["mood"] + int(it.get("mood") or 0))
        if it.get("hunger"):
            p["hunger"] = min(100, p["hunger"] + int(it["hunger"]))
        pet.ui.say(it["name"].upper())
        pet.quest_tick("wash")
        pet.set_anim("happy", 0.8)
    elif kind == "train":
        p["strength"] = min(99, p["strength"] + int(it.get("str") or 4))
        p["hunger"] = max(0, p["hunger"] + int(it.get("hunger") or 0))
        p["trains"] += 1
        pet.ui.say(f"+STR {it['name'].upper()}")
        pet.quest_tick("train")
        pet.set_anim("train", 1.2)
    elif kind == "hatch":
        p["stage_started"] = float(p["stage_started"]) - int(it.get("shave") or 1800)
        pet.ui.say(f"-{int(it.get('shave') or 0) // 60} MIN")
        pet.set_anim("evo", 0.8)
    elif kind == "gamble":
        roll = random.randint(0, 48)
        pet.save["coins"] = int(pet.save.get("coins", 0)) + roll
        pet.ui.say(f"PACK +${roll}")
        pet.pop(f"+${roll}", (255, 220, 70))
    elif kind == "chip":
        buffs["chip"] = int(buffs.get("chip") or 0) + 1
        pet.ui.say("CHIP READY")
    elif kind == "luck":
        buffs["luck"] = int(buffs.get("luck") or 0) + 1
        pet.ui.say("LUCK UP")
    elif kind == "map":
        buffs["map"] = int(buffs.get("map") or 0) + 1
        pet.ui.say("MAP READY")
    elif kind == "flee":
        buffs["flee"] = int(buffs.get("flee") or 0) + 1
        pet.ui.say("SMOKE READY")
    pet.quest_tick("item")
    pet.persist()


def _add_member(pet, member) -> None:
    clan = pet.save.get("clan")
    if not clan or not isinstance(member, dict) or not member.get("id"):
        return
    ids = {m.get("id") for m in clan.get("members") or []}
    if member["id"] in ids:
        return
    clan.setdefault("members", []).append(member)
    pet.persist()
    pet.ui.say(f"+ {str(member.get('name', '?')).upper()}")


def _push_mail(pet, who: str, text: str) -> None:
    if not text:
        return
    inbox = list(pet.save.get("inbox") or [])
    inbox.append({"from": who[:16], "text": text[:40], "t": time.time()})
    pet.save["inbox"] = inbox[-INBOX_MAX:]
    pet.persist()


def _send_chat(pet, text: str) -> None:
    text = (text or "").strip()
    if not text:
        pet.ui.say("EMPTY")
        return
    name = pet.save.get("player_name") or "Trainer"
    _push_mail(pet, name, text)
    if pet.net:
        pet.net.chat(text, name, pet.save.get("player_id") or "")
    pet.ui.together_view = "mail"
    pet.ui.mode = "together"
    pet.ui.say("SENT")


def _buy_gear(pet, aid: str) -> None:
    a = ATTACH_BY_ID.get(aid)
    if not a:
        return
    coins = int(pet.save.get("coins", 0))
    price = shop_cost(a["cost"])
    if coins < price:
        pet.ui.say("BROKE")
        return
    pet.save["coins"] = coins - price
    bag = pet.save.setdefault("gear_bag", {})
    bag[aid] = int(bag.get(aid) or 0) + 1
    pet.quest_tick("shop")
    pet.persist()
    pet.ui.say(f"GOT {a['name'].upper()}")
    pet.pop(a["name"].upper(), (255, 220, 80))


def _wear_gear(pet, aid: str) -> None:
    a = ATTACH_BY_ID.get(aid)
    if not a:
        return
    p = pet.p()
    gear = p.setdefault("gear", {s: "" for s in GEAR_SLOTS})
    bag = pet.save.setdefault("gear_bag", {})
    slot = a["slot"]
    cur = gear.get(slot) or ""
    if cur == aid:
        gear[slot] = ""
        bag[aid] = int(bag.get(aid) or 0) + 1
        pet.ui.say("UNEQUIP")
    else:
        if int(bag.get(aid) or 0) <= 0:
            pet.ui.say("NONE LEFT")
            return
        bag[aid] = int(bag[aid]) - 1
        if bag[aid] <= 0:
            bag.pop(aid, None)
        if cur:
            bag[cur] = int(bag.get(cur) or 0) + 1
        gear[slot] = aid
        pet.ui.say(a["name"].upper())
        pet.pop("GEAR", (180, 220, 255))
    pet.persist()


def _raid_toggle(pet) -> None:
    pet.raid_queued = not bool(getattr(pet, "raid_queued", False))
    if pet.net:
        pet.net.raid_q(pet.raid_queued, pet.save.get("player_name") or "Trainer", pet.save.get("player_id") or "", int(combat_stats(pet.p(), pet.p()["stage_i"])["atk"]))
    pet.ui.say("QUEUED" if pet.raid_queued else "LEFT Q")


def _floor_start(pet) -> None:
    if pet.form() in EGGS:
        pet.ui.say("TOO SMALL")
        return
    p = pet.p()
    if p["hunger"] < 16:
        pet.ui.say("TOO HUNGRY")
        return
    st = combat_stats(p, p["stage_i"])
    pet.ui.floor = {"n": 1, "php": st["hp"], "pmax": st["hp"], "clear": False, "over": False}
    _floor_spawn(pet)


def _floor_spawn(pet) -> None:
    fl = pet.ui.floor
    if not fl:
        return
    p = pet.p()
    n = int(fl.get("n") or 1)
    e = pick_enemy(pet.ln()["tag"], floor_band(n, p["stage_i"], p["strength"]), p["strength"])
    e["hp"] = int(e["hp"] * (1.0 + 0.18 * (n - 1)))
    fl["eid"] = e["id"]
    fl["ename"] = e["name"]
    fl["ehp"] = int(e["hp"])
    fl["emax"] = int(e["hp"])
    fl["status"] = ""
    fl["clear"] = False
    fl["log"] = f"FLOOR {n}  {e['name'].upper()}"
    pet.ui.say(fl["log"])
    pet.panel_open = False
    pet.begin_desktop_fight("floor", e)
    pet.set_anim("train", 0.5)


def _floor_next(pet) -> None:
    fl = pet.ui.floor
    if not fl or not fl.get("clear"):
        return
    if int(fl.get("n") or 1) >= 5:
        fl["over"] = True
        fl["log"] = "DUNGEON CLEAR"
        pet.ui.say("DUNGEON CLEAR")
        pet.persist()
        return
    fl["n"] = int(fl["n"]) + 1
    _floor_spawn(pet)


def _floor_use(pet, mid: str) -> None:
    fl = pet.ui.floor
    if not fl or fl.get("over") or fl.get("clear"):
        return
    p = pet.p()
    e = ENEMY_BY_ID.get(fl.get("eid"))
    if not e:
        return
    if mid == "struggle":
        mv = {"name": "Struggle", "typ": "strike", "pow": 8, "grow": 0}
        lv = 1
    else:
        mv = move_by_id(pet.save["current"], mid)
        lv = int((p.get("moves") or {}).get(mid, 0))
        if not mv or lv <= 0:
            pet.ui.say("NO MOVE")
            return
    stats = combat_stats(p, p["stage_i"])
    hit = roll_hit(mv, lv, stats, e)
    p["hunger"] = max(0, p["hunger"] - 2)
    if hit["miss"]:
        fl["log"] = "MISS"
    else:
        fl["ehp"] = max(0, fl["ehp"] - hit["dmg"])
        if hit["status"]:
            fl["status"] = hit["status"]
        fl["log"] = f"{mv['name'].upper()} {hit['dmg']}" + (" CRIT" if hit["crit"] else "")
        pet.pop(str(hit["dmg"]), (255, 220, 80))
    if fl["ehp"] <= 0:
        loot = random.randint(8, 16) + int(fl.get("n") or 1) * 4
        pet.save["coins"] = int(pet.save.get("coins", 0)) + loot
        grant_xp(p, 10 + int(fl.get("n") or 1) * 6)
        fl["clear"] = True
        n = int(fl.get("n") or 1)
        fl["log"] = f"FLOOR {n} CLEAR  +${loot}"
        pet.quest_tick("win")
        if n >= 5:
            fl["over"] = True
            st = pet.save.setdefault("stats", {})
            st["wins"] = int(st.get("wins") or 0) + 1
            pet.ui.say("DUNGEON CLEAR")
            pet.combat_over_at = time.time()
        else:
            pet.combat_over_at = time.time()
        pet.persist()
        return
    dmg_in = enemy_hit(e, stats, fl.get("status") or "")
    fl["php"] = max(0, fl["php"] - dmg_in)
    fl["log"] += f"  / {dmg_in}"
    if fl["php"] <= 0:
        fl["over"] = True
        pet.save["streak"] = 0
        pet.ui.say("DUNGEON WIPE")
        pet.pop("WIPE", (255, 90, 90))
        pet.combat_over_at = time.time()
    pet.persist()
