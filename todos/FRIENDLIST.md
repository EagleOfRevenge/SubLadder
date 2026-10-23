# TODO - Friend List (SubLadder)

## Objectif général

Créer une liste d'amis moderne inspirée de League of Legends, affichée sur le côté droit de l'écran hors partie, fonctionnant entièrement en temps réel grâce aux WebSockets.

La friend list devra permettre :

* voir les amis en ligne
* voir les amis hors ligne
* voir les amis en partie
* voir le type de partie joué
* envoyer des invitations
* consulter les profils
* bloquer des joueurs
* supprimer des amis
* signaler des joueurs

Cette architecture devra être pensée dès le départ pour accueillir facilement :

* chat privé
* groupes
* clans
* favoris
* invitations Ranked
* statut invisible
* synchronisation Discord
* notifications sociales
* cross-platform

Le système devra être modulaire, maintenable et facilement extensible.

---

# 1. Base de données

## Table friends

Colonnes :

* id
* player_id
* friend_id
* status

  * pending
  * accepted
  * declined
* created_at

Contraintes :

* empêcher les doublons
* empêcher un joueur de s'ajouter lui-même
* supprimer automatiquement les relations lors de la suppression d'un compte

---

## Table blocked_players

Colonnes :

* id
* blocker_id
* blocked_id
* created_at

Le blocage devra empêcher :

* les demandes d'amis
* les invitations
* les futurs messages privés
* les invitations de groupe
* l'apparition dans les suggestions d'amis

---

## Table player_reports

Colonnes :

* id
* reporter_id
* reported_id
* reason
* description
* created_at

Prévoir une protection contre le spam de reports.

---

# 2. Backend

Créer plusieurs services indépendants :

FriendService

Gestion des amis.

PresenceService

Gestion des statuts.

InvitationService

Gestion des invitations.

NotificationService

Gestion des notifications.

ReportService

Gestion des signalements.

ProfileService

Chargement des profils.

Respecter le principe de responsabilité unique (SRP).

---

# 3. API

Friend Requests :

* envoyer une demande
* accepter une demande
* refuser une demande
* annuler une demande
* récupérer les demandes reçues
* récupérer les demandes envoyées

Friends :

* récupérer la liste d'amis
* supprimer un ami

Blocked Players :

* bloquer un joueur
* débloquer un joueur
* récupérer la liste des joueurs bloqués

Reports :

* envoyer un report

Toutes les vérifications devront être effectuées côté serveur.

Le client ne décide jamais si une action est autorisée.

Le serveur reste l'unique source de vérité.

---

# 4. Système de présence

Créer une enum PlayerStatus.

Exemple :

Offline

Online

Away

Lobby

LookingForMatch

MatchFound

LoadingGame

NormalGame

RankedGame

Tutorial

Training

CustomGame

Ne jamais utiliser de chaînes de caractères libres.

Toujours utiliser des enums.

Prévoir la possibilité d'ajouter facilement de nouveaux statuts.

---

# 5. Communication temps réel

Utiliser les WebSockets.

Mettre à jour automatiquement la friend list lorsqu'un joueur :

* se connecte
* se déconnecte
* change de statut
* rejoint un lobby
* quitte un lobby
* démarre une partie
* termine une partie
* accepte une demande
* supprime un ami
* est déconnecté du serveur

Aucune actualisation manuelle ne devra être nécessaire.

Le client écoute uniquement les événements envoyés par le serveur.

---

# 6. Interface principale

Créer un panneau fixe sur le côté droit de l'écran.

Le panneau devra contenir :

* barre de recherche
* catégories repliables
* compteur d'amis
* liste scrollable

Catégories :

En ligne

En partie

Absent

Hors ligne

Exemple :

En ligne (4)

En partie (2)

Absent (1)

Hors ligne (31)

---

# 7. Réduction de la Friend List

Ajouter un bouton dans l'en-tête de la friend list permettant de masquer complètement le panneau.

Lorsque la friend list est fermée :

* le panneau disparaît entièrement
* un bouton reste affiché en bas à droite
* le bouton permet de rouvrir la friend list
* l'ouverture et la fermeture utilisent une animation fluide
* la position du bouton reste fixe
* l'état est sauvegardé entre les sessions

Prévoir une préférence utilisateur :

FriendListCollapsed

true = fermée

false = ouverte

Le bouton devra pouvoir afficher un badge de notifications.

Exemple :

🔴3

👥

Les notifications possibles :

* nouvelle demande d'ami
* invitation de groupe
* ami connecté
* message privé
* notification de clan
* futurs événements sociaux

Une fois la friend list rouverte, les notifications pourront être marquées comme lues.

---

# 8. Mode ouverture rapide (optionnel)

Prévoir un troisième état :

FriendListHoverPreview

Lorsque la friend list est réduite :

* passer la souris sur le bouton ouvre temporairement la liste
* quitter la zone referme automatiquement la liste après quelques centaines de millisecondes

Cela devra être désactivable dans les paramètres.

---

# 9. Carte d'un ami

Chaque ami devra afficher :

* avatar
* pseudo
* niveau
* statut
* icône de statut

Exemples :

🟢 En ligne

🔵 Dans un lobby

🟠 En partie normale

🔴 En partie classée

🟡 Absent

⚫ Hors ligne

Prévoir l'ajout futur :

* rang
* clan
* badges
* sous-marin équipé
* bannière
* icônes spéciales

---

# 10. Tri automatique

Ordre :

1. En ligne
2. En partie
3. Absent
4. Hors ligne

Puis tri alphabétique dans chaque catégorie.

Le tri devra être automatique après chaque mise à jour.

---

# 11. Recherche

Recherche instantanée.

Caractéristiques :

* filtrage temps réel
* insensible à la casse
* recherche par pseudo

Prévoir également :

* recherche par clan
* recherche par tag
* recherche par rang

---

# 12. Menu contextuel (clic droit)

Actions :

Voir le profil

Inviter

Supprimer des amis

Bloquer

Reporter

Le menu devra être facilement extensible.

---

## Voir le profil

Ouvrir exactement la même interface que le menu "Profil".

Seules les données changent.

---

## Inviter

Conditions :

* ami connecté
* ami non bloqué
* ami pas déjà dans le groupe
* ami pas déjà en partie
* uniquement pour les parties normales

Prévoir dès maintenant :

* Ranked
* Coop
* Événements
* Parties personnalisées

---

## Supprimer un ami

Afficher une confirmation.

Mettre automatiquement à jour les deux joueurs.

---

## Bloquer

Afficher une confirmation.

Bloquer devra automatiquement :

* supprimer l'amitié
* supprimer les demandes
* empêcher les invitations
* empêcher les futurs messages privés
* empêcher les futures demandes d'amis

---

## Reporter

Choix possibles :

* triche
* AFK volontaire
* insultes
* harcèlement
* nom inapproprié
* autre

Ajouter un commentaire facultatif.

---

# 13. Invitations de groupe

Créer une fenêtre d'invitation.

Exemple :

Arthur vous invite.

[Accepter]

[Refuser]

Expiration :

30 secondes.

Prévoir plusieurs invitations simultanées.

---

# 14. Fenêtre de profil

Afficher :

* avatar
* pseudo
* niveau
* expérience
* rang
* statistiques
* victoires
* défaites
* ratio
* sous-marin équipé
* badges
* bannière
* historique récent (future fonctionnalité)

Utiliser le même composant que le profil du joueur connecté.

---

# 15. Gestion des erreurs

Le serveur devra toujours vérifier :

* joueur inexistant
* joueur bloqué
* ami déjà existant
* demande déjà envoyée
* joueur déjà en partie
* invitation déjà envoyée
* limite atteinte
* auto-ajout
* relation déjà existante

Le client affiche simplement le message retourné.

---

# 16. Limites configurables

Exemple :

Maximum d'amis :

300

Maximum de demandes envoyées :

30

Maximum de demandes reçues :

100

Ces valeurs devront être configurables côté serveur.

---

# 17. Sécurité

Le client ne devra jamais :

* décider si un joueur est ami
* décider si une invitation est valide
* modifier directement un statut
* créer une relation d'amitié
* supprimer une relation d'amitié
* modifier des données sociales

Toutes les validations importantes seront effectuées côté serveur.

---

# 18. Performances

Objectifs :

* chargement rapide
* cache mémoire des joueurs connectés
* mise à jour partielle des éléments modifiés
* éviter les appels réseau inutiles
* WebSockets ciblés uniquement vers les joueurs concernés
* supporter plusieurs centaines d'amis sans perte de fluidité

---

# 19. Architecture événementielle

Privilégier les événements :

FriendRequestSent

FriendRequestAccepted

FriendAdded

FriendRemoved

FriendBlocked

FriendReported

InvitationSent

InvitationAccepted

InvitationDeclined

PlayerConnected

PlayerDisconnected

PlayerStatusChanged

NotificationCreated

Limiter le couplage entre les services.

Favoriser un Event Bus ou un système Publish/Subscribe.

---

# 20. Directives GitHub Copilot Pro

Le code généré devra :

* être lisible
* être maintenable
* être modulaire
* respecter SOLID
* respecter DRY
* utiliser des DTO
* utiliser des enums
* utiliser des services spécialisés
* documenter les méthodes importantes
* prévoir des tests unitaires
* éviter les dépendances circulaires
* privilégier la clarté avant l'optimisation prématurée
* être facilement extensible
* permettre l'ajout futur de nouvelles fonctionnalités sociales sans réécriture importante

Le serveur devra toujours être l'unique source de vérité.

Toute la logique métier devra être implémentée côté serveur.
