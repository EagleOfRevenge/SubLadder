# Installation Windows

## Option 1 — Build Nuitka (recommandé)

Depuis la racine du projet:

```powershell
.\build_windows_nuitka.bat onefile
```

Sortie:

- [dist/SubLadder-Nuitka/SubLadder.exe](dist/SubLadder-Nuitka/SubLadder.exe)

Ou build dossier standalone:

```powershell
.\build_windows_nuitka.bat standalone
```

Sortie:

- [dist/SubLadder-Nuitka/run.dist](dist/SubLadder-Nuitka/run.dist)

## Option 2 — Comparer onefile vs standalone (taille + démarrage)

```powershell
powershell -ExecutionPolicy Bypass -File .\compare_nuitka_builds.ps1
```

Rapport généré:

- [dist/SubLadder-Nuitka-compare/report.txt](dist/SubLadder-Nuitka-compare/report.txt)

## Option 3 — Générer un dossier installateur prêt à distribuer

Script:

- [build_installer_windows.ps1](build_installer_windows.ps1)

Commande:

```powershell
powershell -ExecutionPolicy Bypass -File .\build_installer_windows.ps1
```

Sortie:

- [dist/SubLadder-Installer](dist/SubLadder-Installer)

Le script détecte automatiquement la sortie Nuitka disponible:
- onefile: [dist/SubLadder-Nuitka/SubLadder.exe](dist/SubLadder-Nuitka/SubLadder.exe)
- standalone: [dist/SubLadder-Nuitka/run.dist](dist/SubLadder-Nuitka/run.dist)

## Ancienne option — Dossier prêt à l’emploi (legacy)

Le binaire a été généré dans :

- [dist/SubLadder-Windows/SubLadder](dist/SubLadder-Windows/SubLadder)

Contenu inclus :
- Exécutable du jeu
- Assets du jeu (langues, questions, images, sons)
- Pas de serveur
- Pas de documentation

Pour l’utiliser :
1. Ouvrir le dossier [dist/SubLadder-Windows/SubLadder](dist/SubLadder-Windows/SubLadder)
2. Double-cliquer sur SubLadder.exe ou sur launch_game.bat

