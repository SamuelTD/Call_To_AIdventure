from unittest.mock import patch

from django.test import SimpleTestCase

from game.services.game_engine import GameEngine
from utils.enums import CharacterClass, PlayerAction
from utils.monster import Monster
from utils.player import Player


def make_player(hp=20):
    return Player(
        name="Stan",
        race="Human",
        p_class=CharacterClass.FIGHTER,
        hp=hp,
        max_hp=20,
    )


def make_monster(hp=8):
    return Monster(
        name="Kobold Warrior",
        armor=10,
        HP=hp,
        max_HP=8,
        challenge_rating=1,
        strength=1,
        dexterity=1,
        constitution=1,
        intelligence=1,
        wisdom=1,
        charisma=1,
        description="A test foe.",
    )


class CombatEngineTests(SimpleTestCase):
    def setUp(self):
        self.engine = GameEngine.__new__(GameEngine)

    @patch("game.services.game_engine.setup_combat")
    @patch("game.services.game_engine.restore_combat")
    def test_start_combat_is_idempotent_when_monster_is_in_session_state(
        self,
        restore_combat,
        setup_combat,
    ):
        state = {
            "player": make_player(),
            "current_monster_name": "Kobold Warrior",
            "current_monster": make_monster(),
        }

        result = self.engine.start_combat(state)

        setup_combat.assert_not_called()
        restore_combat.assert_called_once_with(state["player"], state["current_monster"])
        self.assertEqual(result["mode"], "combat")
        self.assertEqual(result["combat_log"], "Combat already underway.")
        self.assertEqual(result["monster_hp"], 8)

    @patch("game.services.game_engine.get_current_combat_state")
    @patch("game.services.game_engine.monster_attack")
    @patch("game.services.game_engine.player_action")
    @patch("game.services.game_engine.restore_combat")
    def test_combat_action_restores_session_state_before_resolving_action(
        self,
        restore_combat,
        player_action,
        monster_attack,
        get_current_combat_state,
    ):
        player = make_player()
        monster = make_monster()
        state = {
            "player": player,
            "current_monster_name": "Kobold Warrior",
            "current_monster": monster,
        }
        player_action.return_value = (False, ["You attack."])
        monster_attack.return_value = (False, ["The monster attacks."])
        get_current_combat_state.return_value = {
            "player": player,
            "monster": monster,
        }

        result = self.engine.combat_action(state, PlayerAction.ATTACK.value)

        restore_combat.assert_called_once_with(player, monster)
        player_action.assert_called_once_with(PlayerAction.ATTACK)
        monster_attack.assert_called_once()
        self.assertEqual(result["mode"], "combat")

    def test_combat_action_rejects_missing_or_invalid_combat(self):
        missing_combat = self.engine.combat_action(
            {"player": make_player(), "current_monster": None},
            PlayerAction.ATTACK.value,
        )
        invalid_action = self.engine.combat_action(
            {
                "player": make_player(),
                "current_monster_name": "Kobold Warrior",
                "current_monster": make_monster(),
            },
            "dance",
        )

        self.assertEqual(missing_combat["mode"], "error")
        self.assertEqual(missing_combat["error"], "No active combat")
        self.assertEqual(invalid_action["mode"], "error")
        self.assertEqual(invalid_action["error"], "Invalid combat action")
