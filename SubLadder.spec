# SubLadder.spec — v2.4
# PyInstaller spec file for Sub Ladder
#
# Usage (from the SubLadder/ project root):
#   pip install pyinstaller pillow pygame
#   pyinstaller SubLadder.spec
#
# Output: dist/SubLadder/SubLadder(.exe on Windows)

block_cipher = None

added_files = [
    ("data/languages",            "data/languages"),
    ("data/questions",            "data/questions"),
    ("data/achievements.json",    "data"),
    ("data/pictures/backgrounds", "data/pictures/backgrounds"),
    ("data/pictures/logos",       "data/pictures/logos"),
    ("data/pictures/flags",       "data/pictures/flags"),
    ("data/sound/music",          "data/sound/music"),
    ("data/sound/jingles",        "data/sound/jingles"),
]

a = Analysis(
    ["run.py"],
    pathex=["."],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        # game package
        "main", "constants", "game_state", "utils",
        "asset_manager", "first_run",
        # screens
        "screens", "screens.menu", "screens.game_screen",
        "screens.recap", "screens.profile", "screens.top_scores",
        "screens.achievements", "screens.options",
        # singleplayer
        "singleplayer", "singleplayer.logic", "singleplayer.anticheat",
        # multiplayer stubs
        "multiplayer", "multiplayer.server", "multiplayer.p2p",
        "multiplayer.ranked", "multiplayer.anticheat",
        # third-party
        "PIL", "PIL.Image", "PIL.ImageTk", "PIL.ImageDraw", "PIL.ImageFont",
        "pygame", "pygame.mixer",
        "tkinter", "tkinter.font", "tkinter.simpledialog",
        "tkinter.messagebox", "tkinter.filedialog",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="SubLadder",
    debug=False,
    strip=False,
    upx=True,
    console=False,
    # icon="data/pictures/logos/icon_trophy.ico",
)

coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=False, upx=True, upx_exclude=[],
    name="SubLadder",
)


