from dotenv import load_dotenv
load_dotenv()

import json
from llm import llm_call
from prompts import SCHEMA
from prompts import observer_system_prompt
from parse import parse_llm_output
from world import WORLD_STATE
from enviroment_tools import OBSERVER_TOOL_REGISTRY



prompt = (
    "Detect failed nodes, estimate impact, and make a report for the planner agent to be able to use this and plan for infrastructure fixes.\n"
)

# Schema for message history
messages = [
    {"role": "user", "content": "We are simulating a city outage."},
    {"role": "assistant", "content": "Understood. Awaiting instructions."},
]

#parsed = parse_llm_output(raw_output, SCHEMA)

result = llm_call(
    system_prompt=observer_system_prompt,
    prompt=prompt,
    tools=list(OBSERVER_TOOL_REGISTRY.values()),
    messages=[],
    sliding_window = 3, # it holds the last 3 steps
    max_steps=10
)

print("\n================ FINAL OUTPUT ================\n")

raw_output = result.output

print(raw_output)

print("--------------------------------------------------")
