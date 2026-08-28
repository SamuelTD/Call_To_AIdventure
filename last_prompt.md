I've added a "goals" key to the adventures .json files. This list holds every goals the player must achieve in order for the adventure to be complete. This is how it should work : 
-After every player choice resolution, the LLM should check all goals and determined which are complete and which are not. 
-If all goals are completed, the LLM should wrap up the narrative then offer only a "continue" option just like a gameover.
-The next view should be a victory screen where the outro of the adventure (outro.txt, loaded with the relevant function in adventure.py) should be displayed and the session marked as finished.
-The session model should be updated to hold finished goals vs on going goals : when evaluated as completed, a goal should be marked as such and removed from the on-going list so very old context doesn't matter to the LLM for goal evaluation.

Explain what would be your strategy for such an implementation in the current code base, no coding yet.

Show more
3:48 PM



Worked for 32s
Implementation Strategy

I’d treat adventure completion as a first-class ending state, parallel to death/gameover but distinct from combat victory.

Normalize adventure goals at load time

Adventure.goals is already present in 
adventure.py
, and the SQLite schema already stores goals. I’d first fix the small inconsistency where load_all_adventures() JSON-decodes goals, but load_adventure() currently passes the DB text through raw.

Initialize session goal state

In initialize_game() I’d add something like:

"ongoing_goals": adventure.goals.copy(),
"finished_goals": [],
"adventure_completed": False,
"end_reason": None,
Since save state is already JSON stored in SaveGame.state, this likely needs no DB migration. Older saves can be handled defensively: if those keys are missing, rebuild them from state["adventure"].goals.

Add a structured LLM goal evaluator

I’d create a new structured output schema, probably in agents/schemas.py, returning completed goal texts from the current ongoing_goals list only.

The evaluator prompt should receive:

the latest generated story resolution
the latest user choice
recent compressed history
player summary
only ongoing_goals
It should not receive already finished goals. That keeps old context from repeatedly influencing goal evaluation, as you requested.

Insert goal evaluation after story generation

The right graph location is after step_generate_story() in game_master_graph.py.

Flow would become:

player choice
-> agent_think
-> generate_story
-> evaluate_goals
-> maybe_generate_adventure_wrapup
-> get_input
If some goals complete, move them from ongoing_goals to finished_goals.

Generate a final narrative wrap-up when all goals are complete

If ongoing_goals becomes empty, I’d have a dedicated prompt generate a short closing narrative, append it to history, set:

should_end = True
end_reason = "victory"
adventure_completed = True
current_choices = ["Continue."]
This mirrors the current death behavior where the player gets one final “Continue.” option before leaving the play view.

Add a real adventure victory screen

Right now mode: "victory" already means combat victory in combat_action(), so I would avoid reusing that exact meaning blindly. I’d probably return something explicit from GameEngine.step() like:

{"mode": "adventure_victory"}
Then the frontend redirects to a new victory page.

That page should load and display outro.txt via load_adv_outro() from 
adventure.py
. The save/session should be marked finished at this transition, same as gameover currently does.

Update persistence and frontend routing

In StepGameView, when the player clicks the final Continue. and end_reason == "victory", call:

persist_game(request, state, finish=True)
Then return the adventure-victory mode. play.html would redirect to a new /victory/ page, similar to /gameover/.

Test coverage

I’d add tests for:

new sessions initialize ongoing_goals and finished_goals
completed goals move lists correctly
already finished goals are not sent back to the evaluator
all goals complete forces ["Continue."]
clicking continue after completion marks the save finished
victory page displays outro.txt
death/gameover still works separately from victory
One important design detail: I’d keep combat victory and adventure victory separate. Combat victory means “you defeated this monster”; adventure victory means “the adventure’s required goals are complete.” That distinction will save confusion in both code and UI.





3:49 PM





Default permissions




Work locally