from warlock.agents.analytics import AnalyticsAgent
from warlock.agents.data_engineer import DataEngineerAgent
from warlock.agents.data_scientist import DataScientistAgent
from warlock.agents.devops_mlops import DevOpsMLOpsAgent
from warlock.agents.ml_engineer import MLEngineerAgent
from warlock.agents.software_dev import SoftwareDevAgent
from warlock.memory import Memory
from warlock.orchestrator import Orchestrator
from warlock.providers.anthropic import AnthropicClient
from warlock.supervisor import Supervisor

m = Memory()
client = AnthropicClient()

supervisor = Supervisor(memory=m, client=client, model="claude-haiku-4-5-20251001")

orchestrator = Orchestrator(
    memory=m,
    client=client,
    model="claude-haiku-4-5-20251001",
    supervisor=supervisor,
)

orchestrator.register(
    AnalyticsAgent(memory=m, client=client, model="claude-haiku-4-5-20251001")
)
orchestrator.register(
    DataEngineerAgent(memory=m, client=client, model="claude-haiku-4-5-20251001")
)
orchestrator.register(
    DataScientistAgent(memory=m, client=client, model="claude-haiku-4-5-20251001")
)
orchestrator.register(
    DevOpsMLOpsAgent(memory=m, client=client, model="claude-haiku-4-5-20251001")
)
orchestrator.register(
    MLEngineerAgent(memory=m, client=client, model="claude-haiku-4-5-20251001")
)
orchestrator.register(
    SoftwareDevAgent(memory=m, client=client, model="claude-haiku-4-5-20251001")
)

output = orchestrator.run("Build a churn prediction system for a SaaS product")
m.print_log()
m.print_run_summary()
