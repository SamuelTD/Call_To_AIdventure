# Notes orales — E4_Alternance

Personnaliser identité, commanditaire, rôle, dates, budget et preuves externes avant passage.

## 01. Construire une application intégrant l’IA — 100 s

Présenter identité, rôle, commanditaire et contexte scolaire. Le passage isolé du bloc prévoit E4 20 minutes, E5 10 minutes, puis 10 minutes de questions. Personnaliser les contributions réelles et les éventuelles aides reçues. Les slides ne remplacent pas le rapport E4 ni les documentations E5.

Sources : Référentiel 2023, p. 16–21 ; règlement, p. 12

## 02. Permettre de jouer et de retrouver sa progression — 100 s

Expliquer les acteurs et la valeur du service avant la technologie. La session anonyme n’offre pas la même reprise durable qu’une sauvegarde authentifiée. Le commanditaire et les contraintes de volume/budget restent à confirmer dans le document de cadrage ; ne pas les inventer.

Sources : docs/block3/project-brief-requirements.md

## 03. Relier les demandes à des réalisations concrètes — 100 s

Ne pas présenter la plateforme data comme intégrant un service IA : ce lien n’a pas été indiqué. Elle fournit un complément professionnel sur les demandes et arbitrages, tandis que le jeu reste le projet principal E4. Les tickets, critères et validations de l’entreprise sont à joindre sans inventer un processus.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 04. Séparer présentation, métier et persistance — 100 s

Présenter une architecture en couches, pas des microservices déployés qui n’existent pas. Les appels de génération transmettent le contexte utile au service distant. Les secrets restent dans l’environnement. Le schéma est une vue simplifiée ; les modèles du dossier détaillent les flux et les zones de stockage.

Sources : docs/block3/technical-framework-models.md ; services/game_engine.py

## 05. Choisir une architecture adaptée au périmètre — 100 s

Défendre chaque choix avec ses alternatives et ses conséquences. Ne pas appeler l’environnement local une préproduction déployée. Le référentiel C15 attend une preuve de concept accessible en préproduction et une conclusion de poursuite ; joindre cette preuve. Les critères de sobriété des prestataires restent à compléter lorsque le choix est arrêté.

Sources : docs/block3/architecture-decisions.md ; technical-framework-models.md

## 06. Porter une réalisation de bout en bout — 100 s

La contribution de bout en bout est confirmée par le candidat. Cela ne prouve pas automatiquement des rituels agiles, une équipe ou un processus MLOps. Associer une demande réelle aux échanges et à sa validation. Le backlog du jeu reste une pièce disponible dans le dossier initial.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 07. Conserver une progression cohérente — 100 s

Décrire comment une vue délègue au moteur puis décide de persister. Les tests de sauvegarde couvrent l’échec du service IA, les fins de partie et la propriété. Le jeu implique des tirages aléatoires, mais ces règles ne sont pas décidées par le modèle ; les tests contrôlent l’aléatoire pour vérifier les résultats.

Sources : src/django/game/models.py ; services/ ; tests.py

## 08. Protéger les requêtes et les données du joueur — 100 s

Le test CSRF exécuté utilise api_play comme route représentative ; ne pas affirmer qu’il teste individuellement chaque POST. D’autres contrôles testent 413, quota et propriété. Les anciennes notes bloc 1/2 mentionnent encore des exemptions CSRF ; les documents bloc 3 et le code courant décrivent leur migration. Aucun audit global OWASP n’est revendiqué.

Sources : docs/block3/security-threat-model.md ; game/views.py ; tests.py

## 09. Rendre les interactions perceptibles et maîtrisées — 100 s

Les tests exécutés lisent des templates ou leurs réponses HTML ; ils ne font pas fonctionner un lecteur d’écran ni le JavaScript dans un navigateur. L’écoconception repose sur des pratiques, sans score environnemental mesuré. Le dépôt mentionne une ancienne taille Docker : elle n’a pas été revérifiée et n’est pas affichée comme résultat actuel.

Sources : docs/block3/product-quality-audit.md ; ProductQualityTemplateTests

## 10. 44 tests ciblés réussis sur le bloc applicatif — 100 s

Le lot a terminé en 6,091 secondes : c’est une durée de tests, pas une performance de l’application. BrowserSmokeJourneyTests utilise le client Django et un moteur simulé, sans navigateur réel. Le seuil de couverture configuré reste 55 %, mais la couverture n’a pas été recalculée pour ce support. Aucune exécution CI distante n’a été consultée.

Sources : preuves/verification.md ; .github/workflows/block3-ci-cd.yml

## 11. Construire, vérifier et conserver le même artefact — 100 s

Le job staging-deploy-placeholder affiche des instructions : il n’y a aucune commande de déploiement effectif. Ne pas assimiler permission packages:write à une publication d’image. Le health de conteneur utilise une clé factice dans le workflow et ne prouve pas une génération IA. Joindre digest, URL de staging et preuve de rollback réels avant de revendiquer la chaîne complète.

Sources : .github/workflows/block3-ci-cd.yml ; Dockerfile ; docs/block3/ci-cd-delivery.md

## 12. Montrer le parcours, puis les garanties — 100 s

Les autres slides sont également prévues sur 100 secondes, soit E4 en 20 minutes. Préparer les onglets, une sauvegarde de test et le contexte sans données réelles. Une capture du produit n’a pas été créée pendant ce travail. La démonstration manuelle complète et la génération réelle nécessitent l’environnement configuré ; les tests seuls ne les remplacent pas.

Sources : docs/block3/traceability.md ; preuves/verification.md
