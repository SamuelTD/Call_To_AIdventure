# Proposition de cas E5 — Typage à l'ingestion ServiceNow / ClickHouse

Cette fiche prépare le récit d'un incident réel décrit par le candidat. Elle n'est pas une reproduction effectuée par l'assistant ni une preuve de déploiement. Aucun accès entreprise, code de conversion, journal d'erreur ou résultat de test n'a été fourni à ce stade.

## Faits décrits

Le candidat a réalisé et maintenu une plateforme alimentée quotidiennement par Airflow à partir de MongoDB, ServiceNow et Elasticsearch, avec stockage ClickHouse et transformations dbt. Les tables vont de quelques dizaines de milliers à plusieurs dizaines de millions de lignes.

Lors de l'ingestion de données ServiceNow, de nombreux échecs de validation de type se produisaient dans ClickHouse. L'investigation a identifié, dans ce flux, une représentation XML contenant des valeurs lues comme chaînes brutes. Le candidat a développé un système de validation et de transformation de ces chaînes vers les types de données attendus.

Il ne s'agit pas d'affirmer que ServiceNow stocke toutes ses données en XML : on décrit le format rencontré dans l'intégration.

## Récit proposé

1. **Besoin et impact** : alimenter les tables cibles avec des valeurs exploitables. Ajouter l'impact réellement constaté des échecs : exécution échouée, retard ou table partiellement alimentée, uniquement selon les faits.
2. **Détection** : joindre le message exact et expliquer comment il a été découvert. Logs, interface Airflow, notification ou signalement ne sont pas encore précisés.
3. **Reproduction** : isoler un extrait XML anonymisé, le champ concerné, le type attendu et la commande d'ingestion.
4. **Cause** : absence ou inadéquation de conversion entre représentation source en chaînes et types cibles.
5. **Solution** : montrer le convertisseur et les contrôles réellement ajoutés. Préciser les règles et le traitement d'une valeur impossible à convertir.
6. **Validation** : reprendre le même échantillon, montrer la valeur convertie et le résultat ClickHouse ; ajouter les tests existants et une preuve de reprise.
7. **Livraison et suivi** : joindre la référence du correctif, sa validation et les contrôles d'exploitation disponibles.

## Ne pas confondre deux évolutions

- **Conversion des valeurs** : résolution du défaut de typage décrit.
- **Ajout dynamique de colonnes** : adaptation du schéma aux champs nouveaux, autre mécanisme de la plateforme.

Les fenêtres de collecte dynamiques constituent également une preuve d'adaptation à la charge, pas une cause ou correction de ce défaut sans lien supplémentaire établi.

## Pièces manquantes

| Élément | Statut |
|---|---|
| Symptôme, cause générale et contribution personnelle | Décrits par le candidat |
| Format XML dans le flux | Décrit par le candidat |
| Type/champ/valeur précis | À fournir |
| Message d'erreur et impact mesuré | À fournir |
| Code et référence Git | À fournir |
| Résultat avant/après et tests | À fournir |
| Dates, ticket et livraison | À fournir |
| Surveillance et alerte effectives | À préciser |
| Lien de la plateforme au contexte applicatif IA demandé en E5 | Non établi à ce stade |

## Positionnement dans la certification

Ce cas renforce directement C3 (normalisation) et la discussion C4 (import et types) dans E1. Il fournit aussi un exemple clair de démarche de résolution pour C21. Pour en faire le cas principal E5, il faut documenter le monitorage C20 et l'adéquation du contexte au périmètre de l'épreuve. Le dossier de combat de Call To AIdventure reste une alternative déjà liée à une application IA et reproduite localement.

Les 44 tests et l'avant/après du combat du jeu ne constituent aucune preuve de validation de ce convertisseur.
