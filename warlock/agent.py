# agent.py
import anthropic


class Agent:
    def __init__(self, name, identity, memory):
        self.name = name
        self.identity = identity
        self.memory = memory
        self._client = anthropic.Anthropic()

    def run(self, task):
        problem = self.memory.read("problem_statement")

        response = self._client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=[
                {
                    "type": "text",
                    "text": self.identity,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": f"Problem: {problem}\n\nTask: {task}",
                }
            ],
        )

        output = next(block.text for block in response.content if block.type == "text")

        agent_outputs = self.memory.read("agent_outputs") or {}
        agent_outputs[self.name] = output
        self.memory.write("agent_outputs", agent_outputs)

        return output

    def describe(self):
        print(f"Agent: {self.name}")
        print(f"Identity: {self.identity}")
        print(f"Memory: {self.memory.dump()}")
