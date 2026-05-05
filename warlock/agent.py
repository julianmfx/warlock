# agent.py


class Agent:
    def __init__(self, name, identity, memory):
        self.name = name
        self.identity = identity
        self.memory = memory

    def run(self, task):
        raise NotImplementedError("Each specialist agent must implement run()")

    def describe(self):
        print(f"Agent: {self.name}")
        print(f"Identity: {self.identity}")
        print(f"Memory: {self.memory.dump()}")
