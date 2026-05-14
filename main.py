# main.py

# imports
from warlock.agents.data_engineer import DataEngineerAgent
from warlock.memory import Memory
from warlock.providers.anthropic import AnthropicClient

m = Memory()
m.write("problem_statement", "Ingest CSV into BigQuery")

client = AnthropicClient()

data_engineer = DataEngineerAgent(
    memory=m,
    client=client,
    model="claude-haiku-4-5-20251001",
)

output = data_engineer.run("Design the ingestion pipeline for this problem.")
print(output)
