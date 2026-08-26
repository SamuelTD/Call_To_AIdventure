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
    parse_thinker_action,
    retrieve_known_location_context,
    step_generate_story,
    step_agent_think,
    step_evaluate_goals,
    step_evaluate_room_progression,
    step_generate_victory_wrapup,
    step_get_input,
)
from agents.llm_resilience import TemporaryLLMServiceError
from agents.tools import deal_damage_tool, heal_tool, tools
from retrieval.service import (
    clear_retrieval_cache,
    retrieve_location_context,
    retrieve_lore_context,
)
from retrieval.schemas import RetrievalScope
from utils.adventure import Adventure
from utils.enums import CharacterClass, PlayerAction
from utils.monster import Monster
from utils.player import Player
from observability.metrics import (
    GAMES_STARTED,
    LLM_ATTEMPTS,
    LLM_REQUESTS,
    LLM_RETRIES,
    STORY_TURN_READY_DURATION,
)


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

    @patch("game.services.game_engine.describe_current_room")
    def test_check_current_room_preserves_choices(self, describe_current_room):
        describe_current_room.return_value = "The sealed gate waits in the ash."
        state = make_game_state()
        state["current_choices"] = ["Inspect rings", "Light torch", "Listen"]

        result = self.engine.check_current_room(state)

        self.assertEqual(result["mode"], "story")
        self.assertEqual(result["story"], "The sealed gate waits in the ash.")
        self.assertEqual(result["choices"], ["Inspect rings", "Light torch", "Listen"])
        self.assertEqual(state["current_story"], "The sealed gate waits in the ash.")

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


class RetrievalSpeedTests(SimpleTestCase):
    def tearDown(self):
        clear_retrieval_cache()

    @patch("retrieval.service.embed")
    def test_known_location_context_does_not_embed(self, embed):
        context = retrieve_location_context("tomb_dragonkin_sealed_gate")

        embed.assert_not_called()
        self.assertTrue(context.chunks)
        self.assertEqual(
            {result.chunk.entity_id for result in context.chunks},
            {"tomb_dragonkin_sealed_gate"},
        )

    @patch("retrieval.service.query_lore_collection")
    @patch("retrieval.service.embed")
    def test_semantic_retrieval_caches_identical_queries(self, embed, query_lore_collection):
        clear_retrieval_cache()
        embed.return_value = [0.1, 0.2, 0.3]
        query_lore_collection.return_value = {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }
        scope = RetrievalScope(
            available_location_ids=["tomb_dragonkin_sealed_gate"],
            current_location_id="tomb_dragonkin_sealed_gate",
        )

        retrieve_lore_context(
            "Describe the sealed gate.",
            scope,
            entity_types=["location"],
            top_k=3,
        )
        retrieve_lore_context(
            "Describe the sealed gate.",
            scope,
            entity_types=["location"],
            top_k=3,
        )

        embed.assert_called_once_with("Describe the sealed gate.")
        query_lore_collection.assert_called_once()

    def test_graph_known_location_context_respects_adventure_scope(self):
        state = make_game_state()
        state["adventure"].locations.available = ["tomb_dragonkin_sealed_gate"]

        context = retrieve_known_location_context(
            state,
            "tomb_dragonkin_scale_hall",
        )

        self.assertEqual(context, "No relevant world lore was retrieved.")


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


@override_settings(DEBUG=True)
class DevAccountDashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="debug_player", password="old-password")

    def test_dashboard_lists_users_without_exposing_password_hash(self):
        response = self.client.get(reverse("dev_accounts"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "debug_player")
        self.assertNotContains(response, self.user.password)
        self.assertNotContains(response, "old-password")

    @override_settings(DEBUG=False)
    def test_dashboard_is_unavailable_outside_debug_mode(self):
        response = self.client.get(reverse("dev_accounts"))

        self.assertEqual(response.status_code, 404)

    def test_dashboard_is_unavailable_to_non_loopback_requests(self):
        response = self.client.get(reverse("dev_accounts"), REMOTE_ADDR="192.0.2.10")

        self.assertEqual(response.status_code, 404)

    def test_can_set_a_new_password(self):
        response = self.client.post(
            reverse("dev_accounts"),
            {"action": "set_password", "user_id": self.user.pk, "new_password": "new-password"},
        )

        self.assertRedirects(response, reverse("dev_accounts"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("new-password"))

    def test_can_delete_an_account(self):
        response = self.client.post(
            reverse("dev_accounts"),
            {"action": "delete", "user_id": self.user.pk},
        )

        self.assertRedirects(response, reverse("dev_accounts"))
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())


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
        metric = GAMES_STARTED.labels(adventure=adventure.id)
        before = metric._value.get()

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
        self.assertEqual(metric._value.get(), before + 1)

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
    def test_current_room_replaces_story_and_keeps_choices(self, get_engine):
        user = User.objects.create_user(
            username="room_checker",
            password="LongEnoughPassword42",
        )
        self.client.force_login(user)
        state = make_game_state()
        state["current_choices"] = ["Inspect rings", "Light torch", "Listen"]
        session = self.client.session
        session["game_state"] = make_serializable_state(state)
        session.save()

        updated_state = {**state, "current_story": "The basalt gate waits."}
        get_engine.return_value.check_current_room.return_value = {
            "state": updated_state,
            "mode": "story",
            "story": "The basalt gate waits.",
            "choices": state["current_choices"],
        }

        response = self.client.post(
            reverse("api_current_room"),
            {},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["story"], "The basalt gate waits.")
        self.assertEqual(response.json()["choices"], ["Inspect rings", "Light torch", "Listen"])
        self.assertEqual(self.client.session["game_state"]["current_story"], "The basalt gate waits.")
        self.assertEqual(
            self.client.session["game_state"]["current_choices"],
            ["Inspect rings", "Light torch", "Listen"],
        )

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
        attempts = LLM_ATTEMPTS.labels(operation="story generation")
        retries = LLM_RETRIES.labels(operation="story generation")
        successes = LLM_REQUESTS.labels(
            operation="story generation",
            status="success",
        )
        attempts_before = attempts._value.get()
        retries_before = retries._value.get()
        successes_before = successes._value.get()
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
        self.assertEqual(attempts._value.get(), attempts_before + 2)
        self.assertEqual(retries._value.get(), retries_before + 1)
        self.assertEqual(successes._value.get(), successes_before + 1)

    @override_settings(
        LLM_RETRY_MAX_ATTEMPTS=1,
        LLM_RETRY_INITIAL_DELAY_SECONDS=0,
        LLM_RETRY_BACKOFF_MULTIPLIER=1,
        LLM_RETRY_MAX_DELAY_SECONDS=0,
        LLM_RETRY_JITTER_SECONDS=0,
    )
    @patch("agents.game_master_graph.story_chain")
    def test_generate_story_failure_leaves_state_unadvanced(self, story_chain):
        unavailable = LLM_REQUESTS.labels(
            operation="story generation",
            status="unavailable",
        )
        unavailable_before = unavailable._value.get()
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
        self.assertEqual(unavailable._value.get(), unavailable_before + 1)


class MetricsEndpointTests(TestCase):
    def test_metrics_endpoint_exposes_application_metrics(self):
        response = self.client.get("/metrics")
        body = response.content.decode("utf-8")

        self.assertEqual(response.status_code, 200)
        self.assertIn("aidventure_games_started_total", body)
        self.assertIn("django_http_requests_total", body)

    def test_story_turn_metric_records_browser_duration_for_active_adventure(self):
        session = self.client.session
        session["game_state"] = {"adventure": {"id": "emerald_sword"}}
        session.save()
        metric = STORY_TURN_READY_DURATION.labels(adventure="emerald_sword")
        count_before = sum(bucket.get() for bucket in metric._buckets)
        sum_before = metric._sum.get()

        response = self.client.post(
            reverse("api_story_turn_metric"),
            {"duration_seconds": 12.5},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            sum(bucket.get() for bucket in metric._buckets),
            count_before + 1,
        )
        self.assertAlmostEqual(metric._sum.get(), sum_before + 12.5)

    def test_story_turn_metric_rejects_invalid_or_sessionless_observations(self):
        no_session_response = self.client.post(
            reverse("api_story_turn_metric"),
            {"duration_seconds": 2.5},
            content_type="application/json",
        )

        session = self.client.session
        session["game_state"] = {"adventure": {"id": "emerald_sword"}}
        session.save()
        invalid_response = self.client.post(
            reverse("api_story_turn_metric"),
            {"duration_seconds": 901},
            content_type="application/json",
        )

        self.assertEqual(no_session_response.status_code, 400)
        self.assertEqual(invalid_response.status_code, 400)


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

    def test_parse_thinker_action_accepts_responses_api_content_blocks(self):
        message = type("Message", (), {
            "content": [
                {"type": "reasoning", "summary": []},
                {
                    "type": "text",
                    "text": '{"name":"nothing","arguments":{}}',
                },
            ]
        })

        self.assertEqual(parse_thinker_action(message), {"action": "nothing"})

    def test_parse_thinker_action_accepts_native_tool_calls(self):
        message = type("Message", (), {
            "content": "",
            "tool_calls": [{"name": "heal", "args": {"amount": 4}}],
        })

        self.assertEqual(
            parse_thinker_action(message),
            {"action": "heal", "amount": 4},
        )

    @patch("agents.game_master_graph.build_thinker_agent")
    @patch("agents.game_master_graph.thinker_agent", None)
    def test_agent_think_initializes_runtime_when_resuming_after_restart(
        self,
        build_thinker_agent,
    ):
        message = type("Message", (), {"content": '{"action":"nothing"}'})
        build_thinker_agent.return_value.invoke.return_value = {"messages": [message]}
        adventure = type("Adventure", (), {"monsters": []})

        result = step_agent_think({
            "adventure": adventure,
            "current_story": "The road continues.",
            "latest_user": "I keep walking.",
        })

        build_thinker_agent.assert_called_once_with()
        self.assertEqual(result["last_cmd"], "continue")

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
    def make_room_state(self):
        adventure = Adventure(
            id="emerald_sword",
            name="The Emerald Sword",
            description="A test adventure.",
            goals=["Retrieve the Emerald Sword."],
            monsters=[],
            characters={"active": [], "referenceable": []},
            locations={
                "available": [
                    "tomb_dragonkin_sealed_gate",
                    "tomb_dragonkin_scale_hall",
                    "tomb_dragonkin_emerald_shrine",
                ],
                "start": "tomb_dragonkin_sealed_gate",
            },
        )
        return {
            "player": make_player(),
            "adventure": adventure,
            "history": ["Story: The sealed gate blocks the way."],
            "latest_user": "Align the rings.",
            "current_story": "The basalt gate opens with a roar of stone.",
            "current_location_id": "tomb_dragonkin_sealed_gate",
            "location_index": 0,
            "completed_location_ids": [],
            "should_end": False,
        }

    @patch("agents.game_master_graph.room_completion_chain")
    def test_room_progression_stays_when_objective_is_incomplete(self, room_completion_chain):
        room_completion_chain.invoke.return_value = type(
            "RoomResult",
            (),
            {"room_completed": False, "reason": "The gate remains closed."},
        )()
        state = self.make_room_state()
        state["current_story"] = "The rings turn, but the gate remains sealed."

        output = step_evaluate_room_progression(state)

        self.assertEqual(output, {})

    @patch("agents.game_master_graph.retrieve_known_location_context")
    @patch("agents.game_master_graph.story_chain")
    @patch("agents.game_master_graph.room_completion_chain")
    def test_room_progression_advances_linearly_when_objective_completes(
        self,
        room_completion_chain,
        story_chain,
        retrieve_known_location_context,
    ):
        room_completion_chain.invoke.return_value = type(
            "RoomResult",
            (),
            {"room_completed": True, "reason": "The gate opened."},
        )()
        story_chain.invoke.return_value = "You step into the Hall of Fallen Scales."
        retrieve_known_location_context.return_value = "Hall lore"
        state = self.make_room_state()

        output = step_evaluate_room_progression(state)

        self.assertEqual(output["current_location_id"], "tomb_dragonkin_scale_hall")
        self.assertEqual(output["location_index"], 1)
        self.assertEqual(output["completed_location_ids"], ["tomb_dragonkin_sealed_gate"])
        self.assertEqual(output["current_story"], "You step into the Hall of Fallen Scales.")
        self.assertIn("Story: You step into the Hall of Fallen Scales.", output["history"])

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
