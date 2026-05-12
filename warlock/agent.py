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

        agent_outputs = self.memory.read("agent_outputs") or {}
        agent_outputs[self.name] = response.text
        self.memory.write("agent_outputs", agent_outputs)

        token_spend = self.memory.read("token_spend") or {}
        token_spend[self.name] = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "cache_read_tokens": response.usage.cache_read_tokens,
        }
        self.memory.write("token_spend", token_spend)

        output = response.text

        return output

    def describe(self):
        print(f"Agent: {self.name}")
        print(f"Identity: {self.identity}")
        print(f"Memory: {self.memory.dump()}")
