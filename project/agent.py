from enum import Enum

class State(Enum):
    INIT=0
    CONTEXT=1
    PLAN=2
    GENERATE=3
    VALIDATE=4
    FINAL=5

class Agent:
    def __init__(self, model):
        self.model = model
        self.state = State.INIT
        self.memoty = {}
        pass

    def run(self, maxsteps=100):
        steps = 0

        if self.state != State.FINAL:
            steps += 1
        pass