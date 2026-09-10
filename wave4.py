"""Original wave-4 roster: pets, foes, food, hatch, gear, bosses. Data only."""

from __future__ import annotations


def _m(mid, name, typ, buy, up, pow_, grow):
    return {"id": mid, "name": name, "typ": typ, "buy": buy, "up": up, "pow": pow_, "grow": grow}


_MOVE_BANK = {
    "fire": ("Warm Nudge", "Ember Flick", "Ash Kick", "Flame Bite", "Cinder Rush", "Blaze Arc", "Inferno", "Sun Maw"),
    "water": ("Drip", "Puddle Slap", "Spray", "Riptide", "Wave Crash", "Undertow", "Flood", "Tide Crown"),
    "shock": ("Static", "Spark Nip", "Zap", "Arc Bite", "Thunder Dash", "Bolt Storm", "Overload", "Sky Crack"),
    "leaf": ("Sprout", "Thorn Poke", "Vine Whip", "Sap Burst", "Grove Rush", "Bloom Burst", "Root Crush", "Wild Canopy"),
    "ice": ("Frost Kiss", "Snowball", "Chill Bite", "Icicle", "Freeze Dash", "Hail Crash", "Glacier", "White Silence"),
    "wind": ("Puff", "Gust", "Feather Cut", "Gale Kick", "Sky Dive", "Cyclone", "Tempest", "Storm Crown"),
    "curse": ("Hex Tap", "Gloom", "Night Scratch", "Wail", "Shadow Bind", "Hex Storm", "Void Bite", "Last Dusk"),
    "slash": ("Nick", "Cut", "Rake", "Cleave", "Cross Cut", "Razor Arc", "Guillotine", "Moon Edge"),
    "strike": ("Poke", "Tumble", "Headbutt", "Slam", "Haymaker", "Body Crash", "Quake", "Titan Fist"),
    "gun": ("Click", "Pew", "Burst", "Ricochet", "Lock On", "Full Auto", "Rail Shot", "Core Blast"),
    "holy": ("Glow", "Bless", "Sun Tap", "Ward", "Radiance", "Judgment", "Halo Crash", "Dawn"),
}

_BUYS = (12, 14, 16, 22, 28, 40, 52, 68)
_UPS = (10, 11, 12, 14, 16, 20, 24, 28)
_POWS = (10, 12, 14, 18, 21, 26, 32, 38)
_GROWS = (4, 4, 5, 5, 6, 7, 8, 8)


def _kit(prefix: str, typ: str):
    names = _MOVE_BANK.get(typ, _MOVE_BANK["strike"])
    out = []
    for i, nm in enumerate(names):
        use = "strike" if i in (0, 2) and typ not in ("strike", "slash") else typ
        out.append(_m(f"{prefix}{i}", nm, use, _BUYS[i], _UPS[i], _POWS[i], _GROWS[i]))
    return tuple(out)


# id, display, tag, kind, c0, c1, mark, typ, baby, teen, mega, blurb
_SPECS = (
    ("ember", "Emberkit", "WILD", "cat", (230, 110, 40), (180, 50, 20), "flame", "fire", "Emberkit", "Cinderpaw", "Sunflare", "Warm fur. Sparks when mad."),
    ("brook", "Brookling", "SEA", "frog", (50, 160, 190), (20, 80, 110), "hole", "water", "Brookling", "Rivulet", "Tidecrest", "Always damp. Loves rain."),
    ("volt", "Sparkpup", "STORM", "dog", (240, 210, 50), (40, 70, 180), "bolt", "shock", "Sparkpup", "Voltmutt", "Thunderjaw", "Static in the whiskers."),
    ("moss", "Mossbun", "BLOOM", "bunny", (70, 170, 70), (40, 90, 40), "leaf", "leaf", "Mossbun", "Fernhop", "Groveking", "Soft. Smells like wet grass."),
    ("chill", "Chillix", "FROST", "fox", (180, 230, 240), (70, 140, 180), "star", "ice", "Chillix", "Snowfox", "Glacox", "Cold nose. Warmer heart."),
    ("gale", "Galekit", "SKY", "owl", (200, 210, 220), (70, 90, 130), "wing", "wind", "Galekit", "Skyhoot", "Stormfeather", "Hunts on the wind."),
    ("wyrm", "Cinderwyrm", "MYTH", "dragon", (210, 70, 40), (40, 20, 16), "flame", "fire", "Cinderwyrm", "Ashscale", "Solaroc", "A small hoard. Big teeth."),
    ("pebble", "Pebblit", "CAVE", "turtle", (140, 130, 110), (80, 70, 50), "hole", "strike", "Pebblit", "Boulduck", "Titanback", "Slow. Does not care."),
    ("moth", "Duskmoth", "DUSK", "moth", (90, 50, 120), (220, 180, 80), "star", "curse", "Duskmoth", "Lanternwing", "Nightveil", "Drawn to lamps. Eats gloom."),
    ("iron", "Ironbit", "TECH", "bot", (140, 150, 160), (40, 90, 200), "bolt", "gun", "Ironbit", "Cogbyte", "Railcore", "Beeps. Then shoots."),
    ("jelly", "Jellop", "SEA", "slime", (80, 220, 200), (30, 90, 110), "hole", "water", "Jellop", "Bloomgel", "Abyssgel", "Wobbles. Then swallows."),
    ("quartz", "Quartzil", "CAVE", "crystal", (200, 180, 230), (90, 60, 140), "star", "strike", "Quartzil", "Prismite", "Geodeon", "Sharp. Pretty. Heavy."),
    ("shroom", "Capsid", "BLOOM", "mush", (230, 70, 70), (230, 220, 180), "dot", "leaf", "Capsid", "Sporecap", "Mycoroot", "Puffs when hugged."),
    ("puffn", "Pufflet", "FROST", "penguin", (30, 30, 40), (240, 230, 80), "eye", "ice", "Pufflet", "Tuxling", "Emperon", "Waddles into trouble."),
    ("reef", "Reefjaw", "SEA", "shark", (50, 120, 150), (200, 80, 70), "slash", "water", "Reefjaw", "Brinefin", "Maelstrom", "Smiles with too many teeth."),
    ("ashp", "Ashlet", "MYTH", "phoenix", (240, 140, 40), (200, 40, 40), "flame", "fire", "Ashlet", "Cindera", "Solarion", "Burns. Comes back anyway."),
    ("nite", "Nitebat", "DUSK", "bat", (50, 40, 70), (200, 160, 50), "eye", "curse", "Nitebat", "Echofang", "Umbralord", "Sleeps in the speaker grill."),
    ("pinch", "Pinchcrab", "SEA", "crab", (200, 70, 50), (230, 200, 80), "slash", "slash", "Pinchcrab", "Clawtide", "Kingpinch", "Both claws are the good one."),
    ("thorn", "Thornpup", "BLOOM", "wolf", (50, 110, 50), (180, 60, 40), "leaf", "leaf", "Thornpup", "Briarwolf", "Thornking", "Howls. Then plants a tree."),
    ("honey", "Honeybear", "WILD", "bear", (160, 100, 40), (230, 190, 70), "paw", "strike", "Honeybear", "Cloverpaw", "Grizzgold", "Hungry. Always."),
    ("cloud", "Cloudpuff", "SKY", "puff", (230, 230, 240), (140, 180, 220), "star", "wind", "Cloudpuff", "Nimbun", "Stormpuff", "Soft until it rains on you."),
    ("magma", "Magmalisk", "CAVE", "lizard", (220, 70, 30), (40, 30, 28), "flame", "fire", "Magmalisk", "Scorchtail", "Volcaron", "Leaves soot footprints."),
    ("bolt", "Boltmouse", "STORM", "mouse", (250, 230, 70), (50, 50, 180), "bolt", "shock", "Boltmouse", "Ampchu", "Megavolt", "Chews cables for fun."),
    ("grove", "Groveowl", "BLOOM", "owl", (70, 120, 50), (220, 200, 140), "leaf", "leaf", "Groveowl", "Oakhoot", "Canopy Sage", "Wise. Drops acorns on foes."),
    ("snow", "Snowfox", "FROST", "fox", (240, 240, 246), (120, 180, 220), "star", "ice", "Snowfox", "Rimefox", "Aurorox", "Leaves frost hearts."),
    ("hawk", "Stormhawk", "SKY", "owl", (50, 60, 80), (230, 200, 50), "wing", "shock", "Stormhawk", "Cloudbreak", "Tempest King", "Nests in thunderheads."),
    ("cave", "Cavebat", "CAVE", "bat", (90, 70, 50), (200, 160, 80), "eye", "slash", "Cavebat", "Stalafang", "Gloomwing", "Hates flashlights."),
    ("rust", "Rustbit", "TECH", "bot", (180, 90, 40), (60, 60, 70), "bolt", "gun", "Rustbit", "Scrapunit", "Warframe", "Old. Still shooting."),
    ("seed", "Seedlet", "BLOOM", "mush", (180, 200, 70), (80, 120, 40), "leaf", "leaf", "Seedlet", "Sproutling", "Worldtree", "Grows in pockets."),
    ("tide", "Tidepup", "SEA", "dog", (40, 110, 160), (230, 220, 180), "paw", "water", "Tidepup", "Surfmutt", "Seawolf", "Shakes off a whole puddle."),
    ("dusk", "Duskcat", "DUSK", "cat", (40, 30, 50), (180, 80, 200), "eye", "curse", "Duskcat", "Hexpaw", "Nightqueen", "Stares. You lose."),
    ("gold", "Goldgrub", "CAVE", "crab", (220, 180, 50), (90, 70, 30), "star", "strike", "Goldgrub", "Oreclaw", "Vaultking", "Eats coins. Pays them back."),
    ("hare", "Windhare", "SKY", "bunny", (230, 230, 236), (80, 140, 200), "wing", "wind", "Windhare", "Galehop", "Skyhare", "Already gone."),
    ("lava", "Lavapup", "MYTH", "dog", (230, 80, 30), (40, 20, 16), "flame", "fire", "Lavapup", "Magmaw", "Volcdog", "Do not put on the couch."),
    ("crys", "Crystalox", "FROST", "crystal", (180, 230, 255), (70, 110, 180), "star", "ice", "Crystalox", "Shardox", "Glaciox", "Sings when struck."),
    ("hex", "Hexwisp", "DUSK", "slime", (120, 50, 180), (20, 10, 30), "star", "curse", "Hexwisp", "Gloomgel", "Voidwisp", "A sad lamp that bites."),
)

WAVE4_LINES = tuple(
    {"id": s[0], "tag": s[2], "stages": (f"egg_{s[0]}", s[0], f"{s[0]}2", f"{s[0]}3")}
    for s in _SPECS
)
WAVE4_NAMES = {s[0]: s[1] for s in _SPECS}
WAVE4_BLURB = {s[0]: s[11] for s in _SPECS}
WAVE4_LABELS = {}
WAVE4_GEN = []
WAVE4_MOVES = {}
for s in _SPECS:
    lid, _disp, _tag, kind, c0, c1, mark, typ, baby, teen, mega, _blurb = s
    WAVE4_LABELS[f"egg_{lid}"] = f"{baby} Egg"
    WAVE4_LABELS[lid] = baby
    WAVE4_LABELS[f"{lid}2"] = teen
    WAVE4_LABELS[f"{lid}3"] = mega
    WAVE4_GEN.append({"id": f"egg_{lid}", "kind": "egg", "c0": c0, "c1": c1, "mark": mark, "stage": 0})
    WAVE4_GEN.append({"id": lid, "kind": kind, "c0": c0, "c1": c1, "mark": mark, "stage": 0})
    WAVE4_GEN.append({"id": f"{lid}2", "kind": kind, "c0": c0, "c1": tuple(max(0, min(255, v - 20)) for v in c1), "mark": mark, "stage": 1})
    WAVE4_GEN.append({"id": f"{lid}3", "kind": kind, "c0": tuple(max(0, min(255, v + 10)) for v in c0), "c1": c1, "mark": mark, "stage": 2})
    WAVE4_MOVES[lid] = _kit(lid, typ)
WAVE4_GEN = tuple(WAVE4_GEN)

_PALS = (
    ((230, 90, 40), (120, 40, 16)),
    ((50, 160, 190), (20, 70, 100)),
    ((240, 210, 50), (40, 60, 160)),
    ((70, 170, 70), (30, 80, 30)),
    ((180, 230, 240), (50, 110, 160)),
    ((200, 80, 180), (50, 20, 80)),
    ((140, 140, 150), (40, 40, 50)),
    ((220, 160, 50), (90, 50, 20)),
    ((40, 40, 48), (180, 40, 40)),
    ((90, 200, 140), (20, 80, 50)),
    ((200, 70, 50), (80, 20, 16)),
    ((80, 90, 200), (20, 24, 90)),
)
_SHAPES = (
    "beast", "slug", "ghost", "beetle", "flame", "brute", "bird", "serpent",
    "dino", "wing", "ape", "soldier", "fish", "clown", "agent", "armor",
    "drone", "fly", "blob", "skull", "grunt", "elite", "plant",
)
_WEAKS = ("fire", "ice", "water", "shock", "slash", "strike", "holy", "curse", "gun", "leaf", "wind")
_TAGS = ("WILD", "MYTH", "TECH", "SEA", "SKY", "CAVE", "BLOOM", "STORM", "DUSK", "FROST")
_PREFIX = (
    "Ash", "Bog", "Clay", "Dusk", "Ember", "Frost", "Gale", "Hollow", "Iron", "Jade",
    "Knot", "Lurk", "Moss", "Nox", "Oak", "Pale", "Quartz", "Rust", "Shade", "Thorn",
    "Umbra", "Vine", "Wisp", "Yew", "Zinc", "Brine", "Cinder", "Drift", "Echo", "Flint",
    "Gloom", "Haze", "Ivory", "Jolt", "Kite", "Loom",
)
_SUFFIX = (
    "mite", "pup", "bat", "slug", "hawk", "toad", "grub", "wolf", "crab", "moth",
    "drake", "wraith", "knight", "blob", "fiend", "lurk",
)


def _make_foes():
    out = []
    n = 0
    for pre in _PREFIX:
        for suf in _SUFFIX:
            if n >= 120:
                break
            pal = _PALS[n % len(_PALS)]
            shape = _SHAPES[n % len(_SHAPES)]
            tag = _TAGS[n % len(_TAGS)]
            band = n % 4
            hp = 22 + band * 12 + (n % 7)
            atk = 6 + band * 4 + (n % 5)
            defe = 2 + band * 2 + (n % 4)
            out.append(
                {
                    "id": f"w4_{n:03d}",
                    "name": f"{pre}{suf.title()}",
                    "tag": tag,
                    "hp": hp,
                    "atk": atk,
                    "defe": defe,
                    "lo": 7 + band * 5,
                    "hi": 13 + band * 7,
                    "weak": _WEAKS[n % len(_WEAKS)],
                    "band": band,
                    "shape": shape,
                    "c0": pal[0],
                    "c1": pal[1],
                }
            )
            n += 1
        if n >= 120:
            break
    return tuple(out)


WAVE4_ENEMIES = _make_foes()

WAVE4_ITEMS = (
    {"id": "stew", "name": "Hot Stew", "cost": 15, "kind": "food", "hunger": 28, "mood": 8},
    {"id": "dumpling", "name": "Dumpling", "cost": 12, "kind": "food", "hunger": 20, "mood": 8},
    {"id": "noodles", "name": "Noodles", "cost": 14, "kind": "food", "hunger": 24, "mood": 6},
    {"id": "rice", "name": "Rice Bowl", "cost": 10, "kind": "food", "hunger": 18, "mood": 4},
    {"id": "skewer", "name": "Meat Skewer", "cost": 16, "kind": "food", "hunger": 26, "mood": 6},
    {"id": "cake", "name": "Slice Cake", "cost": 18, "kind": "food", "hunger": 14, "mood": 18},
    {"id": "donut", "name": "Donut", "cost": 13, "kind": "food", "hunger": 12, "mood": 16},
    {"id": "waffle", "name": "Waffle", "cost": 14, "kind": "food", "hunger": 18, "mood": 12},
    {"id": "pancake", "name": "Pancake", "cost": 13, "kind": "food", "hunger": 18, "mood": 10},
    {"id": "omelet", "name": "Omelet", "cost": 15, "kind": "food", "hunger": 22, "mood": 8},
    {"id": "corn", "name": "Roast Corn", "cost": 9, "kind": "food", "hunger": 16, "mood": 6},
    {"id": "carrot", "name": "Carrot", "cost": 7, "kind": "food", "hunger": 12, "mood": 6},
    {"id": "grape", "name": "Grapes", "cost": 10, "kind": "food", "hunger": 12, "mood": 10},
    {"id": "melon", "name": "Melon", "cost": 16, "kind": "food", "hunger": 20, "mood": 12},
    {"id": "mango", "name": "Mango", "cost": 14, "kind": "food", "hunger": 16, "mood": 14},
    {"id": "lemon", "name": "Lemon Drop", "cost": 8, "kind": "food", "hunger": 8, "mood": 12},
    {"id": "jam", "name": "Berry Jam", "cost": 11, "kind": "food", "hunger": 14, "mood": 12},
    {"id": "cheese", "name": "Cheese", "cost": 12, "kind": "food", "hunger": 16, "mood": 8},
    {"id": "pretzel", "name": "Pretzel", "cost": 10, "kind": "food", "hunger": 14, "mood": 8},
    {"id": "popcorn", "name": "Popcorn", "cost": 9, "kind": "food", "hunger": 10, "mood": 14},
    {"id": "icecream", "name": "Ice Cream", "cost": 15, "kind": "food", "hunger": 10, "mood": 20},
    {"id": "popsicle", "name": "Popsicle", "cost": 8, "kind": "food", "hunger": 6, "mood": 16},
    {"id": "cocoa", "name": "Hot Cocoa", "cost": 12, "kind": "food", "hunger": 10, "mood": 16},
    {"id": "tea", "name": "Leaf Tea", "cost": 9, "kind": "food", "hunger": 6, "mood": 14},
    {"id": "juice", "name": "Fruit Juice", "cost": 10, "kind": "food", "hunger": 10, "mood": 12},
    {"id": "smoothie", "name": "Smoothie", "cost": 16, "kind": "food", "hunger": 18, "mood": 14},
    {"id": "bento", "name": "Bento", "cost": 20, "kind": "food", "hunger": 34, "mood": 10},
    {"id": "hotdog", "name": "Hot Dog", "cost": 13, "kind": "food", "hunger": 22, "mood": 8},
    {"id": "burrito", "name": "Burrito", "cost": 16, "kind": "food", "hunger": 30, "mood": 8},
    {"id": "soup", "name": "Miso Soup", "cost": 11, "kind": "food", "hunger": 16, "mood": 8},
    {"id": "salad", "name": "Salad", "cost": 12, "kind": "food", "hunger": 14, "mood": 10},
    {"id": "kebab", "name": "Kebab", "cost": 17, "kind": "food", "hunger": 28, "mood": 8},
    {"id": "mochi", "name": "Mochi", "cost": 12, "kind": "food", "hunger": 10, "mood": 16},
    {"id": "taiyaki", "name": "Taiyaki", "cost": 14, "kind": "food", "hunger": 18, "mood": 12},
    {"id": "dango", "name": "Dango", "cost": 11, "kind": "food", "hunger": 12, "mood": 14},
    {"id": "pudding", "name": "Pudding", "cost": 13, "kind": "food", "hunger": 12, "mood": 16},
    {"id": "brownie", "name": "Brownie", "cost": 14, "kind": "food", "hunger": 14, "mood": 16},
    {"id": "churro", "name": "Churro", "cost": 12, "kind": "food", "hunger": 12, "mood": 14},
    {"id": "bagel", "name": "Bagel", "cost": 10, "kind": "food", "hunger": 16, "mood": 6},
    {"id": "croissant", "name": "Croissant", "cost": 13, "kind": "food", "hunger": 16, "mood": 10},
    {"id": "pie", "name": "Pocket Pie", "cost": 15, "kind": "food", "hunger": 22, "mood": 10},
    {"id": "sausage", "name": "Sausage", "cost": 14, "kind": "food", "hunger": 24, "mood": 4},
    {"id": "eggtoast", "name": "Egg Toast", "cost": 12, "kind": "food", "hunger": 20, "mood": 8},
    {"id": "nuts", "name": "Trail Nuts", "cost": 9, "kind": "food", "hunger": 14, "mood": 6},
    {"id": "jerky", "name": "Jerky", "cost": 15, "kind": "food", "hunger": 22, "mood": 2},
    {"id": "kelp", "name": "Kelp Chew", "cost": 8, "kind": "food", "hunger": 10, "mood": 8},
    {"id": "pepper", "name": "Hot Pepper", "cost": 9, "kind": "food", "hunger": 6, "mood": 14},
    {"id": "coconut", "name": "Coconut", "cost": 14, "kind": "food", "hunger": 18, "mood": 10},
    {"id": "plush", "name": "Plush Pal", "cost": 18, "kind": "play", "mood": 28},
    {"id": "frisbee", "name": "Frisbee", "cost": 16, "kind": "play", "mood": 22, "str": 1},
    {"id": "kite", "name": "Tiny Kite", "cost": 14, "kind": "play", "mood": 20},
    {"id": "drum", "name": "Toy Drum", "cost": 15, "kind": "play", "mood": 24},
    {"id": "bubble", "name": "Bubbles", "cost": 10, "kind": "play", "mood": 18},
    {"id": "balm", "name": "Heal Balm", "cost": 16, "kind": "heal", "hygiene": 45, "mood": 6},
    {"id": "tonic", "name": "Tonic", "cost": 22, "kind": "heal", "hygiene": 70, "mood": 8},
    {"id": "bandage", "name": "Bandage", "cost": 9, "kind": "heal", "hygiene": 30},
    {"id": "serum", "name": "Glow Serum", "cost": 36, "kind": "heal", "hygiene": 100, "clear_poop": True, "mood": 12},
    {"id": "dumbbell2", "name": "Iron Ring", "cost": 32, "kind": "train", "str": 9, "hunger": -5},
    {"id": "sprint", "name": "Sprint Can", "cost": 20, "kind": "train", "str": 5, "hunger": -2},
    {"id": "focusgem", "name": "Focus Gem", "cost": 28, "kind": "chip"},
    {"id": "manual", "name": "Field Manual", "cost": 26, "kind": "chip"},
    {"id": "clover", "name": "Four Clover", "cost": 22, "kind": "luck"},
    {"id": "dice", "name": "Lucky Dice", "cost": 20, "kind": "luck"},
    {"id": "compass", "name": "Brass Compass", "cost": 24, "kind": "map"},
    {"id": "flare", "name": "Signal Flare", "cost": 14, "kind": "flee"},
    {"id": "cloakdust", "name": "Cloak Dust", "cost": 16, "kind": "flee"},
    {"id": "sunchew", "name": "Sun Chew", "cost": 50, "kind": "hatch", "shave": 40 * 60},
    {"id": "moonchew", "name": "Moon Chew", "cost": 75, "kind": "hatch", "shave": 80 * 60},
    {"id": "starchew", "name": "Star Chew", "cost": 90, "kind": "hatch", "shave": 100 * 60},
)

WAVE4_HATCH = (
    {"id": "hum", "name": "Hum", "cost": 9, "cd": 200, "shave": 15 * 60, "desc": "A low hum. 15 min gone."},
    {"id": "sunbath", "name": "Sunbath", "cost": 16, "cd": 420, "shave": 24 * 60, "desc": "Park it in a beam. 24 min."},
    {"id": "drizzle", "name": "Drizzle", "cost": 14, "cd": 360, "shave": 20 * 60, "desc": "A warm mist. 20 min."},
    {"id": "thunder", "name": "Thunder Tap", "cost": 22, "cd": 480, "shave": 32 * 60, "desc": "A careful jolt. 32 min."},
    {"id": "lull", "name": "Deep Lull", "cost": 30, "cd": 600, "shave": 45 * 60, "desc": "They sleep hard. 45 min."},
    {"id": "forge", "name": "Forge Heat", "cost": 42, "cd": 720, "shave": 60 * 60, "desc": "Bake a full hour off."},
    {"id": "aurora", "name": "Aurora", "cost": 70, "cd": 900, "shave": 85 * 60, "desc": "Lights in the shell. 85 min."},
    {"id": "eclipse", "name": "Eclipse", "cost": 95, "cd": 240, "shave": 110 * 60, "desc": "A dark snack. Almost two hours."},
)

WAVE4_GEAR = (
    {"id": "goggles", "name": "Storm Goggles", "slot": "head", "cost": 30, "atk": 5, "crit": 6, "blurb": "+atk  +crit"},
    {"id": "tiara", "name": "Moon Tiara", "slot": "head", "cost": 44, "hp": 16, "luck": 8, "blurb": "+hp  +luck"},
    {"id": "hood", "name": "Trail Hood", "slot": "head", "cost": 26, "defe": 7, "xp": 8, "blurb": "+def  +xp"},
    {"id": "mask", "name": "Hex Mask", "slot": "head", "cost": 38, "atk": 8, "crit": 5, "blurb": "+atk  +crit"},
    {"id": "scarf", "name": "Wind Scarf", "slot": "back", "cost": 28, "defe": 6, "luck": 6, "blurb": "+def  +luck"},
    {"id": "banner", "name": "Raid Banner", "slot": "back", "cost": 46, "hp": 12, "atk": 6, "blurb": "+hp  +atk"},
    {"id": "satchel", "name": "Snack Satchel", "slot": "back", "cost": 24, "hp": 10, "hatch": 12, "blurb": "+hp  hatch"},
    {"id": "cape2", "name": "Dawn Cape", "slot": "back", "cost": 50, "defe": 10, "luck": 8, "blurb": "+def  +luck"},
    {"id": "bell", "name": "Charm Bell", "slot": "held", "cost": 22, "luck": 10, "xp": 8, "blurb": "+luck  +xp"},
    {"id": "tome", "name": "Field Tome", "slot": "held", "cost": 36, "hp": 8, "xp": 12, "blurb": "+hp  +xp"},
    {"id": "fang2", "name": "Twin Fang", "slot": "held", "cost": 40, "atk": 13, "blurb": "+13 atk"},
    {"id": "prism", "name": "Prism Core", "slot": "held", "cost": 48, "hp": 12, "crit": 10, "blurb": "+hp  +crit"},
    {"id": "socks", "name": "Wool Socks", "slot": "feet", "cost": 18, "hatch": 14, "defe": 4, "blurb": "hatch  +def"},
    {"id": "skates", "name": "Ice Skates", "slot": "feet", "cost": 32, "atk": 7, "crit": 5, "blurb": "+atk  +crit"},
    {"id": "hooves", "name": "Iron Hooves", "slot": "feet", "cost": 34, "defe": 12, "blurb": "+12 def"},
    {"id": "pads", "name": "Trail Pads", "slot": "feet", "cost": 26, "luck": 8, "xp": 6, "blurb": "+luck  +xp"},
)

WAVE4_BOSSES = (
    {"id": "raid_moth", "name": "Lantern Queen", "hp": 300, "atk": 24, "defe": 13, "weak": "fire", "shape": "wing", "c0": (90, 40, 120), "c1": (230, 180, 60), "lo": 44, "hi": 74, "band": 2},
    {"id": "raid_reef", "name": "Reef Tyrant", "hp": 360, "atk": 27, "defe": 16, "weak": "shock", "shape": "fish", "c0": (30, 90, 130), "c1": (200, 60, 50), "lo": 50, "hi": 84, "band": 3},
    {"id": "raid_ore", "name": "Geode Colossus", "hp": 420, "atk": 26, "defe": 22, "weak": "strike", "shape": "armor", "c0": (180, 160, 210), "c1": (70, 50, 110), "lo": 58, "hi": 92, "band": 3},
    {"id": "raid_storm", "name": "Thunder Roc", "hp": 380, "atk": 30, "defe": 15, "weak": "ice", "shape": "bird", "c0": (50, 60, 90), "c1": (240, 210, 50), "lo": 54, "hi": 88, "band": 3},
    {"id": "raid_bloom", "name": "Canopy Horror", "hp": 340, "atk": 25, "defe": 18, "weak": "fire", "shape": "plant", "c0": (40, 120, 50), "c1": (180, 60, 40), "lo": 48, "hi": 80, "band": 2},
    {"id": "raid_hex", "name": "Hex Monarch", "hp": 400, "atk": 31, "defe": 17, "weak": "holy", "shape": "ghost", "c0": (40, 20, 70), "c1": (180, 60, 200), "lo": 60, "hi": 96, "band": 3},
    {"id": "raid_forge", "name": "Forge Titan", "hp": 450, "atk": 29, "defe": 21, "weak": "water", "shape": "brute", "c0": (200, 70, 30), "c1": (40, 24, 16), "lo": 66, "hi": 104, "band": 3},
    {"id": "raid_frost", "name": "Glacier Wyrm", "hp": 410, "atk": 28, "defe": 20, "weak": "fire", "shape": "serpent", "c0": (160, 220, 240), "c1": (40, 80, 130), "lo": 58, "hi": 94, "band": 3},
    {"id": "raid_rail", "name": "Rail Tyrant", "hp": 370, "atk": 32, "defe": 14, "weak": "shock", "shape": "drone", "c0": (140, 150, 170), "c1": (40, 80, 200), "lo": 56, "hi": 90, "band": 3},
    {"id": "raid_grove", "name": "Root Sovereign", "hp": 430, "atk": 27, "defe": 19, "weak": "fire", "shape": "plant", "c0": (60, 140, 50), "c1": (90, 60, 30), "lo": 62, "hi": 98, "band": 3},
    {"id": "raid_dusk", "name": "Dusk Leviathan", "hp": 480, "atk": 33, "defe": 20, "weak": "holy", "shape": "serpent", "c0": (30, 20, 50), "c1": (160, 50, 180), "lo": 72, "hi": 112, "band": 3},
    {"id": "raid_sun", "name": "Sun Maw", "hp": 500, "atk": 34, "defe": 18, "weak": "water", "shape": "flame", "c0": (250, 160, 40), "c1": (200, 40, 20), "lo": 76, "hi": 118, "band": 3},
)

WAVE4_PLACES = {
    "WILD": ("Meadow Cut", "Briar Lane", "Honey Hollow"),
    "MYTH": ("Ash Spire", "Hoard Vault", "Sun Gate"),
    "TECH": ("Scrap Yard", "Rail Hub", "Core Pit"),
    "SEA": ("Tide Shelf", "Reef Cut", "Brine Hollow"),
    "SKY": ("Cloud Stair", "Nest Cliff", "Gale Pass"),
    "CAVE": ("Quartz Hall", "Drip Gallery", "Ore Heart"),
    "BLOOM": ("Fern Walk", "Canopy", "Root Well"),
    "STORM": ("Spark Field", "Ion Ridge", "Bolt Nest"),
    "DUSK": ("Lamp Alley", "Hex Marsh", "Night Veil"),
    "FROST": ("Rime Path", "White Hollow", "Glacier Lip"),
}

WAVE4_FOES = {
    "WILD": ("Ashmite", "Thornwolf", "Honeybear Shade"),
    "MYTH": ("Cinderdrake", "Solaroc Shade", "Sun Maw"),
    "TECH": ("Ironbit", "Railcore", "Scrapunit"),
    "SEA": ("Brookling", "Reefjaw", "Tide Tyrant"),
    "SKY": ("Galekit", "Stormhawk", "Cloud Horror"),
    "CAVE": ("Pebblit", "Geode Shade", "Ore Colossus"),
    "BLOOM": ("Mossbun", "Capsid", "Canopy Horror"),
    "STORM": ("Sparkpup", "Voltmutt", "Thunder Roc"),
    "DUSK": ("Duskmoth", "Hexwisp", "Nightveil"),
    "FROST": ("Chillix", "Snowfox", "Glacier Wyrm"),
}
