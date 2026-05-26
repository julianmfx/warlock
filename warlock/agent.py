# agent.py
from warlock.llm import LLMClient


class Agent:
    def __init__(self, name, identity, memory, client: LLMClient, model: str):
        self.name = name
        self.identity = identity
        self.memory = memory
        self._client = client
        self._model = model

    def run(self, task):
        problem = self.memory.read("problem_statement")

        response = self._client.complete(
            model=self._model,
            system=self.identity,
            messages=[
                {
                    "role": "user",
                    "content": f"Problem: {problem}\n\nTask: {task}",
                }
            ],
        )

        output = response.text
        self.memory.patch("agent_outputs", self.name, output)
        self.memory.patch(
            "token_spend",
            self.name,
            {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "cache_read_tokens": response.usage.cache_read_tokens,
            },
        )
        return output

    def describe(self):
        print(f"Agent: {self.name}")
        print(f"Identity: {self.identity}")
        print(f"Memory: {self.memory.dump()}")
