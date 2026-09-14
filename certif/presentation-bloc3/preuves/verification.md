# Vérifications — Bloc 3 — 14 septembre 2026

## Tests ciblés

```powershell
uv run python src/django/manage.py test game.tests.CombatEngineTests game.tests.SecurityBoundaryTests game.tests.ProductQualityTemplateTests game.tests.BrowserSmokeJourneyTests game.tests.SaveGamePersistenceTests game.tests.CharacterTemplateTests game.tests.MetricsEndpointTests --noinput
```

Résultat : 44 tests réussis en 6,091 secondes ; aucun problème détecté par les checks Django. Base de tests créée puis détruite. Les appels IA sont simulés. La classe nommée BrowserSmokeJourneyTests utilise le client Django ; elle n'exécute pas un navigateur JavaScript réel. Aucun pourcentage de couverture n'a été calculé.

## Cohérence des migrations

```powershell
uv run python src/django/manage.py makemigrations --check --dry-run
```

Résultat : `No changes detected`. Aucune migration ajoutée.

## Incident

```powershell
uv run python certif/presentation-bloc3/reproduce_incident.py
```

Avant correctif : monstre A 8 PV, monstre B 5 PV. Code actuel : monstre A 5 PV, monstre B 8 PV. Détails, révisions Git et limites dans `incident-combat.json`.

L'ancien code est lu depuis le parent de `8a3cf39`, sans changement de checkout. Le résultat est une reproduction d'imbrication au niveau du cœur de combat, pas une preuve d'incident de production ou un test de charge concurrent.

## Périmètre non exécuté

Pas d'appel de génération réel, d'audit manuel d'accessibilité, de test de charge, de lancement Prometheus/Grafana, de notification externe, de CI distante, de build Docker ou de déploiement pendant cette préparation. Les slides distinguent les configurations existantes des preuves d'exécution.

## Régénérer les supports

```powershell
uv run --with python-pptx --with reportlab python certif/presentation-bloc3/generate_slides.py
```

Le générateur réutilise les fonctions de dessin E1 et de rendu bloc 2, sans régénérer ces anciens supports. Bloc 3 : 23 slides, dont 12 E4 (20 min), 8 E5 (10 min) et 3 annexes. Dix minutes de questions suivent selon le règlement fourni pour le bloc isolé.
