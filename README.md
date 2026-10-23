# Sub Ladder

Sub Ladder is a **Who Wants to Be a Millionaire?**-style quiz game built with
Python and Tkinter. It is designed for streamers and awards virtual "subs"
for correct answers. The repository also contains a separate FastAPI backend
for online profiles and multiplayer features.

## Contents

- [Features](#features)
- [Requirements](#requirements)
- [Run the desktop game](#run-the-desktop-game)
- [Run the backend](#run-the-backend)
- [Project layout](#project-layout)
- [Player data and assets](#player-data-and-assets)
- [Add a language](#add-a-language)
- [Add questions](#add-questions)
- [Build a Windows executable](#build-a-windows-executable)
- [Tests](#tests)

## Features

- Single-player quiz with Easy, Normal, Hard, and Legendary difficulty modes.
- Profiles, achievements, score history, statistics, and profile export.
- English and French interface and question sets.
- Themes, resolution options, sound effects, and music.
- Online account/profile features, social screens, and ranked screens that use
  the configured backend.
- Local/LAN multiplayer and streamer-oriented game screens.

The desktop client and backend are separate applications. Online, ranked,
streamer, and multiplayer flows may require a running and correctly configured
server or external service; the presence of a screen or API endpoint does not
by itself mean that a production deployment has been validated.

## Requirements

- Python 3.10 or newer is recommended.
- Tkinter (included with many Python distributions; install your OS package if
  it is missing).
- The Python packages in the root `requirements.txt` for the desktop client.

On Debian/Ubuntu, install Tkinter with:

```bash
sudo apt install python3-tk
```

## Run the desktop game

From the repository root:

```bash
python -m venv .venv
```

Activate the environment, then install dependencies and launch the game:

```bash
# Linux/macOS
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

```powershell
# Windows
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

The first launch opens a setup flow for language and profile creation. The game
stores writable player data under `%APPDATA%\SubLadder` on Windows and
`~/SubLadder` on other platforms. Language files, questions, and shipped assets
remain in `data/`.

## Run the backend

The FastAPI backend is maintained separately under `server/` and requires
MariaDB/MySQL. See [`server/README.md`](server/README.md) for configuration,
database initialization, launch, and API details.

At a glance, the backend can be installed and started with:

```bash
cd server
python -m venv .venv
# Activate .venv, then:
pip install -r requirements.txt
cp config.example.json config.json
# Edit config.json with database settings and a strong JWT secret.
python database/init_db.py --host 127.0.0.1 --user root --password "your-password"
python server.py
```

The API documentation is available at `http://localhost:8000/docs` when the
server is running. Do not expose a development configuration directly to the
internet; review the backend security and deployment guidance first.

## Project layout

```text
.
├── run.py                     # Desktop game launcher
├── game/
│   ├── main.py                # Tkinter application and screen navigation
│   ├── screens/               # Menus, profiles, game, ranked, streamer, etc.
│   ├── singleplayer/          # Single-player game logic
│   ├── multiplayer/           # Local/LAN and multiplayer client logic
│   ├── auth/                  # Desktop API client and token handling
│   ├── utils.py               # Persistence, language loading, asset checks
│   └── asset_manager.py       # Image and audio loading / fallback assets
├── data/
│   ├── languages/             # Interface translations
│   ├── questions/             # Localized question sets
│   ├── pictures/              # Backgrounds, logos, and flags
│   └── sound/                 # Music and sound effects
├── server/                    # FastAPI backend and MariaDB schema
└── tests/                     # Client and server regression tests
```

## Player data and assets

Player profiles, options, achievements, and avatars are written to the
per-user data directory, not the source `data/` folder. Existing legacy data
may be migrated on first launch. Keep a backup of the per-user directory when
moving a profile to another computer.

Missing optional images and sounds can be generated as placeholders at
startup. The game still expects its language and question data to be present.

## Add a language

1. Copy `data/languages/en.json` to `data/languages/<code>.json`.
2. Set the language `code`, display `name`, and `questions_file`.
3. Translate the strings in the `ui` section.
4. Add the corresponding question set at
   `data/questions/<code>_questions.json`.
5. Optionally add a 64 × 40 flag at `data/pictures/flags/<code>.png`.

Language files are discovered from `data/languages/`; no code change is
normally needed.

## Add questions

Add questions to the matching file in `data/questions/`. A question can use
the following fields:

```json
{
  "id": "en_Q999",
  "level_easy": 5,
  "level_normal": 8,
  "level_hard": 12,
  "level_legendary": 3,
  "theme": "science",
  "question": "What is the chemical symbol for gold?",
  "right_answer": "Au",
  "other_answers": ["Ag", "Go", "Gd", "Fe"],
  "source": "Reference or source",
  "author": "community",
  "contributor": "YourName"
}
```

Guidelines:

- Keep `id` unique within the question file.
- Use `-1` for a mode level if that question is unavailable in that mode.
- Provide at least three `other_answers`; the game selects three to display
  alongside the correct answer.
- A question may include an `explanation` shown after an incorrect answer.
- Existing themes include `general`, `nature`, `geography`, `sport`, `science`,
  `mathematics`, `music`, `cinema`, `history`, `literature`, `videogames`, and
  `spelling`.

## Build a Windows executable

The recommended Windows release build uses Nuitka:

```powershell
.\build_windows_nuitka.bat onefile
```

For a standalone directory build:

```powershell
.\build_windows_nuitka.bat standalone
```

See [`WINDOWS_INSTALLER.md`](WINDOWS_INSTALLER.md) for output locations,
comparison, and installer packaging. The legacy PyInstaller build scripts are
also present; builds should be created on the target operating system.

## Tests

The regression tests use `pytest`. From the repository root, install it in
your development environment if needed and run:

```bash
python -m pytest
```

## Contributing

- **Questions and translations:** contribute via the project Discord.
- **Bug reports and feature requests:** open a GitHub issue.
- **Pull requests:** include a concise description and relevant test results.

## License

See [`LICENSE`](LICENSE).
