# Intégration de l'alternance dans les présentations

Cette révision repose sur les descriptions du candidat, sans accès au code, aux données ou aux outils de l'entreprise. Elle conserve les présentations initiales. Les résultats locaux de Call To AIdventure ne sont jamais attribués aux réalisations professionnelles.

## Répartition proposée

| Épreuve | Présentation proposée | Apport principal |
|---|---|---|
| E1 | Dataplateforme principale ; Tines et jeu en compléments distincts | Collecte multi-source, SQL, transformations, stockage, documentation et interfaces |
| E2 | Étude des benchmarks cyber et critères de sélection ; configuration du jeu en complément | C6 et contribution à C7 ; C8 via les preuves techniques disponibles |
| E3 | Jeu pour l'API/monitoring/CI ; Tines pour les outils de l'agent ; runner pour l'évaluation | Intégration et tests réels de modèles |
| E4 | Jeu principal ; demandes et contribution de bout en bout en entreprise | Compléments sur besoins et coordination |
| E5 | Proposition ServiceNow/ClickHouse ; cas de combat initial conservé en alternative | Cause et solution décrites ; preuves de run et contexte applicatif IA à établir |

Les rapports et les slides doivent présenter les mêmes contextes et responsabilités. Les modalités de mobilisation de plusieurs réalisations sont à aligner avec les consignes du centre ; aucun lien technique entre projets n'est inventé.

## Faits confirmés par le candidat

### Dataplateforme

- Réalisation de toute la chaîne, prise en charge de la scalabilité, correction des bugs et demandes de fonctionnalités.
- DAG Airflow quotidien, alimentation ClickHouse et transformations via dbt vers des marts utilisés par les équipes.
- Sources : MongoDB, ServiceNow et requêtes Elasticsearch.
- Documentation importante dans le projet.
- Selon les tables, quelques dizaines de milliers à plusieurs dizaines de millions de lignes. Ce n'est pas le volume quotidien d'ingestion.
- Plages de récupération quotidienne dynamiques selon les tables et ajout à la volée de colonnes absentes du schéma ClickHouse.
- Incident ServiceNow : chaînes brutes provenant de XML incompatibles avec les types ClickHouse ; système de validation et conversion développé après investigation.

Ce contexte renforce C1/C2/C3/C4. Les volumes et adaptations concrètes renforcent l'argument de passage à l'échelle ; le caractère distribué n'est pas déduit du nom des produits. Le mode de récupération ServiceNow reste à préciser : la représentation XML du flux est confirmée, pas un accès REST précis. Le convertisseur constitue un exemple direct de normalisation. Les modèles Merise et traitements de données personnelles restent à montrer.

### Benchmarks

- Veille sur environ dix benchmarks cyber pour LLM, open source ou utilisables gratuitement.
- Critères comprenant absence de LLM-as-judge et human-as-judge pour le scoring, adaptabilité aux usages cyber et licences.
- Application exécutant des benchmarks cyber avec scores ainsi que des tests de performance : P50, P95, P99, vitesse, concurrence.
- Résultats et métriques enregistrés en base de données.
- Un seul modèle a réellement été exploité, le seul disponible dans l'architecture de l'entreprise. Famille Qwen ; le candidat mentionne « Qwen3.8-27B » de mémoire, référence exacte à confirmer.
- Le script est conçu pour être agnostique des modèles et des benchmarks. Le candidat dispose de preuves de runs, non encore transmises.

L'étude fournit du contenu C6 ; cadence, partage et traces restent à joindre. C7 reste partielle : pas de comparaison empirique multi-modèles à ce stade. Un seul modèle disponible est une contrainte à expliquer, pas une recommandation comparative. C12 est directement renforcée par l'application d'évaluation. C11 exige plus qu'une base de résultats : suivi et restitution opérationnels, et alertes selon le périmètre. C13 n'est pas couvert par une simple campagne de benchmarks.

### Tines

- Quatre stories commencent par un webhook servant d'endpoint.
- Une application Django intégrant un analyste LLM permet à l'agent d'appeler ces endpoints selon un contrat précis pour des types d'entité cyber.
- Les stories interrogent les consoles EDR nécessaires et renvoient les données obtenues.

Cette réalisation contribue à C1 et potentiellement C5, avec un contrat REST et les règles d'accès à expliciter. Les webhooks ne constituent pas automatiquement une API REST sécurisée. Elle contribue à C10 sur la partie outils/connecteurs ; la responsabilité personnelle concernant le code Django et l'agent n'a pas été revendiquée. Elle ne démontre pas C9 à elle seule : les endpoints décrits exposent les données EDR, pas le modèle d'IA.

## Pièces à sélectionner

| Sujet | Pièces utiles |
|---|---|
| Plateforme / extraction | Schéma réel, DAG, extrait de run, mode de collecte et d'actualisation par source |
| SQL / qualité | Modèle dbt expliqué, exemple de nettoyage et rapprochement, entrée/sortie d'un mart |
| Stockage / charge | Modèle, choix ClickHouse, volume, goulot et mesure avant/après d'une optimisation |
| Documentation | Une page effectivement rédigée, son public et son usage |
| Veille | Liste des benchmarks, matrice, exclusions, versions, dates et preuve de partage |
| Évaluation | Modèles exécutés, scores, percentiles avec unité, charge, erreurs, nombre de répétitions |
| Runner | Schéma BDD réel, commande, configuration, gestion d'échec et tests existants |
| Tines | Une story anonymisée, contrat, requête/réponse, contrôle des accès et séparation des clients |
| Coordination | Demande réelle, arbitrage, échanges et validation du changement |
| Incident | Symptôme, cause, reproduction, correctif, validation et trace de livraison |

## Limites maintenues

Pas de chiffres d'entreprise inventés, pas de conclusions sur la licence actuelle, pas de conformité globale RGPD/REST/accessibilité revendiquée. Le registre du jeu concerne uniquement le jeu. Les scores cyber n'établissent pas la qualité narrative du modèle du jeu. Un incident de cybersécurité traité par l'agent n'est pas un bug de l'application résolu par le candidat.

## Fichiers

- E1_Alternance : 15 slides principales et 3 annexes, 15 minutes.
- Bloc2_Alternance : E2 15 minutes + E3 20 minutes, 3 annexes ; exports E2/E3 séparés.
- Bloc3_Alternance : E4 20 minutes + E5 10 minutes, 3 annexes ; exports E4/E5 séparés. L'E5 entreprise est préparatoire : les artefacts d'incident et le contexte requis restent à étayer. L'E5 du jeu reste inchangé dans le dossier initial.
- Chaque export comprend un PowerPoint modifiable, un PDF et des notes orales Markdown.

```powershell
uv run --with python-pptx --with reportlab python certif/presentations-alternance/generate_slides.py
```

Le générateur charge uniquement les définitions et fonctions des scripts précédents ; il n'exécute pas leurs exports et ne réécrit pas les supports initiaux.
