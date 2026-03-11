import random
from pathlib import Path

import gradio as gr
from PIL import Image
from langgraph.graph import StateGraph

from utils.python_utils import clear
from utils.player import load_player, Player
from utils.adventure import load_all_adventures
from utils.enums import PlayerAction
from combat.core import setup_combat, player_action, monster_attack

from agents.game_master_graph import (
    GameState,
    build_pre_input_graph,
    build_post_input_graph,
    initialize_graph_runtime,
    load_adv_intro,
)

seed = random.randrange(2**32)

adventures = load_all_adventures()
pre_graph = build_pre_input_graph(StateGraph(GameState))
post_graph = build_post_input_graph(StateGraph(GameState))


def init(index):
    player = load_player()
    intro = load_adv_intro(adventures[index].id)

    state: GameState = {
        "player": player,
        "adventure": adventures[index],
        "history": [intro],
        "story_steps": 0,
        "should_end": False,
        "combat_result": {"signal": 0, "message": ""},
        "current_story": intro,
        "last_cmd": "continue",
        "after_combat": False,
        "last_choices": [],
        "gold_loot": 0,
        "item_loot": [],
        "current_monster": None,
        "current_monster_name": None,
    }

    initialize_graph_runtime(state)

    ctx = pre_graph.invoke(input=state)
    state["current_choices"] = ctx["current_choices"]
    return state


def step(choice, state):
    state = post_graph.invoke(input={**state, "latest_user": choice})

    if state["last_cmd"] == "combat":
        return (
            gr.update(visible=True),
            gr.update(visible=False),
            state["combat_fluff"],
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(visible=False),
            state,
        )

    state["last_choices"] = state["current_choices"]
    state = pre_graph.invoke(input=state)

    story = state["current_story"]
    choices = state["current_choices"]

    return (
        gr.update(visible=True),
        gr.update(visible=False),
        story,
        gr.update(choices=choices, value=choices[0], visible=True),
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(visible=False),
        state,
    )


def init_load(file_obj):
    return None


def start_callback(index, adventures, mode):
    if mode == "new":
        st = init(index)
    else:
        st = None

    story = st["current_story"]
    choices = st["current_choices"]

    return (
        story,
        gr.update(choices=choices, value=choices[0]),
        st,
        gr.update(visible=False),
        gr.update(visible=True),
        gr.update(value=f"### Call to AIdventure : {st['adventure'].name}")
    )


def show_intro(index, adventures):
    if index is None or index < 0:
        return "", gr.update(visible=False)

    return gr.update(value=adventures[index].description), gr.update(visible=True)


def start_combat(state):
    combat_log, state["current_monster"] = setup_combat(
        state["current_monster_name"],
        state["player"]
    )

    project_root = Path(__file__).resolve().parents[2]
    image_path = project_root / "data" / "pictures" / f"{state['current_monster_name'].replace(' ', '_')}.png"
    image = Image.open(image_path)

    choices = [a.value for a in state["player"].actions]

    return (
        gr.update(visible=False),
        gr.update(visible=True),
        "\n".join(combat_log),
        gr.update(choices=choices, value=choices[0], interactive=True, visible=True),
        gr.update(visible=True),
        gr.update(value=f"### {state['current_monster_name']}"),
        image,
        state,
    )


def start_player_action(state, combat_action):
    player_has_won, combat_log = player_action(PlayerAction(combat_action))
    player_has_died = False

    if not player_has_won:
        player_has_died, combat_log = monster_attack()

    if not player_has_died and not player_has_won:
        choices = [a.value for a in state["player"].actions]
        return (
            "\n".join(combat_log),
            gr.update(choices=choices, value=choices[0], interactive=True),
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=False),
            state,
        )

    if player_has_won:
        state["gold_loot"] = random.randint(*state["current_monster"].gold_loot)
        state["item_loot"] = random.choice(state["current_monster"].items_loot)
        state["player"].inventory.append(state["item_loot"])
        state["after_combat"] = True

        return (
            "\n".join(combat_log),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(visible=False),
            state,
        )

    return (
        "\n".join(combat_log),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=True),
        state,
    )


def render_health_bar(hp_percent: int, length: int = 20, player: bool = True):
    filled_blocks = int(hp_percent / 100 * length)
    empty_blocks = length - filled_blocks
    bar = "🟥" * filled_blocks + "⬛" * empty_blocks
    if player:
        return f"**Your health:** [{bar}] {int(hp_percent)}%"
    return f"**Enemy health:** [{bar}] {int(hp_percent)}%"


def update_health_bar(state):
    return (
        render_health_bar((state["player"].hp / state["player"].max_hp) * 100, state["player"].max_hp),
        render_health_bar((state["current_monster"].HP / state["current_monster"].max_HP) * 100, state["current_monster"].max_HP, False),
    )


def return_to_title_screen():
    return (
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(value=None),
        gr.update(value=None, placeholder="Select an adventure to see its intro…"),
    )


def update_character_sheet(player: Player):
    inv = player.inventory if player.inventory else []
    inventory_md = "\n".join([f"- {item}" for item in inv]) if inv else "*None*"

    return f"""\
**Name:** {player.name}  
**Class:** {player.p_class.value}  
**Race:** {player.race}  
**Money:** 💰 {player.gold} gold  
**Health:** ❤️ {player.hp}/{player.max_hp}  

---
**Weapon:**  
{player.weapon.name}  
**Inventory:**  
{inventory_md}
"""


def show_character_sheet(state):
    return gr.update(value=update_character_sheet(state["player"]))


if __name__ == "__main__":
    clear()

    with gr.Blocks(title="Call to AIdventure (Legacy Gradio)") as demo:
        gr.HTML("""
            <style>
            .large-text textarea {
                font-size: 20px !important;
            }
            </style>
        """)

        with gr.Column(visible=True) as landing:
            gr.Markdown("## 🎲 Welcome to AIdventure")
            adv_drop = gr.Dropdown(
                choices=[(a.name, i) for i, a in enumerate(adventures)],
                label="Choose a new adventure",
                value=None
            )
            intro_box = gr.Textbox(
                label="Adventure Intro",
                interactive=False,
                lines=5,
                placeholder="Select an adventure to see its intro…",
                elem_classes="large-text"
            )
            new_btn = gr.Button("Start New Game", visible=False)
            adv_state = gr.State(adventures)

        with gr.Column(visible=False) as narration_screen:
            title_md = gr.Markdown("")
            with gr.Row():
                with gr.Column(scale=3):
                    story_box = gr.Textbox(interactive=False, elem_classes="large-text")
                    choice_radio = gr.Radio(label="Your action")
                    submit_btn = gr.Button("Next")
                    combat_btn = gr.Button("It's a fight! ⚔️", visible=False)
                    state_holder = gr.State()
                with gr.Column(scale=1):
                    gr.Markdown("### Character Sheet")
                    char_sheet = gr.Markdown("Loading...")
                    stats_panel = gr.JSON(visible=False)

        with gr.Column(visible=False) as combat_screen:
            title_md_combat = gr.Markdown("")
            with gr.Row():
                with gr.Column(scale=3):
                    combat_log = gr.Textbox(interactive=False, elem_classes="large-text", label="Combat Log")
                    combat_radio = gr.Radio(label="Your action")
                    player_health_md = gr.Markdown(render_health_bar(100))
                    combat_action_btn = gr.Button("Next")
                    victory_btn = gr.Button("Victory! 👑", visible=False)
                    defeat_btn = gr.Button("You died... 🪦", visible=False)

                with gr.Column(scale=1):
                    monster_md = gr.Markdown("")
                    monster_image = gr.Image()
                    monster_health_md = gr.Markdown(render_health_bar(100))

        adv_drop.change(
            fn=show_intro,
            inputs=[adv_drop, adv_state],
            outputs=[intro_box, new_btn]
        )

        new_btn.click(
            fn=start_callback,
            inputs=[adv_drop, adv_state, gr.State(value="new")],
            outputs=[
                story_box,
                choice_radio,
                state_holder,
                landing,
                narration_screen,
                title_md,
            ]
        ).then(
            fn=show_character_sheet,
            inputs=[state_holder],
            outputs=[char_sheet]
        )

        submit = submit_btn.click(
            fn=step,
            inputs=[choice_radio, state_holder],
            outputs=[
                narration_screen,
                combat_screen,
                story_box,
                choice_radio,
                submit_btn,
                combat_btn,
                victory_btn,
                state_holder,
            ]
        )
        submit.then(
            fn=show_character_sheet,
            inputs=[state_holder],
            outputs=[char_sheet]
        )

        combat_btn.click(
            fn=start_combat,
            inputs=[state_holder],
            outputs=[
                narration_screen,
                combat_screen,
                combat_log,
                combat_radio,
                combat_action_btn,
                monster_md,
                monster_image,
                state_holder,
            ]
        ).then(
            fn=update_health_bar,
            inputs=[state_holder],
            outputs=[player_health_md, monster_health_md]
        )

        combat_action_btn.click(
            fn=start_player_action,
            inputs=[state_holder, combat_radio],
            outputs=[
                combat_log,
                combat_radio,
                combat_action_btn,
                victory_btn,
                defeat_btn,
                state_holder,
            ]
        ).then(
            fn=update_health_bar,
            inputs=[state_holder],
            outputs=[player_health_md, monster_health_md]
        )

        victory_btn.click(
            fn=step,
            inputs=[choice_radio, state_holder],
            outputs=[
                narration_screen,
                combat_screen,
                story_box,
                choice_radio,
                submit_btn,
                combat_btn,
                victory_btn,
                state_holder,
            ]
        ).then(
            fn=lambda st: st["player"].model_dump(),
            inputs=[state_holder],
            outputs=[stats_panel]
        )

        defeat_btn.click(
            fn=return_to_title_screen,
            inputs=[],
            outputs=[landing, narration_screen, combat_screen, adv_drop, intro_box]
        )

    demo.launch()