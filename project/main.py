from dotenv import load_dotenv
load_dotenv()

import json
from llm import llm_call
from world import WORLD_STATE
from enviroment_tools import OBSERVER_TOOL_REGISTRY

SCHEMA = {
    "type": "object",
    "tools_called": {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "tool_name": {"type": "string"},
                "parameters": {"type": "object"},
                "result": {"type": "object"}
            },
            "required": ["tool_name", "parameters", "result"]
        }
    },
    "reasoning": {
        "type": "string",
        "required": "reasoning"
    },
    "final_output": {
        "type": "string",
        "required": "final_output"
    },

     "transition": {
        "type": "string",
        "description": "Return the next state of the agent after completing the tasks. If all tasks are done, return 'GO_IMPACT_ANALYSIS' else do not return this property.",
    },
}


system_prompt = (
    "You are the Observer Agent responsible for managing city infrastructure failures.\n"
    "Your tasks include detecting failed nodes, estimating their impact\n"
    "REQUIRED: Use the provided tools to accomplish these tasks effectively."
    "Your goal each time is to: Detect failed nodes, estimate impact, gather all info, and prepare\n"
    "a report for the IMPACT_ANALYSIS_AGENT agent presenting the data retrieved \n"
    "to be able to use this and estimate himself for what is the impact of the current state of the infrastructure.\n"
    "OUTPUT: A JSON object with the following structure:\n"
    f"{json.dumps(SCHEMA, indent=2)}\n"
)

prompt = (
    "Detect failed nodes, estimate impact, and make a report for the planner agent to be able to use this and plan for infrastructure fixes.\n"
)

# Schema for message history
messages = [
    {"role": "user", "content": "We are simulating a city outage."},
    {"role": "assistant", "content": "Understood. Awaiting instructions."},
]

result = llm_call(
    system_prompt=system_prompt,
    prompt=prompt,
    tools=list(OBSERVER_TOOL_REGISTRY.values()),
    messages=[],
    sliding_window = 1,
    max_steps=10
)

print("\n================ FINAL OUTPUT ================\n")

raw_output = result.output
print(raw_output)

print("--------------------------------------------------")
