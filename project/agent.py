from enum import Enum
from enviroment_tools import TOOL_REGISTRY
from smolagents import  InferenceClientModel
import json
<<<<<<< Updated upstream
import prompts
from world import WORLD_STATE
=======
>>>>>>> Stashed changes

class State(Enum):
    INIT=0
    FAILURE_DETECTION=1
    IMPACT_ANALYSIS=2
    REPAIR_PLANNING=3
    VALIDATE=4
    FINAL=5

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

ALLOWED_ACTION_TYPES = {
    "tool",
    "transition",
    "final"
}

ALLOWED_TRANSITIONS = {
    "GO_FAILURE_DETECTION",
    "GO_IMPACT_ANALYSIS",
    "GO_REPAIR_PLANNING",
    "GO_VALIDATE",
    "GO_FINAL"
}

ALLOWED_ACTIONS_BY_STATE = {
    State.INIT: {
        ("transition", "GO_FAILURE_DETECTION")
    },
    State.FAILURE_DETECTION: {
        ("transition", "GO_IMPACT_ANALYSIS"),
    },
    State.IMPACT_ANALYSIS: {
        ("transition", "GO_REPAIR_PLANNING")
    },
    State.REPAIR_PLANNING: {
        ("transition", "GO_IMPACT_ANALYSIS"),
        ("transition", "GO_VALIDATE"),
    },
    State.VALIDATE: {
        ("transition", "GO_REPAIR_PLANNING"),
        ("transition", "GO_FINAL")
    },
    State.FINAL: 
    {
        ("final", "FINAL")
    }
}

class Agent:
    def __init__(self, agent):
        self.agent = agent
<<<<<<< Updated upstream
    def __init__(self, agent):
        self.agent = agent
        self.state = State.INIT
        self.memory = []
        self.history_size=10
        self.history_size=10
=======
        self.state = State.INIT
        self.memory = []
        self.history_size=10
>>>>>>> Stashed changes
        pass

    def get_context(self):
        return self.memory

<<<<<<< Updated upstream
    def get_context(self):
        return self.memory

    def update_history(self, role, content):
        self.memory.append({"role": role, "content": content})
        if len(self.memory) > self.history_size:
            removed_msg=self.memory.pop(0)
            print(f"[Memory] Pruned old message:{removed_msg["content"][:20]}...")
=======
>>>>>>> Stashed changes
    def update_history(self, role, content):
        self.memory.append({"role": role, "content": content})
        if len(self.memory) > self.history_size:
            removed_msg=self.memory.pop(0)
            print(f"[Memory] Pruned old message:{removed_msg["content"][:20]}...")

    def run(self, maxsteps=20):
        steps = 0

        while(self.state != State.FINAL and steps <= 20):
<<<<<<< Updated upstream
        while(self.state != State.FINAL and steps <= 20):
=======
>>>>>>> Stashed changes
            print(self.state)
            steps += 1
            system_prompt="""
                You are an infrastructures failure management agent.
                You must respond with a valid JSON object.
                """
            if self.state == State.INIT:
                self.state=State.FAILURE_DETECTION
                continue

            elif self.state == State.FAILURE_DETECTION:
<<<<<<< Updated upstream
                system_prompt=prompts.observer_system_prompt
                #response = self.model.generate(self.memory + system_prompt)
                
                #Request response from agent
=======
                system_prompt+="""
                PHASE: Failure Detection.
                OBJECTIVE: Use the available tools (detect_failure_nodes, estimate_impact) to gather info for node status and impact of failed nodes.
                CONSTRAINT: Do not make a plan, just gather info.
                """
                response = self.model.generate(self.memory + system_prompt)
>>>>>>> Stashed changes
                response = agent.run(system_prompt, 5)

                # Validate response

                # Add to History
                self.update_history(self, "assistant", response)
                self.state=State.IMPACT_ANALYSIS
                continue
            
            elif self.state == State.IMPACT_ANALYSIS:
<<<<<<< Updated upstream
                system_prompt=prompts.planner_system_prompt
                #response = self.model.generate(self.memory + system_prompt)

                #Request response from agent
                response = agent.run(system_prompt, 5)

                # Add to History
                self.update_history(self, "assistant", response)
=======
                system_prompt+="""
                PHASE: Impact Analysis.
                OBJECTIVE: Think a plan to solve the detected failures.
                CONSTRAINT: Think step by step, do not call tools.
                """
                response = self.model.generate(self.memory + system_prompt)
                response = agent.run(system_prompt, 5)
>>>>>>> Stashed changes
                self.state = State.REPAIR_PLANNING
                continue
            
            elif self.state == State.REPAIR_PLANNING:
<<<<<<< Updated upstream
                system_prompt=prompts.repair_system_prompt
                #response = self.model.generate(self.memory + system_prompt)

                #Request response from agent
                response = agent.run(system_prompt, 5)

                # Add to History
                self.update_history(self, "assistant", response)
=======
                system_prompt+="""
                PHASE: Repair Planning
                OBJECTIVE: Use the available tools (assign_repair_crew) to solve the detected problems
                """
                response = self.model.generate(self.memory + system_prompt)
                response = agent.run(system_prompt, 5)
>>>>>>> Stashed changes
                self.state=State.REPAIR_PLANNING
                continue

            elif self.state == State.VALIDATE:
                if self.validate_solution() == True:
                    self.state=State.FINAL
                else:
                    self.state=State.IMPACT_ANALYSIS
                continue

            elif self.state == State.FINAL:
                break

    def validate_solution(self, decision: dict[str, any]) -> list[str]:
        violations=[]

        action_type=decision["action_type"]
        action=decision["action"]
        args=decision.get["arguements", {}] or {}

        if action_type == "tool" and action == "assign_repair_crew":
            if WORLD_STATE["crews"][args["crew_ids"]]["availability"] == False:
                violations.append("Crew is unavailable")
            
        return violations

    def route_decision(self, decision):
        action_type=decision.get("action_type")
        action=decision.get("action")

        if action_type not in ALLOWED_ACTION_TYPES:
            return {
                "ok":False, 
                "action_type": action_type,
                "error": f"Action type {action_type} not on allowed action types.",
                "observation": {"safe state": True}
            }

        if (action_type, action) not in ALLOWED_ACTIONS_BY_STATE:
            return {
                "ok": False,
                action_type: action,
                "error": f"Action '{action}' not allowed in state '{self.state}'.",
                "observation": {"safe state", True}
            }
        
        if action_type == "transition":
            if action not in ALLOWED_TRANSITIONS:
                return {
                    "ok": False,
                    "transition": action,
                    "error": f"Transition '{action}' not allowed in system.",
                    "observation": {"safe state", True}
                }
            else:

<<<<<<< Updated upstream

=======
>>>>>>> Stashed changes
                return {
                    "ok": True, 
                    "transition": action,
                    "error": "No error",
                    "observation": {"transition": action}
                }
        
        if action_type == "tool":
            if action not in TOOL_REGISTRY:
                return {
                    "ok": False,
                    "tool": action,
                    "error": f"Action {action} not in tool registry.",
                    "observation": {"safe state": True}
                }

        if action_type == "final":
            return {
                "ok": True,
                "final": True,
                "error": "No error",
                "observation": "None"
            }
        
agent = Agent(model=InferenceClientModel())
agent.run()