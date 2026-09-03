import random as r
from contextvars import ContextVar
from dataclasses import dataclass, field

from utils.enums import PlayerAction
from utils.monster import Monster, get_monster
from utils.player import Player
from utils.python_utils import clear


@dataclass
class CombatSession:
    player: Player
    monster: Monster
    log: list[str] = field(default_factory=list)
    player_is_defending: bool = False


def setup_combat_session(enemy: str, param_player: Player) -> tuple[list[str], CombatSession | None]:
    monster = get_monster(enemy)
    if not monster:
        return [f"{enemy} not found in database."], None

    session = CombatSession(
        player=param_player,
        monster=monster,
        log=[f"You are facing {monster.name}!"],
    )
    return session.log, session


def restore_combat_session(
    param_player: Player,
    param_monster: Monster,
    param_combat_log=None,
) -> CombatSession:
    return CombatSession(
        player=param_player,
        monster=param_monster,
        log=list(param_combat_log or []),
    )


def resolve_player_action(session: CombatSession, action: PlayerAction) -> tuple[bool, list[str]]:
    session.player_is_defending = False
    match action:
        case PlayerAction.ATTACK:
            dmg = r.randint(session.player.weapon.min_dmg, session.player.weapon.max_dmg) + session.player.strength
            session.monster.HP -= dmg
            session.log.append(
                f"You attack {session.monster.name} with your {session.player.weapon.name} "
                f"and deal {dmg} damage points to them."
            )
        case PlayerAction.DEFEND:
            session.player_is_defending = True
            session.log.append(
                f"You focus on defending yourself against {session.monster.name} attacks."
            )

    if session.monster.HP <= 0:
        session.log.append(f"You have defeated {session.monster.name}!")
    return session.monster.HP <= 0, session.log


def resolve_monster_attack(session: CombatSession) -> tuple[bool, list[str]]:
    dmg = r.randint(1, 6) + session.monster.strength
    if session.player_is_defending:
        dmg = int(dmg / 2)

    if dmg < 0:
        dmg = 0

    session.player.hp -= dmg
    session.log.append(f"{session.monster.name} attacks you! You suffer {dmg} damage points.")
    if session.player.hp <= 0:
        session.log.append("You have died!")
    return session.player.hp <= 0, session.log

_legacy_combat_session: ContextVar[CombatSession | None] = ContextVar(
    "legacy_combat_session",
    default=None,
)

def restore_combat(param_player: Player, param_monster, param_combat_log=None):
    session = restore_combat_session(param_player, param_monster, param_combat_log)
    _legacy_combat_session.set(session)

def setup_combat(enemy: str, param_player: Player):
    log, session = setup_combat_session(enemy, param_player)
    if session is None:
        _legacy_combat_session.set(None)
        return log, None

    _legacy_combat_session.set(session)
    return log, session.monster

def player_action(action: PlayerAction):
    session = _legacy_combat_session.get()
    if session is None:
        raise RuntimeError("No active combat session")

    won, log = resolve_player_action(session, action)
    return won, log

def monster_attack():
    session = _legacy_combat_session.get()
    if session is None:
        raise RuntimeError("No active combat session")

    return resolve_monster_attack(session)

def get_current_combat_state():
    session = _legacy_combat_session.get()
    return {
        "player": session.player if session else None,
        "monster": session.monster if session else None,
    }

# def run_combat(enemy: str, player: Player):
#     global current_monster
    
#     current_monster = get_monster(enemy)
        
    
    
#     while True:
#         print(f"You attack {current_monster.name}.")
#         damage = r.randint(10, 100)
#         current_monster.HP -= damage
#         print(f"{current_monster.name} suffers {damage} damage. (Remaining : {current_monster.HP})\n")
        
#         sleep(1)
        
#         if current_monster.HP <= 0:
#             break
        
#         print(f"{current_monster.name} attacks {player.name}.")
#         damage = r.randint(1, 6) + current_monster.strength
#         if damage < 0: damage = 0
#         player.hp -= damage
#         print(f"You suffer {damage} damage. (Remaining : {player.hp})\n")
        
        
#         sleep(1)
        
#         if player.hp <= 0:
#             break
        
#     signal = ""
#     msg = ""
#     if player.hp <= 0:
#         msg = "You died!"
#         signal = 2
#     else:
#         msg = f"You vanquished {current_monster.name}!"
#         signal = 1
    
#     return {"signal": signal, "message": msg}
        
        
if __name__ == "__main__":
    clear()
    # print(run_combat("goblin warrior", load_player("data/world/other/player.json")))
