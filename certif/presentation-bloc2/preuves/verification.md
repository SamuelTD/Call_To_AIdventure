# Vérifications locales — 14 septembre 2026

Ces vérifications ont été exécutées pendant la préparation des slides. Aucun appel de génération réel ni benchmark payant n'a été effectué.

## Tests ciblés

```powershell
uv run python src/django/manage.py test game.test_ai_api game.tests.FrenchAgentPromptTests game.tests.RetrievalSpeedTests game.tests.HealingToolTests game.tests.GoalEvaluationTests game.tests.MetricsEndpointTests --noinput
```

Résultat : 33 tests réussis, 3,711 secondes de tests ; Django ne signale aucun problème de configuration. Base de tests créée et détruite automatiquement. Cette durée n'est pas une latence d'inférence. Ce lot ne représente ni la suite complète ni un résultat de couverture.

## Dataset et RAG

```powershell
$env:PYTHONPATH='src'
uv run python -m evaluation.runner --output certif/presentation-bloc2/preuves/evaluation-offline.json
uv run python -m retrieval.ingest --dry-run
```

Dataset : 4 cas validés par le runner hors ligne. Cette validation porte sur des contrôles limités du fichier, pas sur la réussite d'un modèle. Le runner live n'exécute que les deux cas de choix ; RAG et frontière API restent validés hors ligne.

RAG : 57 fragments préparés (36 personnages, 21 lieux), sans embeddings ni écriture Chroma. La mesure actuelle remplace l'ancien chiffre de 39 présent dans la documentation RAG.

## Limites et préparation de l'oral

- Aucun benchmark comparatif de modèles, audit humain FR/EN ni mesure de rappel n'a été exécuté.
- Prometheus, Grafana, notification externe, CI distante, publication Docker et staging n'ont pas été exécutés pour ce support.
- Compléter la veille C6, le budget, les dates, l'identité et le rôle réel.
- Préparer une partie de démonstration appartenant à un compte de test ; conserver ses cookies et secrets hors des supports.
- Ne pas présenter le health de configuration comme une disponibilité vérifiée du fournisseur.
- Le support signale les écarts de contrat API observés ; il ne modifie aucun code applicatif.

## Régénération

```powershell
uv run --with python-pptx --with reportlab python certif/presentation-bloc2/generate_slides.py
```

Le générateur réutilise uniquement les fonctions de dessin du générateur E1. Il ne réécrit pas la présentation E1. E2 : 10 slides, 15 minutes ; E3 : 12 slides, 20 minutes, plus 3 annexes. Bloc complet : 25 slides, 35 minutes, puis 10 minutes de questions selon le règlement fourni.
