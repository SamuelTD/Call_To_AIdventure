# Notes orales — Bloc2_Alternance

Personnaliser identité, commanditaire, rôle, dates, budget et preuves externes avant passage.

## 01. Choisir comment évaluer les LLM en cybersécurité — 90 s

Travaux rapportés par le candidat ; les noms des benchmarks et modèles, résultats et versions restent à joindre. Les composants configurés du jeu restent un complément C8 clairement séparé. Les scores cyber ne sont pas utilisés pour justifier le modèle narratif du jeu.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 02. Évaluer la pertinence et les contraintes d’usage — 90 s

Le candidat confirme que l’application exécute les benchmarks et obtient des scores. Aucun modèle nommé, classement, seuil ni recommandation finale n’est encore fourni. La performance mesurée doit préciser le périmètre : requête complète, premier token, décodage ou autre métrique réellement implémentée.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 03. Sélectionner des évaluations adaptées — 90 s

L’absence de LLM/humain comme juge est un critère rapporté de sélection. Elle ne démontre pas automatiquement une évaluation objective ou exhaustive. Expliquer la règle effective : assertion, sortie attendue, exécution, tests ou autre mécanisme, sans en inventer un. Open source et gratuit ne sont pas synonymes. Cette slide décrit l’étude passée, pas un avis juridique sur les licences actuelles.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 04. Environ dix benchmarks cyber étudiés — 90 s

Ne plus qualifier la veille comme absente : le candidat l’a réalisée. Distinguer contenu de recherche confirmé et modalités non décrites. Le référentiel demande une veille organisée et partagée ; joindre les dates, outils et restitutions effectivement utilisés. N’inventer ni suivi hebdomadaire ni présentation d’équipe.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 05. Un modèle exécuté, un runner extensible — 90 s

Le candidat mentionne « Qwen3.8-27B » de mémoire et doit vérifier la référence. Le support évite de figer cet identifiant. Un seul modèle réellement exécuté : ne pas annoncer benchmark multi-modèles ni sélection du meilleur modèle. C7 peut être complétée par une analyse de services candidats et des exclusions documentées, mais la contrainte du modèle disponible ne remplace pas cette analyse.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 06. Une génération hébergée, un RAG local — 90 s

La justification actuelle vise la génération multilingue et structurée sans héberger un gros modèle, un petit corpus vectoriel local et des transitions explicites. Le lore retrouvé est injecté dans les prompts envoyés au service de génération : rendre ce flux clair. Ne pas présenter cette décision qualitative comme un benchmark déjà conclu. Cette slide concerne exclusivement Call To AIdventure, pas l’application de benchmark ni l’analyste cyber de l’entreprise. Elle fournit une preuve technique complémentaire C8.

Sources : docs/block2/ai-requirements-and-selection.md ; docs/rag-system.md

## 07. Rendre la configuration explicite — 90 s

Lire les valeurs réellement configurées avant démonstration. Le nom du modèle par défaut est une chaîne du dépôt, pas une vérification de disponibilité commerciale. La commande check_ai_services valide les paramètres ; son option --connect vérifie Ollama, pas une génération réelle du fournisseur. Ne jamais afficher le fichier .env. Cette slide concerne exclusivement Call To AIdventure, pas l’application de benchmark ni l’analyste cyber de l’entreprise. Elle fournit une preuve technique complémentaire C8.

Sources : src/agents/runtime_config.py ; .env.example

## 08. Préparer le contexte avant la génération — 90 s

Le dry-run exécuté prépare 36 fragments de personnages et 21 de lieux. La documentation ancienne annonce 39 : la mesure du code courant prime. Aucun serveur Ollama ni Chroma n’a été testé en ligne ici. L’objectif de rappel des sources doit être mesuré séparément ; le runner actuel ne le calcule pas. Cette slide concerne exclusivement Call To AIdventure, pas l’application de benchmark ni l’analyste cyber de l’entreprise. Elle fournit une preuve technique complémentaire C8.

Sources : src/retrieval/ ; vérification du 14/09/2026

## 09. Conserver et interpréter chaque campagne — 90 s

Le candidat peut fournir des preuves de runs mais elles ne sont pas encore jointes. La présence de métadonnées précises en base n’est pas supposée : montrer ce qui est réellement enregistré et compléter la traçabilité si nécessaire. La reproductibilité ne découle pas automatiquement du stockage des métriques.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 10. Une veille concrète et un outil d’évaluation opérationnel — 90 s

L’étude de benchmarks n’est pas la sélection d’un service LLM. On peut expliquer pourquoi l’architecture impose un candidat disponible, puis comparer les alternatives documentées sans inventer d’exécutions. Ne pas annoncer que tous les besoins C7 sont satisfaits. Les preuves C8 du jeu restent séparées de la configuration entreprise.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 11. Intégration et évaluation : des preuves complémentaires — 100 s

L’application Django cyber est distincte du jeu. Le candidat n’a pas déclaré avoir créé toute cette application ou son agent ; sa contribution confirmée porte sur Tines. Le runner de benchmarks n’est pas présenté comme connecté à l’agent sans confirmation de ce lien.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 12. Exposer trois points d’entrée documentés — 100 s

Le health renvoie des booléens, pas un ping fournisseur. Décrire le body {"choice": "Open the gate"}. L’API réutilise StepGameView pour déclencher le moteur. Le contrat YAML existe, mais quelques écarts contrat/code sont identifiés en annexe et ne doivent pas être présentés comme une conformité OpenAPI parfaite. Contexte de cette preuve conservée : Call To AIdventure. Aucun résultat de cette slide ne doit être attribué aux projets entreprise.

Sources : src/django/game/ai_api.py ; docs/block2/openapi.yaml

## 13. Contrôler avant de solliciter le modèle — 100 s

Résultats vérifiés : utilisateur étranger rejeté, choix arbitraire rejeté avec liste renseignée, CSRF refusé sans jeton et quota exercé. Limite importante : le code ne rejette pas par ce contrôle un choix lorsque current_choices est vide. Ne pas affirmer une prévention générale des injections de prompt. Ne pas montrer d’identifiants de session réels. Contexte de cette preuve conservée : Call To AIdventure. Aucun résultat de cette slide ne doit être attribué aux projets entreprise.

Sources : src/django/game/ai_api.py ; src/django/game/test_ai_api.py

## 14. L’agent demande des données aux stories Tines — 100 s

C10 : cette réalisation contribue à l’intégration des outils de l’agent, mais il faut délimiter qui a écrit l’adaptateur Django, les appels et la logique de l’agent. C9 reste porté par l’API du jeu, car Tines n’est pas décrit comme un endpoint d’inférence. Préciser les quatre types d’entité sans inventer leurs noms. Authentification, autorisation client, gestion des erreurs et tests restent à joindre.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 15. Valider la forme et protéger la progression — 100 s

Les tests ciblés ont exercé les prompts FR, la reprise narrative, l’échec sans progression, les outils de soin et les objectifs. La classe SaveGamePersistenceTests n’appartient pas au lot de 33 exécuté ici : ne pas attribuer à ce lot la totalité des tests de persistance. Les cas sont simulés ; aucune qualité linguistique en réel n’est mesurée. Contexte de cette preuve conservée : Call To AIdventure. Aucun résultat de cette slide ne doit être attribué aux projets entreprise.

Sources : src/agents/schemas.py ; src/django/game/tests.py

## 16. Observer disponibilité, qualité et coût — 100 s

Expliquer compteur et histogramme, ainsi que la fenêtre de calcul. Les métriques exposées ont des tests ciblés, mais la chaîne Prometheus/Grafana n’a pas été lancée pour ce support. Les tokens peuvent dépendre des données d’usage fournies par le service ; l’estimation de coût nécessite des tarifs à jour. Les labels bornés évitent données sensibles et cardinalité excessive. Contexte de cette preuve conservée : Call To AIdventure. Aucun résultat de cette slide ne doit être attribué aux projets entreprise.

Sources : src/observability/ ; docs/block2/monitoring-slos.md ; monitoring/

## 17. Transformer un signal en action — 100 s

Le seuil précis de RAG documenté est plus de deux échecs en quinze minutes. La latence doit être élevée pendant dix minutes. Préparer un déclenchement contrôlé en bac à sable avec capture horodatée et retour à la règle initiale. Ce projet ajuste l’intégration ; il ne réentraîne pas automatiquement le modèle distant. Contexte de cette preuve conservée : Call To AIdventure. Aucun résultat de cette slide ne doit être attribué aux projets entreprise.

Sources : docs/block2/monitoring-slos.md ; monitoring/alertmanager/

## 18. Exécuter des benchmarks cyber et de performance — 100 s

L’utilisateur confirme que le runner obtient des scores et métriques. Il n’a pas fourni de logs ni valeurs ; aucun taux de réussite n’est inventé. Montrer aussi la validation du dataset, les dépendances, la gestion d’échecs et les tests du runner s’ils existent. C12 est particulièrement bien servi par ce travail, sans prétendre qu’une étape d’entraînement existe.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 19. Présenter un run du modèle disponible — 100 s

Présenter le runner comme réalisé et exécuté. Les champs de la slide sont des emplacements pour une preuve existante, pas une simulation. Le seul modèle déclaré est Qwen avec version à confirmer. Mesure de performance du service, qualité cyber et tests du logiciel de benchmark sont trois périmètres différents.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 20. Automatiser les contrôles avant livraison — 100 s

Décrire PR, push main et déclenchement manuel. Le conteneur est construit et chargé localement dans le job : le workflow ne prouve pas la publication d’une image dans un registre. Le smoke test utilise une clé factice et RAG désactivé ; il vérifie le démarrage HTTP, pas le modèle. La couverture 55 % est un seuil configuré, pas une mesure obtenue aujourd’hui. Contexte de cette preuve conservée : Call To AIdventure. Aucun résultat de cette slide ne doit être attribué aux projets entreprise.

Sources : .github/workflows/block2-ai.yml ; docs/block2/delivery.md

## 21. Promouvoir un artefact, prévoir le retour arrière — 100 s

Garder au moins un artefact connu bon. Le modèle hébergé peut évoluer si son identifiant n’est pas une version figée ; expliciter cette limite. Versionner une collection RAG fait partie de la procédure à organiser, pas d’une preuve d’activation déjà produite ici. Staging, registre et liens de jobs restent à renseigner. Contexte de cette preuve conservée : Call To AIdventure. Aucun résultat de cette slide ne doit être attribué aux projets entreprise.

Sources : docs/block2/delivery.md ; src/evaluation/runner.py

## 22. Montrer une preuve par réalisation — 100 s

Les slides CI et monitoring conservées concernent le jeu. Ne pas annoncer une CI, un déploiement ou une alerte du runner qui n’ont pas été décrits. Joindre un export réel avant passage. Les preuves locales du jeu restent disponibles dans certif/presentation-bloc2/preuves/.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 23. Écarts repérés entre contrat et code — 0 s

Ces observations proviennent du code local, sans test d’exploitation. Le lot courant couvre une liste de choix non vide. Ajouter des tests de contrat et corriger les écarts avant de revendiquer une conformité stricte. Ce support ne change pas le périmètre de la demande en tâche de développement. Contexte de cette preuve conservée : Call To AIdventure. Aucun résultat de cette slide ne doit être attribué aux projets entreprise.

Sources : docs/block2/openapi.yaml ; src/django/game/ai_api.py

## 24. Assembler les pièces sans mélanger les projets — 0 s

Le dossier préparatoire joint précise les preuves à fournir. Aucune source entreprise n’a été inspectée directement pendant cette révision. Les intitulés et détails reposent sur les explications du candidat.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 25. Défendre le protocole et les interfaces — 0 s

Répondre à partir des implémentations et résultats réels. Aucun lien entre le choix du modèle narratif du jeu et les scores cyber n’est établi. La contribution aux endpoints Tines ne signifie pas création de toute l’application analyste.

Sources : Alternance : description du candidat ; pièces techniques à joindre
