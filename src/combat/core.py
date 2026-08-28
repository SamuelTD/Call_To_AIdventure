from utils.player import Player
from utils.monster import get_monster
from utils.enums import PlayerAction
import random as r
from utils.python_utils import clear

current_monster = ""
combat_log = []
player = ""
player_is_defending = False

def restore_combat(param_player: Player, param_monster, param_combat_log=None):
    global current_monster, combat_log, player, player_is_defending

    player = param_player
    current_monster = param_monster
    combat_log = list(param_combat_log or [])
    player_is_defending = False

def setup_combat(enemy: str, param_player: Player):
    global current_monster, combat_log, player
    
    player = param_player
    current_monster = get_monster(enemy)
    if not current_monster:
        combat_log = [f"{enemy} not found in database."]
        return combat_log, None
    combat_log = []
    combat_log.append(f"You are facing {current_monster.name}!")
    return combat_log, current_monster

def player_action(action: PlayerAction):
    global player_is_defending
    
    player_is_defending = False
    match action:
        case PlayerAction.ATTACK:
            dmg = r.randint(player.weapon.min_dmg, player.weapon.max_dmg)+player.strength
            current_monster.HP -= dmg
            combat_log.append(f"You attack {current_monster.name} with your {player.weapon.name} and deal {dmg} damage points to them.")
        case PlayerAction.DEFEND:
            player_is_defending = True
            combat_log.append(f"You focus on defending yourself against {current_monster.name} attacks.")
    
    if current_monster.HP <= 0:
        combat_log.append(f"You have defeated {current_monster.name}!")
    return current_monster.HP <= 0, combat_log

def monster_attack():
    dmg = r.randint(1, 6)+current_monster.strength
    if player_is_defending:
        dmg /= 2
        dmg = int(dmg)
        
    if dmg < 0:
        dmg = 0
        
    player.hp -= dmg
    combat_log.append(f"{current_monster.name} attacks you! You suffer {dmg} damage points.")
    if player.hp<= 0:
        combat_log.append("You have died!")
    return player.hp <= 0, combat_log

def get_current_combat_state():
    return {
        "player": player,
        "monster": current_monster,
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
