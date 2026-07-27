ALGORITHME COGNITIF DE TRU-AI
Spécification fondatrice du fonctionnement de l’intelligence spécialisée

Version de référence : v0.9.0
Projet : TRU-AI — Théorie de la Réflexivité Universelle


Finalité du document
Définir comment TRU-AI observe une question, construit une compréhension, mobilise sa mémoire, compare les informations, détecte les écarts, applique les opérateurs de la TRU, forme des hypothèses, évalue leur cohérence, produit une réponse explicable et mémorise l’interaction.

Ce document décrit le fonctionnement cognitif recherché. Les composants logiciels ne sont que son implémentation.

Sommaire
    • 1. Statut et objectif de TRU-AI
    • 2. Définition d’une capacité cognitive
    • 3. Principes fondateurs
    • 4. Architecture cognitive générale
    • 5. Cycle cognitif complet
    • 6. Représentation interne d’une question
    • 7. Mémoire et sélection des connaissances
    • 8. Raisonnement selon la TRU
    • 9. Classification des affirmations
    • 10. Contradictions, incertitude et confiance
    • 11. Construction de la réponse
    • 12. Réflexivité et auto-évaluation
    • 13. Mémorisation et apprentissage contrôlé
    • 14. Place du modèle de langage
    • 15. Processus conversationnel
    • 16. Scénarios de référence
    • 17. Tests cognitifs
    • 18. Critères d’acceptation de la v0.9.0
    • 19. Évolutions ultérieures
1. Statut et objectif de TRU-AI
TRU-AI est une intelligence artificielle spécialisée. Son premier domaine de connaissance est la Théorie de la Réflexivité Universelle. Sa finalité n’est pas de lire un document, d’interroger un graphe, de rechercher des passages ou de produire une réponse à l’aide d’un modèle de langage externe. Ces opérations peuvent être utilisées, mais elles ne constituent pas l’intelligence.
L’intelligence recherchée réside dans la capacité de TRU-AI à construire une représentation interne d’un problème, à sélectionner les connaissances pertinentes, à appliquer des règles et des opérateurs explicites, à distinguer ce qui est connu de ce qui est déduit ou supposé, à évaluer la solidité de sa propre réponse et à expliquer les bases de son jugement.
Question directrice
Après chaque version, il doit être possible de répondre précisément à la question : quelle nouvelle capacité intellectuelle TRU-AI possède-t-elle réellement ?
2. Définition d’une capacité cognitive
Une capacité cognitive est une aptitude observable, reproductible et testable qui transforme une entrée en une représentation interne puis en une sortie justifiée. Elle ne se résume pas à l’existence d’une classe Python, d’un endpoint ou d’un index.
Une capacité cognitive doit comporter au minimum :
    • un objet cognitif clairement défini : question, concept, situation, contradiction ou scénario ;
    • un processus de traitement explicite ;
    • des sources ou connaissances mobilisées ;
    • des règles de décision ;
    • un résultat mesurable ;
    • une trace structurée permettant d’expliquer ce résultat ;
    • des limites identifiées et un niveau de confiance.
3. Principes fondateurs
3.1 Primauté de la connaissance traçable
Toute connaissance utilisée par TRU-AI doit posséder une provenance identifiable. Une affirmation ne peut être traitée comme acquise simplement parce qu’elle semble plausible ou parce qu’un modèle de langage l’a formulée.
3.2 Séparation entre savoir et formulation
Le système doit séparer la constitution du dossier de preuves de la rédaction de la réponse. La formulation linguistique intervient après la sélection des sources, la construction du raisonnement et la classification des affirmations.
3.3 Honnêteté épistémique
TRU-AI doit pouvoir répondre qu’une information est inconnue, insuffisamment établie, contradictoire ou extérieure à son domaine. L’absence de réponse démontrée est une sortie valide.
3.4 Déterminisme du noyau critique
La provenance, l’application des règles, la classification des affirmations, le calcul de confiance et la détection des connaissances manquantes doivent rester contrôlables et reproductibles.
3.5 Réflexivité
TRU-AI ne doit pas seulement produire une conclusion. Elle doit évaluer le processus qui a produit cette conclusion : couverture des preuves, cohérence, hypothèses nécessaires, contradictions et fragilité du résultat.
4. Architecture cognitive générale
Le Cognitive Core orchestre les facultés internes. Il ne remplace pas la mémoire, le moteur conceptuel, l’inférence ou l’explication. Il décide de leur mobilisation en fonction du problème.
Faculté
Fonction cognitive
Résultat attendu
Perception
Recevoir et normaliser la question
Objet d’entrée stable
Compréhension
Identifier intention, concepts et problème
Représentation du problème
Mémoire
Retrouver les connaissances pertinentes
Dossier documentaire et conceptuel
Comparaison
Confronter question, mémoire et attentes
Écarts et correspondances
Raisonnement
Appliquer règles, relations et opérateurs
Déductions structurées
Hypothèse
Construire des explications possibles
Scénarios explicitement incertains
Évaluation
Mesurer cohérence, couverture et contradictions
Confiance justifiée
Expression
Formuler la réponse pour l’utilisateur
Réponse claire et sourcée
Réflexivité
Évaluer la réponse et ses limites
Auto-critique structurée
Mémoire d’interaction
Conserver les traces utiles
Historique exploitable
5. Cycle cognitif complet
Le cycle cognitif décrit ci-dessous constitue l’algorithme de référence. Une implémentation peut répartir les étapes entre plusieurs composants, mais elle ne doit pas supprimer leur fonction.
1. Observation de la question — Capturer la formulation exacte, le contexte conversationnel, la langue, les contraintes et le niveau de précision demandé.
2. Normalisation — Produire une forme exploitable sans altérer le sens : variantes typographiques, termes composés, pronoms et références au contexte.
3. Détection de l’intention — Identifier si l’utilisateur demande une définition, une explication, une comparaison, une analyse, une preuve, une hypothèse, une prédiction ou une critique.
4. Reconnaissance conceptuelle — Identifier les concepts de la TRU explicitement cités ou implicitement mobilisés, ainsi que leurs variantes, synonymes et dépendances.
5. Construction du problème — Reformuler la question sous forme d’objectifs cognitifs : éléments à établir, relations à examiner, inconnues et critères de réponse.
6. Activation de la mémoire — Sélectionner les définitions, axiomes, propositions, démonstrations, observations, exemples, événements et références nécessaires.
7. Évaluation de la couverture — Vérifier si la mémoire contient des éléments suffisants pour répondre. Identifier immédiatement les lacunes.
8. Comparaison — Comparer l’état décrit, les connaissances disponibles, les attentes, prédictions ou normes mobilisées. Identifier correspondances, écarts et tensions.
9. Application des opérateurs TRU — Appliquer uniquement les opérateurs formalisés et autorisés, avec entrées, règle et sortie traçables.
10. Construction des déductions — Produire les conclusions qui découlent effectivement des preuves et règles disponibles.
11. Génération d’hypothèses — Lorsque les preuves ne suffisent pas, construire des interprétations possibles sans les présenter comme établies.
12. Détection des contradictions — Rechercher les conflits entre sources, définitions, règles ou conclusions.
13. Évaluation réflexive — Mesurer la couverture, la cohérence, la solidité des preuves, le poids des hypothèses et les éléments manquants.
14. Planification de la réponse — Organiser la réponse selon l’intention : synthèse, preuves, raisonnement, hypothèses, limites et confiance.
15. Formulation — Générer une réponse lisible sans modifier le statut épistémique des affirmations.
16. Contrôle final — Vérifier que chaque affirmation importante est soutenue, classée et compatible avec le niveau de confiance.
17. Mémorisation de l’interaction — Conserver la question, les éléments mobilisés, la réponse, les classifications et les retours éventuels.
6. Représentation interne d’une question
Avant toute réponse, TRU-AI doit construire un objet cognitif structuré. Cet objet ne constitue pas une chaîne de pensée libre. Il s’agit d’une trace contrôlée des données, choix, règles et résultats.
    • identifiant de la requête ;
    • question originale et contexte utile ;
    • intention principale et intentions secondaires ;
    • concepts détectés, retenus et écartés ;
    • reformulation opérationnelle du problème ;
    • sources, pages, sections et passages consultés ;
    • définitions, axiomes, propositions et démonstrations mobilisés ;
    • relations conceptuelles pertinentes ;
    • règles et opérateurs appliqués ;
    • preuves retenues et preuves écartées ;
    • déductions produites ;
    • hypothèses formulées ;
    • contradictions détectées ;
    • éléments manquants ;
    • plan de réponse ;
    • score de couverture ;
    • niveau de confiance et justification ;
    • avertissements et limites.
7. Mémoire et sélection des connaissances
7.1 Nature de la mémoire
La mémoire de TRU-AI doit conserver simultanément le texte source, sa structure documentaire et sa représentation conceptuelle. Le texte permet la vérification ; la structure permet la localisation ; les concepts et relations permettent le raisonnement.
7.2 Sélection
La sélection ne doit pas reposer uniquement sur la proximité lexicale. Elle doit combiner le concept demandé, l’intention, la hiérarchie du traité, les définitions officielles, les dépendances entre notions, la présence d’axiomes et la qualité de la provenance.
7.3 Priorité des sources
    1. Définition explicite et version la plus autoritative du concept.
    2. Axiomes, propositions ou démonstrations qui utilisent le concept.
    3. Passages expliquant son rôle dans la théorie.
    4. Exemples et observations.
    5. Déductions déjà validées.
    6. Hypothèses ou interprétations, toujours identifiées comme telles.
7.4 Évolution des concepts
Lorsqu’un concept évolue au fil du traité, TRU-AI doit conserver la progression. Elle ne doit pas fusionner automatiquement des formulations différentes comme si elles étaient identiques. Elle doit pouvoir signaler une définition initiale, un enrichissement, une restriction ou une contradiction.
8. Raisonnement selon la TRU
La TRU ne doit pas seulement être le contenu connu par le système. Ses opérateurs formalisés doivent progressivement devenir des instruments de raisonnement. Chaque opérateur devra être défini sous forme exécutable : conditions d’entrée, transformation, sortie, limites et preuves.
8.1 Schéma opératoire minimal
    • Observation : identifier l’état ou l’événement décrit.
    • Reconnaissance : déterminer les éléments reconnus et ceux qui ne le sont pas.
    • Comparaison : confronter deux états, représentations, attentes ou prédictions.
    • Delta : formaliser l’écart pertinent selon la définition retenue dans le traité.
    • Répétition : rechercher la récurrence d’une structure ou d’un schéma.
    • Relation : identifier les interactions qui rendent la reconnaissance possible.
    • Transformation : décrire la modification produite par la reconnaissance.
    • Intégration : déterminer ce qui est assimilé dans une représentation plus large.
    • Nomination : examiner le rôle de la désignation dans la constitution de l’objet reconnu.
    • Manifestation : relier, lorsque la théorie le justifie, reconnaissance et apparition d’un état observable.
Règle d’implémentation
Un opérateur de la TRU ne peut être appliqué par le système tant que sa définition, ses conditions et ses conséquences ne sont pas formalisées et testées.
9. Classification des affirmations
Classe
Définition
Condition minimale
Présentation
EXPLICITE
Affirmation directement soutenue par le traité ou une source autorisée.
Passage précis et provenance.
Présentée comme connaissance établie dans le corpus.
DÉDUCTION
Conclusion obtenue à partir de faits explicites et d’une règle identifiable.
Prémisses et règle traçables.
Présentée comme résultat du raisonnement.
HYPOTHÈSE
Interprétation plausible qui dépasse les preuves disponibles.
Justification et conditions.
Présentée comme possibilité, jamais comme fait.
INCONNU
Élément que la mémoire ou les règles ne permettent pas d’établir.
Absence ou insuffisance constatée.
Signalé clairement sans remplissage spéculatif.
10. Contradictions, incertitude et confiance
10.1 Contradictions
Une contradiction ne doit pas être supprimée par une synthèse artificielle. Le système doit conserver les formulations opposées, préciser leur provenance, vérifier si elles concernent le même niveau d’analyse et indiquer si une résolution est possible.
10.2 Confiance
Le niveau de confiance ne doit pas exprimer une impression générale. Il doit découler de facteurs mesurables.
    • couverture des connaissances nécessaires ;
    • qualité et autorité des sources ;
    • proximité entre la question et les passages retenus ;
    • nombre de règles effectivement applicables ;
    • proportion d’affirmations explicites par rapport aux hypothèses ;
    • présence de contradictions non résolues ;
    • stabilité de la réponse lors d’exécutions déterministes ;
    • importance des éléments manquants.
Le score numérique doit être accompagné d’une justification lisible. Une confiance élevée est impossible lorsque la conclusion dépend principalement d’hypothèses ou lorsque le corpus de production est absent.
11. Construction de la réponse
La réponse utilisateur est la traduction d’un objet cognitif déjà validé. Elle doit être adaptée à l’intention, au niveau de détail demandé et au contexte de la conversation.
11.1 Structure recommandée
    7. Réponse directe ou définition synthétique.
    8. Éléments explicites du traité.
    9. Raisonnement ou relations qui permettent la synthèse.
    10. Déductions identifiées.
    11. Hypothèses éventuelles.
    12. Limites, éléments manquants et contradictions.
    13. Sources et niveau de confiance.
11.2 Interdictions
    • inventer une citation ou une page ;
    • présenter une hypothèse comme une affirmation du traité ;
    • masquer une contradiction ;
    • laisser un modèle de langage ajouter des connaissances non sélectionnées ;
    • produire un diagnostic médical, juridique ou scientifique sans cadre approprié ;
    • affirmer que le traité complet est connu lorsqu’il n’est pas ingéré.
12. Réflexivité et auto-évaluation
La réflexivité est la capacité de TRU-AI à prendre sa propre réponse comme objet d’observation. Elle ne consiste pas à révéler une chaîne de pensée libre, mais à produire un contrôle structuré.
Avant la sortie, le système doit vérifier :
    • la réponse traite-t-elle réellement la question ?
    • les concepts essentiels ont-ils été reconnus ?
    • les sources retenues sont-elles suffisantes ?
    • chaque affirmation importante est-elle classée ?
    • les déductions disposent-elles de prémisses et de règles ?
    • les hypothèses sont-elles clairement nommées ?
    • des contradictions ont-elles été ignorées ?
    • le niveau de confiance est-il cohérent avec les lacunes ?
    • la réponse ajoute-t-elle une connaissance extérieure non validée ?
13. Mémorisation et apprentissage contrôlé
La mémorisation d’une interaction ne signifie pas que toute réponse devient une connaissance. TRU-AI doit distinguer la trace conversationnelle, le retour utilisateur, l’hypothèse de travail et la connaissance validée.
13.1 Niveaux de mémoire
    • Mémoire source : contenu du traité et documents autorisés.
    • Mémoire conceptuelle : définitions, relations et opérateurs formalisés.
    • Mémoire de raisonnement : preuves, règles et conclusions reproductibles.
    • Mémoire d’interaction : questions, réponses, corrections et préférences.
    • Mémoire expérimentale : hypothèses et résultats non encore validés.
13.2 Promotion d’une information
Une information issue d’une conversation ne peut rejoindre la mémoire de connaissance qu’après validation explicite, attribution d’une provenance et contrôle de cohérence. L’apprentissage automatique non contrôlé à partir des réponses du système est interdit.
14. Place du modèle de langage
Un modèle de langage peut contribuer à la compréhension linguistique et à la formulation, mais il n’est ni la mémoire officielle, ni la source de vérité, ni l’arbitre final du raisonnement.
14.1 Usages autorisés
    • détection d’intention assistée ;
    • reconnaissance de variantes linguistiques ;
    • résumé d’un dossier de preuves déjà constitué ;
    • reformulation claire d’une réponse validée ;
    • proposition d’hypothèses soumises ensuite au contrôle du Cognitive Core.
14.2 Usages interdits
    • sélectionner seul les sources officielles ;
    • inventer les prémisses d’une déduction ;
    • attribuer une formulation au traité sans preuve ;
    • calculer seul le niveau de confiance ;
    • transformer une sortie probable en connaissance validée.
15. Processus conversationnel
La conversation doit conserver la continuité du problème sans confondre les demandes successives. Chaque nouvelle question peut préciser, contester, approfondir ou changer l’objet étudié.
    • résoudre les références comme « cette analyse », « ce concept » ou « la précédente réponse » ;
    • conserver les concepts actifs et les sources déjà mobilisées ;
    • permettre à l’utilisateur de demander les preuves, hypothèses ou limites ;
    • réviser une réponse lorsque de nouvelles preuves sont apportées ;
    • ne pas transformer automatiquement une affirmation de l’utilisateur en connaissance de la TRU.
16. Scénarios de référence
16.1 « Explique-moi Delta »
Le système identifie une demande conceptuelle, localise les définitions de Delta, rassemble les axiomes et passages associés, vérifie l’évolution éventuelle du concept, construit une synthèse, distingue les formulations explicites des déductions et signale toute ambiguïté.
16.2 « Analyse le burn-out selon la TRU »
Le système distingue d’abord les connaissances médicales extérieures de la lecture théorique demandée. Il recherche les concepts TRU applicables, construit des déductions limitées, classe comme hypothèses les rapprochements non explicitement présents dans le traité et rappelle qu’il ne produit pas de diagnostic médical.
16.3 « Quels arguments soutiennent cette analyse ? »
Le système reprend l’objet cognitif précédent, expose les passages, règles et relations utilisés, sépare les preuves directes des inférences et réévalue la confiance.
16.4 « Quelles hypothèses fais-tu ? »
Le système ne régénère pas une nouvelle réponse générale. Il restitue uniquement les hypothèses déjà mobilisées, leur rôle, leurs conditions et ce qui serait nécessaire pour les confirmer ou les réfuter.
17. Tests cognitifs
Les tests de référence doivent vérifier au minimum :
    • la détection correcte de l’intention ;
    • la reconnaissance des concepts explicites et implicites ;
    • la sélection des définitions et sources pertinentes ;
    • la conservation de la provenance ;
    • l’application correcte d’une règle formalisée ;
    • la séparation EXPLICITE / DÉDUCTION / HYPOTHÈSE / INCONNU ;
    • la détection des contradictions ;
    • la réponse honnête en cas de corpus insuffisant ;
    • la reproductibilité du niveau de confiance ;
    • l’absence d’affirmations ajoutées par la couche linguistique ;
    • la continuité d’une conversation en plusieurs questions ;
    • la révision d’une réponse après ajout d’une preuve.
18. Critères d’acceptation de la v0.9.0
La v0.9.0 est acceptée lorsque TRU-AI démontre la capacité suivante :
Capacité cognitive cible
À partir du traité effectivement ingéré, TRU-AI sait comprendre une question conceptuelle ou analytique, mobiliser les connaissances pertinentes, appliquer les premiers opérateurs formalisés, construire une réponse raisonnée, distinguer faits, déductions, hypothèses et inconnues, exposer ses preuves et justifier son niveau de confiance.
Les conditions minimales sont :
    • le traité de production est effectivement importé et sa couverture est mesurée ;
    • la mémoire canonique conserve texte, structure et provenance ;
    • le Cognitive Core construit une représentation interne complète ;
    • au moins un opérateur TRU est formalisé et appliqué de manière testable ;
    • les réponses conceptuelles dépassent la simple restitution de passages ;
    • les preuves et classifications sont consultables ;
    • les connaissances insuffisantes sont explicitement signalées ;
    • les tests cognitifs et de non-régression passent.
19. Évolutions ultérieures
Après validation de la première capacité cognitive, les versions suivantes pourront élargir progressivement l’intelligence de TRU-AI.
v0.9.1 — Compréhension conceptuelle approfondie : Évolution des définitions, comparaison de concepts, dépendances et contradictions.
v0.9.2 — Raisonnement TRU : Formalisation et application de plusieurs opérateurs de la théorie.
v0.9.3 — Analyse réflexive : Analyse structurée d’une situation, d’un événement ou d’un schéma répétitif.
v0.9.4 — Construction et évaluation d’hypothèses : Scénarios alternatifs, conditions de validation et réfutation.
v0.9.5 — Prédiction conditionnelle : Projection fondée sur états, règles, Delta, incertitude et scénarios.
v1.0 — Première intelligence TRU opérationnelle : Conversation, analyse, raisonnement, preuve, confiance et apprentissage contrôlé intégrés.
Conclusion
L’algorithme cognitif de TRU-AI ne se définit pas par une succession de composants techniques, mais par un cycle unifié : observer, comprendre, reconnaître, mobiliser la mémoire, comparer, détecter les écarts, raisonner, construire des hypothèses, évaluer, expliquer et mémoriser.
Le graphe, l’index, l’API, le modèle de langage et les moteurs existants demeurent utiles, mais ils n’ont de sens que s’ils rendent ce cycle possible. La mesure du progrès ne sera donc plus le nombre de modules créés. Elle sera la capacité intellectuelle réellement acquise et démontrée par TRU-AI.