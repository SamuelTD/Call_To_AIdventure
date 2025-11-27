# -*- coding: utf-8 -*-

import os
import dotenv
import chromadb
import json
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.llm import LLMChain
from utils.python_utils import clear
from utils.player import Player, save_player, load_player
from combat.core import run_combat
from langchain_groq import ChatGroq
from langchain.agents import Tool, initialize_agent, AgentType
import state


dotenv.load_dotenv()

# Chroma collections
CHAR_COL = "characters"
LOC_COL = "locations"

# Le modèle d'embedding (doit être le même que celui utilisé pour la création).
EMBEDDING_MODEL = "mxbai-embed-large:latest"

# Le modèle de LLM à utiliser pour la génération de la réponse.
LLM_MODEL = "llama3.2:latest"

# Initialise le client Ollama pour les embeddings
ollama_embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)

# Vector stores 

vectorstore_char = Chroma(
    client=chromadb.PersistentClient(path="db/chroma"),
    collection_name=CHAR_COL,
    embedding_function=ollama_embeddings
)

vectorstore_loc = Chroma(
    client=chromadb.PersistentClient(path="db/chroma"),
    collection_name=LOC_COL,
    embedding_function=ollama_embeddings
)

# Retrievers
lulu_retriever = vectorstore_char.as_retriever(search_kwargs={"k":1, "filter": {
            "$and": [
                {"type": {"$eq": "character"}},
                {"id":   {"$eq": "lulu_the_wise"}}
            ]
        }})

char_retriever = vectorstore_char.as_retriever(search_kwargs={"k": 5, "filter": {"id" : {"$ne": "lulu_the_wise"}}})

loc_retriever = vectorstore_loc.as_retriever(search_kwargs={"k": 3})


# Model with OLLAMA
# llm = ChatOllama(model=LLM_MODEL)

llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model="llama-3.3-70b-versatile")

# Memory
history = []

# Prompt Template

template = ChatPromptTemplate.from_template("{full_prompt}")


chain = LLMChain(
    llm=llm,
    prompt=template
)

player = None    
story_steps = 0

def combat_tool(enemy: str) -> str:
    state.last_decision = json.dumps({"action":"combat","enemy":enemy})
    state.enemy_name = enemy
    return ""

def nothing_tool(target: str) -> str:
    agent_report = json.dumps({"action":"continue"})
    return ""

tools = [
    Tool(
      name="combat",
      func=combat_tool,
      description="Call when combat should start against a monster or a creature; arg: enemy name."
    ),
     Tool(
      name="nothing",
      func=nothing_tool,
      description="Call when no combat should start, and then stop. Returns an empty string."
    )
]

agent = initialize_agent(
    tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True, max_iterations=1,
    early_stopping_method="generate"
)

# Main loop

if __name__ == "__main__":
   
#    character_creation_step = 0
   loop_step = 0
   
   while True:
    match loop_step:
        case 0:
            print("Welcome to Call to AIdventure. What do you wish to do?")
            print("1. Character creation (type 1)")
            print("2. Play (type 2)")
            q = input("Type 1 or 2 : ")
            if q == "1":
                loop_step = 1
                clear()
            elif q == "2":
                loop_step = 2
                clear()
            else:
                clear()
                print("Please enter a valid value.\n\n")
        case 1: #Character creation         
            name = input("What is your name? ")
            player_class = input("What is your class? ")
            race = input("What is your race? ")
            gold = int(input("How much gold do you have? "))
            player = Player(name=name, race=race, p_class=player_class, gold=gold)
            save_player(player)
            clear()
            print("Uploading data, please wait...")
            loop_step = 2
            clear()
        case 2:  #Main LLM Loop
            if player == None:
                player = load_player()    
            player_summary = (f"Name : {player.name} - Race : {player.race} - Job : {player.p_class}")
            
            if story_steps == 0 :
                with open("data/documents/intro2.txt", "r") as file:
                    intro = file.read()
                print(intro)                
                history.append(intro)
            
            q = input("You : ")
            if q.lower()=="exit": 
                print("Farewell, adventurer.")
                break
            
            chat_hist = "\n".join(history)
            
            decision = agent.invoke({"input": f"{chat_hist}\nPlayer: {q}"})
            cmd = json.loads(state.last_decision)
            
            if cmd["action"] == "combat":
                combat_result = run_combat(cmd["enemy"], player)
                if combat_result["signal"] == 2:
                    print(combat_result["message"])
                    break
                else:
                    full_prompt = f"""
                    Here are the informations on the user :
                    {player_summary}
                    
                    Here is the adventure so far:
                    {chat_hist}

                    You are the Game Master for a narrative adventure game. You take the user input and continue the story\
                        based on the events so far and the user input. You use a refined, fantasy inspired tone to craft the story.\
                            You write in the second person and conclude every message by "Now, what do you do?".\
                                Limit each of your answer to six sentences maximum. The user juste vanquished {state.enemy_name}.\
                                    Start your output by "You vanquished {state.enemy_name} and go from there.

                    User input: {q}
                    """
            
            elif cmd["action"] == "continue":            
                full_prompt = f"""
                Here are the informations on the user :
                {player_summary}
                
                Here is the adventure so far:
                {chat_hist}

                You are the Game Master for a narrative adventure game. You take the user input and continue the story\
                    based on the events so far and the user input. You use a refined, fantasy inspired tone to craft the story.\
                        You write in the second person and conclude every message by "Now, what do you do?".\
                            Limit each of your answer to six sentences maximum.

                User input: {q}
                """
            

            # 4) Invoke the chain *once*
            answer = chain.predict(full_prompt=full_prompt)
            print("Story:", answer,"\n\n")

            # 5) Update history
            history.append(f"You: {q}")
            history.append(f"Story: {answer}")
            
            story_steps += 1
