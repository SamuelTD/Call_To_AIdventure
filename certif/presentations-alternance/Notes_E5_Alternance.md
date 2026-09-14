# Notes orales — E5_Alternance

Personnaliser identité, commanditaire, rôle, dates, budget et preuves externes avant passage.

## 01. Fiabiliser l’ingestion ServiceNow vers ClickHouse — 75 s

Le référentiel E5 vise la surveillance et la résolution d’un incident d’application dans le bloc IA. Le lien de cette plateforme à une application IA n’a pas été indiqué : ne pas le créer artificiellement. Ce scénario entreprise est une proposition à rattacher au périmètre accepté de l’épreuve. Le cas du jeu, dans son dossier d’origine, reste disponible comme alternative directement liée à l’application IA. Aucun run de reproduction entreprise n’a été inspecté ici.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 02. Identifier le signal qui révèle l’échec d’ingestion — 75 s

Les moyens de détection et de journalisation n’ont pas été décrits. Les cartes sont une trame de preuve, pas une configuration attestée. Les metrics et logs du jeu ne sont pas ceux de l’entreprise et ne doivent pas être attribués à ce cas. Si la surveillance professionnelle manque, conserver les slides C20 du support E5 initial et expliquer le changement de contexte.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 03. Suivre le succès et la qualité de l’alimentation — 75 s

C20 reste à prouver. Demander les métriques, seuils et notifications réellement utilisés. Ne pas réutiliser les alertes IA du jeu comme preuve du défaut de typage de la plateforme. Vérifier la confidentialité des lignes XML et des logs avant présentation ; ne pas afficher de données clients identifiantes.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 04. Isoler une ligne qui déclenche l’erreur de type — 75 s

Ne pas inventer un message ClickHouse, une date, un type concret ou une capture. Le candidat a décrit l’incident et son diagnostic mais pas l’exemple minimal. Conserver l’entrée, le schéma et les paramètres nécessaires à une reproduction hors données de production.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 05. Le format de transport ne porte pas les bons types — 75 s

Ne pas affirmer que toutes les données internes ServiceNow sont stockées en XML. Ce fait concerne le flux rencontré. Distinguer parsing XML, normalisation de valeur et validation de type. Le détail des champs, valeurs nulles et formats temporels n’est pas fourni ; ne pas inventer leurs règles.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 06. Valider et convertir avant de charger — 75 s

Le candidat a développé la validation et les conversions ; les règles et le comportement des rejets restent à montrer. La dernière phrase exprime un principe à défendre, pas une affirmation que le code fait ou ne fait pas cette substitution. Joindre commit/MR, tests et documentation lorsqu’ils sont disponibles. Aucun correctif entreprise n’a été apporté par cet assistant.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 07. Comparer le même échantillon avant et après — 75 s

Ne pas attribuer les 44 tests du jeu à cette correction. Aucun test du convertisseur n’a été fourni ou exécuté ici. Une preuve de run réussi sur le même cas et un test de non-régression permettraient d’étayer fortement C21. L’évolution dynamique de colonnes relève d’une autre contrainte à distinguer du défaut de typage.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 08. Une résolution métier à soutenir par ses pièces — 75 s

Une correction de pipeline peut démontrer une méthode de résolution mais ne doit pas être présentée comme incident d’un service IA si aucun lien n’existe. Le référentiel et les consignes du centre déterminent le périmètre de l’épreuve. Le dossier initial du combat est conservé avec sa reproduction vérifiée ; la version entreprise est préparatoire.

Sources : Alternance : description du candidat ; pièces techniques à joindre

## 09. Le cas du combat reste disponible — 0 s

Pour revenir au cas démontré, utiliser Presentation_E5.pptx dans le dossier certif/presentation-bloc3. Le dossier Dossier_incident_E5.md et le script reproduce_incident.py contiennent les révisions et limites exactes. Ne pas mélanger les deux causes ni les chronologies.

Sources : certif/presentation-bloc3/Dossier_incident_E5.md ; preuves/incident-combat.json

## 10. Retrouver les pièces du dossier — 0 s

Ne pas confondre le modèle de diagramme C4 avec la compétence C4 du bloc 1. Les références au référentiel concernent les PDF locaux fournis. Compléter aussi l’identité, les dates, le budget, l’hébergement et l’audit manuel demandés par le dossier de certification.

Sources : docs/block3/ ; docs/monitoring.md ; Dossier_incident_E5.md

## 11. Les points qui changent la solidité du dossier — 0 s

La compétence C7 reste moins étayée qu’un vrai comparatif de services. C20 et le lien applicatif IA du cas d’incident doivent être précisés. La contribution C16 mérite des traces de coordination, pas seulement une responsabilité technique. Les schémas et contrôles d’accès Tines ne sont pas déduits du seul contrat.

Sources : Alternance : description du candidat ; pièces techniques à joindre
