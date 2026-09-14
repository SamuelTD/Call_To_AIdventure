"""Alternance variants; preserve original decks and distinguish reported work from local checks."""
from pathlib import Path

HERE = Path(__file__).resolve().parent
CERTIF = HERE.parent

def load(folder):
    path = CERTIF / folder / 'generate_slides.py'
    source = path.read_text(encoding='utf-8-sig')
    # All original deck definitions precede their first assertion and rendering calls.
    namespace = {'__file__': str(path), '__name__': 'deck_definitions'}
    exec(compile(source[:source.index('\nassert sum(')], str(path), 'exec'), namespace)
    return namespace

renderer = load('presentation-bloc2')
renderer['OUT'] = HERE
render = renderer['render']
e1 = load('presentation-e1')['slides']
b2 = load('presentation-bloc2')['slides']
b3 = load('presentation-bloc3')['slides']
SOURCE = 'Alternance : description du candidat ; pièces techniques à joindre'

def replace(deck, number, tag, title, subtitle, cards, takeaway, notes, source=SOURCE):
    old = deck[number-1]
    old.update(tag=tag, title=title, subtitle=subtitle, cards=cards,
               takeaway=takeaway, notes=notes, source=source)

replace(e1,1,'E1 · C1 À C5','Industrialiser les données de l’entreprise','Alternance : dataplateforme quotidienne et interfaces de collecte',
 [('COLLECTER','MongoDB, ServiceNow et requêtes Elasticsearch.\nOrchestration quotidienne avec Airflow.'),('TRANSFORMER','Chargement dans ClickHouse.\nTransformations dbt.\nMarts pour des usages métier réels.'),('PARTAGER','Documentation de la plateforme.\nComplément distinct : endpoints Tines au service d’un agent cyber.')],
 'Une chaîne réalisée et maintenue de bout en bout pendant l’alternance.',
 'Présenter l’entreprise de manière autorisée, votre rôle, les dates et le besoin. Vous déclarez avoir réalisé l’ensemble de la chaîne, sa montée en charge, ses corrections et évolutions. Tines est un second projet, pas une API des marts ClickHouse. Le jeu reste une preuve complémentaire explicitement identifiée pour certains critères.')
replace(e1,2,'CONTEXTE · ENTREPRISE','Transformer les données internes en usages métier','Des sources opérationnelles aux tables exploitées par les équipes.',
 [('BESOIN','Rendre les données internes disponibles sous une forme adaptée aux cas d’usage des équipes.'),('RÉPONSE','Une alimentation quotidienne.\nDes transformations centralisées.\nDes marts destinés à la consommation métier.'),('CONTRIBUTION','Conception et réalisation complètes.\nScalabilité, correction des bugs et demandes d’évolution.\nDocumentation.')],
 'Ajouter un exemple réel de mart et la décision métier qu’il permet.',
 'Le candidat a confirmé l’exploitation par des équipes, sans préciser les métiers, les métriques de valeur ni un exemple de mart. Compléter avec un cas réel : besoin, champs nécessaires, résultat utilisé et bénéfice constaté. Ne pas inventer de gain de temps ou de fréquence supérieure au quotidien.')
replace(e1,3,'CADRAGE','Concevoir, exploiter et faire évoluer la chaîne','Périmètre personnel confirmé : l’ensemble de la dataplateforme.',
 [('RÉALISATION','Connexion aux sources.\nOrchestration et chargement.\nTransformations dbt.\nMise à disposition des marts.'),('MAINTENANCE','Résolution des bugs.\nAdaptation à la charge.\nPrise en compte des demandes de fonctionnalités.'),('À CHIFFRER','Volumes et croissance.\nDurée du DAG et fraîcheur.\nCalendrier et budget.\nBénéfices pour les équipes.')],
 'Distinguer la responsabilité exercée des résultats chiffrés encore à ajouter.',
 'Ne pas reprendre les chiffres du pipeline de monstres : ils n’appartiennent pas à ce projet. Préciser les arbitrages de scalabilité réellement réalisés et leurs mesures avant/après. L’outil de ticket, les revues ou la méthode agile n’ont pas encore été décrits.')
replace(e1,4,'C1 → C4 · FLUX','De trois sources aux marts métier','Schéma fonctionnel de la réalisation décrite.',
 [('SOURCES','MongoDB\nServiceNow\nElasticsearch\n\nDonnées internes hétérogènes.'),('ORCHESTRATION','DAG Airflow quotidien\n↓\nChargement ClickHouse\n\nModalités par source à détailler.'),('TRANSFORMATIONS','Projet dbt\n↓\nDonnées traitées et améliorées\n↓\nMarts consommés par les équipes.')],
 'La documentation explique le trajet de la donnée et les choix de transformation.',
 'Le flux global est rapporté par le candidat ; les protocoles ServiceNow, les dépendances exactes du DAG et le lancement de dbt doivent être précisés avec le schéma réel. Ne pas supposer que dbt est déclenché dans le même DAG si ce n’est pas le cas. Ne pas relier Tines à ClickHouse sans preuve de ce lien.')
replace(e1,5,'C1 · EXTRACTION','Trois sources avec des contraintes différentes','Les connecteurs et les règles de récupération constituent la preuve.',
 [('MONGODB','Collections et champs utiles.\nFiltres et identifiants.\nMode complet ou incrémental à expliciter.'),('SERVICENOW','Source confirmée.\nPréciser le mode d’accès réel : API, connecteur ou autre accès à la donnée.'),('ELASTICSEARCH','Requêtes d’extraction.\nPérimètre et filtres.\nPagination, volume et erreurs à documenter selon le code.')],
 'La diversité est réelle ; chaque mécanisme doit être montré tel qu’il est implémenté.',
 'Parler de collections MongoDB plutôt que de tables si c’est le format réel. L’utilisateur parle de BDD ServiceNow : ne pas convertir cette description automatiquement en accès SQL ou REST. Les requêtes Elasticsearch renforcent la preuve d’extraction, sans suffire seules à qualifier tout le projet de big data.')
replace(e1,6,'C3 · TRANSFORMATIONS','Rendre les données utilisables par les équipes','dbt porte les transformations et la construction des marts.',
 [('ENTRÉE','Données issues des sources internes.\nFormats et qualité propres à chaque source.'),('RÈGLES MÉTIER','Traitements et enrichissements réalisés dans dbt.\nChoisir un modèle représentatif et expliquer son SQL.'),('SORTIE','Mart utilisé par une équipe.\nColonnes et granularité définies.\nLien avec un cas d’usage réel.')],
 'Preuve à insérer : un exemple réel avant / après transformation.',
 'Les transformations sont confirmées, mais les règles précises ne sont pas fournies. Ne pas affirmer que dédoublonnage, nettoyage de NULL, quarantaine ou tests dbt sont en place sans un exemple. Pour C3, montrer explicitement nettoyage, homogénéisation et rapprochement des sources effectivement réalisés.')
replace(e1,7,'C3 · AGRÉGATION','Expliquer comment un mart est construit','Relier la requête, la granularité et l’usage final.',
 [('ORIGINES','Sélectionner un mart réel.\nIdentifier ses sources et les objets intermédiaires nécessaires.'),('LOGIQUE','Présenter les jointures, filtres ou calculs réellement utilisés.\nJustifier la clé de rapprochement et la granularité.'),('VALIDATION','Montrer un résultat attendu.\nExpliquer le traitement des anomalies observées.\nJoindre les contrôles existants.')],
 'La simple présence de plusieurs sources ne prouve pas leur agrégation.',
 'Slide de démonstration à compléter avec un modèle réel. La séparation staging/intermediate/marts n’est pas déduite du seul usage de dbt. Un lignage dbt peut faciliter l’explication s’il existe. Décrire seulement les tests ou validations effectivement utilisés.')
replace(e1,8,'EXPLOITATION · SCALABILITÉ','Faire tenir la chaîne dans la durée','Montée en charge, bugs et évolutions : responsabilités exercées.',
 [('CHARGE','Scalabilité prise en charge.\nAjouter : volumétrie, goulot identifié, modification et mesure avant / après.'),('FIABILITÉ','Bugs résolus pendant la maintenance.\nAjouter un exemple : symptôme, cause, correction et contrôle.'),('ÉVOLUTION','Demandes de fonctionnalités intégrées.\nMontrer une demande et son résultat pour l’équipe.')],
 'Aucun volume, temps de traitement ou taux de disponibilité n’est inventé.',
 'Cette slide remplace les compteurs du jeu, qui ne décrivent pas la plateforme. Scalabilité confirmée par déclaration ; choix techniques et chiffres restent à joindre. Un bug bien documenté pourrait aussi devenir un cas E5 après vérification de son contexte et des critères de l’épreuve.')
replace(e1,9,'C2 · SQL','Défendre les requêtes par leur usage','Le projet dbt fournit une base de preuves SQL professionnelle.',
 [('SÉLECTION','Champs utiles et filtres.\nConditions liées au besoin métier.\nLimiter les données inutiles.'),('TRANSFORMATION','Jointures et agrégations réelles.\nCalculs et granularité.\nRésultat attendu du mart.'),('OPTIMISATION','Choix ClickHouse et SQL à expliquer.\nMesures avant / après à joindre.\nNe pas inventer moteur ou partitionnement.')],
 'Un extrait SQL commenté vaut mieux qu’une liste de technologies.',
 'C2 demande des requêtes fonctionnelles et une documentation des sélections, conditions, jointures et optimisations. Choisir une requête que le candidat a écrite et peut expliquer. ClickHouse et Elasticsearch sont pertinents pour parler de systèmes analytiques distribués si l’architecture et le volume réels le justifient ; les seuls noms ne prouvent pas le volet big data.')
replace(e1,10,'C4 · STOCKAGE','Justifier ClickHouse et le modèle des données','La création, l’import et la documentation relèvent du périmètre réalisé.',
 [('MODÈLE','Décrire les entités, identifiants et relations du cas retenu.\nJoindre les modèles conceptuel et physique.'),('STOCKAGE','Présenter les tables ClickHouse et les choix de stockage réellement appliqués.'),('IMPORT','Expliquer chargement et actualisation.\nMontrer une exécution et les objets produits.\nPréciser la stratégie de reprise.')],
 'Un graphe de dépendances dbt ne remplace pas automatiquement un modèle Merise.',
 'Les modèles exacts, moteurs, clés de tri, partitions et stratégies d’upsert n’ont pas été fournis. Ne pas les déduire. Le référentiel C4 demande le formalisme Merise ; produire ou joindre le modèle fidèle à l’existant si le dossier ne le contient pas encore.')
replace(e1,11,'DOCUMENTATION','Rendre la plateforme compréhensible et transmissible','La documentation est un axe majeur du travail d’alternance.',
 [('COMPRENDRE','Architecture et sources.\nDéfinition des données.\nLogique des transformations et usages des marts.'),('EXPLOITER','Installation et accès.\nLancement et diagnostic.\nProcédures de maintenance à montrer lorsqu’elles existent.'),('ÉVOLUER','Dépendances et impacts.\nChoix techniques argumentés.\nMise à jour liée aux changements.')],
 'Montrer une page réellement produite et expliquer à qui elle sert.',
 'Ces rubriques organisent les preuves à sélectionner ; le candidat a confirmé l’importance de la documentation, pas la présence exhaustive de chaque rubrique. Présenter le format réel, la version, les destinataires et un exemple d’usage. Une documentation générée peut être complétée par les raisons métier des transformations.')
e1[11]['tag']='C4 · COMPLÉMENT CALL TO AIDVENTURE'
e1[11]['subtitle']='Registre du jeu ; ne décrit pas les traitements internes de l’entreprise.'
e1[11]['notes'] += ' Dans cette version multi-projets, cette preuve concerne exclusivement le jeu. Les données clients EDR et les données internes nécessitent une analyse propre au contexte professionnel, non fournie ici. Ne pas leur appliquer les durées proposées pour le jeu.'
replace(e1,13,'C1 / C5 · PROJET COMPLÉMENTAIRE','Tines fournit les données à l’agent cyber','Quatre stories exposent chacune un webhook avec un contrat d’API précis.',
 [('APPELANT','Application Django avec analyste LLM.\nL’agent peut demander des informations sur une entité cyber.'),('INTERFACE','Webhook Tines\n↓\nStory correspondant au type d’entité\n↓\nAppels aux consoles EDR nécessaires.'),('RÉPONSE','Données des API EDR renvoyées à l’appelant.\nMontrer contrat, accès et erreurs sur un exemple réel.')],
 'Projet distinct : ces endpoints ne sont pas présentés comme une API des marts.',
 'Le candidat a créé les quatre stories. Le système appelant est décrit, sans attribution de toute l’application Django au candidat. Un webhook HTTP peut contribuer à C5, mais sa présence seule ne prouve pas une API REST complète ni sa sécurisation. Documenter méthodes, schémas, authentification/autorisation, isolation client, erreurs et tests réellement présents. La connexion aux EDR renforce C1 pour la collecte web.')
replace(e1,14,'E1 · DÉMONSTRATION','Montrer le trajet de la donnée','Préparer les pièces réelles et anonymisées pour la soutenance.',
 [('PLATEFORME','DAG quotidien.\nUne extraction représentative.\nUn modèle dbt et son résultat.\nUne page de documentation.'),('MISE À DISPOSITION','Un mart et son usage métier.\nPuis, projet distinct : une story Tines et son contrat d’entrée / sortie.'),('GARANTIES','Montrer une évolution ou un bug corrigé.\nAjouter mesures de charge et validation si disponibles.')],
 'Le support décrit tes travaux ; aucune connexion aux systèmes d’entreprise n’a été exécutée ici.',
 'Cette séquence dure 1 min 45 selon le minutage conservé. Utiliser des captures ou jeux de données autorisés et anonymisés. Les captures d’exécution Airflow, SQL et story n’ont pas encore été fournies. Si la démo Tines est rejouée, préparer un environnement de test et ne pas afficher les secrets des webhooks.')
replace(e1,15,'E1 · BILAN','Des réalisations professionnelles complémentaires','Un fil conducteur data et une preuve distincte d’interface API.',
 [('C1 / C2','Extraction multi-source quotidienne.\nRequêtes Elasticsearch et transformations SQL dbt.\nContraintes de charge à chiffrer.'),('C3 / C4','Marts métier et maintenance.\nModèle et import ClickHouse.\nNettoyage, Merise et données personnelles à expliciter.'),('C5','Stories Tines avec contrat précis.\nCaractère REST, accès et tests à documenter.\nAPI du jeu disponible en complément.')],
 'Attribuer chaque preuve à son projet et à ta contribution exacte.',
 'Cette synthèse ne prononce pas une validation de compétence. Les fichiers/scraping du jeu restent des preuves complémentaires pour la diversité d’extraction. Ne pas affirmer que ServiceNow est une API tant que le mode d’accès n’est pas clarifié. Les rapports écrits doivent reprendre la même répartition et expliciter le lien entre chaque réalisation et la compétence.')
e1[15]['tag']='ANNEXE A · SQL DU JEU'
e1[15]['subtitle']='Preuve complémentaire existante ; à remplacer par un extrait dbt si disponible.'
replace(e1,17,'ANNEXE B · PIÈCES','Préparer les preuves d’alternance','Le contenu métier vient des descriptions du candidat, sans accès au code entreprise.',
 [('DATAP LATEFORME','DAG et extrait de run.\nModèle SQL dbt et résultat.\nSchéma de stockage.\nDocumentation et mesures.'),('TINES','Une story représentative.\nContrat anonymisé.\nRequête / réponse.\nTests et politique d’accès.'),('COMPLÉMENT JEU','Sources fichier / scraping.\nRegistre et modèles propres au jeu.\nAPI et tests déjà disponibles.')],
 'Aucune mesure locale du jeu n’est attribuée à la plateforme de l’entreprise.',
 'Le support distingue trois contextes : plateforme interne, intégration Tines et Call To AIdventure. Ne pas fusionner leurs politiques d’accès, leurs bases ou leurs résultats. Les chemins et commandes des supports initiaux restent disponibles dans leurs dossiers d’origine.')
replace(e1,18,'ANNEXE C · QUESTIONS','Défendre les décisions sans extrapoler','Les points à préparer avant passage.',
 [('SCALABILITÉ','Quel volume et quelle croissance ?\nQuel goulot ?\nQuel changement et quelle mesure ?'),('QUALITÉ','Quel nettoyage réel ?\nQuelle règle de rapprochement ?\nComment détecter une régression ?'),('MISE À DISPOSITION','Qui consomme les marts ?\nQui appelle les webhooks ?\nQuel contrôle des accès clients ?')],
 'Nommer les faits, les résultats et les limites propres à chaque projet.',
 'Préparer une réponse fondée sur un artefact pour chaque question. Rester précis sur les formes d’accès ServiceNow et le formalisme de l’API Tines. Les bénéfices de la documentation peuvent être démontrés par un usage réel sans inventer de métrique.')

replace(b2,1,'E2 · C6 À C8','Choisir comment évaluer les LLM en cybersécurité','Alternance : veille, sélection de benchmarks et application d’évaluation.',
 [('BESOIN','Évaluer les modèles selon les usages cyber de l’entreprise et leurs performances.'),('VEILLE / SÉLECTION','Environ 10 benchmarks examinés.\nOpen source ou utilisables gratuitement.\nCritères de scoring, adaptation et licence.'),('MISE EN ŒUVRE','Application de benchmark cyber et performance.\nScores et métriques enregistrés en base.')],
 'Distinguer sélection du dispositif d’évaluation et sélection du modèle.',
 'Travaux rapportés par le candidat ; les noms des benchmarks et modèles, résultats et versions restent à joindre. Les composants configurés du jeu restent un complément C8 clairement séparé. Les scores cyber ne sont pas utilisés pour justifier le modèle narratif du jeu.')
replace(b2,2,'C7 · BESOIN MÉTIER','Évaluer la pertinence et les contraintes d’usage','Deux dimensions complémentaires de l’évaluation.',
 [('CAPACITÉS CYBER','Mesurer les modèles sur des tâches en lien avec les usages réels de l’entreprise.'),('PERFORMANCE','P50, P95, P99.\nVitesse et concurrence.\nDéfinir la charge et les conditions de mesure.'),('DÉCISION','Comparer les résultats aux contraintes métier.\nModèles évalués et recommandation finale à documenter.')],
 'Un score cyber élevé ne suffit pas si le service ne tient pas la charge requise.',
 'Le candidat confirme que l’application exécute les benchmarks et obtient des scores. Aucun modèle nommé, classement, seuil ni recommandation finale n’est encore fourni. La performance mesurée doit préciser le périmètre : requête complète, premier token, décodage ou autre métrique réellement implémentée.')
replace(b2,3,'C6 / C7 · CRITÈRES','Sélectionner des évaluations adaptées','Critères de sélection explicitement indiqués par le candidat.',
 [('SCORING','Exclure LLM-as-judge.\nExclure human-as-judge pour le calcul des scores.\nMontrer le mécanisme retenu.'),('PERTINENCE','Adaptabilité aux usages cyber réels de l’entreprise.\nPérimètre et limites des tâches à préciser.'),('ACCÈS / LICENCE','Open source ou usage gratuit.\nCompatibilité de licence étudiée.\nGratuité et droits de réutilisation distingués.')],
 'Un score sans juge reste à examiner pour sa validité et ses biais.',
 'L’absence de LLM/humain comme juge est un critère rapporté de sélection. Elle ne démontre pas automatiquement une évaluation objective ou exhaustive. Expliquer la règle effective : assertion, sortie attendue, exécution, tests ou autre mécanisme, sans en inventer un. Open source et gratuit ne sont pas synonymes. Cette slide décrit l’étude passée, pas un avis juridique sur les licences actuelles.')
replace(b2,4,'C6 · VEILLE RÉALISÉE','Environ dix benchmarks cyber étudiés','Une recherche comparative orientée vers un besoin d’entreprise.',
 [('RECENSER','Identifier les benchmarks ouverts ou utilisables gratuitement.\nConserver les sources et versions consultées.'),('ANALYSER','Comparer scoring, pertinence métier, adaptabilité et licence.\nExpliciter les exclusions.'),('RESTITUER','Joindre la matrice de comparaison et la synthèse.\nPréciser dates, rythme de veille et partage réel.')],
 'L’étude est réalisée ; son organisation régulière et sa diffusion restent à documenter.',
 'Ne plus qualifier la veille comme absente : le candidat l’a réalisée. Distinguer contenu de recherche confirmé et modalités non décrites. Le référentiel demande une veille organisée et partagée ; joindre les dates, outils et restitutions effectivement utilisés. N’inventer ni suivi hebdomadaire ni présentation d’équipe.')
replace(b2,5,'C7 · DEUX NIVEAUX DE COMPARAISON','Choisir les benchmarks, puis comparer les modèles','Les deux décisions utilisent des critères différents.',
 [('ÉVALUATIONS','Quel benchmark représente le besoin ?\nQuel scoring, quelle licence et quelles limites ?'),('MODÈLES','Quels LLM exécutés dans les mêmes conditions ?\nQuels scores et distributions de latence ?'),('RECOMMANDATION','Quel modèle ou service répond au besoin ?\nPourquoi retenir ou écarter un candidat ?\nConclusion à joindre.')],
 'C7 est mieux étayée par une recommandation de service fondée sur les résultats.',
 'La comparaison de benchmarks et l’application d’évaluation sont confirmées. La liste des modèles effectivement évalués et la décision finale ne sont pas encore fournies. Présenter les conclusions cyber dans leur contexte professionnel ; elles ne démontrent pas automatiquement la qualité narrative FR/EN de Call To AIdventure.')
for index in (5,6,7):
    b2[index]['tag'] += ' · COMPLÉMENT JEU'
    b2[index]['notes'] += ' Cette slide concerne exclusivement Call To AIdventure, pas l’application de benchmark ni l’analyste cyber de l’entreprise. Elle fournit une preuve technique complémentaire C8.'
replace(b2,9,'ÉVALUATION · PROTOCOLE','Conserver les conditions qui rendent les scores comparables','L’application enregistre les résultats et métriques en BDD.',
 [('IDENTIFIER','Modèle et version.\nBenchmark et version.\nConfiguration et date.\nChamps effectivement conservés à montrer.'),('MESURER','Score cyber.\nP50 / P95 / P99.\nVitesse et concurrence.\nUnités et périmètre à préciser.'),('INTERPRÉTER','Nombre de cas et erreurs.\nCharge et répétitions.\nDifférences significatives.\nLimites de représentativité.')],
 'La base est une preuve de traçabilité ; son schéma réel doit être présenté.',
 'Seul le stockage des scores et métriques est confirmé ; la présence des métadonnées détaillées doit être vérifiée sur le schéma réel. Éviter de transformer une moyenne ou un percentile en preuve de qualité globale. Aucun chiffre de performance n’a été fourni et aucun test entreprise n’a été exécuté par cet assistant.')
replace(b2,10,'E2 · BILAN','Une sélection documentée, une exécution instrumentée','Les réalisations d’alternance complètent les preuves techniques du jeu.',
 [('C6','Étude d’environ 10 benchmarks.\nCritères explicites.\nMatrice et traces de restitution à joindre.'),('C7','Évaluation adaptée aux usages cyber.\nRésultats par modèle et recommandation à insérer.'),('C8','Configuration du jeu disponible.\nAjouter l’environnement réel du runner et des modèles si tu l’as configuré.')],
 'Transition E3 : intégrer des outils de collecte et exécuter les évaluations.',
 'Ne pas traiter l’application de benchmark comme une chaîne de livraison continue déjà déployée. C8 peut être renforcée par la configuration de l’environnement d’évaluation si elle appartient à la contribution personnelle, mais ses détails ne sont pas connus ici.')
replace(b2,11,'E3 · C9 À C13','Intégration et évaluation : des preuves complémentaires','Trois contextes identifiés, sans fusion artificielle de leurs architectures.',
 [('CALL TO AIDVENTURE','API du jeu et intégration IA.\nContrôles d’accès, métriques et workflow existants.'),('ANALYSTE CYBER','Application Django et agent LLM.\nContribution personnelle : quatre stories Tines fournissant des données EDR.'),('ÉVALUATION','Application de benchmarks cyber et performance.\nScores et métriques enregistrés en base.')],
 'Attribuer chaque résultat et chaque responsabilité au bon projet.',
 'L’application Django cyber est distincte du jeu. Le candidat n’a pas déclaré avoir créé toute cette application ou son agent ; sa contribution confirmée porte sur Tines. Le runner de benchmarks n’est pas présenté comme connecté à l’agent sans confirmation de ce lien.')
replace(b2,14,'C10 · INTÉGRATION PAR OUTILS','L’agent demande des données aux stories Tines','Contribution confirmée : quatre stories avec un contrat d’API précis.',
 [('APPLICATION DJANGO','L’analyste LLM dispose d’outils permettant d’appeler les endpoints selon l’entité cyber à examiner.'),('TINES','Webhook d’entrée\n↓\nStory dédiée\n↓\nInterrogation des consoles EDR nécessaires.'),('RETOUR À L’AGENT','Les données récupérées sont renvoyées à l’appelant.\nContrat et exemple d’échange à joindre.')],
 'Ces endpoints exposent des données et des outils ; ils n’exposent pas le modèle lui-même.',
 'C10 : cette réalisation contribue à l’intégration des outils de l’agent, mais il faut délimiter qui a écrit l’adaptateur Django, les appels et la logique de l’agent. C9 reste porté par l’API du jeu, car Tines n’est pas décrit comme un endpoint d’inférence. Préciser les quatre types d’entité sans inventer leurs noms. Authentification, autorisation client, gestion des erreurs et tests restent à joindre.')
replace(b2,18,'C12 · ÉVALUATION AUTOMATISÉE','Exécuter des benchmarks cyber et de performance','Réalisation d’alternance : une application de lancement et de stockage des résultats.',
 [('CYBERSÉCURITÉ','Exécution des benchmarks retenus.\nProduction de scores.\nRègles de scoring sans juge humain ni LLM recherchées à la sélection.'),('PERFORMANCE','Mesures P50, P95, P99.\nVitesse et concurrence.\nDéfinir les unités, le scénario et le nombre de requêtes.'),('PERSISTANCE','Métriques et résultats en BDD.\nJoindre une exécution réelle, son contexte et les résultats correspondants.')],
 'Les tests du logiciel et les évaluations des modèles restent deux preuves distinctes.',
 'L’utilisateur confirme que le runner obtient des scores et métriques. Il n’a pas fourni de logs ni valeurs ; aucun taux de réussite n’est inventé. Montrer aussi la validation du dataset, les dépendances, la gestion d’échecs et les tests du runner s’ils existent. C12 est particulièrement bien servi par ce travail, sans prétendre qu’une étape d’entraînement existe.')
replace(b2,19,'C12 · RESTITUTION DES RÉSULTATS','Relier score cyber et comportement sous charge','Emplacement réservé aux résultats réels issus de la base entreprise.',
 [('QUALITÉ CYBER','Modèle : à renseigner.\nBenchmark : à renseigner.\nScore et unité : à joindre.\nVersion du jeu de cas.'),('PERFORMANCE','P50 / P95 / P99 : à joindre.\nVitesse : unité à préciser.\nConcurrence et durée du test.\nNombre d’erreurs.'),('ANALYSE','Quel compromis observé ?\nQuel candidat retenu ?\nQuelles limites ?\nQuelle suite décidée ?')],
 'Aucun graphique ni classement synthétique n’est présenté comme un résultat mesuré.',
 'Remplacer ces champs par un export ou un tableau réel, anonymisé si nécessaire. Ne pas réutiliser les résultats offline du jeu comme scores de l’entreprise. C11 peut être renforcée si les campagnes sont suivies dans le temps et donnent lieu à un tableau de bord, des alertes ou des décisions ; une base de résultats seule ne démontre pas une chaîne de monitorage.')
replace(b2,22,'E3 · DÉMONSTRATION','Montrer une preuve par réalisation','Préparer les contrats, les résultats et la traçabilité.',
 [('API DU JEU','Montrer la frontière authentifiée et un contrôle d’accès.\nTests locaux disponibles dans le dossier initial.'),('OUTILS TINES','Un contrat réel.\nUne story et son parcours EDR.\nUne requête / réponse anonymisée.\nContribution personnelle délimitée.'),('BENCHMARKS','Une campagne d’évaluation.\nRésultats cyber et performance.\nEnregistrement en base.\nInterprétation des écarts.')],
 'La livraison continue et l’alerte restent des sujets distincts des campagnes de benchmarks.',
 'Les slides CI et monitoring conservées concernent le jeu. Ne pas annoncer une CI, un déploiement ou une alerte du runner qui n’ont pas été décrits. Joindre un export réel avant passage. Les preuves locales du jeu restent disponibles dans certif/presentation-bloc2/preuves/.')
replace(b2,24,'ANNEXE B · PREUVES','Assembler les pièces sans mélanger les projets','Sources d’alternance à joindre ; code du jeu déjà disponible.',
 [('E2','Matrice des benchmarks.\nCritères et exclusions.\nRestitution de veille.\nModèles et recommandation.'),('E3 · ENTREPRISE','Code et commande du runner.\nSchéma BDD et résultats.\nContrat Tines et story.\nTests d’intégration disponibles.'),('E3 · JEU','API et tests.\nConfiguration / RAG.\nMétriques et workflow.\nLimites du dossier initial conservées.')],
 'Une campagne de test n’est pas une surveillance continue ni une livraison.',
 'Le dossier préparatoire joint précise les preuves à fournir. Aucune source entreprise n’a été inspectée directement pendant cette révision. Les intitulés et détails reposent sur les explications du candidat.')
replace(b2,25,'ANNEXE C · QUESTIONS','Défendre le protocole et les interfaces','Questions probables sur les nouveaux travaux.',
 [('SANS JUGE ?','Quel mécanisme donne le score ?\nQue mesure-t-il vraiment ?\nQuels biais et quels cas non couverts ?'),('COMPARAISON ÉQUITABLE ?','Versions, charge et paramètres identiques ?\nCombien de cas / répétitions ?\nQuel traitement des erreurs ?'),('TINES ET L’AGENT ?','Quel contrat ?\nQui peut appeler quoi ?\nComment isoler les clients ?\nQuelle part as-tu développée ?')],
 'Une automatisation du scoring ne garantit pas à elle seule la validité de l’évaluation.',
 'Répondre à partir des implémentations et résultats réels. Aucun lien entre le choix du modèle narratif du jeu et les scores cyber n’est établi. La contribution aux endpoints Tines ne signifie pas création de toute l’application analyste.')

replace(b3,3,'C14 · BESOINS ET ÉVOLUTIONS','Relier les demandes à des réalisations concrètes','Jeu : critères formalisés ; alternance : évolutions de plateforme réalisées.',
 [('CALL TO AIDVENTURE','Reprise des sauvegardes.\nPropriété des données.\nÉchec IA sans progression.\nCritères et tests disponibles.'),('DATAP LATEFORME','Demandes de fonctionnalités prises en charge.\nBugs corrigés et adaptation à la charge.'),('PREUVE À JOINDRE','Une demande réelle, sa reformulation, le changement livré et sa validation par l’utilisateur métier.')],
 'La plateforme illustre la relation au besoin ; le contexte applicatif IA reste explicite.',
 'Ne pas présenter la plateforme data comme intégrant un service IA : ce lien n’a pas été indiqué. Elle fournit un complément professionnel sur les demandes et arbitrages, tandis que le jeu reste le projet principal E4. Les tickets, critères et validations de l’entreprise sont à joindre sans inventer un processus.')
replace(b3,6,'C16 · CONTRIBUTION PERSONNELLE','Porter une réalisation de bout en bout','Alternance : développement, maintenance et évolution de la plateforme.',
 [('RÉALISER','Chaîne multi-source complète.\nAirflow, ClickHouse et dbt.\nDocumentation des travaux.'),('ADAPTER','Scalabilité.\nRésolution des bugs.\nDemandes de fonctionnalités.\nArbitrages à illustrer.'),('COORDONNER','Préciser interlocuteurs, priorités, outils de suivi, revues et échanges réellement pratiqués.')],
 'L’autonomie technique renforce le récit ; les pratiques de coordination doivent être prouvées.',
 'La contribution de bout en bout est confirmée par le candidat. Cela ne prouve pas automatiquement des rituels agiles, une équipe ou un processus MLOps. Associer une demande réelle aux échanges et à sa validation. Le backlog du jeu reste une pièce disponible dans le dossier initial.')
b3[19]['notes'] += ' Le candidat rapporte aussi des bugs corrigés sur la plateforme d’alternance. Sans description précise de cause, reproduction et correction, ils ne remplacent pas encore le cas de combat vérifié. Un incident sur le runner de benchmark ou l’intégration Tines peut offrir un contexte IA plus direct, si réellement rencontré.'
replace(b3,23,'ANNEXE C · COMPLÉMENTS ENTREPRISE','Choisir les preuves selon les compétences','Les travaux d’alternance ne remplacent pas indistinctement toutes les preuves.',
 [('C14 / C16','Demandes et évolutions de plateforme.\nContribution complète.\nÉchanges et validations à joindre.'),('C15 / C17','Architecture Django / agent / Tines / EDR.\nDélimiter la contribution aux stories et les responsabilités des autres composants.'),('C20 / C21','Bugs de plateforme signalés.\nCas précis encore à documenter.\nConserver le combat comme cas démontré tant que nécessaire.')],
 'Ne pas confondre un incident cyber analysé et un bug de l’application corrigé.',
 'Le dossier E5 initial reste fondé sur le défaut historique du jeu et sa reproduction locale. Les projets entreprise n’apportent pas encore de preuve décrite de CI/CD, alerting opérationnel ou audit d’accessibilité. Maintenir ces limites plutôt que les considérer automatiquement levées.')

# Additional facts provided by the candidate during preparation.
replace(e1,8,'EXPLOITATION · SCALABILITÉ','Adapter la collecte au volume et aux schémas','Selon les tables : quelques dizaines de milliers à plusieurs dizaines de millions de lignes.',
 [('VOLUME','Des tailles de tables très différentes.\nAdapter le traitement à chaque source et table.'),('FENÊTRES DYNAMIQUES','Plages de récupération quotidienne ajustées selon les tables.\nRègle de calcul réelle à montrer.'),('SCHÉMA ÉVOLUTIF','Ajout à la volée de colonnes absentes des schémas ClickHouse.\nTypes et contrôles à expliciter.')],
 'La scalabilité est illustrée par des mécanismes concrets ; les gains restent à mesurer.',
 'Ordres de grandeur et mécanismes confirmés par le candidat. Ce sont des tailles de tables, pas des volumes ingérés chaque jour. Ne pas inventer partitionnement, sharding, cluster ou réduction de durée. Expliquer la règle de fenêtre, la prévention des trous/doublons et la gestion des nouvelles colonnes uniquement selon l’implémentation réelle. Les métriques avant/après restent à joindre.')
replace(e1,6,'C3 · NORMALISATION','Convertir les données ServiceNow avant ingestion','Des chaînes issues du XML provoquaient des erreurs de type dans ClickHouse.',
 [('ENTRÉE','Dans cette intégration, les lignes ServiceNow sont représentées en XML.\nLes valeurs arrivent comme chaînes brutes.'),('TRANSFORMATION','Système de validation développé.\nConversion des chaînes vers les types de données attendus.\nRègles exactes à illustrer.'),('CIBLE','Valeurs adaptées au schéma ClickHouse.\nTraitement des données invalides et validation du résultat à documenter.')],
 'Un cas métier réel pour démontrer nettoyage, typage et fiabilisation de la collecte.',
 'Ne pas généraliser : il s’agit du format rencontré dans cette intégration ServiceNow, pas d’une affirmation sur le stockage interne de tous les produits ServiceNow. Le candidat confirme le diagnostic et la conversion des strings. Aucun exemple de type, code d’erreur ni comportement de rejet n’a encore été fourni. Joindre une ligne XML anonymisée, les conversions et le résultat d’ingestion correspondant.')
replace(b2,5,'C7 · PÉRIMÈTRE RÉEL','Un modèle exécuté, un runner extensible','Modèle de la famille Qwen ; référence exacte à confirmer.',
 [('EXÉCUTION','Un seul modèle disponible dans l’architecture entreprise a été exploité à ce stade.\nPreuves de runs disponibles.'),('CONCEPTION','Script conçu pour être agnostique des modèles et des benchmarks cyber.\nInterfaces de configuration à montrer.'),('LIMITE C7','Pas encore de comparaison empirique entre plusieurs modèles.\nDistinguer contrainte d’architecture et recommandation de service.')],
 'L’extensibilité du runner n’est pas une comparaison multi-modèles déjà réalisée.',
 'Le candidat mentionne « Qwen3.8-27B » de mémoire et doit vérifier la référence. Le support évite de figer cet identifiant. Un seul modèle réellement exécuté : ne pas annoncer benchmark multi-modèles ni sélection du meilleur modèle. C7 peut être complétée par une analyse de services candidats et des exclusions documentées, mais la contrainte du modèle disponible ne remplace pas cette analyse.')
replace(b2,9,'ÉVALUATION · TRAÇABILITÉ','Conserver et interpréter chaque campagne','Un modèle exécuté ; cyber et performance mesurés par le même outil.',
 [('RÉSULTATS','Scores de benchmarks cyber.\nP50 / P95 / P99.\nVitesse et concurrence.\nEnregistrement en BDD.'),('RUNNER AGNOSTIQUE','Prise en compte de différents modèles et benchmarks prévue par conception.\nMontrer l’interface de configuration.'),('PREUVES À JOINDRE','Référence Qwen confirmée.\nUne campagne réelle.\nConditions, unités et erreurs.\nSchéma des résultats stockés.')],
 'Présenter les scores du modèle disponible, sans fabriquer de classement.',
 'Le candidat peut fournir des preuves de runs mais elles ne sont pas encore jointes. La présence de métadonnées précises en base n’est pas supposée : montrer ce qui est réellement enregistré et compléter la traçabilité si nécessaire. La reproductibilité ne découle pas automatiquement du stockage des métriques.')
replace(b2,10,'E2 · BILAN','Une veille concrète et un outil d’évaluation opérationnel','La comparaison porte aujourd’hui sur les benchmarks, pas encore sur plusieurs modèles.',
 [('C6','Environ dix benchmarks étudiés.\nScoring, usage et licences comparés.\nMatrice et traces de partage à joindre.'),('C7','Un modèle imposé par sa disponibilité.\nComparaison et recommandation de services encore à étayer.'),('C8','Configuration du jeu en complément.\nJoindre l’environnement et la référence exacte du modèle entreprise.')],
 'Le point fort nouveau est C12 ; la limite de comparaison C7 reste explicite.',
 'L’étude de benchmarks n’est pas la sélection d’un service LLM. On peut expliquer pourquoi l’architecture impose un candidat disponible, puis comparer les alternatives documentées sans inventer d’exécutions. Ne pas annoncer que tous les besoins C7 sont satisfaits. Les preuves C8 du jeu restent séparées de la configuration entreprise.')
replace(b2,19,'C12 · RUN À PRÉSENTER','Présenter un run du modèle disponible','Famille Qwen ; référence exacte et résultats à insérer depuis les preuves.',
 [('CYBER','Benchmark et version.\nScore obtenu et unité.\nNombre de cas.\nMécanisme de scoring retenu.'),('PERFORMANCE','P50 / P95 / P99.\nVitesse et unité.\nConcurrence exercée.\nCharge, erreurs et durée du test.'),('INTERPRÉTATION','Ce que le run démontre.\nSes limites.\nDécisions possibles pour l’usage.\nAucun classement multi-modèles.')],
 'Les runs existent selon le candidat ; aucune valeur n’est recopiée avant réception des pièces.',
 'Présenter le runner comme réalisé et exécuté. Les champs de la slide sont des emplacements pour une preuve existante, pas une simulation. Le seul modèle déclaré est Qwen avec version à confirmer. Mesure de performance du service, qualité cyber et tests du logiciel de benchmark sont trois périmètres différents.')

replace(b3,13,'E5 · CAS D’ALTERNANCE','Fiabiliser l’ingestion ServiceNow vers ClickHouse','Incident décrit par le candidat ; pièces techniques de résolution à joindre.',
 [('SYMPTÔME','Erreurs répétées de validation de types pendant l’ingestion des données ServiceNow.'),('CAUSE IDENTIFIÉE','Dans ce flux, les lignes issues de XML apportent des chaînes brutes non adaptées aux types attendus.'),('CORRECTION','Développement d’un système de validation et de conversion vers les types de données attendus.')],
 'Cas data professionnel : son adéquation au contexte applicatif IA d’E5 reste à établir.',
 'Le référentiel E5 vise la surveillance et la résolution d’un incident d’application dans le bloc IA. Le lien de cette plateforme à une application IA n’a pas été indiqué : ne pas le créer artificiellement. Ce scénario entreprise est une proposition à rattacher au périmètre accepté de l’épreuve. Le cas du jeu, dans son dossier d’origine, reste disponible comme alternative directement liée à l’application IA. Aucun run de reproduction entreprise n’a été inspecté ici.')
replace(b3,14,'C20 · SURVEILLANCE À DOCUMENT ER','Identifier le signal qui révèle l’échec d’ingestion','Le dispositif réel de détection de l’entreprise reste à préciser.',
 [('OBSERVATION','Bugs de validation de types constatés pendant l’ingestion.\nJoindre un message d’erreur réel et anonymisé.'),('CONTEXTE','Table concernée.\nÉtape du DAG.\nChamp et type attendus.\nValeur ou forme d’entrée impliquée.'),('DÉTECTION','Préciser comment le défaut a été détecté : run, logs, alerte ou signalement.\nNe pas inventer d’alerte.')],
 'La présence d’Airflow ne prouve pas une chaîne d’alerting opérationnelle.',
 'Les moyens de détection et de journalisation n’ont pas été décrits. Les cartes sont une trame de preuve, pas une configuration attestée. Les metrics et logs du jeu ne sont pas ceux de l’entreprise et ne doivent pas être attribués à ce cas. Si la surveillance professionnelle manque, conserver les slides C20 du support E5 initial et expliquer le changement de contexte.')
replace(b3,15,'C20 · CONTRÔLES PROPOSÉS','Suivre le succès et la qualité de l’alimentation','Signaux à documenter ou à ajouter ; pas de seuils entreprise fournis.',
 [('EXÉCUTION','État et durée du DAG.\nRetard de la donnée.\nFenêtre réellement traitée.\nReprises éventuelles.'),('QUALITÉ','Échecs de conversion.\nLignes acceptées / invalides.\nChamps et colonnes nouveaux.\nÉcarts de schéma.'),('RÉACTION','Seuils et destinataire réels.\nProcédure de diagnostic.\nPreuve d’une détection puis d’une résolution.')],
 'Ces contrôles sont proposés ; leur présence et leurs valeurs ne sont pas affirmées.',
 'C20 reste à prouver. Demander les métriques, seuils et notifications réellement utilisés. Ne pas réutiliser les alertes IA du jeu comme preuve du défaut de typage de la plateforme. Vérifier la confidentialité des lignes XML et des logs avant présentation ; ne pas afficher de données clients identifiantes.')
replace(b3,16,'C21 · REPRODUCTION À JOINDRE','Isoler une ligne qui déclenche l’erreur de type','Construire la preuve à partir du cas réel rencontré.',
 [('ENTRÉE RÉELLE','Un extrait XML anonymisé.\nUne valeur brute problématique.\nLe champ concerné.'),('ATTENDU','Le type prévu dans ClickHouse.\nLa règle de conversion.\nLa politique pour une valeur invalide.'),('OBSERVÉ AVANT','Message d’erreur de type.\nÉtape et commande d’ingestion.\nÉchantillon minimal reproductible.')],
 'La reproduction n’a pas encore été exécutée dans ce dossier : la pièce réelle reste à joindre.',
 'Ne pas inventer un message ClickHouse, une date, un type concret ou une capture. Le candidat a décrit l’incident et son diagnostic mais pas l’exemple minimal. Conserver l’entrée, le schéma et les paramètres nécessaires à une reproduction hors données de production.')
replace(b3,17,'C21 · CAUSE RACINE','Le format de transport ne porte pas les bons types','Le flux ServiceNow fournissait des chaînes issues de XML.',
 [('SOURCE','Dans l’intégration concernée : données représentées en XML, lues comme chaînes brutes.'),('ÉCART','Les valeurs transmises ne correspondaient pas aux types exigés par le schéma ClickHouse.'),('EFFET','L’ingestion rencontrait des erreurs de validation.\nLe contrôle devait intervenir avant l’écriture typée.')],
 'Cette cause est rapportée par le candidat ; un exemple de valeur doit l’illustrer.',
 'Ne pas affirmer que toutes les données internes ServiceNow sont stockées en XML. Ce fait concerne le flux rencontré. Distinguer parsing XML, normalisation de valeur et validation de type. Le détail des champs, valeurs nulles et formats temporels n’est pas fourni ; ne pas inventer leurs règles.')
replace(b3,18,'C21 · SOLUTION RÉALISÉE','Valider et convertir avant de charger','Système de conversion des chaînes développé par le candidat.',
 [('ENTRÉE','Lire les valeurs brutes du flux ServiceNow.\nIdentifier les types attendus selon le contrat réel.'),('CONVERSION','Appliquer les règles développées pour obtenir les valeurs typées attendues.\nCode à joindre.'),('VALIDATION','Contrôler avant l’insertion.\nDocumenter les cas invalides et le comportement effectivement choisi.')],
 'Ne pas remplacer silencieusement une donnée invalide par une valeur arbitraire.',
 'Le candidat a développé la validation et les conversions ; les règles et le comportement des rejets restent à montrer. La dernière phrase exprime un principe à défendre, pas une affirmation que le code fait ou ne fait pas cette substitution. Joindre commit/MR, tests et documentation lorsqu’ils sont disponibles. Aucun correctif entreprise n’a été apporté par cet assistant.')
replace(b3,19,'C21 · VALIDATION À MONTRER','Comparer le même échantillon avant et après','L’incident et sa correction sont décrits ; les résultats de validation restent à joindre.',
 [('AVANT','Erreur de type sur le cas identifié.\nEntrée et schéma connus.\nTrace du défaut.'),('APRÈS','Même entrée convertie.\nValeur typée obtenue.\nRésultat ClickHouse à montrer.\nAbsence de perte à vérifier.'),('NON-RÉGRESSION','Cas valides et invalides.\nFormats limites réellement rencontrés.\nTest automatisé ou contrôle de reprise disponible.')],
 'Aucun taux de réussite ni compteur de lignes corrigées n’est inventé.',
 'Ne pas attribuer les 44 tests du jeu à cette correction. Aucun test du convertisseur n’a été fourni ou exécuté ici. Une preuve de run réussi sur le même cas et un test de non-régression permettraient d’étayer fortement C21. L’évolution dynamique de colonnes relève d’une autre contrainte à distinguer du défaut de typage.')
replace(b3,20,'E5 · BILAN ET PÉRIMÈTRE','Une résolution métier à soutenir par ses pièces','La contribution est claire ; le dossier de preuve reste à compléter.',
 [('CONFIRMÉ','Incident de typage ServiceNow.\nInvestigation et cause.\nValidation / conversion développées.\nResponsabilité de maintenance.'),('À JOINDRE','Message et échantillon anonymisés.\nCode / commit.\nAvant / après.\nNon-régression et trace de livraison.'),('PÉRIMÈTRE E5','Relier le cas au contexte exigé.\nDocumenter la surveillance réelle.\nAlternative disponible : incident de combat du jeu.')],
 'Le cas entreprise ne remplace définitivement le cas du jeu qu’avec un périmètre et des preuves adaptés.',
 'Une correction de pipeline peut démontrer une méthode de résolution mais ne doit pas être présentée comme incident d’un service IA si aucun lien n’existe. Le référentiel et les consignes du centre déterminent le périmètre de l’épreuve. Le dossier initial du combat est conservé avec sa reproduction vérifiée ; la version entreprise est préparatoire.')
replace(b3,21,'ANNEXE A · ALTERNATIVE VÉRIFIÉE','Le cas du combat reste disponible','Call To AIdventure : défaut historique reproduit et correction vérifiée.',
 [('DÉFAUT','Deux combats peuvent partager les références globales dans l’ancien cœur de combat.'),('CORRECTION','Session de combat passée explicitement aux fonctions.\nCommit historique identifié.'),('PREUVE','Script et JSON avant / après.\nTest d’isolation.\nDossier E5 initial conservé dans presentation-bloc3/.')],
 'Ces résultats concernent le jeu ; ils ne valident pas le convertisseur ServiceNow.',
 'Pour revenir au cas démontré, utiliser Presentation_E5.pptx dans le dossier certif/presentation-bloc3. Le dossier Dossier_incident_E5.md et le script reproduce_incident.py contiennent les révisions et limites exactes. Ne pas mélanger les deux causes ni les chronologies.',
 'certif/presentation-bloc3/Dossier_incident_E5.md ; preuves/incident-combat.json')
replace(b3,23,'ANNEXE C · PREUVES ENTREPRISE','Les points qui changent la solidité du dossier','Faire porter chaque réalisation sur son apport réel.',
 [('DATAP LATEFORME','Volumes importants par table.\nFenêtres dynamiques.\nColonnes ajoutées à la volée.\nConversion du XML ServiceNow.'),('BENCHMARKS','Un seul modèle exécuté.\nRunner agnostique.\nScores et charge mesurés.\nRéférence Qwen à confirmer.'),('TINES','Quatre endpoints par webhook.\nContrat et appels EDR.\nIntégration comme outils de l’agent Django.')],
 'Documents et runs à joindre ; contexte et responsabilité explicités pour chaque preuve.',
 'La compétence C7 reste moins étayée qu’un vrai comparatif de services. C20 et le lien applicatif IA du cas d’incident doivent être précisés. La contribution C16 mérite des traces de coordination, pas seulement une responsabilité technique. Les schémas et contrôles d’accès Tines ne sont pas déduits du seul contrat.')

# Keep source projects explicit on slides retained from the initial decks.
for index in (11,12,14,15,16,19,20,22):
    if index < len(b2) and index not in (13,17,18,21):
        b2[index]['notes'] += ' Contexte de cette preuve conservée : Call To AIdventure. Aucun résultat de cette slide ne doit être attribué aux projets entreprise.'

assert sum(s['seconds'] for s in e1)==900
assert sum(s['seconds'] for s in b2)==2100
assert sum(s['seconds'] for s in b3)==1800
for deck in (e1,b2,b3):
    for slide in deck:
        slide['tag']=slide['tag'].replace('DOCUMENT ER','DOCUMENTER')
        slide['cards']=[(heading.replace('DATAP LATEFORME','DATAPLATEFORME'),body) for heading,body in slide['cards']]

# Keep editable text and PDF aligned; reduce only overflowing text by at most 2 pt.
original_txt=renderer['txt']
def fit_txt(slide,x,y,w,h,value,size=20,color=renderer['WHITE'],bold=False):
    for reduction in range(3):
        try:
            return original_txt(slide,x,y,w,h,value,size-reduction,color,bold)
        except ValueError as exc:
            if not str(exc).startswith('Text overflow:') or reduction==2:
                raise
renderer['txt']=fit_txt
render('E1_Alternance',e1)
render('Bloc2_Alternance',b2)
render('E2_Alternance',[s for s in b2 if s['part']=='E2'])
render('E3_Alternance',[s for s in b2 if s['part'] in {'E3','ANNEXE'}])
render('Bloc3_Alternance',b3)
render('E4_Alternance',[s for s in b3 if s['part']=='E4'])
render('E5_Alternance',[s for s in b3 if s['part'] in {'E5','ANNEXE'}])
