import json

from warlock.llm import LLMClient

ROLE = """You are the Supervisor of a multi-agent AI platform.

You work with a team of agents to complete tasks and one orchestrator.
The orchestrator is responsible for scheduling and coordinating the agents.
Each agent is responsible for a specific task.

Your job is to review the output of a specialist agent and decide if it meets the quality bar.
You will be given in this order:
    - The original problem
    - The agent's name
    - The task the agent was assigned
    - The agent's output

Evaluate the output on two criteria:
    1. ON-DOMAIN: Did the agent stay within its assigned domain? Did it avoid crossing into other specialists' domains?
    2. QUALITY: Is the output substantive and useful? Does it actually addresses the task?

Return ONLY a JSON object with exactly two keys:
    - "accepted": true or false
    - "reason": one sentence explaining your decision

No explanation. No markdown. No code fences. Only the JSON object.
"""


class Supervisor:
    def __init__(self, memory, client: LLMClient, model: str):
        self._memory = memory
        self._client = client
        self._model = model

    def validate(self, agent_name: str, task: str, output: str) -> bool:
        problem = self._memory.read("problem_statement")

        response = self._client.complete(
            model=self._model,
            system=ROLE,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Problem: {problem}\n"
                        f"Agent: {agent_name}\n"
                        f"Task assigned: {task}\n"
                        f"Agent output: {output}\n"
                    ),
                }
            ],
            temperature=0,
        )

        token_spend = self._memory.read("token_spend") or {}
        current_tokens = token_spend.get(
            "supervisor",
            {"input_tokens": 0, "output_tokens": 0, "cache_read_tokens": 0},
        )
        self._memory.patch(
            "token_spend",
            "supervisor",
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
        result = json.loads(text)

        self._memory.patch(
            "validation_results",
            agent_name,
            {
                "accepted": result["accepted"],
                "reason": result["reason"],
            },
        )
        return result["accepted"]
