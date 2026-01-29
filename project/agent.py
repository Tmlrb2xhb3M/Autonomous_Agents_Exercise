from enum import Enum
import enviroment_tools

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
        ("transition", "GO_IMPACT_ANALYSIS")
        ("transition", "GO_VALIDATE")
    }
}

class Agent:
    def __init__(self, model):
        self.model = model
        self.state = State.INIT
        self.memory = []
        pass

    def run(self, maxsteps=100):
        steps = 0

        if self.state == State.FAILURE_DETECTION:
            ctx = enviroment_tools.detect_failure_nodes()
            self.memory.append(ctx)
            self.state = State.IMPACT_ANALYSIS
        
        elif self.state == State.IMPACT_ANALYSIS:
            pass
        
        elif self.state == State.REPAIR_PLANNING:
            pass

        elif self.state == State.VALIDATE:
            pass