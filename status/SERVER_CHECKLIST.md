# Checklist serveur SubLadder — état actuel

Mise à jour : 2026-07-20

## ✅ Déjà présent dans le dépôt

- `server/config.json` est bien présent localement
- `server/server.py` démarre une application FastAPI
- Authentification JWT implémentée
- Endpoints profil et admin présents
- Matchmaking WebSocket présent
- Schema DB complet
- `server/api/score.py` et `server/api/leaderboard.py` existent déjà

## ✅ Ajouts réalisés récemment
- [x] Connecteurs live Twitch IRC et YouTube Data API v3 implémentés
- [x] Mode P2P local/LAN complété côté logique avec session hôte/joindre, lobby normal et matchmaking ranked
- [x] Hardening serveur appliqué sur JWT, auth/admin/social et validation d’input
- [x] Scripts d’installation et de lancement Ubuntu ajoutés
- [x] Tests de régression ciblés ajoutés pour le flux P2P, le lobby/ranked et la sécurité serveur
- [x] Statuts client/serveur mis à jour pour refléter les avancées réalisées

## ⚠️ Ce qui reste à faire réellement

### Priorité 1 — validation fonctionnelle
- Vérifier le flux complet d’authentification + profil + score + leaderboard
- Vérifier les données renvoyées par les endpoints sur une vraie base
- Tester le WebSocket de matchmaking en conditions réelles

### Priorité 2 — finalisation des stubs
- [x] `server/chat/twitch.py` — connecteur IRC Twitch réel implémenté
- [x] `server/chat/youtube.py` — connecteur YouTube Data API v3 réel implémenté
- Finaliser le mode live streamer / intégration chat si cela doit être exploitable

### Priorité 3 — P2P / LAN
- [x] Implémenter le mode P2P local/LAN côté client/serveur
- [x] Le fichier `game/multiplayer/p2p.py` expose maintenant une session hôte/joindre locale minimale et testée
- [x] Ajouter la couche `NormalLobby` pour les tables visibles du mode normal
- [x] Ajouter le `RankedMatchmaker` pour le pairage ELO et la sélection d’hôte

### Priorité 4 — durcissement serveur
- [x] Vérifier les secrets dans `server/config.json`
- [x] Sécuriser JWT et DB credentials via config/env
- [x] Ajouter ou renforcer le rate limiting
- [ ] Vérifier les headers et CORS en production
- [x] Contrôler la validation des inputs et les cas d’erreur

### Priorité 5 — qualité et déploiement
- Vérifier `requirements.txt` pour les dépendances de production
- Ajouter des tests automatisés
- Mettre en place une CI simple
- Documenter le déploiement / rollback
- Préparer la stratégie de backup et migration DB

## ✅ Checklist de progression

### Blocage immédiat à gérer
- [x] `server/config.json` présent
- [x] Vérifier les credentials et le secret JWT
- [ ] Exécuter l’initialisation DB si besoin
- [ ] Lancer le serveur localement
- [ ] Vérifier le health check et l’API docs

### Flux critiques à tester
- [ ] Authentification register/login
- [ ] Endpoint profile
- [ ] Endpoint score
- [ ] Endpoint leaderboard
- [ ] WebSocket multiplayer

### Fonctionnalités à finaliser
- [x] Twitch chat live
- [x] YouTube chat live
- [x] Mode P2P LAN (version locale minimale, testée)
- [x] Sécurité production (base) 
- [ ] Observabilité / CI / tests

## Notes importantes

1. Le fichier de config n’est plus un manque à créer : il existe déjà sous `server/config.json`.
2. Les endpoints `score` et `leaderboard` sont déjà présents dans le dépôt, mais ils doivent être vérifiés en exécution.
3. Le travail restant est surtout de validation, de robustesse, de sécurité et de finition des sous-systèmes encore en stub.
4. Le mode `streamer` et les intégrations live sont maintenant bien avancés, mais restent à valider en environnement réel.
5. Les connecteurs de chat Twitch IRC et YouTube Data API v3 sont désormais implémentés (2026-07-19).
6. Le mode multijoueur local P2P a été complété avec un test de régression ciblé et une couche de lobby/matchmaking minimale (2026-07-20).

