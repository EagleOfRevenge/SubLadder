# Todo list — éléments manquants / priorités SubLadder

Ce document regroupe les points à traiter pour reprendre le projet proprement après plusieurs semaines sans travail.

## Priorité 1 — stabiliser le projet

- [ ] Vérifier que le jeu démarre correctement sur Windows/Linux
- [ ] Vérifier les dépendances Python et la version de Python supportée
- [ ] Vérifier le fichier de configuration (secrets, base de données, JWT)
- [ ] Exécuter l'initialisation de la base de données si nécessaire
- [ ] Tester le flux complet : lancement → authentification → partie → score

## Priorité 2 — compléter les briques serveur

- [ ] Vérifier les endpoints d'authentification et les flux de connexion
- [ ] Vérifier les endpoints de profil et leur cohérence avec le client
- [ ] Vérifier la logique de score et l'enregistrement des résultats
- [ ] Vérifier les endpoints de leaderboard / classement
- [ ] Vérifier le matchmaking multijoueur et les salles
- [ ] Vérifier les logs et la gestion des erreurs côté serveur

## Priorité 3 — sécurité et durcissement

- [ ] Extraire les secrets dans des variables d'environnement
- [ ] Sécuriser la configuration de production
- [ ] Restreindre les origines CORS et les accès réseau
- [ ] Renforcer la validation des entrées et la sanitization
- [ ] Ajouter ou améliorer le rate limiting
- [ ] Vérifier les tokens JWT et la rotation/expiration
- [ ] Passer en HTTPS/TLS en environnement de production

## Priorité 4 — anti-cheat et modération

- [ ] Vérifier et améliorer la détection de comportements suspects
- [ ] Ajouter ou consolider les logs d'anti-cheat
- [ ] Vérifier les mécanismes de signalement et de modération
- [ ] Finaliser les workflows de ban / unban / historique
- [ ] Ajouter des règles de protection contre les abus et les manipulations

## Priorité 5 — expérience utilisateur / client

- [ ] Finaliser le redesign du menu si ce n'est pas entièrement propre
- [ ] Vérifier la cohérence visuelle des thèmes et la lisibilité du texte
- [ ] Compléter la prise en charge des langues supplémentaires
- [ ] Vérifier les messages d'erreur et les feedbacks utilisateur
- [ ] Améliorer les transitions et animations si nécessaire

## Priorité 6 — contenu et assets

- [ ] Ajouter ou remplacer les assets graphiques manquants
- [ ] Ajouter des sons/jingles d'interface et de fin de partie
- [ ] Ajouter de nouvelles questions et enrichir les packs
- [ ] Vérifier les fichiers de traduction et la qualité des traductions

## Priorité 7 — fonctionnalités de roadmap / avancées

- [ ] Finaliser le système ranked / classement compétitif
- [ ] Compléter la progression et statistiques joueurs
- [ ] Vérifier le mode streamer / interactions viewers
- [ ] Améliorer le matchmaking et la qualité des parties
- [ ] Évaluer les fonctionnalités de replay / tutoriel / accessibilité

## Priorité 8 — qualité logicielle et déploiement

- [ ] Ajouter des tests unitaires et d'intégration
- [ ] Mettre en place une CI simple (lint/tests)
- [ ] Documenter les étapes de déploiement et de rollback
- [ ] Préparer un packaging ou build reproductible
- [ ] Ajouter monitoring / logs structurés / observabilité de base

## Petit backlog “quick wins”

- [ ] Vérifier les fichiers TODO/FIXME restants dans le code
- [ ] Supprimer ou clarifier les éléments obsolètes
- [ ] Faire un passage rapide sur la documentation README / QUICK_START / SERVER_CHECKLIST
- [ ] Créer une checklist de validation avant chaque release

## Points souvent oubliés mais importants

- [ ] Ajouter des tests unitaires et d’intégration pour les flux critiques
- [ ] Mettre en place une CI simple (lint, tests, vérification de build)
- [ ] Ajouter un environnement Docker / containerisation de base
- [ ] Vérifier les versions de dépendances et figer les versions de production
- [ ] Ajouter des migrations de base de données et une stratégie de backup
- [ ] Implémenter un vrai système de rôles / permissions administrateur
- [ ] Finaliser les parties multijoueur P2P / serveur si elles sont encore en TODO
- [ ] Ajouter la traçabilité des statistiques avancées comme le maximum d’ELO atteint
- [ ] Documenter les variables d’environnement, la configuration de production et les procédures de déploiement
- [ ] Ajouter un monitoring minimal (logs structurés, santé du service, alertes basiques)
