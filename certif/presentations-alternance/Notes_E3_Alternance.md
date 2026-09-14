# Notes orales — E3_Alternance

Personnaliser identité, commanditaire, rôle, dates, budget et preuves externes avant passage.

## 01. Intégration et évaluation : des preuves complémentaires — 100 s

L’application Django cyber est distincte du jeu. Le candidat n’a pas déclaré avoir créé toute cette application ou son agent ; sa contribution confirmée porte sur Tines. Le runner de benchmarks n’est pas présenté comme connecté à l’agent sans confirmation de ce lien.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 02. Exposer trois points d’entrée documentés — 100 s

Le health renvoie des booléens, pas un ping fournisseur. Décrire le body {"choice": "Open the gate"}. L’API réutilise StepGameView pour déclencher le moteur. Le contrat YAML existe, mais quelques écarts contrat/code sont identifiés en annexe et ne doivent pas être présentés comme une conformité OpenAPI parfaite. Contexte de cette preuve conservée : Call To AIdventure. Aucun résultat de cette slide ne doit être attribué aux projets entreprise.

Sources : src/django/game/ai_api.py ; docs/block2/openapi.yaml

## 03. Contrôler avant de solliciter le modèle — 100 s

Résultats vérifiés : utilisateur étranger rejeté, choix arbitraire rejeté avec liste renseignée, CSRF refusé sans jeton et quota exercé. Limite importante : le code ne rejette pas par ce contrôle un choix lorsque current_choices est vide. Ne pas affirmer une prévention générale des injections de prompt. Ne pas montrer d’identifiants de session réels. Contexte de cette preuve conservée : Call To AIdventure. Aucun résultat de cette slide ne doit être attribué aux projets entreprise.

Sources : src/django/game/ai_api.py ; src/django/game/test_ai_api.py

## 04. L’agent demande des données aux stories Tines — 100 s

C10 : cette réalisation contribue à l’intégration des outils de l’agent, mais il faut délimiter qui a écrit l’adaptateur Django, les appels et la logique de l’agent. C9 reste porté par l’API du jeu, car Tines n’est pas décrit comme un endpoint d’inférence. Préciser les quatre types d’entité sans inventer leurs noms. Authentification, autorisation client, gestion des erreurs et tests restent à joindre.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 05. Valider la forme et protéger la progression — 100 s

Les tests ciblés ont exercé les prompts FR, la reprise narrative, l’échec sans progression, les outils de soin et les objectifs. La classe SaveGamePersistenceTests n’appartient pas au lot de 33 exécuté ici : ne pas attribuer à ce lot la totalité des tests de persistance. Les cas sont simulés ; aucune qualité linguistique en réel n’est mesurée. Contexte de cette preuve conservée : Call To AIdventure. Aucun résultat de cette slide ne doit être attribué aux projets entreprise.

Sources : src/agents/schemas.py ; src/django/game/tests.py

## 06. Observer disponibilité, qualité et coût — 100 s

Expliquer compteur et histogramme, ainsi que la fenêtre de calcul. Les métriques exposées ont des tests ciblés, mais la chaîne Prometheus/Grafana n’a pas été lancée pour ce support. Les tokens peuvent dépendre des données d’usage fournies par le service ; l’estimation de coût nécessite des tarifs à jour. Les labels bornés évitent données sensibles et cardinalité excessive. Contexte de cette preuve conservée : Call To AIdventure. Aucun résultat de cette slide ne doit être attribué aux projets entreprise.

Sources : src/observability/ ; docs/block2/monitoring-slos.md ; monitoring/

## 07. Transformer un signal en action — 100 s

Le seuil précis de RAG documenté est plus de deux échecs en quinze minutes. La latence doit être élevée pendant dix minutes. Préparer un déclenchement contrôlé en bac à sable avec capture horodatée et retour à la règle initiale. Ce projet ajuste l’intégration ; il ne réentraîne pas automatiquement le modèle distant. Contexte de cette preuve conservée : Call To AIdventure. Aucun résultat de cette slide ne doit être attribué aux projets entreprise.

Sources : docs/block2/monitoring-slos.md ; monitoring/alertmanager/

## 08. Exécuter des benchmarks cyber et de performance — 100 s

L’utilisateur confirme que le runner obtient des scores et métriques. Il n’a pas fourni de logs ni valeurs ; aucun taux de réussite n’est inventé. Montrer aussi la validation du dataset, les dépendances, la gestion d’échecs et les tests du runner s’ils existent. C12 est particulièrement bien servi par ce travail, sans prétendre qu’une étape d’entraînement existe.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 09. Présenter un run du modèle disponible — 100 s

Présenter le runner comme réalisé et exécuté. Les champs de la slide sont des emplacements pour une preuve existante, pas une simulation. Le seul modèle déclaré est Qwen avec version à confirmer. Mesure de performance du service, qualité cyber et tests du logiciel de benchmark sont trois périmètres différents.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 10. Automatiser les contrôles avant livraison — 100 s

Décrire PR, push main et déclenchement manuel. Le conteneur est construit et chargé localement dans le job : le workflow ne prouve pas la publication d’une image dans un registre. Le smoke test utilise une clé factice et RAG désactivé ; il vérifie le démarrage HTTP, pas le modèle. La couverture 55 % est un seuil configuré, pas une mesure obtenue aujourd’hui. Contexte de cette preuve conservée : Call To AIdventure. Aucun résultat de cette slide ne doit être attribué aux projets entreprise.

Sources : .github/workflows/block2-ai.yml ; docs/block2/delivery.md

## 11. Promouvoir un artefact, prévoir le retour arrière — 100 s

Garder au moins un artefact connu bon. Le modèle hébergé peut évoluer si son identifiant n’est pas une version figée ; expliciter cette limite. Versionner une collection RAG fait partie de la procédure à organiser, pas d’une preuve d’activation déjà produite ici. Staging, registre et liens de jobs restent à renseigner. Contexte de cette preuve conservée : Call To AIdventure. Aucun résultat de cette slide ne doit être attribué aux projets entreprise.

Sources : docs/block2/delivery.md ; src/evaluation/runner.py

## 12. Montrer une preuve par réalisation — 100 s

Les slides CI et monitoring conservées concernent le jeu. Ne pas annoncer une CI, un déploiement ou une alerte du runner qui n’ont pas été décrits. Joindre un export réel avant passage. Les preuves locales du jeu restent disponibles dans certif/presentation-bloc2/preuves/.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 13. Écarts repérés entre contrat et code — 0 s

Ces observations proviennent du code local, sans test d’exploitation. Le lot courant couvre une liste de choix non vide. Ajouter des tests de contrat et corriger les écarts avant de revendiquer une conformité stricte. Ce support ne change pas le périmètre de la demande en tâche de développement. Contexte de cette preuve conservée : Call To AIdventure. Aucun résultat de cette slide ne doit être attribué aux projets entreprise.

Sources : docs/block2/openapi.yaml ; src/django/game/ai_api.py

## 14. Assembler les pièces sans mélanger les projets — 0 s

Le dossier préparatoire joint précise les preuves à fournir. Aucune source entreprise n’a été inspectée directement pendant cette révision. Les intitulés et détails reposent sur les explications du candidat.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 15. Défendre le protocole et les interfaces — 0 s

Répondre à partir des implémentations et résultats réels. Aucun lien entre le choix du modèle narratif du jeu et les scores cyber n’est établi. La contribution aux endpoints Tines ne signifie pas création de toute l’application analyste.

Sources : Alternance : description du candidat ; pièces techniques à joindre
