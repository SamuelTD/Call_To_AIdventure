def build_lore_section(rag_context: str) -> str:
    return f"""
Connaissances pertinentes sur l'univers :
{rag_context}

Règles concernant ces connaissances :
- Ne les utilise que lorsqu'elles sont pertinentes pour la scène actuelle.
- N'introduis aucun personnage ni lieu extérieur au périmètre de l'aventure actuelle.
- L'état actuel de la partie et les événements déjà résolus priment sur ces connaissances.
""".strip()


def build_pre_combat_fluff_prompt(current_story, latest_user, monster_name, rag_context):
    return f"""
Tu es le maître du jeu d'un jeu de rôle fantastique. Écris en français une courte scène descriptive,
de deux ou trois phrases maximum, qui précède un combat. Appuie-toi sur le contexte et l'action du joueur.

Contexte : {current_story}
Action du joueur : {latest_user}
L'ennemi que le joueur va affronter est {monster_name}.

{build_lore_section(rag_context)}
""".strip()


def build_post_combat_story_prompt(player_summary, chat_history, enemy, gold_loot, item_loot, rag_context):
    return f"""
Informations sur le joueur :
{player_summary}

L'aventure jusqu'ici :
{chat_history}

{build_lore_section(rag_context)}

Tu es le maître du jeu d'un jeu d'aventure narratif. Poursuis l'histoire en français dans un style raffiné
inspiré de la fantasy. Écris à la deuxième personne du pluriel et limite ta réponse à quatre phrases.
Le joueur vient de vaincre et tuer {enemy}. Commence exactement par « Vous avez vaincu {enemy} »,
puis poursuis en considérant que cet ennemi est mort. Le joueur trouve sur le corps {gold_loot} pièces d'or
et {item_loot}. Intègre naturellement ce butin au récit.
""".strip()


def build_post_heal_story_prompt(player_summary, chat_history, latest_user, requested_heal_amount, actual_heal_amount, current_hp, max_hp, rag_context):
    return f"""
Informations sur le joueur :
{player_summary}

L'aventure jusqu'ici :
{chat_history}

{build_lore_section(rag_context)}

Tu es le maître du jeu d'un jeu d'aventure narratif. Poursuis l'histoire en français, à la deuxième personne
du pluriel, dans un style raffiné inspiré de la fantasy, en quatre phrases maximum. La dernière action a permis
au joueur de récupérer {actual_heal_amount} PV. Intègre naturellement ce soin sans inventer de trésor,
de combat ni de récompense mécanique supplémentaire.

Action du joueur : {latest_user}
""".strip()


def build_post_damage_story_prompt(player_summary, chat_history, latest_user, requested_damage_amount, actual_damage_amount, current_hp, max_hp, player_has_died, rag_context):
    death_instruction = (
        "Les dégâts ont réduit les PV du joueur à zéro. Décris clairement sa mort ou son effondrement, sans proposer de choix ni poursuivre au-delà de cet instant."
        if player_has_died
        else "Le joueur a survécu aux dégâts. Poursuis naturellement la scène."
    )
    return f"""
Informations sur le joueur :
{player_summary}

L'aventure jusqu'ici :
{chat_history}

{build_lore_section(rag_context)}

Tu es le maître du jeu d'un jeu d'aventure narratif. Poursuis l'histoire en français, à la deuxième personne
du pluriel, dans un style raffiné inspiré de la fantasy, en quatre phrases maximum. La dernière action a fait
perdre {actual_damage_amount} PV au joueur, qui possède maintenant {current_hp}/{max_hp} PV.
{death_instruction}
Intègre naturellement cette perte de santé sans inventer de trésor, de combat ni de récompense supplémentaire.

Action du joueur : {latest_user}
""".strip()


def build_regular_story_prompt(player_summary, chat_history, latest_user, rag_context):
    return f"""
Informations sur le joueur :
{player_summary}

L'aventure jusqu'ici :
{chat_history}

{build_lore_section(rag_context)}

Tu es le maître du jeu d'un jeu d'aventure narratif. Interprète l'action du joueur et poursuis l'histoire en français.
Adopte un style raffiné inspiré de la fantasy et écris à la deuxième personne du pluriel. Limite chaque réponse
à quatre phrases. Fais progresser l'histoire sans la précipiter. Tu peux et dois infliger des conséquences
défavorables au joueur lorsqu'elles sont cohérentes avec le récit.

Action du joueur : {latest_user}
""".strip()


def build_current_room_prompt(player_summary, current_story, rag_context):
    return f"""
Informations sur le joueur :
{player_summary}

Récit actuel :
{current_story}

{build_lore_section(rag_context)}

Tu es le maître du jeu d'un jeu d'aventure narratif. Décris à nouveau en français la pièce où se trouve le joueur.
Il s'agit d'une vérification de débogage, pas d'un nouveau tour. Utilise les connaissances sur la pièce comme
source principale. Ne fais pas avancer le temps, ne déclenche aucun combat, ne valide aucun objectif, n'accorde
aucun butin, ne déplace pas le joueur et ne propose aucun choix. Écris à la deuxième personne du pluriel,
dans un style fantasy raffiné, en quatre phrases maximum.
""".strip()


def build_room_completion_prompt(player_summary, current_location_id, room_objective, room_signals, chat_history, latest_user, current_story):
    signals = "\n".join(f"- {signal}" for signal in room_signals) or "- Aucun"
    return f"""
Tu évalues l'achèvement d'une pièce dans un donjon narratif linéaire. Détermine uniquement si le dernier récit
résolu accomplit l'objectif actuel. Ne valide pas la pièce à partir d'une simple intention du joueur,
d'une vague annonce ou d'un projet futur. Elle n'est achevée que si le dernier récit résout clairement
l'objectif ou correspond à l'un des signaux d'achèvement.

Joueur : {player_summary}
Identifiant de la pièce : {current_location_id}
Objectif : {room_objective}
Signaux d'achèvement :
{signals}
Contexte récent : {chat_history}
Dernier choix du joueur : {latest_user}
Dernier récit résolu : {current_story}
""".strip()


def build_room_arrival_prompt(player_summary, previous_story, previous_location_id, next_location_id, rag_context):
    return f"""
Informations sur le joueur : {player_summary}
Le joueur a terminé la pièce : {previous_location_id}
Récit précédent : {previous_story}
Le joueur entre maintenant dans la pièce : {next_location_id}

{build_lore_section(rag_context)}

Tu es le maître du jeu d'une aventure de donjon linéaire. Décris brièvement en français l'arrivée dans
la nouvelle pièce, en utilisant les connaissances récupérées comme source principale. Ne propose aucun choix,
ne déclenche aucun combat, n'accorde aucun butin, ne valide aucun objectif et ne va pas au-delà de cette pièce.
Écris à la deuxième personne du pluriel, dans un style fantasy raffiné, en quatre phrases maximum.
""".strip()


def build_goal_evaluation_prompt(player_summary, chat_history, latest_user, current_story, ongoing_goals):
    goals = "\n".join(f"- {goal}" for goal in ongoing_goals)
    return f"""
Tu évalues l'accomplissement des objectifs d'un jeu de rôle narratif. N'évalue que les objectifs en cours
ci-dessous. Les objectifs déjà accomplis sont volontairement absents. Ne valide un objectif que si le dernier
récit résolu montre clairement que le joueur l'a accompli. Ignore les indices vagues, intentions futures et
anciens événements sans rapport. Retourne uniquement les textes exacts de la liste des objectifs en cours.

Joueur : {player_summary}
Contexte récent : {chat_history}
Dernier choix : {latest_user}
Dernier récit résolu : {current_story}
Objectifs en cours :
{goals}
""".strip()


def build_victory_wrapup_prompt(player_summary, chat_history, latest_user, current_story, finished_goals):
    goals = "\n".join(f"- {goal}" for goal in finished_goals)
    return f"""
Informations sur le joueur : {player_summary}
L'aventure jusqu'ici : {chat_history}
Dernier choix du joueur : {latest_user}
Dernier récit résolu : {current_story}
Tous les objectifs requis sont accomplis :
{goals}

Tu es le maître du jeu d'un jeu d'aventure narratif. Écris en français une courte conclusion intégrée au récit,
à la deuxième personne du pluriel, dans un style fantasy raffiné. Limite-la à quatre phrases et ne propose aucun choix.
""".strip()
