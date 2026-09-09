# PetFriendlyPC

A Windows desktop pet. It walks on your second monitor.

## Run

Double-click `PetFriendlyPC.exe` (in `dist/PetFriendlyPC/` after a build).

Or from source:

```
pythonw digimon_pet.py
```

Save data is `state.json` next to the exe (or next to the scripts if you run from source).

## Grind

One starter is free. Extra partners cost millions. Shop, gear, hatch tools, and moves are expensive. Each move upgrade costs more than the last.

## Build the exe

```
pip install pyinstaller pillow numpy
pyinstaller --noconfirm --clean --windowed --name PetFriendlyPC --add-data "sprites;sprites" --add-data "ui;ui" digimon_pet.py
```

The launcher is `dist/PetFriendlyPC/PetFriendlyPC.exe`.
