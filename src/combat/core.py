from utils.player import Player, load_player
from utils.monster import get_monster
from utils.enums import PlayerAction
import random as r
from time import sleep
from utils.python_utils import clear

current_monster = ""
combat_log = []
player = ""
player_is_defending = False

def setup_combat(enemy: str, param_player: Player):
    global current_monster, combat_log, player
    
    player = param_player
    current_monster = get_monster(enemy)
    if not current_monster:
        return f"{enemy} not found in database."
    combat_log = []

def player_action(action: PlayerAction):
    global player_is_defending
    
    player_is_defending = False
    match action:
        case PlayerAction.ATTACK:
            dmg = r.randint(player.weapon.min_dmg, player.weapon.max_dmg)+player.strength
            current_monster.HP -= dmg
            combat_log.append(f"You attack {current_monster.name} with your {player.weapon.name} and deal {dmg} damage points to them.\
                ({current_monster.HP} health remaining)")
        case PlayerAction.DEFEND:
            player_is_defending = True
            combat_log.append(f"You focus on defending yourself against {current_monster.name} attacks.")
    
    if current_monster.HP <= 0:
        return True
    
    return False

def monster_attack():
    dmg = r.randint(1, 6)+current_monster.strength
    if player_is_defending:
        dmg /= 2
        if dmg < 0:
            dmg = 0
    player.hp -= dmg
    combat_log.append(f"{current_monster.name} attacks you! You suffer {dmg} damage points. ({player.hp} health remaining)")

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