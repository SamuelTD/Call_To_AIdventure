from utils.player import Player, load_player
from utils.monster import get_monster
import random as r
from time import sleep
from utils.python_utils import clear

def run_combat(enemy: str, player: Player):
    monster = get_monster(enemy)
    
    player.hp = 400
    
    if not monster:
        return f"{enemy} not found in database."
    
    while True:
        print(f"You attack {monster.name}.")
        damage = r.randint(10, 100)
        monster.HP -= damage
        print(f"{monster.name} suffers {damage} damage. (Remaining : {monster.HP})\n")
        
        sleep(1)
        
        if monster.HP <= 0:
            break
        
        print(f"{monster.name} attacks {player.name}.")
        damage = r.randint(1, 6) + monster.strength
        if damage < 0: damage = 0
        player.hp -= damage
        print(f"You suffer {damage} damage. (Remaining : {player.hp})\n")
        
        
        sleep(1)
        
        if player.hp <= 0:
            break
        
    signal = ""
    msg = ""
    if player.hp <= 0:
        msg = "You died!"
        signal = 2
    else:
        msg = f"You vanquished {monster.name}!"
        signal = 1
    
    return {"signal": signal, "message": msg}
        
        
if __name__ == "__main__":
    clear()
    print(run_combat("goblin warrior", load_player("data/world/other/player.json")))