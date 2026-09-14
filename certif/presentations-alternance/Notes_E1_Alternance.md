# Notes orales — E1_Alternance

Personnaliser identité, commanditaire, rôle, dates, budget et preuves externes avant passage.

## 01. Industrialiser les données de l’entreprise — 30 s

Présenter l’entreprise de manière autorisée, votre rôle, les dates et le besoin. Vous déclarez avoir réalisé l’ensemble de la chaîne, sa montée en charge, ses corrections et évolutions. Tines est un second projet, pas une API des marts ClickHouse. Le jeu reste une preuve complémentaire explicitement identifiée pour certains critères.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 02. Transformer les données internes en usages métier — 45 s

Le candidat a confirmé l’exploitation par des équipes, sans préciser les métiers, les métriques de valeur ni un exemple de mart. Compléter avec un cas réel : besoin, champs nécessaires, résultat utilisé et bénéfice constaté. Ne pas inventer de gain de temps ou de fréquence supérieure au quotidien.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 03. Concevoir, exploiter et faire évoluer la chaîne — 45 s

Ne pas reprendre les chiffres du pipeline de monstres : ils n’appartiennent pas à ce projet. Préciser les arbitrages de scalabilité réellement réalisés et leurs mesures avant/après. L’outil de ticket, les revues ou la méthode agile n’ont pas encore été décrits.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 04. De trois sources aux marts métier — 60 s

Le flux global est rapporté par le candidat ; les protocoles ServiceNow, les dépendances exactes du DAG et le lancement de dbt doivent être précisés avec le schéma réel. Ne pas supposer que dbt est déclenché dans le même DAG si ce n’est pas le cas. Ne pas relier Tines à ClickHouse sans preuve de ce lien.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 05. Trois sources avec des contraintes différentes — 70 s

Parler de collections MongoDB plutôt que de tables si c’est le format réel. L’utilisateur parle de BDD ServiceNow : ne pas convertir cette description automatiquement en accès SQL ou REST. Les requêtes Elasticsearch renforcent la preuve d’extraction, sans suffire seules à qualifier tout le projet de big data.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 06. Convertir les données ServiceNow avant ingestion — 65 s

Ne pas généraliser : il s’agit du format rencontré dans cette intégration ServiceNow, pas d’une affirmation sur le stockage interne de tous les produits ServiceNow. Le candidat confirme le diagnostic et la conversion des strings. Aucun exemple de type, code d’erreur ni comportement de rejet n’a encore été fourni. Joindre une ligne XML anonymisée, les conversions et le résultat d’ingestion correspondant.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 07. Expliquer comment un mart est construit — 60 s

Slide de démonstration à compléter avec un modèle réel. La séparation staging/intermediate/marts n’est pas déduite du seul usage de dbt. Un lignage dbt peut faciliter l’explication s’il existe. Décrire seulement les tests ou validations effectivement utilisés.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 08. Adapter la collecte au volume et aux schémas — 55 s

Ordres de grandeur et mécanismes confirmés par le candidat. Ce sont des tailles de tables, pas des volumes ingérés chaque jour. Ne pas inventer partitionnement, sharding, cluster ou réduction de durée. Expliquer la règle de fenêtre, la prévention des trous/doublons et la gestion des nouvelles colonnes uniquement selon l’implémentation réelle. Les métriques avant/après restent à joindre.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 09. Défendre les requêtes par leur usage — 70 s

C2 demande des requêtes fonctionnelles et une documentation des sélections, conditions, jointures et optimisations. Choisir une requête que le candidat a écrite et peut expliquer. ClickHouse et Elasticsearch sont pertinents pour parler de systèmes analytiques distribués si l’architecture et le volume réels le justifient ; les seuls noms ne prouvent pas le volet big data.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 10. Justifier ClickHouse et le modèle des données — 70 s

Les modèles exacts, moteurs, clés de tri, partitions et stratégies d’upsert n’ont pas été fournis. Ne pas les déduire. Le référentiel C4 demande le formalisme Merise ; produire ou joindre le modèle fidèle à l’existant si le dossier ne le contient pas encore.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 11. Rendre la plateforme compréhensible et transmissible — 55 s

Ces rubriques organisent les preuves à sélectionner ; le candidat a confirmé l’importance de la documentation, pas la présence exhaustive de chaque rubrique. Présenter le format réel, la version, les destinataires et un exemple d’usage. Une documentation générée peut être complétée par les raisons métier des transformations.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 12. Documenter les traitements et les droits — 60 s

Restituer le registre interne, sans présenter les durées proposées comme des obligations légales ou une conformité acquise. Montrer la différence entre données de référence et données liées aux comptes. La purge se prévisualise sans --apply. Ne jamais afficher un véritable export utilisateur devant le jury. Dans cette version multi-projets, cette preuve concerne exclusivement le jeu. Les données clients EDR et les données internes nécessitent une analyse propre au contexte professionnel, non fournie ici. Ne pas leur appliquer les durées proposées pour le jeu.

Sources : docs/block1/gdpr-register.md ; docs/block1/backup-restore.md

## 13. Tines fournit les données à l’agent cyber — 70 s

Le candidat a créé les quatre stories. Le système appelant est décrit, sans attribution de toute l’application Django au candidat. Un webhook HTTP peut contribuer à C5, mais sa présence seule ne prouve pas une API REST complète ni sa sécurisation. Documenter méthodes, schémas, authentification/autorisation, isolation client, erreurs et tests réellement présents. La connexion aux EDR renforce C1 pour la collecte web.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 14. Montrer le trajet de la donnée — 105 s

Cette séquence dure 1 min 45 selon le minutage conservé. Utiliser des captures ou jeux de données autorisés et anonymisés. Les captures d’exécution Airflow, SQL et story n’ont pas encore été fournies. Si la démo Tines est rejouée, préparer un environnement de test et ne pas afficher les secrets des webhooks.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 15. Des réalisations professionnelles complémentaires — 40 s

Cette synthèse ne prononce pas une validation de compétence. Les fichiers/scraping du jeu restent des preuves complémentaires pour la diversité d’extraction. Ne pas affirmer que ServiceNow est une API tant que le mode d’accès n’est pas clarifié. Les rapports écrits doivent reprendre la même répartition et expliciter le lien entre chaque réalisation et la compétence.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 16. Revenir à l’origine d’un monstre — 0 s

Afficher cette annexe pour expliquer une jointure, la liaison du paramètre et le tri de la source sélectionnée. Ne pas remplacer le paramètre par une concaténation de texte.

Sources : db/sqlite/queries/monster_dataset.sql, Q2

## 17. Préparer les preuves d’alternance — 0 s

Le support distingue trois contextes : plateforme interne, intégration Tines et Call To AIdventure. Ne pas fusionner leurs politiques d’accès, leurs bases ou leurs résultats. Les chemins et commandes des supports initiaux restent disponibles dans leurs dossiers d’origine.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 18. Défendre les décisions sans extrapoler — 0 s

Préparer une réponse fondée sur un artefact pour chaque question. Rester précis sur les formes d’accès ServiceNow et le formalisme de l’API Tines. Les bénéfices de la documentation peuvent être démontrés par un usage réel sans inventer de métrique.

Sources : Alternance : description du candidat ; pièces techniques à joindre
