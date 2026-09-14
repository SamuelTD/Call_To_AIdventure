# Notes orales — Presentation_E2

Personnaliser identité, commanditaire, rôle, dates, budget et preuves externes avant passage.

## 01. Choisir et configurer le service d’IA — 90 s

Présenter votre identité, votre rôle exact et le commanditaire. E2 dure 15 minutes ; E3 suit pendant 20 minutes, puis le bloc prévoit 10 minutes de questions. Le rapport professionnel reste distinct de ce support. Le choix du service doit être défendu par des preuves, pas uniquement par son utilisation dans le code.

Sources : Référentiel 2023, p. 6–9 ; règlement, p. 12

## 02. Raconter, proposer, agir : trois contrats — 90 s

Illustrer avec une porte fermée : la narration décrit la situation, le modèle propose trois actions, puis le joueur en choisit une. Le modèle ne doit pas inventer directement les nouvelles statistiques. Les schémas imposent une forme, pas la pertinence narrative ou la langue : celles-ci nécessitent une évaluation distincte.

Sources : docs/block2/ai-requirements-and-selection.md ; src/agents/schemas.py

## 03. Définir la réussite avant de comparer — 90 s

Expliquer p95 : 95 % des observations sont sous cette durée sur une fenêtre définie. Ne pas confondre timeout d’un appel et durée totale d’un tour, qui peut contenir plusieurs appels et reprises. Budget, volume réel et arbitrage final ne sont pas fournis. Le taux de 90 % exige un corpus représentatif et une notation adaptée.

Sources : docs/block2/ai-requirements-and-selection.md ; ai-test-strategy.md

## 04. Une veille à rattacher aux décisions — 90 s

Le référentiel demande au minimum une heure hebdomadaire. Le document de diagnostic renvoie C6 à un dossier séparé : son absence dans ce dépôt ne prouve pas que vous ne l’avez pas réalisé ailleurs. Insérer vos dates, outils, sources identifiées, synthèses et destinataires. Cette slide est une trame, pas une veille effectivement conduite ni un état de l’art actualisé.

Sources : Référentiel, C6, p. 6–8 ; certif/block-2-technical-gap-analysis.md

## 05. Comparer sur un protocole identique — 90 s

Pour chaque candidat, relever version, date, validité, qualité FR/EN, p50/p95, tokens, coût estimé, région de traitement et rétention. Inclure les informations disponibles sur la démarche écoresponsable. Expliciter les services non étudiés et pourquoi. Ce support ne remplace pas le benchmark exigé par C7 ; aucune invocation payante n’a été réalisée.

Sources : docs/block2/ai-requirements-and-selection.md

## 06. Une génération hébergée, un RAG local — 90 s

La justification actuelle vise la génération multilingue et structurée sans héberger un gros modèle, un petit corpus vectoriel local et des transitions explicites. Le lore retrouvé est injecté dans les prompts envoyés au service de génération : rendre ce flux clair. Ne pas présenter cette décision qualitative comme un benchmark déjà conclu.

Sources : docs/block2/ai-requirements-and-selection.md ; docs/rag-system.md

## 07. Rendre la configuration explicite — 90 s

Lire les valeurs réellement configurées avant démonstration. Le nom du modèle par défaut est une chaîne du dépôt, pas une vérification de disponibilité commerciale. La commande check_ai_services valide les paramètres ; son option --connect vérifie Ollama, pas une génération réelle du fournisseur. Ne jamais afficher le fichier .env.

Sources : src/agents/runtime_config.py ; .env.example

## 08. Préparer le contexte avant la génération — 90 s

Le dry-run exécuté prépare 36 fragments de personnages et 21 de lieux. La documentation ancienne annonce 39 : la mesure du code courant prime. Aucun serveur Ollama ni Chroma n’a été testé en ligne ici. L’objectif de rappel des sources doit être mesuré séparément ; le runner actuel ne le calcule pas.

Sources : src/retrieval/ ; vérification du 14/09/2026

## 09. Maîtriser coûts, données et dépendances — 90 s

La formule complète utilise des tarifs par million de tokens : diviser la consommation par un million et distinguer entrée/sortie. Aucun tarif actuel n’est avancé. Les coûts estimés ne sont pas une facture. Éviter d’affirmer qu’un modèle local est automatiquement moins cher ou plus sobre ; cela dépend du matériel et des usages.

Sources : docs/block2/ai-requirements-and-selection.md ; docs/rag-system.md

## 10. Une solution configurée, une sélection à étayer — 90 s

Rappeler ce qui fonctionne dans le code et ce qui reste à montrer en réel. Préparer une démonstration safe de configuration et une sortie structurée issue d’un vrai appel, en conservant modèle, date et contexte d’évaluation. Le bilan ne prétend pas valider toutes les compétences E2.

Sources : docs/block2/evidence-checklist.md
