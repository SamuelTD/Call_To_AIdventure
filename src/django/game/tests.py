from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from game.services.game_engine import GameEngine
from agents.game_master_graph import (
    normalize_damage_amount,
    normalize_heal_amount,
    step_generate_story,
    step_agent_think,
    step_get_input,
)
from agents.tools import deal_damage_tool, heal_tool, tools
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


class AccountFlowTests(TestCase):
    def test_login_page_renders(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Log In")
        self.assertContains(response, "Create Account")

    def test_signup_creates_and_logs_in_user(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "save_runner",
                "password1": "LongEnoughPassword42",
                "password2": "LongEnoughPassword42",
            },
            follow=True,
        )

        self.assertRedirects(response, reverse("landing"))
        self.assertTrue(User.objects.filter(username="save_runner").exists())
        self.assertContains(response, "save_runner")

    def test_logged_in_user_can_log_out_from_landing(self):
        user = User.objects.create_user(
            username="loaded_player",
            password="LongEnoughPassword42",
        )
        self.client.force_login(user)

        response = self.client.post(reverse("logout"), follow=True)

        self.assertRedirects(response, reverse("landing"))
        self.assertNotContains(response, "loaded_player")


class HealingToolTests(SimpleTestCase):
    def test_tool_schemas_use_named_parameters_for_provider_tool_calls(self):
        tool_args = {tool.name: tool.args for tool in tools}

        self.assertEqual(
            tool_args["combat"],
            {
                "enemy": {
                    "description": "Exact monster name to fight.",
                    "title": "Enemy",
                    "type": "string",
                }
            },
        )
        self.assertEqual(tool_args["nothing"], {})
        self.assertEqual(
            tool_args["heal"],
            {
                "amount": {
                    "anyOf": [{"type": "integer"}, {"type": "string"}],
                    "description": "Health amount as an integer or numeric string.",
                    "title": "Amount",
                }
            },
        )
        self.assertEqual(tool_args["deal_damage"], tool_args["heal"])

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
        self.assertIn("recovered 2 HP", prompt)


class DamageToolTests(SimpleTestCase):
    def test_deal_damage_tool_returns_damage_intent(self):
        self.assertEqual(deal_damage_tool(5), {"action": "damage", "amount": 5})

    def test_normalize_damage_amount_rejects_invalid_or_negative_values(self):
        self.assertEqual(normalize_damage_amount("9"), 9)
        self.assertEqual(normalize_damage_amount(-3), 0)
        self.assertEqual(normalize_damage_amount("not a number"), 0)

    @patch("agents.game_master_graph.thinker_agent", create=True)
    def test_agent_think_normalizes_deal_damage_tool_name(self, thinker_agent):
        message = type("Message", (), {"content": '<function=deal_damage{"amount":5}</function>'})
        adventure = type("Adventure", (), {"monsters": []})
        thinker_agent.invoke.return_value = {"messages": [message]}

        result = step_agent_think({
            "adventure": adventure,
            "current_story": "A blade springs from the wall.",
            "latest_user": "I step on the pressure plate.",
        })

        self.assertEqual(result["last_cmd"], "damage")
        self.assertEqual(result["damage_amount"], 5)
        self.assertEqual(result["heal_amount"], 0)

    @patch("agents.game_master_graph.story_chain")
    def test_generate_story_applies_damage_and_marks_death(self, story_chain):
        story_chain.invoke.return_value = "The stones rush up, and darkness follows."
        player = make_player(hp=4)
        state = {
            "player": player,
            "history": ["Story: A broken bridge spans the chasm."],
            "latest_user": "Leap across the gap.",
            "last_cmd": "damage",
            "damage_amount": 9,
            "story_steps": 2,
            "should_end": False,
        }

        result = step_generate_story(state)

        self.assertEqual(player.hp, 0)
        self.assertEqual(state["actual_damage_amount"], 4)
        self.assertEqual(state["damage_amount"], 0)
        self.assertTrue(state["should_end"])
        self.assertTrue(result["should_end"])
        self.assertEqual(result["last_cmd"], "continue")
        self.assertEqual(result["current_story"], "The stones rush up, and darkness follows.")

        prompt = story_chain.invoke.call_args.args[0]["full_prompt"]
        self.assertIn("lost 4 HP", prompt)
        self.assertIn("0/20 HP", prompt)
        self.assertIn("clear death or collapse scene", prompt)

    def test_get_input_limits_choices_when_game_should_end(self):
        result = step_get_input({"should_end": True})

        self.assertEqual(result["current_choices"], ["Continue."])

    def test_engine_step_transitions_pending_death_to_gameover(self):
        engine = GameEngine.__new__(GameEngine)
        state = {
            "player": make_player(hp=0),
            "should_end": True,
        }

        result = engine.step(state, "Continue.")

        self.assertEqual(result["mode"], "gameover")
        self.assertIs(result["state"], state)

    @patch("agents.game_master_graph.story_chain")
    def test_engine_step_limits_choices_after_fatal_narrative_damage(self, story_chain):
        story_chain.invoke.return_value = "The trap closes, and your strength leaves you."
        engine = GameEngine.__new__(GameEngine)
        def invoke_post(input):
            return {**input, **step_generate_story(input)}

        def invoke_pre(input):
            return {**input, **step_get_input(input)}

        engine.pre_graph = type(
            "PreGraph",
            (),
            {"invoke": staticmethod(invoke_pre)},
        )()
        engine.post_graph = type(
            "PostGraph",
            (),
            {"invoke": staticmethod(invoke_post)},
        )()
        state = {
            "player": make_player(hp=1),
            "history": ["Story: A narrow hall waits ahead."],
            "current_choices": ["Walk forward"],
            "latest_user": "Walk forward",
            "last_cmd": "damage",
            "damage_amount": 1,
            "story_steps": 3,
            "should_end": False,
        }

        result = engine.step(state, "Walk forward")

        self.assertEqual(result["mode"], "story")
        self.assertEqual(result["state"]["player"].hp, 0)
        self.assertTrue(result["state"]["should_end"])
        self.assertEqual(result["choices"], ["Continue."])
