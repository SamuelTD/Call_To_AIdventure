# Notes orales — Présentation E1

15 diapositives principales : 15 minutes. 3 annexes pour les questions.

À personnaliser avant passage : identité, rôle exact, commanditaire, budget réel et dates du projet. Le règlement local prévoit 15 min + 10 min de questions pour le bloc 1 isolé.

## 01. Call To AIdventure — 30 s

Présenter votre nom et votre rôle. Le fil conducteur est le catalogue de monstres utilisé par un jeu narratif avec IA. Le support adopte le format E1 isolé : 15 minutes, puis 10 minutes de questions. Pour un passage du titre complet, ajuster le minutage avec le centre.

Sources : Référentiel Dev IA 2023, p. 1–6 ; règlement, p. 9 et 12

## 02. Une donnée fiable pour un jeu cohérent — 45 s

Décrire le projet scolaire, les joueurs, le développeur et le jury. Le moteur narratif et le RAG donnent le contexte ; E1 porte ici sur les flux de données des monstres. Ne pas présenter le catalogue SQLite comme la base vectorielle du RAG.

Sources : README.md ; docs/block3/project-brief-requirements.md

## 03. Un périmètre local et reproductible — 45 s

Compléter avant soutenance les éléments personnels attendus par le référentiel : commanditaire, contribution, planning et budget. Ne pas inventer de coût nul : distinguer poste local, hébergement éventuel et appels IA du jeu. L’ordre des étapes est un plan de présentation, pas un historique daté.

Sources : pyproject.toml ; docs/block3/agile-execution.md

## 04. Une chaîne de données traçable — 60 s

Suivre le trajet d’un monstre. Les fichiers bruts permettent d’inspecter l’entrée ; les données nettoyées portent le résultat de fusion ; le manifeste résume le traitement ; SQLite et l’API servent les consommateurs.

Sources : src/data_pipeline/ ; docs/block1/data-pipeline.md

## 05. Deux entrées, une origine à expliciter — 70 s

Le run vérifié charge des snapshots locaux : il ne prouve pas un scraping en direct. La documentation signale une page de vérification côté site. Aucune nouvelle collecte réseau n’a été exécutée pour ce support. Distinguer source de collecte et API d’exposition. Les exigences service web et big data ne sont pas couvertes par ces seuls fichiers.

Sources : docs/block1/data-pipeline.md ; src/data_pipeline/sources.py

## 06. Transformer sans perdre le sens — 65 s

Expliquer la clé stable sans accent, le typage numérique et la conservation de la fraction initiale. Les valeurs absentes de difficulté peuvent devenir NULL. Le parsing extrait la composante entière des HP/armure : il ne s’agit pas d’une compréhension de toute expression de dés. Le cas invalide est testé même si les snapshots ne génèrent aucun rejet.

Sources : src/data_pipeline/normalize.py ; tests/test_data_pipeline.py

## 07. Résoudre les conflits de façon déterministe — 60 s

Présenter cet exemple comme une fixture de test et non comme un conflit mesuré sur le catalogue réel. La fusion se fait sur la clé de nom normalisée. Limite : cette clé peut rapprocher des homonymes ; une identité métier plus robuste serait nécessaire si le périmètre évolue.

Sources : src/data_pipeline/pipeline.py ; tests/test_data_pipeline.py

## 08. 1 020 entrées deviennent 510 monstres — 55 s

Le run de preuve a utilisé --no-database : il vérifie les sorties sans modifier la base du jeu. Le test de persistance crée une base temporaire et vérifie les sources et rejets. Les cinq tests ne sont pas la suite complète API, RGPD ou application. Aucun temps de performance ni résultat de tests API n’est revendiqué ici.

Sources : preuves/20260914T093833Z-b0d37253/manifest.json ; tests/test_data_pipeline.py

## 09. Extraire une donnée utile et explicable — 70 s

Expliquer SELECT, WHERE, JOIN et GROUP BY avec les finalités métier. Q2 utilise :monster_id. Les index évitent des parcours inutiles selon le plan choisi. La commande explain_queries.py est disponible, mais aucun avant/après de performance n’a été exécuté pour ce support. Une annexe contient la requête exacte.

Sources : db/sqlite/queries/monster_dataset.sql ; src/data_pipeline/storage.py

## 10. Séparer le catalogue et les données de compte — 70 s

Distinguer MCD (entités et associations), MLD (clés et relations) et modèle physique (DDL SQLite). Chaque source acceptée est liée au monstre canonique et à l’import. Les rejets sont rattachés à l’import. Le modèle affiché est simplifié et ne remplace pas les modèles complets du dossier.

Sources : docs/block1/data-models.md ; src/data_pipeline/storage.py

## 11. SQLite répond au volume de la démonstration — 55 s

Le code remplace monsters et monster_sources. Ne pas affirmer qu’un ancien run permet de relire toutes ses anciennes lignées dans SQLite : les artefacts de run sont à conserver. Les IDs numériques du catalogue ne sont pas une identité stable entre imports. La procédure de restauration Django est documentée, pas exécutée pendant la création des slides.

Sources : src/data_pipeline/storage.py ; docs/block1/backup-restore.md

## 12. Documenter les traitements et les droits — 60 s

Restituer le registre interne, sans présenter les durées proposées comme des obligations légales ou une conformité acquise. Montrer la différence entre données de référence et données liées aux comptes. La purge se prévisualise sans --apply. Ne jamais afficher un véritable export utilisateur devant le jury.

Sources : docs/block1/gdpr-register.md ; docs/block1/backup-restore.md

## 13. Partager le catalogue avec un contrat clair — 70 s

Exemple de lecture : /api/v1/monsters/?page_size=5&challenge_max=1. Expliquer 400 pour paramètre invalide, 404 pour absence, 401/403 pour accès au résumé. Le rate limiting distribué du catalogue est une mesure prévue au reverse proxy, pas une protection démontrée ici. La documentation interactive dépend du CDN, contrairement au contrat YAML local.

Sources : docs/block1/openapi.yaml ; docs/block1/api-security.md

## 14. Suivre un résultat de bout en bout — 105 s

Ne pas lancer une reconstruction --reset sur une base utile pendant l’oral. Préparer un environnement de démonstration séparé. L’API nécessite Django configuré et une base construite ; elle n’a pas été démarrée pour générer ces slides. Si le serveur manque, montrer le contrat et annoncer explicitement que ce n’est pas une réponse HTTP en direct.

Sources : Notes orales : commandes et prérequis ; preuves/ ; docs/block1/openapi.yaml

## 15. Un socle concret, des écarts à traiter — 40 s

Conclure sur le résultat métier et les choix justifiés. Ne pas affirmer que le faible volume dispense des exigences big data écrites dans le référentiel. Faire traiter cet écart avec le centre. Inviter le jury à examiner les annexes sur SQL, les preuves et les arbitrages.

Sources : Référentiel, C1–C5 ; docs/block1/ ; preuves/manifest.json (run horodaté)

## 16. Revenir à l’origine d’un monstre — annexe

Afficher cette annexe pour expliquer une jointure, la liaison du paramètre et le tri de la source sélectionnée. Ne pas remplacer le paramètre par une concaténation de texte.

Sources : db/sqlite/queries/monster_dataset.sql, Q2

## 17. Où retrouver les éléments du dossier — annexe

Les documents locaux de certification sont la référence de ce support ; aucune vérification d’une version réglementaire plus récente n’a été réalisée. Le rapport professionnel individuel reste un livrable distinct des slides.

Sources : Dépôt local et documents de certification fournis

## 18. Défendre les choix et leurs limites — annexe

Préparer aussi : collision de clés stables, IDs renouvelés après import, conservation des anciens runs, validation des droits d’exploitation des sources, sécurité et durées des données personnelles.

Sources : docs/block1/ ; tests/test_data_pipeline.py

## Démonstration — commandes PowerShell

Depuis la racine du dépôt, pour régénérer les artefacts sans modifier la base du jeu :

```powershell
$env:PYTHONPATH='src'
uv run python -m data_pipeline --no-database --output-dir certif/presentation-e1/preuves
uv run python -m unittest discover -s tests -p test_data_pipeline.py
```

API : préparer au préalable Django et une base de démonstration selon README.md. Ouvrir `/api/v1/monsters/?page_size=5&challenge_max=1`, puis le détail d’un ID renvoyé et `/api/v1/docs/`. Ne pas supposer qu’un ID est conservé après reconstruction.

## Vérification réalisée

14 septembre 2026 : pipeline sur snapshots locaux, sans écriture dans la base du jeu. 1 020 collectés et acceptés, 0 rejet, 510 fusionnés, 5 conflits. Suite `tests/test_data_pipeline.py` : 5 tests réussis. API et restauration non exécutées pour ce support.

## Régénérer le support

```powershell
uv run --with python-pptx --with reportlab python certif/presentation-e1/generate_slides.py
```

Le PDF reprend la même mise en page que le PowerPoint. Tous les textes et blocs du PowerPoint sont modifiables. Les notes orales figurent également dans les notes du présentateur.