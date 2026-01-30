from enum import Enum
from enviroment_tools import TOOL_REGISTRY
from smolagents import  InferenceClientModel
import smolagents

class State(Enum):
    INIT=0
    FAILURE_DETECTION=1
    IMPACT_ANALYSIS=2
    REPAIR_PLANNING=3
    VALIDATE=4
    FINAL=5

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
    def __init__(self, model: smolagents.Model):
        self.model = model
        self.state = State.INIT
        self.memory = []
        pass

    def update_history():
        pass

    def run(self, maxsteps=20):
        steps = 0

        while(self.state != State.FINAL and steps <= 100):
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
                system_prompt+="""
                PHASE: Failure Detection.
                OBJECTIVE: Use the available tools (detect_failure_nodes, estimate_impact) to gather info for node status and impact of failed nodes.
                CONSTRAINT: Do not make a plan, just gather info.
                """
                response = self.model.generate(system_prompt)

                # Validate response

                # Add to History
                self.state=State.IMPACT_ANALYSIS
                continue
            
            elif self.state == State.IMPACT_ANALYSIS:
                system_prompt+="""
                PHASE: Impact Analysis.
                OBJECTIVE: Think a plan to solve the detected failures.
                CONSTRAINT: Think step by step, do not call tools.
                """
                response = self.model.generate(system_prompt)
                self.state = State.REPAIR_PLANNING
                continue
            
            elif self.state == State.REPAIR_PLANNING:
                system_prompt+="""
                PHASE: Repair Planning
                OBJECTIVE: Use the available tools (assign_repair_crew) to solve the detected problems
                """
                response = self.model.generate(system_prompt)
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

    def validate_solution():
        pass

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