# E5 — Interférence entre deux états de combat

Document établi le 14 septembre 2026 à partir de l'historique Git et d'une reproduction locale. Il décrit un défaut technique historique reconstruit pour la certification, pas un incident observé en production. La date de découverte, le déclarant, un ticket d'origine, le nombre de joueurs concernés et un déploiement ne sont pas établis par les pièces consultées.

## Contexte et comportement attendu

Call To AIdventure conserve un état de partie par session. Deux joueurs peuvent posséder chacun un joueur et un monstre distincts. Une action initiée dans le combat A doit modifier uniquement les objets de A, même si un autre combat B est restauré avant la résolution de cette action.

Le cas d'étude met en évidence une violation de cette règle dans l'ancienne implémentation. L'impact potentiel est une corruption de progression entre combats. Aucun volume d'impact réel ni durée d'indisponibilité n'est avancé.

## Pièces vérifiées

- Code antérieur : parent du commit `8a3cf39702a0920582862904c28ce65f74a545cf`, fichier `src/combat/core.py`.
- Correctif versionné : commit `8a3cf39`, daté du 3 septembre 2026. Il comprend la refonte du cœur de combat et de `src/django/game/services/game_engine.py`, ainsi que d'autres modifications.
- Code testé : révision `a79321ed8b0a0a945901fd92fef9ece64ea0c48d`.
- Reproduction : `reproduce_incident.py` ; résultats dans `preuves/incident-combat.json`.
- Non-régression : `game.tests.CombatEngineTests.test_combat_actions_are_isolated_between_session_states`.
- Lot applicatif : 44 tests ciblés réussis le 14 septembre 2026 ; liste et commandes dans `preuves/verification.md`.

## Reproduction contrôlée

Chaque monstre commence avec 8 PV. Les dégâts de l'attaque sont fixés à 3 par un mock de l'aléatoire.

1. Restaurer l'état du combat A.
2. Avant l'attaque prévue pour A, restaurer l'état du combat B.
3. Reprendre l'action initialement destinée à A.
4. Observer les PV des deux monstres.

| Version | PV de A après action | PV de B après action | Interprétation |
|---|---:|---:|---|
| Attendu | 5 | 8 | Seul le combat A est touché |
| Code historique | 8 | 5 | L'attaque touche le combat B |
| Code actuel | 5 | 8 | L'action utilise explicitement la session A |

La reproduction est une imbrication déterministe des fonctions cœur, pas un lancement de threads ni une charge HTTP concurrente. Elle illustre le changement de références possible entre restauration et résolution. Le script lit l'ancien code dans Git et l'exécute dans un module isolé sans le copier dans le chemin applicatif. Il ne change ni branche ni base de données et ne contacte aucun fournisseur.

```powershell
uv run python certif/presentation-bloc3/reproduce_incident.py
```

## Cause racine et diagnostic

L'ancien `combat.core` utilisait `player`, `current_monster`, `combat_log` et `player_is_defending` comme variables globales de module. `restore_combat` remplaçait ces références. `player_action` et `monster_attack` lisaient ensuite implicitement cet état partagé.

L'adaptateur Django restaurait les données de la partie avant l'action, mais une restauration de B intercalée à cet endroit pouvait remplacer les références utilisées par A. L'isolement du stockage en session ne garantissait donc pas l'isolement de la fonction métier dans un même processus.

Le calcul des dégâts n'est pas la cause dans la reproduction : il est fixé à 3 et reste correct. L'identité de la cible est incorrecte. Une réponse HTTP réussie ou un compteur de combats ne suffit pas à détecter cette violation d'invariant.

La lecture du diff local fournit la preuve de l'évolution. Aucune recherche externe effectuée à l'époque ni procédure de débogage enregistrée dans un outil de ticket n'a été retrouvée ; elles ne sont pas inventées ici.

## Solution existante

Le correctif introduit `CombatSession`, qui contient joueur, monstre, journal et état de défense. Le chemin Django crée ou restaure une instance à partir de l'état de la partie, puis la passe explicitement à :

- `resolve_player_action(session, action)` ;
- `resolve_monster_attack(session)`.

`GameEngine` réaffecte ensuite `state['player']` et `state['current_monster']` depuis cette session de combat. Le chemin Django ne dépend plus du dernier combat restauré dans les variables globales historiques.

## Validation et limites

Le script vérifie par assertions que l'ancien code reproduit `(A=8, B=5)` et que le code actuel produit `(A=5, B=8)` pour le même scénario conceptuel.

Le test Django d'isolation complète cette reproduction : il joue une attaque sur un état, puis une défense sur un second état et vérifie séparément leurs PV. Il ne constitue pas non plus un test multi-thread. Les tests de combat, requêtes, sauvegardes, personnages, templates, parcours simulé et métriques sélectionnés passent : 44 tests au total.

Cela ne démontre pas l'absence de toutes les races applicatives. Restent notamment à examiner le partage du graphe, la concurrence de deux requêtes sur une même sauvegarde, les caches et le comportement multi-worker. Aucune réparation de données historiques ni mise en production du correctif n'a été réalisée pendant la préparation de ce support.

## Monitorage C20

Le dépôt contient `/metrics`, des compteurs de jeu et d'IA, des histogrammes de durée, les configurations Prometheus/Grafana et des règles Alertmanager. Les loggers `agents` et `retrieval` écrivent en console avec date, niveau, logger et message.

Exemples de règles présentes :

| Signal | Condition configurée | Maintien |
|---|---|---|
| Opérations IA indisponibles | augmentation > 2 sur 10 min, par série | 2 min |
| Latence IA | p95 > 30 s, calcul sur 15 min | 10 min |
| Sorties structurées invalides | augmentation > 0 sur 15 min | 1 min |
| Erreurs RAG | augmentation > 2 sur 15 min | 2 min |

Le récepteur Alertmanager nommé `local-log` n'a pas de configuration de notification. Son nom ne prouve pas une journalisation des notifications. La chaîne de réception externe n'est pas démontrée. Aucune règle actuelle ne détecte directement l'erreur d'isolation de combat.

La métrique de durée navigateur compte le temps jusqu'aux choix redevenus utilisables pour les tours de récit ; elle exclut combats, fins et échecs. Les labels de métriques évitent les identités et les prompts, mais les messages d'exception et les journaux doivent aussi être examinés avant partage. Le format des journaux est du texte structuré en champs, pas du JSON.

## Actions à compléter avant la soutenance

1. Rattacher ce dossier à un ticket réel de suivi, en conservant sa date de création actuelle et sans inventer une chronologie passée.
2. Ajouter les échanges et dates de découverte uniquement s'ils sont disponibles.
3. Montrer localement la collecte, le tableau de bord et une notification de test autorisée, avec dates et rétablissement de la configuration initiale.
4. Ajouter un contrôle synthétique des invariants de combat ou des assertions instrumentées sans identifiants personnels ; cette amélioration n'est pas implémentée ici.
5. Tester concurrence et charge sur les chemins applicatifs concernés.
6. Conserver la référence de l'image réellement déployée, la validation après livraison et la stratégie de rollback compatible avec les migrations.

Le dossier constitue une documentation rétrospective vérifiable. Il ne se substitue pas aux preuves opérationnelles encore manquantes pour C20/C21.
