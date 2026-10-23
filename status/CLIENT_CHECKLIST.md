# Checklist client SubLadder — état actuel

Mise à jour : 2026-07-20

## ✅ Déjà présent dans le dépôt

- `game/screens/menu.py` + package `game/screens/menu/` : menu principal réorganisé avec navigation clavier/souris
- `game/screens/options.py` : écran des options, thèmes, résolution, volume, langue
- `game/screens/profile/build.py` : écran de profil local/online avec onglets et stats
- `game/screens/ranked.py` : écran ranked avec stats, leaderboard, matchmaking
- `game/screens/streamer_config.py` : écran de configuration du mode streamer
- `game/screens/streamer_game_streamer.py` et `game/screens/streamer_game_viewvers.py` : écrans de jeu streamer/viewvers
- `game/screens/top_scores.py` : écran des meilleurs scores
- `game/screens/achievements.py` : écran des achievements
- `game/auth/client.py` : client API pour la partie online
- gestion des assets et fallbacks via `game/asset_manager.py`

## ✅ Ajouts réalisés récemment
- [x] Nouvelle vue profil en style launcher avec onglets Profile / Stats / Achievements / Ranking / Top players
- [x] Bouton de promotion d’un profil offline vers online via Discord ou Steam
- [x] Onglets Achievements, Ranking et Top players intégrés dans le profil
- [x] Base P2P locale hôte/joindre + logique lobby visible + matchmaking ranked
- [x] Nouveau lobby normal multijoueur côté UI avec création/join de table
- [x] Meilleur fallback réseau dans l’onglet overview du profil online
- [x] Tests de régression profil et multijoueur validés localement

## ⚠️ Ce qui reste à faire réellement

### Priorité 1 — stabilisation du client
- Vérifier le lancement du client sur Windows/Linux sans crash majeur
- Vérifier la cohérence des écrans après changement de thème / langue / résolution
- Vérifier le flux complet : menu → profil → singleplayer / multiplayer / ranked → retour au menu

### Priorité 2 — amélioration UX / robustesse
- Finaliser les transitions et feedbacks visuels dans les écrans de menu
- Vérifier le comportement des écrans en cas de connexion serveur indisponible
- Vérifier les messages d’erreur et les états de chargement sur toutes les vues online
- Harmoniser la lisibilité des textes sur le thème “White” et autres thèmes clairs

### Priorité 3 — fonctionnalités partielles / mortes
- [x] Le mode P2P local/LAN côté logique a désormais une base de session hôte/joindre locale testée
- [x] Brancher le flux de lobby visible "Normal" côté UI : tables ouvertes, nombre de joueurs, lock/password
- [ ] Brancher le flux de matchmaking "Ranked" côté UI : invisible, pairing proche en ELO, hôte choisi selon stabilité
- [ ] Vérifier le flux streamer/viewers en vraie session, pas seulement au niveau des écrans
- [ ] Vérifier les écrans `old_profile.py` / anciens sous-systèmes pour éviter le code mort ou doublon

### Priorité 4 — contenu / assets / polish
- Compléter ou remplacer les assets manquants
- Vérifier les sons/jingles et leur déclenchement correct
- Ajouter des messages de feedback sur les modes encore non intégrés

## ✅ Checklist de progression

### Écrans / menus déjà présents
- [x] Menu principal
- [x] Sous-menu singleplayer
- [x] Sous-menu multiplayer
- [x] Écran ranked
- [x] Écran profil
- [x] Écran options
- [x] Écran achievements
- [x] Écran top scores
- [x] Écran streamer config
- [x] Écrans streamer streamer/viewvers

### À valider en exécution
- [ ] Navigation clavier/souris du menu sur toutes les plateformes
- [ ] Theme contrast / legacy white theme
- [ ] Connexion online dans le client sans blocage
- [ ] Synchro du profil online avec le backend
- [x] Lobby visible "Normal" depuis le client : création de table, affichage des tables, lock/password
- [ ] Matchmaking ranked depuis le client
- [ ] Streamer mode complet depuis l’UI

### À améliorer / finaliser
- [ ] UX du menu principal encore trop dense ou peu homogène selon certaines zones
- [ ] Feedback visuel lors des chargements réseau
- [ ] Cohérence générale des libellés / couleurs / tailles des widgets
- [ ] Tests manuels du flux complet client

## Notes importantes

1. Le client a une base UI assez solide et plusieurs écrans sont déjà présents.
2. Le travail restant est surtout sur la cohérence UX, la robustesse et la validation des flux network.
3. Les préférences de thème, langue, résolution et son sont déjà intégrées, mais restent à vérifier complètement en exécution.
4. Les modes streamer et P2P sont maintenant bien avancés côté expérience utilisateur, avec une base locale de session / lobby / matchmaking déjà présente côté logique et UI.
