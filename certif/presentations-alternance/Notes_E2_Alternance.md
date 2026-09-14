# Notes orales — E2_Alternance

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
