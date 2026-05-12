# main.py

# imports
from warlock.agent import Agent
from warlock.memory import Memory

m = Memory()
m.write("problem_statement", "Ingest CSV into BigQuery")

data_engineer = Agent(
    name="data_engineer",
    identity="I am a data engineer with over 30 years of experience. I move data, create data pipelines, build data models. I do pipelines, ingestion, transformation, schemas and data quality checks",
    memory=m,
)

output = data_engineer.run("Design the ingestion pipeline for this problem.")
print(output)
