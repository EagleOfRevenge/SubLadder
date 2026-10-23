# Changelog — Sub Ladder

All notable changes to this project are documented here.

---

## [2.3] — Current development build

### Added
- **Système XP & Niveaux** — chaque bonne réponse rapporte des XP selon la difficulté
  et la position de la question (Q1-5 ×1, Q6-10 ×2, Q11-15 ×3) :
  - Easy : 5 XP · Normal : 10 XP · Hard : 20 XP · Legendary : 40 XP
- **Bonus XP de complétion** pour avoir gagné une partie complète :
  - Easy +50 · Normal +100 · Hard +200 · Legendary +500
- **Titres de niveau** dans la langue du jeu : Novice → Amateur → Challenger →
  Expert → Maître → Champion → Légende → Mythique (à partir du niveau 40)
- **Affichage XP en jeu** — toast `+XX XP ✨` après chaque bonne réponse
- **Popup Level-up** — flash doré centré avec nouveau niveau et nouveau titre
- **Barre de progression XP** dans le profil et dans l'écran de récap
- **Niveau + titre** affichés sous le nom du profil dans le menu principal
- **7 nouveaux succès XP** : Level 5/10/20/30/40, 1000 XP total, Parcours Parfait
- XP inclus dans l'export profil JSON

### Fixed
- `UnboundLocalError: history` dans `_record_score_raw` lors d'un abandon (Walk Away) —
  `history` était défini après son premier usage dans la même fonction.

---

## [2.1] — Previous build

### Added
- Timer de pause reprend à la seconde restante (au lieu de repartir de zéro).
- Mode + question affichés sous "Charger une partie" dans le menu.
- Récap : bouton "même mode" coloré + bouton "changer de mode".
- Stats par mode dans le profil (win rate, best, played).
- Top Scores filtrables par mode (onglets).
- Historique des 10 dernières parties dans le profil.
- Mode affiché en permanence en jeu `[Hard]  ⏱ 28s`.
- Champ `explanation` dans le JSON — s'affiche après mauvaise réponse.
- Confirmation Walk Away.
- 3 succès Legendary + triggers `win_legendary`, `win_all_modes`.
- Coquille `Maria` → `Marie` corrigée.

---

## [2.0] — Stable release

### Added
- 4 modes : Easy, Normal, Hard, Legendary 🔒 (déblocage sur victoire Hard).
- Structure JSON étendue : `level_easy/normal/hard/legendary` (-1 = absent).
- Écran de sélection du mode, écran Pause, timer relancé après Switch.
- Validation au démarrage, temps moyen de réponse, taux par niveau.
- EN : 143 questions · FR : 158 questions (dont émission Marie 26/08/2004).
- Thèmes `spelling` et `mathematics`. `README.md` complet.

---

## [1.5] — Previous stable

### Added
- Timer visuel, écran récapitulatif scrollable, stats avancées, export profil JSON.

### Fixed
- Double `tk.Tk()` empêchait la création de `data.json`.

---

## [1.4] — 2025
- `asset_manager.py`, `first_run.py`, fonds dynamiques, sons, bouton Discord, `run.py`.

## [1.3] — 2025
- `data/languages/`, `data/questions/`, 60q EN + 60q FR, 15 succès.

## [1.2] — 2025
- Menu, profils, sauvegarde, Top Scores, Options, subs, Walk Away.

## [1.1] — 2025
- `right_answer` + `other_answers[]`, position A/B/C/D aléatoire.

## [1.0] — 2025
- Jeu quiz tkinter initial, 45 questions, 15 niveaux, 3 aides.


All notable changes to this project are documented here.
Format: [version] — summary

---

## [2.1] — Current development build

### Added
- **Stats par mode** — win rate, best score, games played per difficulty shown in Profile.
- **Historique des 10 dernières parties** — visible in Profile with mode, level reached, subs won.
- **Mode affiché en jeu** — mode label (e.g. `[Hard]`) shown next to timer in the question bar.
- **Explication après mauvaise réponse** — optional `explanation` field in question JSON shown below answers.
- **Confirmation Walk Away** — dialog asks "Walk away and keep X subs?" before abandoning.
- **Top Scores filtrables par mode** — tabs (All / Easy / Normal / Hard / Legendary) in Top Scores screen.
- **Mode + question visible sous "Charger une partie"** — e.g. `Normal · Q11 / 15` shown in main menu.
- **Recap: deux boutons rejouer** — "Same mode again" (colored) + "Change mode" (gold) in recap screen.
- **3 nouveaux succès Legendary** : unlock Legendary, win Legendary, win all 4 modes.
- **v2.5 planifiée** : mode Chrono (timer éliminatoire) avec ses propres achievements.

### Fixed
- **Timer de pause** reprenait à zéro au lieu de reprendre à la seconde restante.
- **"Rejouer" depuis le récap** ne proposait pas le sélecteur de mode.

---

## [2.0] — Current release

### Added
- **4 modes de difficulté** : Easy, Normal, Hard, Legendary 🔒.
- **Legendary verrouillé** — se débloque en gagnant une partie Hard.
- **Structure JSON étendue** : chaque question a `level_easy`, `level_normal`, `level_hard`, `level_legendary`  
  (valeur -1 = absent dans ce mode). Recyclage des questions entre modes.
- **Écran de sélection du mode** avant chaque partie.
- **Écran Pause** ⏸ — cache la question, freeze le timer.
- **Timer relancé** après le joker Switch.
- **Validation au démarrage** — message clair si fichier critique manquant.
- **Temps moyen de réponse** et **taux de réussite par niveau** dans le profil.
- **Déblocage Legendary** enregistré dans le profil.
- **Version affichée** (v2.0) en bas du menu principal.
- EN : 143 questions — 4 modes couverts niveaux 1-15.
- FR : 158 questions dont les 15 questions de l'émission de Marie (26/08/2004, première gagnante du million €).
- Thèmes `spelling` et `mathematics` ajoutés.
- `README.md` complet.

---

## [1.5] — Previous build

### Added
- Timer visuel par question (chiffre + barre couleur).
- Écran récapitulatif de fin de partie scrollable.
- Stats avancées : win rate, avg score, win streak, export profil JSON.
- `requirements.txt` et `CHANGELOG.md`.

### Fixed
- `name_var.get()` → `entry.get()` dans first_run.py.
- Double `tk.Tk()` empêchait la création de `data.json`.

---

## [1.4] — 2025

### Added
- `asset_manager.py` — images + sons avec génération automatique des placeholders.
- `first_run.py` — wizard premier lancement (langue + profil).
- Fonds dynamiques par palier, musiques, jingles, volume.
- Bouton Discord, `run.py`, build PyInstaller.

---

## [1.3] — 2025

### Added
- `data/languages/` + `data/questions/` — langue lie les chaînes UI et le pool de questions.
- 60 questions EN + 60 questions FR (QVGDM, 12CDM, TLMVTSP).
- Succès (15 achievements), toast popups.

---

## [1.2] — 2025

### Added
- Menu principal, profils multiples, sauvegarde/chargement.
- Top Scores, Options (langue, résolution, plein écran).
- Échelle en subs (1→100), Walk Away.

---

## [1.1] — 2025

### Added
- `right_answer` + `other_answers[]` — position A/B/C/D aléatoire à chaque partie.

---

## [1.0] — 2025 — Initial release

### Added
- Jeu quiz tkinter — 45 questions, 15 niveaux, 3 aides, échelle de gains.


All notable changes to this project are documented here.
Format: [version] — date — summary

---

## [1.5] — 2025 — Current development build

### Added
- **Visual countdown timer** per question — chiffre (⏱ 30s) + colour-coded
  progress bar (green → orange → red). Timer is display-only; no penalty on
  reaching zero.
- **End-of-game recap screen** — replaces the old simple overlay. Shows every
  question played: your answer vs. correct answer, time spent, source of the
  question. Global stats: ✅/❌ counts, success %, average time per question.
- **Advanced profile stats** — win rate %, average score per game, win streak,
  alongside existing stats (games played, total subs, best game, correct answers).
- **Profile export** — export any profile's stats and top scores to a JSON file
  via a native save dialog (📤 Export button in Profile screen).
- **Robust error handling** — corrupted `data.json` is backed up automatically
  and a fresh file is created; missing question files fall back to English.
- `requirements.txt` added.
- `CHANGELOG.md` added (this file).

### Changed
- Project restructured: Python source files moved from `data/` to `game/`
  package directory. `game/__init__.py` added for clean PyInstaller bundling.
- `run.py` rewritten — no more `os.chdir()`, cleaner path resolution.
- First-run wizard now runs in its own `Tk()` root **before** `App(tk.Tk)` is
  created, fixing the double-Tk conflict that prevented `data.json` creation.
- `save_data()` now raises on first-run failures (previously silent).

### Fixed
- **Bug** : `name_var.get()` in first_run.py returned empty string due to
  `StringVar` losing its widget binding after step transition. Fixed by reading
  `entry.get()` directly.
- **Bug** : `data.json` was never created because the wizard crash above meant
  `save_data()` was never reached.
- Timer `after()` callbacks now cancelled correctly when leaving the game screen,
  preventing phantom ticks after navigation.

---

## [1.4] — 2025

### Added
- `asset_manager.py` — centralised image + sound engine with graceful fallbacks.
- `first_run.py` — language selection + profile creation wizard on first launch.
- Placeholder background images generated at runtime (calm → serious → tense
  gradient per question range).
- Placeholder WAV sounds generated at runtime (menu music, 3 × game music,
  jingles for correct / wrong / safe haven / win / achievement).
- Volume slider in Options (saved to `data.json`).
- Flag thumbnails in language selector (Options + first-run wizard).
- Discord button in main menu (opens browser to discord.gg/YgQZTaxnPx).
- `run.py` launcher at project root — no more manual `cd data/`.
- PyInstaller build files: `SubLadder.spec`, `build_windows.bat`, `build.sh`,
  `BUILD.md`.

---

## [1.3] — 2025

### Added
- `data/languages/en.json` and `fr.json` — language files now drive both UI
  strings **and** the questions file to load (`questions_file` field).
- `data/questions/en_questions.json` — 60 EN questions (WWTBAM), 4 per level.
- `data/questions/fr_questions.json` — 60 FR questions (QVGDM + 12CDM +
  TLMVTSP), 4 per level.
- Achievements system with 15 achievements; toast popups on unlock.
- Discord button in main menu.

### Changed
- Language change in Options now reloads the matching question pool immediately.
- Languages discovered dynamically from `data/languages/` — adding a new
  language file is all that is needed.

---

## [1.2] — 2025

### Added
- Main menu screen.
- Multiple profiles with persistent stats (games played, total subs, best game,
  correct answers).
- Save / Load mid-game (exact question, lifelines, level all preserved).
- Top Scores screen — global leaderboard across all profiles, top 10.
- Options screen: language (English / Français), resolution presets, fullscreen.
- Prize ladder updated to subs: 1 → 2 → 3 → 5 → **10** 🔒 → … → **100** 🏆.
- Walk Away button.
- "Switch" lifeline replaces "Phone a Friend".

---

## [1.1] — 2025

### Added
- `questions.json` restructured: `right_answer` + `other_answers[]` format.
- Game picks 3 wrong answers at random from the pool and shuffles all 4 into
  A/B/C/D — correct answer position changes every session.

---

## [1.0] — 2025 — Initial release

### Added
- Core quiz game (Python + tkinter).
- 45 questions, 3 per level (1–15), general knowledge.
- Prize ladder (cosmetic), safe havens at levels 5 and 10.
- Lifelines: 50/50, Chat Vote (simulated, weighted), Switch.
- Answer animation: orange on click → green (correct) / red (wrong).
- `questions.json` with `A/B/C/D` fixed format.
