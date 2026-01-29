from enum import Enum
from enviroment_tools import assign_repair_crew, estimate_impact, detect_failure_nodes
from smolagents import  InferenceClientModel
import smolagents

class State(Enum):
    INIT=0
    FAILURE_DETECTION=1
    IMPACT_ANALYSIS=2
    REPAIR_PLANNING=3
    VALIDATE=4
    FINAL=5

ALLOWED_ACTION_TYPES = {"tool", "transition", "final"}

ALLOWED_BY_STATE = {
    State.FAILURE_DETECTION: {
        ("tool", "detect_failure_nodes"),
        ("tool", "estimate_impact"),
        ("transition", "GO_IMPACT_ANALYSIS"),
    },
    State.IMPACT_ANALYSIS: {
        ("transition", "GO_REPAIR_PLANNING")
    },
    State.REPAIR_PLANNING: {
        ("tool", "assign_repair_crew"),
        ("transition", "GO_IMPACT_ANALYSIS"),
        ("transition", "GO_VALIDATE"),
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

agent = Agent(model=InferenceClientModel())
agent.run()