# Système de Ranked — Sub Ladder v6.0

## 📋 Vue d'ensemble

Le système de Ranked est un mode compétitif basé sur le système ELO qui permet aux joueurs de rivaliser pour atteindre les plus hauts rangs.

## 🏆 Système de Rangs

### Hiérarchie des Rangs (Du Meilleur au Pire)

1. **Grand Champion** (Top 500 worldwide)
   - 2500+ ELO
   - Pas de divisions

2. **Champion**
   - 2400-2499 ELO
   - Pas de divisions

3. **Diamond I/II/III**
   - 2100-2399 ELO
   - 3 divisions

4. **Ruby I/II/III**
   - 1800-2099 ELO
   - 3 divisions

5. **Emerald I/II/III**
   - 1500-1799 ELO
   - 3 divisions

6. **Platinum I/II/III**
   - 1200-1499 ELO
   - 3 divisions

7. **Gold I/II/III**
   - 1000-1199 ELO
   - 3 divisions

8. **Silver I/II/III**
   - 800-999 ELO
   - 3 divisions

9. **Bronze I/II/III**
   - 600-799 ELO
   - 3 divisions

10. **Iron I/II/III**
    - 0-599 ELO
    - 3 divisions

### Structure des Divisions

Chaque division (excepté Grand Champion et Champion) est organisée ainsi:
- **Division III**: Bas de la division (0-99 points)
- **Division II**: Milieu de la division (100-199 points)
- **Division I**: Haut de la division (200-299 points)

Exemple: **Gold II** va de 1100-1199 ELO

## ⚙️ Système ELO

### Configuration de Base

- **ELO par défaut**: 1000 points
- **K-factor standard**: 32 points par match
- **K-factor réduit** (2400+ ELO): 16 points par match
- **Plage de matchmaking**: ±200 ELO

### Calcul ELO après un match

```python
Expected Score = 1 / (1 + 10^((opponent_elo - player_elo) / 400))

New Elo = Player Elo + K-factor * (actual_score - expected_score)
```

**Exemple**:
- Joueur A: 1200 ELO vs Joueur B: 1000 ELO
- Joueur A bat Joueur B
- Gain pour A: +22 ELO → 1222
- Perte pour B: -22 ELO → 978

## 🎮 Matchmaking

### Critères de Matchmaking

1. **Plage ELO**: Les adversaires doivent être dans ±200 points
2. **Jeux joués minimum**: Les joueurs doivent avoir joué au moins 5 matchs rangés
3. **Priorité d'appariement**: Les joueurs les plus proches en ELO sont prioritaires

### Exemple de Plage

- Votre ELO: 1250
- Plage acceptée: 1050-1450
- Adversaires elegibles: Tout joueur entre 1050 et 1450 ELO

## � Système de Decay (Champions & Grand Champions)

Le système de decay prévient la stagnation aux plus hauts rangs en pénalisant les joueurs Champion et Grand Champion inactifs.

### Fonctionnement du Decay

**Quand commence le decay?**
- Dès qu'un joueur atteint 2400+ ELO (rang Champion)
- Initialisation: 21 jours de "décay buffer"

**Comment fonctionne le decay?**

1. **Accumuler du décay**: Chaque match rangé gagné = +1 jour de décay buffer (max 21)
   
2. **Perdre du décay**: À minuit chaque jour:
   - Le buffer décay diminue de 1 jour (minimum 0)
   - Si buffer = 0 depuis hier: -15 ELO

**Exemple de Timeline**:
```
Jour 1: Joueur passe Diamond à Champion
   → Décay buffer = 21 jours
   → Gagne 1 match → Décay buffer = 21 (max atteint)

Jour 2 à minuit:
   → Décay buffer = 20 jours
   
Jour 22 à minuit:
   → Décay buffer = 0 jours

Jour 23 à minuit:
   → Décay buffer reste à 0
   → Joueur perd 15 ELO (2385 → 2370)
   
Jour 24 à minuit:
   → Décay buffer reste à 0
   → Joueur perd 15 ELO (2370 → 2355)
   
... Chaque jour sans match: -15 ELO par jour
```

**Comment regagner du décay?**
- Jouer 1 match rangé = regagner 1 jour de décay buffer
- Le buffer reste plafonné à 21 jours

### Champs de Base de Données

```sql
decay_days            INT (0-21) -- Buffer de protection
last_decay_check      DATETIME   -- Dernière vérification du decay
last_match_played     DATETIME   -- Dernière partie jouée
```

### Pénalité de Decay

- **Trigger**: Décay buffer atteint 0 et minuit passe
- **Pénalité**: -15 ELO par jour
- **Fréquence**: Une fois par jour (à minuit UTC)
- **Maximum**: Environ 15-20 ELO par jour de inactivité après 21 jours

### Tableau de Progression du Decay

| Jour | Action | Décay Buffer | ELO (exemple) |
|------|--------|--------------|---------------|
| 0    | Atteint Champion (2400 ELO) | 21 → 21 | 2400 |
| 1    | Joue 1 match | 20 → 21 | 2405 |
| 2    | Inactif | 20 | 2405 |
| ...  | ... | ... | ... |
| 21   | Inactif | 1 | 2405 |
| 22   | Inactif | 0 | 2405 |
| 23   | Minuit passe (décay) | 0 | 2390 (-15) |
| 24   | Minuit passe (décay) | 0 | 2375 (-15) |
| 24   | Joue 1 match | 1 | 2380 |

## 🌅 Tâches Quotidiennes (Minuit UTC)

Le serveur exécute automatiquement les tâches suivantes à minuit UTC:

### 1. Vérification du Decay
- Iterate sur tous les Champions et Grand Champions
- Diminue le buffer de décay de 1
- Si buffer était 0 et reste 0: applique -15 ELO

### 2. Recalculation des Top 500 Grand Champions
- Compte les joueurs à 2500+ ELO
- Si plus de 500: ajuste le threshold automatiquement
- Assure que seuls les 500 meilleurs sont Grand Champion

**Exemple**:
- 503 joueurs à 2500+ ELO
- Les 500 meilleurs conservent Grand Champion (2500+)
- Les 3 autres sont reclassés en Champion (2400-2499)

## �📊 Routes API Serveur

### Endpoints Disponibles

#### GET `/api/ranked/profile/{profile_name}/stats`
Récupère les statistiques rangées d'un joueur, incluant le decay.

#### GET `/api/ranked/season/current`
Retourne la saison active, ses dates et les placements enregistrés pour l'année en cours.

#### GET `/api/ranked/season/{year}/rewards`
Retourne la grille de récompenses prévue pour la saison demandée.

#### GET `/api/ranked/season/{year}/placement/{profile_name}`
Retourne le placement de saison d'un profil précis et sa récompense associée.

**Réponse (joueur normal)**:
```json
{
  "profile_name": "ProPlayer",
  "elo": 1250,
  "games_played": 15,
  "games_won": 9,
  "win_rate": 60.0,
  "current_rank": {
    "tier": "Gold",
    "division": 2,
    "display": "Gold II",
    "icon": "gold_2"
  },
  "progression_to_next": {
    "current": "Gold II",
    "next": "Gold I",
    "current_elo": 1250,
    "elo_to_next": 50,
    "progress_percent": 50.0
  },
  "decay_days": null,
  "is_decaying": false
}
```

**Réponse (Champion/Grand Champion)**:
```json
{
  "profile_name": "ChampionPlayer",
  "elo": 2450,
  "games_played": 150,
  "games_won": 100,
  "win_rate": 66.67,
  "current_rank": {
    "tier": "Champion",
    "division": null,
    "display": "Champion",
    "icon": "champion"
  },
  "progression_to_next": {
    "current": "Champion",
    "next": "Grand Champion",
    "current_elo": 2450,
    "elo_to_next": 50,
    "progress_percent": 50.0
  },
  "decay_days": 18,
  "is_decaying": true
}
```

**Signification des champs decay**:
- `decay_days`: Nombre de jours avant la pénalité de -15 ELO
  - 21: Vient de devenir Champion, protection maximale
  - 1: Demain la pénalité commence
  - 0: Pénalité appliquée chaque minuit jusqu'à ce qu'il joue
- `is_decaying`: `true` si le joueur est subject au decay (2400+ ELO)

#### GET `/api/ranked/leaderboard`
Récupère le classement global rangé.

**Paramètres**:
- `limit` (défaut: 50, max: 500)
- `offset` (défaut: 0)

**Réponse**:
```json
{
  "total": 1234,
  "limit": 50,
  "offset": 0,
  "leaderboard": [
    {
      "rank": 1,
      "game_name": "ProPlayer",
      "discord_username": "ProPlayer#1234",
      "elo": 2850,
      "games_played": 250,
      "games_won": 180,
      "win_rate": 72.0,
      "rank_tier": "Grand Champion",
      "rank_division": null,
      "rank_display": "Grand Champion"
    }
  ]
}
```

#### POST `/api/ranked/match/result`
Soumet le résultat d'un match rangé et met à jour les ELO.

**Paramètres**:
- `winner_profile_id` (int)
- `loser_profile_id` (int)

**Réponse**:
```json
{
  "match_id": 12345,
  "winner_id": 101,
  "loser_id": 102,
  "winner_elo_before": 1200,
  "winner_elo_after": 1222,
  "loser_elo_before": 1000,
  "loser_elo_after": 978,
  "elo_change_winner": 22,
  "elo_change_loser": -22
}
```

#### POST `/api/ranked/matchmaking/find`
Cherche un adversaire rangé.

**Réponse (match trouvé)**:
```json
{
  "status": "match_found",
  "opponent": {
    "profile_id": 102,
    "profile_name": "Opponent",
    "elo": 1230,
    "rank": {
      "tier": "Gold",
      "division": 2,
      "display": "Gold II",
      "icon": "gold_2"
    }
  }
}
```

**Réponse (en attente)**:
```json
{
  "status": "waiting",
  "message": "No opponent available in your ELO range",
  "your_elo": 1250,
  "your_rank": { "tier": "Gold", "division": 2, ... },
  "elo_range": "1050 - 1450"
}
```

#### GET `/api/ranked/top-100`
Récupère les top 100 joueurs mondiaux.

#### GET `/api/ranked/comparison/{profile_name_1}/{profile_name_2}`
Compare les statistiques de deux joueurs.

## 🎯 Interface Client

### Écran Ranked

L'écran Ranked dispose de 3 onglets:

#### 1. **📊 My Stats**
- Affiche votre rang actuel
- Affiche votre ELO
- Affiche vos statistiques (jeux joués, gagnés, taux de victoire)
- Affiche votre progression vers le prochain rang

#### 2. **🏆 Leaderboard**
- Affiche le classement global des top 50 joueurs
- Affiche le rang, ELO, et statistiques de chacun
- Affiche des médailles (🥇🥈🥉) pour les top 3

#### 3. **⚡ Matchmaking**
- Bouton pour rechercher un adversaire
- Affiche votre plage ELO acceptée
- Affiche les critères de matchmaking
- Affiche le statut de la recherche

## 📱 Intégration Client

### Ajout au Menu Principal

Le bouton "⚔ Ranked" est maintenant disponible dans le menu principal, entre "Load Game" et "Top Scores".

### Fichiers Modifiés

- `game/screens/ranked.py` - Nouvel écran Ranked
- `game/main.py` - Ajout de `show_ranked()`
- `game/screens/menu.py` - Ajout du bouton Ranked au menu
- `game/multiplayer/ranked.py` - Logique ELO complète

### Fichiers de Langue

- `data/languages/en.json` - Traduction anglaise
- `data/languages/fr.json` - Traduction française

## 🛠️ Intégration Serveur

### Configuration Base de Données

La table `elo_ratings` stocke:
- `profile_id` - Référence au profil joueur
- `elo` - ELO actuel du joueur
- `games_played` - Nombre total de matchs rangés
- `games_won` - Nombre de victoires
- `updated_at` - Dernière mise à jour

La table `matches` stocke:
- `room_id` - ID unique du match
- `player1_id` - Joueur 1
- `player2_id` - Joueur 2
- `winner_profile_id` - ID du gagnant
- `mode` - Mode de jeu (défini à "ranked")
- `status` - Statut du match (finished)

### Fichiers Serveur

- `server/api/ranked.py` - API endpoints pour le ranked
- `server/server.py` - Intégration de la route ranked

## 🔄 Workflow Complet d'un Match Rangé

1. **Recherche d'adversaire**
   - Le client appelle `POST /api/ranked/matchmaking/find`
   - Le serveur cherche un joueur avec ELO compatible
   - L'adversaire est proposé ou attente

2. **Match en cours**
   - Les deux joueurs jouent le match
   - Les réponses et performances sont enregistrées

3. **Résultat du Match**
   - Le client appelle `POST /api/ranked/match/result` avec le gagnant
   - Le serveur calcule les nouveaux ELO
   - Les statistiques des deux joueurs sont mises à jour

4. **Mise à Jour du Profil**
   - Les deux joueurs voient leurs nouveaux ELO et rangs
   - L'écran "My Stats" se met à jour

## 📈 Progression Typique

### Nouveau Joueur
- ELO: 1000 (Iron III)
- Taux de progression: ~25-35 ELO par victoire

### Joueur Intermédiaire
- ELO: 1500-1800
- Rang: Emerald à Ruby
- Taux de progression: ~20-25 ELO par victoire

### Joueur Expert
- ELO: 2100+
- Rang: Diamond et au-delà
- Taux de progression: ~15-20 ELO par victoire (K-factor réduit à 2400+)

### Top Joueur
- ELO: 2500+
- Rang: Grand Champion
- Taux de progression: ~10-16 ELO par victoire

## 🎓 Conseils pour les Joueurs

1. **Comprendre l'ELO**: Plus votre adversaire a un ELO élevé, plus vous gagnez de points
2. **Consistance**: Maintenir une bonne win rate requiert de la consistance
3. **Défis**: Jouer contre des meilleurs joueurs accelere votre progression
4. **Sérénité**: Le matchmaking ±200 crée des matchs équilibrés

## 🔐 Sécurité et Anti-triche

- Les résultats doivent être validés par le serveur
- Les gains ELO anormaux sont détectés
- Les statistiques suspectes sont loggées pour révision
- Anti-cheat basé sur les patterns de jeu

## 📋 Futures Améliorations

- [ ] Système de saisons avec réinitialisation partielle
- [ ] Récompenses pour les rangs élevés
- [ ] Tableau de classement par division
- [ ] Historique des matchs
- [ ] Statistiques détaillées par adversaire
- [ ] Système de placement (placement matches)
- [ ] Duo/équipe ranked

---

**Version**: 6.0  
**Dernière mise à jour**: 23 Mai 2026  
**État**: Implémenté et déployé ✅
