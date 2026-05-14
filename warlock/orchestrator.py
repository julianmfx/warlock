import json

from warlock.llm import LLMClient

ROLE = """You are an orchestrator for a multi-agent data and AI platform.
Your job is to decompose a problem into sub-tasks and assign each to the correct specialist domain.

Available domains: {domains}

Return ONLY a JSON array. Each item must have exactly two keys:
- "domain": one of the available domains listed above
- "task": a clear, self-contained instruction for that specialist

No explanation. No markdown. No code fences. No extra keys. Only the JSON array.
"""


class Orchestrator:
    def __init__(self, memory, client: LLMClient, model: str):
        self._memory = memory
        self._client = client
        self._model = model
        self._agents = {}

    def register(self, agent):
        self._agents[agent.name] = agent

    def decompose(self, problem):
        domains = ", ".join(self._agents.keys())
        system = ROLE.format(domains=domains)
        response = self._client.complete(
            model=self._model,
            system=system,
            messages=[{"role": "user", "content": problem}],
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(text)

    def run(self, problem):
        self._memory.write("problem_statement", problem)
        tasks = self.decompose(problem)
        self._memory.write("task_decomposition", tasks)
        for item in tasks:
            agent = self._agents.get(item["domain"])
            if agent:
                agent.run(item["task"])
