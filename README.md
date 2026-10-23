# Sub Ladder 🎯

A **"Who Wants to Be a Millionaire?"** style quiz game built with Python + tkinter,
designed for streamers (Twitch / YouTube). Prizes are measured in **subs**.

---

## Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the game
python run.py
```

> **Linux**: if tkinter is missing → `sudo apt install python3-tk`

---

## Project structure

```
SubLadder/
├── run.py                  ← launcher (start here)
├── requirements.txt
├── CHANGELOG.md
├── README.md
├── SubLadder.spec          ← PyInstaller build config
├── build_windows.bat       ← Windows build script
├── build.sh                ← Linux / macOS build script
├── BUILD.md                ← detailed build instructions
│
├── game/                   ← Python source package
│   ├── __init__.py
│   ├── game.py             ← main application
│   ├── first_run.py        ← first-launch wizard
│   └── asset_manager.py    ← images, sounds, asset generation
│
└── data/                   ← assets & config (no .py files)
    ├── data.json           ← assets/config shipped with the game
    ├── languages/
    │   ├── en.json         ← English UI strings + questions_file pointer
    │   └── fr.json         ← French UI strings + questions_file pointer
    ├── questions/
    │   ├── en_questions.json
    │   └── fr_questions.json
    ├── pictures/
    │   ├── backgrounds/    ← menu.png, bg_q1_5.png, bg_q6_10.png, bg_q11_15.png
    │   ├── logos/          ← icon PNGs for UI elements
    │   └── flags/          ← flag thumbnails (en.png, fr.png, …)
    └── sound/
        ├── music/          ← menu.wav, music_q1_5.wav, music_q6_10.wav, music_q11_15.wav
        └── jingles/        ← correct.wav, wrong.wav, safe_haven.wav, win.wav, …
```

User-writable state is stored in `%APPDATA%\SubLadder` on Windows, including `data.json`, `achievements.json`, avatars, and the anti-cheat log.

> **Missing assets** are generated automatically at first launch when needed.
> gradients / WAV tones). Replace them with real assets at any time — the game
> picks them up on next start.

---

## Game modes

| Mode | Description | Unlock |
|---|---|---|
| **Easy** | Easier questions, appears at lower levels | Always available |
| **Normal** | Standard difficulty | Always available |
| **Hard** | Harder questions at earlier levels | Always available |
| **Legendary** 🔒 | Only hardest questions, brutal pace | Win a Hard game |

---

## Adding a language

1. Copy `data/languages/en.json` → `data/languages/xx.json`
2. Set `"code"`, `"name"` and `"questions_file"` in the new file
3. Translate all strings in the `"ui"` section
4. Create the matching `data/questions/xx_questions.json`
5. Optionally add `data/pictures/flags/xx.png` (64×40 px)

The game discovers language files automatically — no code change needed.

---

## Adding questions

Edit the relevant `data/questions/xx_questions.json`.
Each question follows this schema:

```json
{
  "id":            "en_Q999",
  "level_easy":    5,
  "level_normal":  8,
  "level_hard":    12,
  "level_legendary": 3,
  "theme":         "science",
  "question":      "What is the chemical symbol for Gold?",
  "right_answer":  "Au",
  "other_answers": ["Ag", "Go", "Gd", "Fe"],
  "source":        "WWTBAM",
  "author":        "community",
  "contributor":   "YourName"
}
```

**Rules:**
- `id` must be unique across the entire file
- Set a `level_*` to `-1` if the question should not appear in that mode
- `other_answers` must have at least 3 entries (the game picks 3 randomly)
- Themes: `general` `nature` `geography` `sport` `science` `mathematics`
  `music` `cinema` `history` `literature` `videogames` `spelling`

---

## Building an executable (no Python required for players)

See **BUILD.md** for full instructions.

**Recommended (Windows release hardening): Nuitka**
```bash
# from project root on Windows
build_windows_nuitka.bat onefile
# Output: dist/SubLadder-Nuitka/SubLadder.exe
```

Alternative mode:
```bash
build_windows_nuitka.bat standalone
# Output: dist/SubLadder-Nuitka/run.dist/SubLadder.exe
```

Compare both (size + startup):
```powershell
powershell -ExecutionPolicy Bypass -File .\compare_nuitka_builds.ps1
```

Nuitka keeps the project in Python but compiles to a native executable,
which is harder to reverse engineer than a classic bytecode bundle.
The provided script uses Nuitka's MinGW64 toolchain automatically, so a
separate Visual Studio compiler install is not required for this build path.
For this project, Python 3.12 is recommended for release builds
(the repository already includes a .venv312 environment path used first
by the script when available).

**Short version:**
```bash
pip install pyinstaller pillow pygame
pyinstaller SubLadder.spec
# Output: dist/SubLadder/SubLadder(.exe on Windows)
```

Build must be run on each target OS separately (PyInstaller limitation).

---

## Roadmap

| Version | Feature |
|---|---|
| v2.0 | Difficulty selection in-game |
| v3.0 | Themed 15-question packs |
| v4.0 | Community translations |
| v5.0 | Community question submission + greenlight system |
| v6.0 | Online global leaderboard (dedicated server) |
| v7.0 | Real-time multiplayer + ELO ranked + Steam? |

---

## Contributing

- **Questions**: open a thread on the [Discord server](https://discord.gg/YgQZTaxnPx)
- **Translations**: copy a language file, translate, submit via Discord
- **Bug reports**: Discord or GitHub issues

---

## License

Free to use, modify and share. If you stream it, a shout-out is appreciated! 🎮
