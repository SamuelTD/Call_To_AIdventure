from unittest.mock import patch

from django.test import SimpleTestCase

from game.services.game_engine import GameEngine
from agents.game_master_graph import normalize_heal_amount, step_generate_story
from agents.tools import heal_tool
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


class HealingToolTests(SimpleTestCase):
    def test_heal_tool_returns_heal_intent(self):
        self.assertEqual(heal_tool(7), {"action": "heal", "amount": 7})

    def test_normalize_heal_amount_rejects_invalid_or_negative_values(self):
        self.assertEqual(normalize_heal_amount("6"), 6)
        self.assertEqual(normalize_heal_amount(-4), 0)
        self.assertEqual(normalize_heal_amount("not a number"), 0)

    @patch("agents.game_master_graph.story_chain")
    def test_generate_story_applies_healing_and_caps_at_max_hp(self, story_chain):
        story_chain.invoke.return_value = "Warmth returns to your limbs."
        player = make_player(hp=18)
        state = {
            "player": player,
            "history": ["Story: You find a quiet shrine."],
            "latest_user": "Drink from the silver font.",
            "last_cmd": "heal",
            "heal_amount": 8,
            "story_steps": 2,
        }

        result = step_generate_story(state)

        self.assertEqual(player.hp, 20)
        self.assertEqual(state["actual_heal_amount"], 2)
        self.assertEqual(state["heal_amount"], 0)
        self.assertEqual(result["last_cmd"], "continue")
        self.assertEqual(result["current_story"], "Warmth returns to your limbs.")

        prompt = story_chain.invoke.call_args.args[0]["full_prompt"]
        self.assertIn("requested healing amount was 8 HP", prompt)
        self.assertIn("actually recovered 2 HP", prompt)
        self.assertIn("20/20 HP", prompt)
