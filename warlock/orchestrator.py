import json
import time
import uuid

from warlock.llm import LLMClient
from warlock.trace_logger import TraceLogger

ROLE = """You are an orchestrator for a multi-agent data and AI platform.
Your job is to decompose a problem into sub-tasks and assign each to the correct specialist domain.

Available domains: {domains}

Domain ownership:
- data_engineer — data ingestion, pipelines, warehouse loading, schema handling; dbt project config/readiness.
- data_scientist — the research cycle: problem formulation, experiment design, feature analysis, model training, evaluation and interpretation.
- ml_engineer — the production cycle: packaging/registration, deployment and serving, model monitoring (drift, model performance, data quality), retraining pipelines.
- devops_mlops — infrastructure: CI/CD and deployment automation, traffic/routing infra (e.g. A/B splitting), secrets and environment wiring, infra monitoring (latency, error rate, resource use).
- software_dev — the application surface: API endpoints, request routing, auth, service code.
- analytics — measurement and reporting: dashboards, KPIs, business metrics (e.g. CTR, conversion lift).

Boundary rules (the distinctions that are easy to get wrong):
1. Model training always belongs to data_scientist, even when the approach is fully specified. ml_engineer takes over only at a production artifact (serving endpoint, batch job, registered model).
2. Monitoring splits by what the metric is about: model/prediction metrics (drift, model performance, data quality) -> ml_engineer; service/infra metrics (latency, error rate, resource use) -> devops_mlops.
3. software_dev owns the API surface (HTTP endpoint, contract, auth); ml_engineer owns the inference/serving layer behind it.
4. Pipelines: dbt project config and readiness -> data_engineer; CI/CD workflow files, deployment scripts, secrets -> devops_mlops.

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
            temperature=0,
        )

        token_spend = self._memory.read("token_spend") or {}
        current_tokens = token_spend.get(
            "orchestrator",
            {"input_tokens": 0, "output_tokens": 0, "cache_read_tokens": 0},
        )
        self._memory.patch(
            "token_spend",
            "orchestrator",
            {
                "input_tokens": current_tokens["input_tokens"]
                + response.usage.input_tokens,
                "output_tokens": current_tokens["output_tokens"]
                + response.usage.output_tokens,
                "cache_read_tokens": current_tokens["cache_read_tokens"]
                + (response.usage.cache_read_tokens or 0),
            },
        )

        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(text)

    def run(self, problem):
        self._memory.write("problem_statement", problem)
        run_id = str(uuid.uuid4())
        trace_logger = TraceLogger(run_id)

        start = time.time()
        tasks = self.decompose(problem)
        end = time.time()
        elapsed = round(end - start, 2)

        self._memory.patch("timing", "orchestrator", elapsed)
        self._memory.write("task_decomposition", tasks)
        for item in tasks:
            agent = self._agents.get(item["domain"])
            if agent:
                start = time.time()
                agent.run(item["task"])
                end = time.time()
                elapsed = round(end - start, 2)
                self._memory.patch("timing", item["domain"], elapsed)

                if self._supervisor:
                    output = self._memory.read("agent_outputs")[item["domain"]]

                    sv_start = time.time()
                    accepted = self._supervisor.validate(
                        item["domain"], item["task"], output
                    )
                    trace_logger.log(
                        problem=problem,
                        agent=item["domain"],
                        task=item["task"],
                        output=output,
                        accepted=accepted,
                        reason=self._memory.read("validation_results")[item["domain"]][
                            "reason"
                        ],
                        iteration=0,
                    )
                    if not accepted:
                        agent.run(item["task"])
                    sv_end = time.time()
                    timing = self._memory.read("timing") or {}
                    sv_elapsed = round(
                        timing.get("supervisor", 0) + (sv_end - sv_start), 2
                    )
                    self._memory.patch("timing", "supervisor", sv_elapsed)
