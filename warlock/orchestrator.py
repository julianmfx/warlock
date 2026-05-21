import json
import time

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
    def __init__(self, memory, client: LLMClient, model: str, supervisor=None):
        self._memory = memory
        self._client = client
        self._model = model
        self._agents = {}
        self._supervisor = supervisor

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

        token_spend = self._memory.read("token_spend") or {}
        token_spend["orchestrator"] = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "cache_read_tokens": response.usage.cache_read_tokens,
        }

        self._memory.write("token_spend", token_spend)

        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(text)

    def run(self, problem):
        self._memory.write("problem_statement", problem)

        start = time.time()
        tasks = self.decompose(problem)
        end = time.time()
        elapsed = round(end - start, 2)
        timing = self._memory.read("timing") or {}
        timing["orchestrator"] = elapsed

        self._memory.write("timing", timing)
        self._memory.write("task_decomposition", tasks)
        for item in tasks:
            agent = self._agents.get(item["domain"])
            if agent:
                start = time.time()
                agent.run(item["task"])
                end = time.time()
                elapsed = round(end - start, 2)

                timing = self._memory.read("timing") or {}
                timing[item["domain"]] = elapsed
                self._memory.write("timing", timing)

                if self._supervisor:
                    output = self._memory.read("agent_outputs")[item["domain"]]

                    sv_start = time.time()
                    self._supervisor.validate(item["domain"], item["task"], output)
                    sv_end = time.time()
                    timing = self._memory.read("timing") or {}
                    sv_elapsed = round(
                        timing.get("supervisor", 0) + (sv_end - sv_start), 2
                    )
                    timing["supervisor"] = sv_elapsed
                    self._memory.write("timing", timing)
