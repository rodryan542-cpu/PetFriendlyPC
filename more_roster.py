"""More lines, foods, enemies. Merged by game_data."""

MORE_LINES = (
    {"id": "squirt", "tag": "POKEMON", "stages": ("egg_squirt", "squirtle", "wartortle", "blastoise")},
    {"id": "yoshi", "tag": "NINTENDO", "stages": ("egg_yoshi", "yoshi", "yoshi2")},
    {"id": "deku", "tag": "HERO", "stages": ("egg_deku", "deku", "deku2")},
    {"id": "ichigo", "tag": "BLEACH", "stages": ("egg_ichigo", "ichigo", "ichigo2")},
    {"id": "vegeta", "tag": "DBZ", "stages": ("egg_vegeta", "vegeta", "vegeta2")},
    {"id": "sanji", "tag": "ONE PIECE", "stages": ("egg_sanji", "sanji", "sanji2")},
    {"id": "bunny", "tag": "ANIMAL", "stages": ("egg_bunny", "bunny", "bunny2")},
    {"id": "frog", "tag": "ANIMAL", "stages": ("egg_frog", "tadpole", "frog")},
)

MORE_NAMES = {
    "squirt": "Squirtle",
    "yoshi": "Yoshi",
    "deku": "Deku",
    "ichigo": "Ichigo",
    "vegeta": "Vegeta",
    "sanji": "Sanji",
    "bunny": "Bunny",
    "frog": "Frog",
}

MORE_BLURB = {
    "squirt": "Blue shell. Water first.",
    "yoshi": "Green dino. Eats anything.",
    "deku": "Smash. Notes in a book.",
    "ichigo": "Orange hair. Big blade.",
    "vegeta": "Pride. Never second.",
    "sanji": "Kicks. Cooks. Smokes.",
    "bunny": "Hop. Soft. Steals carrots.",
    "frog": "Ribbit. Loves rain.",
}

MORE_LABELS = {
    "egg_squirt": "Squirt Egg",
    "squirtle": "Squirtle",
    "wartortle": "Wartortle",
    "blastoise": "Blastoise",
    "egg_yoshi": "Yoshi Egg",
    "yoshi": "Yoshi",
    "yoshi2": "Yoshi+",
    "egg_deku": "Hero Egg",
    "deku": "Deku",
    "deku2": "Deku+",
    "egg_ichigo": "Soul Egg",
    "ichigo": "Ichigo",
    "ichigo2": "Ichigo+",
    "egg_vegeta": "Pride Egg",
    "vegeta": "Vegeta",
    "vegeta2": "Majin Vegeta",
    "egg_sanji": "Cook Egg",
    "sanji": "Sanji",
    "sanji2": "Sanji+",
    "egg_bunny": "Bunny Egg",
    "bunny": "Bunny",
    "bunny2": "Bunny+",
    "egg_frog": "Frog Egg",
    "tadpole": "Tadpole",
    "frog": "Frog",
}

MORE_FORMS = {k: f"{k}.png" for k in MORE_LABELS}

MORE_GEN = (
    {"id": "egg_squirt", "kind": "egg", "c0": (70, 160, 200), "c1": (40, 90, 140), "mark": "hole", "stage": 0},
    {"id": "squirtle", "kind": "turtle", "c0": (70, 160, 200), "c1": (180, 160, 90), "mark": "hole", "stage": 0},
    {"id": "wartortle", "kind": "turtle", "c0": (50, 130, 180), "c1": (160, 80, 50), "mark": "hole", "stage": 1},
    {"id": "blastoise", "kind": "turtle", "c0": (40, 90, 150), "c1": (180, 180, 190), "mark": "hole", "stage": 2},
    {"id": "egg_yoshi", "kind": "egg", "c0": (70, 190, 70), "c1": (220, 70, 70), "mark": "star", "stage": 0},
    {"id": "yoshi", "kind": "yoshi", "c0": (70, 190, 70), "c1": (220, 70, 70), "mark": "star", "stage": 1},
    {"id": "yoshi2", "kind": "yoshi", "c0": (240, 140, 180), "c1": (70, 190, 70), "mark": "star", "stage": 2},
    {"id": "egg_deku", "kind": "egg", "c0": (50, 160, 90), "c1": (200, 40, 40), "mark": "star", "stage": 0},
    {"id": "deku", "kind": "deku", "c0": (50, 160, 90), "c1": (40, 40, 48), "mark": "star", "stage": 1},
    {"id": "deku2", "kind": "deku", "c0": (40, 40, 48), "c1": (50, 160, 90), "mark": "star", "stage": 2},
    {"id": "egg_ichigo", "kind": "egg", "c0": (230, 120, 40), "c1": (30, 30, 36), "mark": "sword", "stage": 0},
    {"id": "ichigo", "kind": "bleach", "c0": (230, 120, 40), "c1": (30, 30, 36), "mark": "sword", "stage": 1},
    {"id": "ichigo2", "kind": "bleach", "c0": (230, 80, 30), "c1": (200, 40, 40), "mark": "sword", "stage": 2},
    {"id": "egg_vegeta", "kind": "egg", "c0": (40, 50, 140), "c1": (230, 200, 50), "mark": "star", "stage": 0},
    {"id": "vegeta", "kind": "vegeta", "c0": (40, 50, 140), "c1": (30, 30, 36), "mark": "star", "stage": 1},
    {"id": "vegeta2", "kind": "vegeta", "c0": (160, 40, 90), "c1": (230, 200, 50), "mark": "star", "stage": 2},
    {"id": "egg_sanji", "kind": "egg", "c0": (230, 180, 50), "c1": (40, 40, 48), "mark": "flame", "stage": 0},
    {"id": "sanji", "kind": "cook", "c0": (230, 180, 50), "c1": (40, 40, 48), "mark": "flame", "stage": 1},
    {"id": "sanji2", "kind": "cook", "c0": (40, 40, 48), "c1": (230, 180, 50), "mark": "flame", "stage": 2},
    {"id": "egg_bunny", "kind": "egg", "c0": (240, 230, 220), "c1": (230, 140, 160), "mark": "paw", "stage": 0},
    {"id": "bunny", "kind": "bunny", "c0": (240, 230, 220), "c1": (230, 140, 160), "mark": "paw", "stage": 1},
    {"id": "bunny2", "kind": "bunny", "c0": (230, 140, 160), "c1": (240, 230, 220), "mark": "paw", "stage": 2},
    {"id": "egg_frog", "kind": "egg", "c0": (70, 180, 70), "c1": (240, 220, 80), "mark": "eye", "stage": 0},
    {"id": "tadpole", "kind": "frog", "c0": (40, 90, 70), "c1": (240, 220, 80), "mark": "eye", "stage": 0},
    {"id": "frog", "kind": "frog", "c0": (70, 180, 70), "c1": (240, 220, 80), "mark": "eye", "stage": 1},
)


def _m(mid, name, typ, buy, up, pow_, grow):
    return {"id": mid, "name": name, "typ": typ, "buy": buy, "up": up, "pow": pow_, "grow": grow}


MORE_MOVES = {
    "squirt": (
        _m("sq_tackle", "Tackle", "strike", 12, 10, 11, 4),
        _m("sq_bubble", "Bubble", "water", 16, 12, 14, 5),
        _m("sq_withdraw", "Withdraw", "strike", 14, 11, 10, 4),
        _m("sq_watergun", "Water Gun", "water", 22, 14, 18, 6),
        _m("sq_bite", "Bite", "slash", 24, 15, 19, 6),
        _m("sq_surf", "Surf", "water", 40, 20, 26, 7),
        _m("sq_cannon", "Hydro Pump", "water", 54, 24, 32, 8),
        _m("sq_skull", "Skull Bash", "strike", 66, 28, 36, 8),
    ),
    "yoshi": (
        _m("yo_chomp", "Egg Chomp", "strike", 14, 11, 12, 4),
        _m("yo_tongue", "Tongue", "strike", 16, 12, 14, 5),
        _m("yo_flutter", "Flutter", "wind", 18, 13, 15, 5),
        _m("yo_egg", "Egg Throw", "strike", 24, 15, 19, 6),
        _m("yo_stomp", "Stomp", "strike", 28, 16, 21, 6),
        _m("yo_ground", "Ground Pound", "strike", 40, 20, 26, 7),
        _m("yo_fire", "Fire Spit", "fire", 48, 22, 29, 7),
        _m("yo_rainbow", "Rainbow Egg", "holy", 64, 26, 35, 8),
    ),
    "deku": (
        _m("dk_smash", "Smash", "strike", 14, 11, 13, 4),
        _m("dk_shoot", "Air Force", "wind", 18, 12, 15, 5),
        _m("dk_kick", "St. Louis", "strike", 20, 13, 17, 5),
        _m("dk_detroit", "Detroit", "strike", 28, 16, 22, 6),
        _m("dk_blackwhip", "Blackwhip", "curse", 34, 18, 24, 6),
        _m("dk_float", "Float Kick", "wind", 42, 20, 27, 7),
        _m("dk_fajin", "Fa Jin", "strike", 52, 24, 32, 8),
        _m("dk_united", "United States", "holy", 72, 30, 38, 8),
    ),
    "ichigo": (
        _m("ic_slash", "Getsuga", "slash", 16, 12, 14, 5),
        _m("ic_guard", "Guard Break", "strike", 14, 11, 12, 4),
        _m("ic_flash", "Shunpo", "slash", 20, 13, 16, 5),
        _m("ic_moon", "Getsuga Juu", "slash", 28, 16, 22, 6),
        _m("ic_mask", "Hollow Mask", "curse", 36, 18, 25, 7),
        _m("ic_bankai", "Bankai", "slash", 46, 22, 30, 7),
        _m("ic_mugetsu", "Mugetsu", "dark", 58, 26, 34, 8),
        _m("ic_true", "True Slash", "holy", 74, 30, 39, 8),
    ),
    "vegeta": (
        _m("vg_galick", "Galick Gun", "shock", 16, 12, 15, 5),
        _m("vg_rush", "Pride Rush", "strike", 14, 11, 13, 4),
        _m("vg_kick", "Dirty Kick", "strike", 18, 13, 16, 5),
        _m("vg_final", "Final Flash", "shock", 30, 17, 23, 6),
        _m("vg_bang", "Big Bang", "fire", 40, 20, 27, 7),
        _m("vg_ss", "SS Burst", "strike", 48, 22, 30, 7),
        _m("vg_finalflash", "Final Shine", "holy", 58, 26, 34, 8),
        _m("vg_ego", "Ultra Ego", "curse", 76, 30, 40, 9),
    ),
    "sanji": (
        _m("sj_kick", "Collier", "strike", 14, 11, 13, 4),
        _m("sj_diable", "Diable Jambe", "fire", 20, 13, 17, 5),
        _m("sj_concasse", "Concasse", "strike", 24, 15, 19, 6),
        _m("sj_flot", "Flot", "wind", 22, 14, 16, 5),
        _m("sj_mutton", "Mutton Shot", "strike", 32, 18, 23, 6),
        _m("sj_party", "Party Table", "fire", 42, 20, 27, 7),
        _m("sj_ifrit", "Ifrit Jambe", "fire", 54, 24, 33, 8),
        _m("sj_hell", "Hell Memories", "fire", 70, 28, 38, 8),
    ),
    "bunny": (
        _m("bn_hop", "Hop", "strike", 12, 10, 11, 4),
        _m("bn_kick", "Bunny Kick", "strike", 16, 12, 14, 5),
        _m("bn_nibble", "Nibble", "slash", 14, 11, 12, 4),
        _m("bn_thump", "Thump", "strike", 20, 13, 16, 5),
        _m("bn_dash", "Dash", "wind", 26, 16, 20, 6),
        _m("bn_carrot", "Carrot Toss", "leaf", 32, 17, 22, 6),
        _m("bn_moon", "Moon Hop", "holy", 46, 22, 29, 7),
        _m("bn_stampede", "Stampede", "strike", 62, 26, 34, 8),
    ),
    "frog": (
        _m("fr_ribbit", "Ribbit", "water", 12, 10, 10, 4),
        _m("fr_tongue", "Tongue", "strike", 16, 12, 14, 5),
        _m("fr_hop", "Hop", "strike", 14, 11, 12, 4),
        _m("fr_splash", "Splash", "water", 20, 13, 16, 5),
        _m("fr_rain", "Rain Dance", "water", 26, 16, 18, 6),
        _m("fr_swallow", "Swallow", "strike", 34, 18, 23, 6),
        _m("fr_storm", "Pond Storm", "shock", 48, 22, 29, 7),
        _m("fr_king", "Frog King", "holy", 64, 26, 35, 8),
    ),
}

MORE_ITEMS = (
    {"id": "apple", "name": "Apple", "cost": 8, "kind": "food", "hunger": 14, "mood": 6},
    {"id": "bread", "name": "Bread", "cost": 9, "kind": "food", "hunger": 16, "mood": 2},
    {"id": "sushi", "name": "Sushi", "cost": 16, "kind": "food", "hunger": 22, "mood": 10},
    {"id": "curry", "name": "Curry", "cost": 18, "kind": "food", "hunger": 32, "mood": 8},
    {"id": "milk", "name": "Warm Milk", "cost": 10, "kind": "food", "hunger": 12, "mood": 10},
    {"id": "cookie", "name": "Cookie", "cost": 11, "kind": "food", "hunger": 10, "mood": 14},
    {"id": "peach", "name": "Peach", "cost": 12, "kind": "food", "hunger": 14, "mood": 12},
    {"id": "taco", "name": "Taco", "cost": 14, "kind": "food", "hunger": 24, "mood": 8},
)

MORE_ENEMIES = (
    {"id": "nomu", "name": "Nomu", "tag": "HERO", "hp": 36, "atk": 12, "defe": 5, "lo": 12, "hi": 18, "weak": "fire", "band": 0, "shape": "brute", "c0": (40, 40, 70), "c1": (180, 40, 40)},
    {"id": "thug_h", "name": "Villain", "tag": "HERO", "hp": 26, "atk": 8, "defe": 3, "lo": 8, "hi": 14, "weak": "strike", "band": 0, "shape": "soldier", "c0": (40, 40, 48), "c1": (160, 40, 40)},
    {"id": "nomu2", "name": "High Nomu", "tag": "HERO", "hp": 50, "atk": 16, "defe": 8, "lo": 16, "hi": 25, "weak": "holy", "band": 1, "shape": "ape", "c0": (70, 40, 90), "c1": (30, 16, 40)},
    {"id": "nomu3", "name": "Near High", "tag": "HERO", "hp": 58, "atk": 18, "defe": 8, "lo": 18, "hi": 28, "weak": "fire", "band": 2, "shape": "wing", "c0": (30, 30, 40), "c1": (200, 40, 40)},
    {"id": "afo", "name": "AFO Shade", "tag": "HERO", "hp": 70, "atk": 22, "defe": 10, "lo": 24, "hi": 36, "weak": "holy", "band": 3, "shape": "skull", "c0": (20, 16, 22), "c1": (180, 30, 40)},
    {"id": "hollow", "name": "Hollow", "tag": "BLEACH", "hp": 28, "atk": 9, "defe": 3, "lo": 9, "hi": 14, "weak": "holy", "band": 0, "shape": "skull", "c0": (230, 230, 220), "c1": (40, 40, 48)},
    {"id": "menos", "name": "Menos", "tag": "BLEACH", "hp": 40, "atk": 13, "defe": 6, "lo": 13, "hi": 20, "weak": "holy", "band": 1, "shape": "ghost", "c0": (30, 30, 36), "c1": (200, 40, 40)},
    {"id": "adjuchas", "name": "Adjuchas", "tag": "BLEACH", "hp": 48, "atk": 16, "defe": 7, "lo": 16, "hi": 25, "weak": "slash", "band": 2, "shape": "beast", "c0": (80, 70, 60), "c1": (200, 40, 40)},
    {"id": "espada", "name": "Espada", "tag": "BLEACH", "hp": 62, "atk": 20, "defe": 9, "lo": 22, "hi": 34, "weak": "holy", "band": 3, "shape": "agent", "c0": (20, 20, 24), "c1": (200, 40, 40)},
    {"id": "arrancar", "name": "Arrancar", "tag": "BLEACH", "hp": 36, "atk": 14, "defe": 5, "lo": 14, "hi": 21, "weak": "slash", "band": 1, "shape": "soldier", "c0": (230, 230, 230), "c1": (30, 30, 36)},
)

MORE_PLACES = {
    "HERO": ("UA High", "Kamino", "Musutafu"),
    "BLEACH": ("Soul Society", "Hueco Mundo", "Karakura"),
}

MORE_FOES = {
    "HERO": ("Villain", "Nomu", "AFO Shade"),
    "BLEACH": ("Hollow", "Menos", "Espada"),
}
