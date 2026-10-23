# Menu Package — Sub Ladder

Ce package gère tous les écrans de menu du jeu.

## Structure

```
menu/
├── __init__.py                    # Export principal
├── menu.py                        # build() — Menu principal
├── singleplayer_submenu.py        # build_singleplayer_submenu() — Sous-menu Solo
├── mode_picker.py                 # build_mode_picker() — Sélecteur de difficulté
├── color_utils.py                 # Utilitaires de colorimétrie (HEX/RGB)
├── avatar.py                      # Chargement d'avatars de profil
├── profile_display.py             # build_profile_section() — Affichage profil
├── menu_renderer.py               # render_menu(), animation, navigation state
├── menu_navigation.py             # Bindings clavier/souris
└── README.md                      # Ce fichier
```

## Fonctionnalités implémentées

### Menu principal (`menu.py`)
- ✅ Affichage du profil (avatar, nom, niveau, titre)
- ✅ Navigation clavier (↑/↓) et souris (molette, clic)
- ✅ Animation de pulsation sur l'item sélectionné
- ✅ Affichage du save hint (mode + niveau de sauvegarde)
- ✅ Statut du serveur (online/offline)
- ✅ Numéro de version en bas à droite
- ✅ Sous-menu "Singleplayer"

### Sous-menu Singleplayer (`singleplayer_submenu.py`)
- ✅ Bouton "Nouvelle Partie"
- ✅ Bouton "Charger la partie"
- ✅ Save hint contextuel
- ✅ Bouton "Retour" vers le menu principal

### Sélecteur de difficulté (`mode_picker.py`)
- ✅ Mode Normal (toujours disponible)
- ✅ Mode Hard (toujours disponible)
- ✅ Mode Legendary (verrouillé, débloqué après une victoire en Hard)
- ✅ Effets hover sur les boutons
- ✅ Bouton "Retour"

### Profil (`profile_display.py`)
- ✅ Affichage avatar (PIL/Tkinter)
- ✅ Niveau et titre basés sur XP
- ✅ Statut de synchronisation (online profiles: ✓/⏳/✗)
- ✅ Gestion profil offline

### Utilitaires (`color_utils.py`, `avatar.py`)
- ✅ blend_colors() — Interpolation entre deux couleurs HEX
- ✅ hex_to_rgb() / rgb_to_hex() — Conversion HEX/RGB
- ✅ load_menu_avatar() — Chargement + redimensionnement d'avatar

## Fonctionnalités à implémenter

- [ ] **Thèmes visuels** — Changement de thème (clair/sombre, palettes)
- [ ] **Animations d'entrée/sortie** — Transitions fluides entre écrans
- [ ] **Tooltips** — Infobulles sur les items du menu
- [ ] **Historique des parties** — Accès rapide aux dernières parties
- [ ] **Accès rapide aux achievements** — Aperçu dans le menu
- [ ] **Configuration des raccourcis clavier** — Personnalisation des bindings
- [ ] **Easter eggs** — Animations cachées (Konami code, clic répétitif, etc.)
- [ ] **Menu Ranked** — Écran dédié au mode classé (si non implémenté ailleurs)
- [ ] **Menu Profile** — Écran dédié au profil (si non implémenté ailleurs)
- [ ] **Menu Achievements** — Écran dédié aux achievements (si non implémenté ailleurs)
- [ ] **Menu Options** — Écran dédié aux options (si non implémenté ailleurs)

## Dépendances

- `tkinter` — Interface graphique
- `PIL` (Pillow) — Gestion d'images (avatars)
- `constants` — Configuration du jeu (GAME_MODES, couleurs, etc.)
- `utils` — Utilitaires (get_avatar_path)
- `game.auth.cache` — Cache de profil (synchronisation online)

## Utilisation

```python
# Dans game/main.py :
from screens.menu import build, build_mode_picker, build_singleplayer_submenu

# Menu principal
build(app)

# Sélecteur de difficulté
build_mode_picker(app)

# Sous-menu Singleplayer
build_singleplayer_submenu(app)
```
