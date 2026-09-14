# Index des annexes techniques

## Note au jury

Les documents de ce dossier sont des documents techniques de développement et
de production, initialement trouvable dans le dépôt du projet. Ils sont présentés ici pour la facilité d'usage et certains sont référencés dans les rapports. Ils ont été rédigés en anglais afin de rester cohérents avec les
conventions du projet, les noms de composants, les commandes, les traces de CI
et la documentation technique généralement utilisée dans l'environnement de
développement.

Les rapports professionnels E1 à E5 sont rédigés en français. Le présent dossier
sert d'annexe générale : il contient les preuves, décisions, modèles, procédures
et documents de travail sur lesquels les rapports s'appuient.

## Correspondance avec les rapports

### Rapport E1 - Collecte, stockage et mise à disposition des données

Documents principaux :

- `docs/block1/data-pipeline.md`
- `docs/block1/data-models.md`
- `docs/block1/database-and-sql.md`
- `docs/block1/gdpr-register.md`
- `docs/block1/api-security.md`
- `docs/block1/backup-restore.md`
- `docs/block1/openapi.yaml`

Éléments associés dans le dépôt :

- `data/documents/monsters.json`
- `monster_scrapping/monsters.json`
- `data/world/adventures/`
- `data/world/characters/`
- `data/world/locations/`
- `db/sqlite/setup_db.py`
- `db/sqlite/queries/monster_dataset.sql`
- `src/data_pipeline/`
- `src/django/game/dataset_api.py`

### Rapport E2 - Sélection et paramétrage d'un service IA

Documents principaux :

- `docs/block2/ai-requirements-and-selection.md`
- `docs/block2/api-security.md`
- `docs/block2/ai-test-strategy.md`
- `docs/block2/monitoring-slos.md`
- `docs/block2/delivery.md`
- `docs/block2/evidence-checklist.md`

Éléments associés dans le dépôt :

- `.env.example`
- `evaluation/dataset.json`
- `evaluation/e2-offline-report.json`
- `src/agents/runtime_config.py`
- `src/agents/llm_runtime.py`
- `src/agents/llm_resilience.py`
- `src/retrieval/embedder.py`
- `src/evaluation/runner.py`

### Rapport E3 - Exposition et intégration d'un service IA

Documents principaux :

- `docs/block2/openapi.yaml`
- `docs/block2/traceability.md`
- `docs/block2/ai-test-strategy.md`
- `docs/block2/monitoring-slos.md`
- `docs/block2/delivery.md`
- `docs/rag-system.md`
- `docs/monitoring.md`

Éléments associés dans le dépôt :

- `.github/workflows/block2-ai.yml`
- `Dockerfile`
- `compose.monitoring.yml`
- `evaluation/dataset.json`
- `evaluation/e3-offline-report.json`
- `src/django/game/ai_api.py`
- `src/agents/game_master_graph.py`
- `src/agents/tools.py`
- `src/observability/metrics.py`
- `db/chroma/world_lore`

### Rapport E4 - Application intégrant un service IA

Documents principaux :

- `docs/block3/project-brief-requirements.md`
- `docs/block3/architecture-decisions.md`
- `docs/block3/technical-framework-models.md`
- `docs/block3/agile-execution.md`
- `docs/block3/traceability.md`
- `docs/block3/product-quality-audit.md`
- `docs/block3/security-threat-model.md`
- `docs/block3/ci-cd-delivery.md`
- `docs/django-app-architecture.md`

Éléments associés dans le dépôt :

- `.github/workflows/block3-ci-cd.yml`
- `Dockerfile`
- `compose.delivery.yml`
- `.env.example`
- `src/django/`
- `src/combat/core.py`
- `src/retrieval/`
- `src/agents/`

### Rapport E5 - Monitorage et résolution d'incident

Documents principaux :

- `docs/monitoring.md`
- `docs/block2/monitoring-slos.md`
- `docs/block3/security-threat-model.md`
- `docs/block3/agile-execution.md`
- `docs/block3/traceability.md`

Éléments associés dans le dépôt :

- `compose.monitoring.yml`
- `monitoring/prometheus/prometheus.yml`
- `monitoring/prometheus/alerts.yml`
- `monitoring/alertmanager/alertmanager.yml`
- `monitoring/grafana/dashboards/call-to-aidventure-overview.json`
- `src/observability/metrics.py`
- `src/combat/core.py`
- `src/django/game/tests.py`

