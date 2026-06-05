from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from django.urls import reverse

from game.models import CharacterTemplate, SaveGame
from game.services.game_engine import GameEngine
from game.services.tools import ensure_goal_state, make_serializable_state
from agents.game_master_graph import (
    normalize_damage_amount,
    normalize_heal_amount,
    step_generate_story,
    step_agent_think,
    step_evaluate_goals,
    step_generate_victory_wrapup,
    step_get_input,
)
from agents.llm_resilience import TemporaryLLMServiceError
from agents.tools import deal_damage_tool, heal_tool, tools
from utils.adventure import Adventure
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


def make_adventure():
    return Adventure(
        id="emerald_sword",
        name="The Emerald Sword",
        description="A test adventure.",
        goals=["Retrieve the Emerald Sword."],
        monsters=[],
        characters={"active": [], "referenceable": []},
        locations={"available": [], "start": None},
    )


def make_character_payload():
    return {
        "name": "Stan",
        "race": "Human",
        "class": CharacterClass.FIGHTER.value,
        "gender": "Male",
    }


def make_game_state():
    adventure = make_adventure()
    return {
        "player": make_player(),
        "adventure": adventure,
        "history": ["An old road waits."],
        "story_steps": 1,
        "should_end": False,
        "ongoing_goals": list(adventure.goals),
        "finished_goals": [],
        "adventure_completed": False,
        "end_reason": None,
        "current_story": "An old road waits.",
        "current_choices": ["Walk onward."],
        "last_cmd": "continue",
    }


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


class CharacterTemplateTests(TestCase):
    def test_guest_cannot_save_character_template(self):
        response = self.client.post(
            reverse("api_character_template_save"),
            {"character": make_character_payload()},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)
        self.assertFalse(CharacterTemplate.objects.exclude(user_id=-1).exists())

    def test_logged_in_user_can_save_character_template(self):
        user = User.objects.create_user(
            username="template_saver",
            password="LongEnoughPassword42",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("api_character_template_save"),
            {"character": make_character_payload()},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["created"])
        template = CharacterTemplate.objects.get(user=user)
        self.assertEqual(template.name, "Stan")
        self.assertEqual(template.race, "Human")
        self.assertEqual(template.character_class, CharacterClass.FIGHTER.value)
        self.assertEqual(template.gender, "Male")

    def test_saving_same_template_name_updates_existing_template(self):
        user = User.objects.create_user(
            username="template_updater",
            password="LongEnoughPassword42",
        )
        self.client.force_login(user)

        first_response = self.client.post(
            reverse("api_character_template_save"),
            {"character": make_character_payload()},
            content_type="application/json",
        )
        second_payload = {
            **make_character_payload(),
            "race": "Elf",
            "class": CharacterClass.WIZARD.value,
            "gender": "Female",
        }
        second_response = self.client.post(
            reverse("api_character_template_save"),
            {"character": second_payload},
            content_type="application/json",
        )

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.assertFalse(second_response.json()["created"])
        self.assertEqual(CharacterTemplate.objects.filter(user=user).count(), 1)
        template = CharacterTemplate.objects.get(user=user, name="Stan")
        self.assertEqual(template.race, "Elf")
        self.assertEqual(template.character_class, CharacterClass.WIZARD.value)
        self.assertEqual(template.gender, "Female")

    def test_saving_identical_template_is_noop(self):
        user = User.objects.create_user(
            username="template_duplicate",
            password="LongEnoughPassword42",
        )
        self.client.force_login(user)

        first_response = self.client.post(
            reverse("api_character_template_save"),
            {"character": make_character_payload()},
            content_type="application/json",
        )
        template = CharacterTemplate.objects.get(user=user)
        updated_at = template.updated_at
        second_response = self.client.post(
            reverse("api_character_template_save"),
            {"character": make_character_payload()},
            content_type="application/json",
        )

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.assertFalse(second_response.json()["created"])
        self.assertTrue(second_response.json()["skipped"])
        self.assertEqual(CharacterTemplate.objects.filter(user=user).count(), 1)
        template.refresh_from_db()
        self.assertEqual(template.updated_at, updated_at)

    def test_template_save_rejects_invalid_character(self):
        user = User.objects.create_user(
            username="template_validator",
            password="LongEnoughPassword42",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("api_character_template_save"),
            {
                "character": {
                    **make_character_payload(),
                    "name": "",
                }
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(CharacterTemplate.objects.filter(user=user).exists())

    def test_template_list_includes_generic_templates_for_guests(self):
        response = self.client.get(reverse("api_character_templates"))

        self.assertEqual(response.status_code, 200)
        templates = response.json()["templates"]
        generic_templates = [template for template in templates if template["is_generic"]]
        self.assertEqual(len(generic_templates), 3)
        self.assertEqual(
            {
                (template["name"], template["race"], template["class"], template["gender"])
                for template in generic_templates
            },
            {
                ("Borin Stoneguard", "Dwarf", CharacterClass.FIGHTER.value, "Male"),
                ("Mira Quickstep", "Human", CharacterClass.ROGUE.value, "Female"),
                ("Elara Moonveil", "Elf", CharacterClass.WIZARD.value, "Female"),
            },
        )

    def test_template_list_includes_user_templates_for_logged_in_user(self):
        user = User.objects.create_user(
            username="template_lister",
            password="LongEnoughPassword42",
        )
        other_user = User.objects.create_user(
            username="other_template_lister",
            password="LongEnoughPassword42",
        )
        CharacterTemplate.objects.create(
            user=user,
            name="My Fighter",
            race="Human",
            character_class=CharacterClass.FIGHTER.value,
            gender="Male",
        )
        CharacterTemplate.objects.create(
            user=other_user,
            name="Other Rogue",
            race="Human",
            character_class=CharacterClass.ROGUE.value,
            gender="Female",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("api_character_templates"))

        self.assertEqual(response.status_code, 200)
        templates = response.json()["templates"]
        self.assertIn("My Fighter", [template["name"] for template in templates])
        self.assertNotIn("Other Rogue", [template["name"] for template in templates])
        self.assertEqual(len([template for template in templates if template["is_generic"]]), 3)

    def test_logged_in_user_can_delete_own_template(self):
        user = User.objects.create_user(
            username="template_deleter",
            password="LongEnoughPassword42",
        )
        template = CharacterTemplate.objects.create(
            user=user,
            name="Delete Me",
            race="Human",
            character_class=CharacterClass.ROGUE.value,
            gender="Female",
        )
        self.client.force_login(user)

        response = self.client.post(reverse("api_character_template_delete", args=[template.id]))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(CharacterTemplate.objects.filter(id=template.id).exists())

    def test_guest_cannot_delete_template(self):
        generic_template = CharacterTemplate.objects.filter(user_id=-1).first()

        response = self.client.post(reverse("api_character_template_delete", args=[generic_template.id]))

        self.assertEqual(response.status_code, 401)
        self.assertTrue(CharacterTemplate.objects.filter(id=generic_template.id).exists())

    def test_user_cannot_delete_generic_template(self):
        user = User.objects.create_user(
            username="generic_delete_blocked",
            password="LongEnoughPassword42",
        )
        generic_template = CharacterTemplate.objects.filter(user_id=-1).first()
        self.client.force_login(user)

        response = self.client.post(reverse("api_character_template_delete", args=[generic_template.id]))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(CharacterTemplate.objects.filter(id=generic_template.id).exists())

    def test_user_cannot_delete_another_users_template(self):
        owner = User.objects.create_user(
            username="template_owner",
            password="LongEnoughPassword42",
        )
        other = User.objects.create_user(
            username="template_intruder",
            password="LongEnoughPassword42",
        )
        template = CharacterTemplate.objects.create(
            user=owner,
            name="Private Template",
            race="Elf",
            character_class=CharacterClass.WIZARD.value,
            gender="Female",
        )
        self.client.force_login(other)

        response = self.client.post(reverse("api_character_template_delete", args=[template.id]))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(CharacterTemplate.objects.filter(id=template.id).exists())


class SaveGamePersistenceTests(TestCase):
    def test_goal_state_backfill_uses_unfinished_adventure_goals(self):
        state = {
            "adventure": make_adventure(),
            "finished_goals": ["Retrieve the Emerald Sword."],
        }

        ensured_state = ensure_goal_state(state)

        self.assertEqual(ensured_state["finished_goals"], ["Retrieve the Emerald Sword."])
        self.assertEqual(ensured_state["ongoing_goals"], [])
        self.assertFalse(ensured_state["adventure_completed"])
        self.assertIsNone(ensured_state["end_reason"])

    def test_goal_state_backfill_preserves_existing_ongoing_goals(self):
        state = {
            "adventure": make_adventure(),
            "ongoing_goals": ["Find the hidden vault."],
            "finished_goals": [],
        }

        ensured_state = ensure_goal_state(state)

        self.assertEqual(ensured_state["ongoing_goals"], ["Find the hidden vault."])

    def test_goal_state_backfill_removes_finished_goals_from_ongoing_goals(self):
        state = {
            "adventure": make_adventure(),
            "ongoing_goals": ["Retrieve the Emerald Sword.", "Find the hidden vault."],
            "finished_goals": ["Retrieve the Emerald Sword."],
        }

        ensured_state = ensure_goal_state(state)

        self.assertEqual(ensured_state["ongoing_goals"], ["Find the hidden vault."])

    @patch("game.views.get_engine")
    @patch("game.views.initialize_game")
    def test_anonymous_start_keeps_state_in_session_without_db_save(
        self,
        initialize_game,
        get_engine,
    ):
        state = make_game_state()
        adventure = state["adventure"]
        initialize_game.return_value = (state, "An old road waits.", adventure)
        get_engine.return_value.initialize.return_value = state

        response = self.client.post(
            reverse("api_start"),
            {
                "adventure_id": adventure.id,
                "character": make_character_payload(),
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(SaveGame.objects.count(), 0)
        self.assertIn("game_state", self.client.session)
        self.assertNotIn("save_game_id", self.client.session)

    @patch("game.views.get_engine")
    @patch("game.views.initialize_game")
    def test_logged_in_user_can_start_same_adventure_multiple_times(
        self,
        initialize_game,
        get_engine,
    ):
        user = User.objects.create_user(
            username="multi_runner",
            password="LongEnoughPassword42",
        )
        self.client.force_login(user)
        adventure = make_adventure()
        get_engine.return_value.initialize.side_effect = lambda state: state

        for index in range(2):
            state = make_game_state()
            state["current_story"] = f"Run {index + 1} begins."
            initialize_game.return_value = (state, state["current_story"], adventure)

            response = self.client.post(
                reverse("api_start"),
                {
                    "adventure_id": adventure.id,
                    "character": make_character_payload(),
                },
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 200)

        saves = SaveGame.objects.filter(user=user, adventure_id=adventure.id)
        self.assertEqual(saves.count(), 2)
        self.assertIn(self.client.session["save_game_id"], list(saves.values_list("id", flat=True)))

    def test_load_save_requires_owner_and_restores_session(self):
        owner = User.objects.create_user(
            username="owner",
            password="LongEnoughPassword42",
        )
        other = User.objects.create_user(
            username="other",
            password="LongEnoughPassword42",
        )
        state = make_game_state()
        save = SaveGame.objects.create(
            user=owner,
            adventure_id=state["adventure"].id,
            adventure_name=state["adventure"].name,
            state={
                "player": state["player"].to_dict(),
                "adventure": state["adventure"].to_dict(),
                "current_story": state["current_story"],
                "current_choices": state["current_choices"],
            },
        )

        self.client.force_login(other)
        forbidden_response = self.client.post(reverse("api_save_load", args=[save.id]))
        self.assertEqual(forbidden_response.status_code, 404)

        self.client.force_login(owner)
        response = self.client.post(reverse("api_save_load", args=[save.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session["save_game_id"], save.id)
        self.assertEqual(self.client.session["game_state"]["current_story"], state["current_story"])

    def test_save_list_splits_active_saves_and_history(self):
        user = User.objects.create_user(
            username="historian",
            password="LongEnoughPassword42",
        )
        self.client.force_login(user)
        state = make_game_state()
        active_save = SaveGame.objects.create(
            user=user,
            adventure_id=state["adventure"].id,
            adventure_name="Active Run",
            state=make_serializable_state(state),
        )
        finished_save = SaveGame.objects.create(
            user=user,
            adventure_id=state["adventure"].id,
            adventure_name="Finished Run",
            state={**make_serializable_state(state), "end_reason": "victory"},
            is_finished=True,
            finished_at=timezone.now(),
        )

        response = self.client.get(reverse("api_saves"))
        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual([save["id"] for save in payload["saves"]], [active_save.id])
        self.assertEqual([save["id"] for save in payload["history"]], [finished_save.id])
        self.assertTrue(payload["history"][0]["is_finished"])
        self.assertEqual(payload["history"][0]["ending_reason"], "Ending: Victory")

    def test_finished_save_cannot_be_loaded(self):
        user = User.objects.create_user(
            username="done_runner",
            password="LongEnoughPassword42",
        )
        self.client.force_login(user)
        state = make_game_state()
        save = SaveGame.objects.create(
            user=user,
            adventure_id=state["adventure"].id,
            adventure_name=state["adventure"].name,
            state=make_serializable_state(state),
            is_finished=True,
            finished_at=timezone.now(),
        )

        response = self.client.post(reverse("api_save_load", args=[save.id]))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Finished games are in history and cannot be loaded")

    @patch("game.views.get_engine")
    @override_settings(
        LLM_SERVICE_UNAVAILABLE_MESSAGE="The storyteller is unavailable. Try again soon.",
        LLM_SERVICE_UNAVAILABLE_STATUS_CODE=503,
    )
    def test_step_service_unavailable_does_not_persist_failed_state(self, get_engine):
        user = User.objects.create_user(
            username="paused_runner",
            password="LongEnoughPassword42",
        )
        self.client.force_login(user)
        state = make_game_state()
        save = SaveGame.objects.create(
            user=user,
            adventure_id=state["adventure"].id,
            adventure_name=state["adventure"].name,
            state=make_serializable_state(state),
        )
        session = self.client.session
        session["game_state"] = make_serializable_state(state)
        session["save_game_id"] = save.id
        session.save()
        failed_state = {**state, "current_story": "This should not persist."}
        get_engine.return_value.step.return_value = {
            "state": failed_state,
            "mode": "service_unavailable",
        }

        response = self.client.post(
            reverse("api_step"),
            {"choice": "Walk onward."},
            content_type="application/json",
        )

        save.refresh_from_db()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["mode"], "service_unavailable")
        self.assertEqual(response.json()["error"], "The storyteller is unavailable. Try again soon.")
        self.assertEqual(save.state["current_story"], "An old road waits.")

    @patch("game.views.get_engine")
    def test_gameover_marks_current_save_as_finished(self, get_engine):
        user = User.objects.create_user(
            username="fallen_runner",
            password="LongEnoughPassword42",
        )
        self.client.force_login(user)
        state = make_game_state()
        save = SaveGame.objects.create(
            user=user,
            adventure_id=state["adventure"].id,
            adventure_name=state["adventure"].name,
            state=make_serializable_state(state),
        )
        session = self.client.session
        session["game_state"] = make_serializable_state(state)
        session["save_game_id"] = save.id
        session.save()
        state["player"].hp = 0
        state["should_end"] = True
        get_engine.return_value.step.return_value = {
            "state": state,
            "mode": "gameover",
        }

        response = self.client.post(
            reverse("api_step"),
            {"choice": "Continue."},
            content_type="application/json",
        )

        save.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(save.is_finished)
        self.assertIsNotNone(save.finished_at)

    @patch("game.views.get_engine")
    def test_adventure_victory_marks_current_save_as_finished(self, get_engine):
        user = User.objects.create_user(
            username="victorious_runner",
            password="LongEnoughPassword42",
        )
        self.client.force_login(user)
        state = make_game_state()
        state["should_end"] = True
        state["end_reason"] = "victory"
        save = SaveGame.objects.create(
            user=user,
            adventure_id=state["adventure"].id,
            adventure_name=state["adventure"].name,
            state=make_serializable_state(state),
        )
        session = self.client.session
        session["game_state"] = make_serializable_state(state)
        session["save_game_id"] = save.id
        session.save()
        get_engine.return_value.step.return_value = {
            "state": state,
            "mode": "adventure_victory",
        }

        response = self.client.post(
            reverse("api_step"),
            {"choice": "Continue."},
            content_type="application/json",
        )

        save.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["mode"], "adventure_victory")
        self.assertTrue(save.is_finished)
        self.assertIsNotNone(save.finished_at)

    @patch("game.views.load_adv_outro")
    def test_victory_page_displays_adventure_outro(self, load_adv_outro):
        load_adv_outro.return_value = "The realm remembers your courage."
        state = make_game_state()
        state["should_end"] = True
        state["end_reason"] = "victory"
        session = self.client.session
        session["game_state"] = make_serializable_state(state)
        session.save()

        response = self.client.get(reverse("victory"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The Emerald Sword")
        self.assertContains(response, "The realm remembers your courage.")
        load_adv_outro.assert_called_once_with("emerald_sword")

    @patch("game.views.get_engine")
    def test_combat_defeat_marks_current_save_as_finished(self, get_engine):
        user = User.objects.create_user(
            username="defeated_runner",
            password="LongEnoughPassword42",
        )
        self.client.force_login(user)
        state = make_game_state()
        state["current_monster_name"] = "Kobold Warrior"
        state["current_monster"] = make_monster()
        save = SaveGame.objects.create(
            user=user,
            adventure_id=state["adventure"].id,
            adventure_name=state["adventure"].name,
            state=make_serializable_state(state),
        )
        session = self.client.session
        session["game_state"] = make_serializable_state(state)
        session["save_game_id"] = save.id
        session.save()
        state["player"].hp = 0
        get_engine.return_value.combat_action.return_value = {
            "state": state,
            "mode": "defeat",
            "combat_log": "The final blow lands.",
        }

        response = self.client.post(
            reverse("api_combat_action"),
            {"action": PlayerAction.ATTACK.value},
            content_type="application/json",
        )

        save.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(save.is_finished)
        self.assertIsNotNone(save.finished_at)


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

    @override_settings(
        LLM_RETRY_MAX_ATTEMPTS=2,
        LLM_RETRY_INITIAL_DELAY_SECONDS=0,
        LLM_RETRY_BACKOFF_MULTIPLIER=1,
        LLM_RETRY_MAX_DELAY_SECONDS=0,
        LLM_RETRY_JITTER_SECONDS=0,
    )
    @patch("agents.game_master_graph.story_chain")
    def test_generate_story_retries_transient_story_failures(self, story_chain):
        story_chain.invoke.side_effect = [
            TimeoutError("temporary timeout"),
            "Warmth returns after a brief silence.",
        ]
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

        self.assertEqual(story_chain.invoke.call_count, 2)
        self.assertEqual(result["current_story"], "Warmth returns after a brief silence.")
        self.assertEqual(player.hp, 20)

    @override_settings(
        LLM_RETRY_MAX_ATTEMPTS=1,
        LLM_RETRY_INITIAL_DELAY_SECONDS=0,
        LLM_RETRY_BACKOFF_MULTIPLIER=1,
        LLM_RETRY_MAX_DELAY_SECONDS=0,
        LLM_RETRY_JITTER_SECONDS=0,
    )
    @patch("agents.game_master_graph.story_chain")
    def test_generate_story_failure_leaves_state_unadvanced(self, story_chain):
        story_chain.invoke.side_effect = TimeoutError("temporary timeout")
        player = make_player(hp=18)
        state = {
            "player": player,
            "history": ["Story: You find a quiet shrine."],
            "current_story": "You find a quiet shrine.",
            "latest_user": "Drink from the silver font.",
            "last_cmd": "heal",
            "heal_amount": 8,
            "story_steps": 2,
        }

        with self.assertRaises(TemporaryLLMServiceError):
            step_generate_story(state)

        self.assertEqual(player.hp, 18)
        self.assertEqual(state["history"], ["Story: You find a quiet shrine."])
        self.assertEqual(state["story_steps"], 2)
        self.assertEqual(state["last_cmd"], "heal")
        self.assertEqual(state["heal_amount"], 8)


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

    def test_engine_step_transitions_pending_victory_to_adventure_victory(self):
        engine = GameEngine.__new__(GameEngine)
        state = {
            "player": make_player(),
            "should_end": True,
            "end_reason": "victory",
        }

        result = engine.step(state, "Continue.")

        self.assertEqual(result["mode"], "adventure_victory")
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


class GoalEvaluationTests(SimpleTestCase):
    @patch("agents.game_master_graph.goal_evaluator_chain")
    def test_evaluate_goals_moves_only_exact_ongoing_goal_matches(self, goal_evaluator_chain):
        result = type(
            "GoalResult",
            (),
            {
                "completed_goals": [
                    "Retrieve the Emerald Sword.",
                    "Invented extra goal.",
                ]
            },
        )()
        goal_evaluator_chain.invoke.return_value = result
        state = make_game_state()

        output = step_evaluate_goals(state)

        self.assertEqual(output["finished_goals"], ["Retrieve the Emerald Sword."])
        self.assertEqual(output["ongoing_goals"], [])
        self.assertTrue(output["adventure_completed"])

    @patch("agents.game_master_graph.goal_evaluator_chain")
    def test_evaluate_goals_ignores_already_finished_goal_context(self, goal_evaluator_chain):
        state = make_game_state()
        state["finished_goals"] = ["Retrieve the Emerald Sword."]
        state["ongoing_goals"] = ["Find the hidden vault."]
        goal_evaluator_chain.invoke.return_value = type(
            "GoalResult",
            (),
            {"completed_goals": ["Retrieve the Emerald Sword."]},
        )()

        output = step_evaluate_goals(state)

        self.assertEqual(output["finished_goals"], ["Retrieve the Emerald Sword."])
        self.assertEqual(output["ongoing_goals"], ["Find the hidden vault."])
        self.assertFalse(output["adventure_completed"])

    @patch("agents.game_master_graph.story_chain")
    def test_victory_wrapup_marks_story_as_victory_ending(self, story_chain):
        story_chain.invoke.return_value = "The sword rises, and the realm breathes again."
        state = make_game_state()
        state["ongoing_goals"] = []
        state["finished_goals"] = ["Retrieve the Emerald Sword."]
        state["latest_user"] = "Take the sword."

        output = step_generate_victory_wrapup(state)

        self.assertTrue(output["should_end"])
        self.assertEqual(output["end_reason"], "victory")
        self.assertTrue(output["adventure_completed"])
        self.assertEqual(output["current_choices"], ["Continue."])
        self.assertEqual(output["current_story"], "The sword rises, and the realm breathes again.")
