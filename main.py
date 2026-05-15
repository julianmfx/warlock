from warlock.agents.data_engineer import DataEngineerAgent
from warlock.memory import Memory
from warlock.orchestrator import Orchestrator
from warlock.providers.anthropic import AnthropicClient

m = Memory()
client = AnthropicClient()

data_engineer = DataEngineerAgent(
    memory=m,
    client=client,
    model="claude-haiku-4-5-20251001",
)

orchestrator = Orchestrator(
    memory=m,
    client=client,
    model="claude-haiku-4-5-20251001",
)

orchestrator.register(data_engineer)

output = orchestrator.run("Ingest CSV into BigQuery")
m.print_log()
