from dataclasses import dataclass, field


@dataclass
class EvalCase:
    id: str
    problem: str
    expected_domains: list[str]
    notes: str = ""
    verified: bool = False
    gold_decomposition: list[dict] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Single-domain (sd-*)
# ---------------------------------------------------------------------------

SINGLE_DOMAIN: list[EvalCase] = [
    EvalCase(
        id="sd-01",
        problem=(
            "Our finance team drops CSV expense reports to S3 every night. "
            "Build the ingestion pipeline that lands those files in raw.expenses "
            "in Snowflake, handling schema mismatches and sending a Slack alert "
            "on failure. No downstream transformations or dashboards needed yet."
        ),
        expected_domains=["data_engineer"],
        notes=(
            "Included: data_engineer — ingestion pipeline, schema handling, warehouse load. "
            "Excluded: analytics (no dashboard asked), "
            "software_dev (a Slack webhook is an inline error handler inside the pipeline, not a standalone service), "
            "devops_mlops (operational hooks that live inside a pipeline — schedule, alert — are owned by whoever builds the pipeline; no CI/CD or infra design asked), "
            "ml_engineer (no model), data_scientist (no experimentation)."
        ),
        verified=True,
    ),
    EvalCase(
        id="sd-02",
        problem=(
            "Our warehouse already has orders, sessions, and products tables "
            "populated by the data team. Build a weekly KPI dashboard in Metabase "
            "showing revenue, AOV, and conversion rate broken down by channel. "
            "Data pipelines are handled separately — just the dashboard layer."
        ),
        expected_domains=["analytics"],
        notes=(
            "Included: analytics — KPI definitions, the SQL view/semantic layer behind the dashboard, "
            "and Metabase build; writing aggregation SQL for one's own dashboard is analytics work, not data engineering. "
            "Excluded: data_engineer — ingestion and source-table maintenance are scoped out ('handled separately'); "
            "the dashboard's own derived views are not data engineering. "
            "data_scientist (no statistical inference — trend reporting, not causal analysis), "
            "software_dev (building Metabase cards/views is not a deployable service), "
            "ml_engineer (no model), devops_mlops (no infra)."
        ),
        verified=True,
    ),
    EvalCase(
        id="sd-03",
        problem=(
            "Our data science team has delivered fraud_model_v3 — trained, evaluated, "
            "and signed off. Package it as a Docker image with a REST inference endpoint, "
            "run the production validation suite against a reference dataset, and register "
            "it in our model registry with evaluation metrics attached. "
            "No retraining, no CI/CD pipeline."
        ),
        expected_domains=["ml_engineer"],
        notes=(
            "Included: ml_engineer — packaging, production validation, model registration. "
            "The inference server lives inside the Docker image and serves only the model; "
            "ml_engineer owns both the serving layer and the packaging as a single deliverable. "
            "Excluded: data_scientist (model is already trained and signed off — research cycle "
            "is closed; 'no retraining' is explicit), "
            "devops_mlops ('no CI/CD pipeline' is explicit — packaging a Docker image is ML "
            "engineering, not deployment automation), "
            "data_engineer (no data pipeline — reference dataset is assumed available), "
            "software_dev (inference endpoint is part of ML packaging, not a user-facing service "
            "— it has no independent lifecycle outside the model image), "
            "analytics (no dashboard)."
        ),
        verified=True,
    ),
    EvalCase(
        id="sd-04",
        problem=(
            "Last month we changed the checkout flow for 50% of users in a holdout. "
            "Sessions, conversions, and revenue are already logged in analytics.events. "
            "Tell us whether the redesign caused the lift in conversion we observed, "
            "controlling for day-of-week effects and device type."
        ),
        expected_domains=["data_scientist"],
        notes=(
            "Included: data_scientist — causal inference, experiment evaluation, "
            "statistical controls. "
            "Excluded: analytics (not a dashboard or recurring report — this is a "
            "one-time inference question; exploratory queries and result visualization "
            "are subordinate steps inside the causal analysis, owned by the data_scientist), "
            "ml_engineer (no model to build or deploy), "
            "data_engineer (data already collected and logged), "
            "software_dev (no service), devops_mlops (no infra)."
        ),
        verified=True,
    ),
    EvalCase(
        id="sd-05",
        problem=(
            "Our FastAPI service is deployed manually today — zip the repo, SSH in, "
            "restart the process. Wire up a GitHub Actions pipeline that builds a Docker image "
            "on every push to main, pushes it to ECR, and deploys it to our ECS service. "
            "The application code and Dockerfile already exist."
        ),
        expected_domains=["devops_mlops"],
        notes=(
            "Included: devops_mlops — CI/CD pipeline, Docker build/push, ECS deployment. "
            "Excluded: software_dev (application code and Dockerfile already exist — no code changes; "
            "reviewing existing code for deployment readiness is a subordinate step owned by devops_mlops "
            "when setting up the pipeline, not an independent software engineering deliverable), "
            "data_engineer (no data pipeline), analytics (no analysis), "
            "ml_engineer (no model), data_scientist (no experimentation)."
        ),
        verified=True,
    ),
    EvalCase(
        id="sd-06",
        problem=(
            "Add a GET /users/{id}/orders endpoint to our FastAPI service. "
            "It queries orders and order_items from PostgreSQL, paginates results "
            "(default 20, max 100), and returns JSON. "
            "Authentication is handled by existing JWT middleware. No new database tables."
        ),
        expected_domains=["software_dev"],
        notes=(
            "Included: software_dev — API endpoint, service integration. "
            "Writing optimized SQL for a read-through API endpoint is a subordinate step "
            "of the endpoint implementation, owned by software_dev — it has no independent lifecycle. "
            "Excluded: data_engineer (no ETL or pipeline — this is a read-through API; "
            "'no new database tables' is explicit; querying existing tables from inside an API "
            "endpoint is application work, not data engineering), "
            "analytics (no analysis or dashboarding), "
            "devops_mlops (no deployment infrastructure asked — just build the endpoint), "
            "ml_engineer (no model), data_scientist (no experimentation)."
        ),
        verified=True,
    ),
]

# ---------------------------------------------------------------------------
# Two-to-three-domain (md-*)
# ---------------------------------------------------------------------------

MULTI_DOMAIN: list[EvalCase] = [
    EvalCase(
        id="md-01",
        problem=(
            "Pull daily spend and performance data from Google Ads, Facebook Ads, "
            "and HubSpot APIs and load it into marketing.ad_performance in our warehouse. "
            "Then build a Metabase dashboard showing spend, CPL, and ROAS per channel "
            "per week. No attribution modeling — just raw spend vs. leads."
        ),
        expected_domains=["data_engineer", "analytics"],
        notes=(
            "Included: data_engineer (multi-source API ingestion, warehouse load), "
            "analytics (Metabase dashboard, channel performance metrics). "
            "Excluded: data_scientist ('no attribution modeling' is explicit — no causal "
            "or statistical inference; data validation of a loaded pipeline is a data "
            "engineering concern, not a research activity), "
            "ml_engineer (no model), "
            "software_dev (ingestion is a pipeline, not a user-facing service), "
            "devops_mlops (no CI/CD or infra design asked; scheduling and monitoring are "
            "operational hooks inside the pipeline, owned by data_engineer)."
        ),
        verified=True,
    ),
    EvalCase(
        id="md-02",
        problem=(
            "We have a trained churn model (churn_v2.pkl) and labeled historical data. "
            "Retrain it weekly on the latest 6 months of data, run a holdout evaluation, "
            "promote it if AUC improves, and alert the ML team if input feature drift "
            "exceeds 10% PSI. The model serves predictions via existing batch jobs."
        ),
        expected_domains=["ml_engineer", "devops_mlops"],
        notes=(
            "Included: ml_engineer (operational retraining, holdout evaluation against "
            "a pre-agreed metric, model promotion), "
            "devops_mlops (weekly scheduling, drift alerting, promotion automation). "
            "Excluded: data_scientist (metric and promotion threshold are pre-agreed — "
            "'promote if AUC improves' is explicit; if the metric choice or threshold "
            "needed design justification, data_scientist would be added — the 10% PSI "
            "threshold is given, so implementing PSI monitoring is ml_engineer/devops_mlops work, "
            "not a research activity), "
            "data_engineer (no pipeline building asked — data is already available), "
            "analytics (drift alert is an ops concern, not a reporting dashboard), "
            "software_dev (existing batch jobs handle serving — no new service asked; "
            "'The model serves predictions via existing batch jobs' is explicit)."
        ),
        verified=True,
    ),
    EvalCase(
        id="md-03",
        problem=(
            "We split homepage traffic 50/50 for 3 weeks. Event logs are in "
            "analytics.page_events. Run significance tests on checkout conversion "
            "(primary metric) and session depth (guardrail metric). "
            "Then build time-series charts of both metrics across the test window "
            "so the product team sees the trend, not just the p-value."
        ),
        expected_domains=["data_scientist", "analytics"],
        notes=(
            "Included: data_scientist (significance testing, experiment evaluation), "
            "analytics (time-series charts, metric visualization for the product team — "
            "building charts for a product audience is an analytics deliverable, not a software service). "
            "Excluded: ml_engineer (no model), data_engineer (data already in analytics.page_events), "
            "software_dev (no service — time-series charts are not a deployable application), "
            "devops_mlops (no infra)."
        ),
        verified=True,
    ),
    EvalCase(
        id="md-04",
        problem=(
            "We track user clickstream events in Kafka. Compute 7-day rolling features "
            "per user (page views, add-to-cart rate, search count) and write them to a "
            "Redis feature store. Our recommendation model reads from that store at "
            "inference time. Include a backfill job for historical data and an online "
            "update path for live events."
        ),
        expected_domains=["data_engineer", "ml_engineer"],
        notes=(
            "Included: data_engineer (Kafka consumption, feature computation, Redis writes, "
            "backfill job), ml_engineer (feature store design for ML serving, inference integration). "
            "Excluded: devops_mlops (the feature store is data/ML infrastructure, not CI/CD "
            "or deployment pipeline — no scheduling or monitoring was asked; operational concerns "
            "such as lag monitoring and scheduling live inside the data_engineer pipeline unless a "
            "separate deployment or observability deliverable is explicitly requested), "
            "data_scientist (no experimentation — feature set is specified, consistent with "
            "md-02's pre-agreed-threshold logic), "
            "software_dev (not a user-facing API — the inference-time layer that reads features "
            "for the recommendation model is ml_engineer's serving integration, not a standalone service), "
            "analytics (no dashboard)."
        ),
        verified=True,
    ),
    EvalCase(
        id="md-05",
        problem=(
            "Stripe sends webhook events to POST /webhooks/stripe on "
            "payment_intent.succeeded, charge.refunded, and subscription.updated. "
            "The endpoint must acknowledge Stripe within 200ms, validate the signature, "
            "and stream the payload into raw.stripe_events in BigQuery via Pub/Sub. "
            "No downstream transformation yet."
        ),
        expected_domains=["software_dev", "data_engineer"],
        notes=(
            "Included: software_dev (webhook endpoint, async offload, signature validation), "
            "data_engineer (Pub/Sub streaming ingestion into BigQuery — Pub/Sub topic and "
            "BigQuery subscription setup are part of the pipeline deliverable, not infrastructure design). "
            "Excluded: analytics ('no downstream transformation' is explicit — no dashboard), "
            "devops_mlops (no CI/CD or infra design asked — just build the service and the pipe; "
            "monitoring and alerting are operational surface not requested by the problem), "
            "ml_engineer (no model), data_scientist (no experimentation)."
        ),
        verified=True,
    ),
    EvalCase(
        id="md-06",
        problem=(
            "Users acquired through paid search, organic, and referral in Q1 are tracked "
            "in events.user_activity. Build retention curves (30/60/90-day) per acquisition "
            "channel. Then test whether paid search users retain statistically differently "
            "from organic users at 30 days (two-proportion z-test or equivalent). "
            "Report both the visual and the p-value."
        ),
        expected_domains=["analytics", "data_scientist"],
        notes=(
            "Included: analytics (retention curve visualization per channel), "
            "data_scientist (significance test, statistical inference between groups). "
            "Excluded: ml_engineer (no predictive model — correlation/test only), "
            "data_engineer (data assumed available in events.user_activity — extracting "
            "from an existing table and computing retention flags is subordinate SQL work "
            "owned by analytics and data_scientist as part of their own analysis), "
            "software_dev (no service), devops_mlops (no infra)."
        ),
        verified=True,
    ),
    EvalCase(
        id="md-07",
        problem=(
            "Our prediction service is a Flask app at services/predictor/. "
            "Dockerize it with a multi-stage build and non-root user, and add a /health endpoint. "
            "Set up GitHub Actions: run pytest on PR, build and push the Docker image on merge, "
            "and deploy to EKS via kubectl rollout on merge to main. "
            "Model weights are already in S3."
        ),
        expected_domains=["devops_mlops", "software_dev"],
        notes=(
            "Included: devops_mlops (CI/CD pipeline, EKS deployment, Docker image promotion), "
            "software_dev (Dockerfile authoring, /health endpoint, service structure for containerization). "
            "Excluded: ml_engineer (model already exists and is in S3 — this is deployment, not training), "
            "data_engineer (no data pipelines — S3 path verification and IAM setup are subordinate steps "
            "owned by devops_mlops/software_dev as part of the deployment, not a data engineering task), "
            "analytics (no dashboards), data_scientist (no experimentation)."
        ),
        verified=True,
    ),
    EvalCase(
        id="md-08",
        problem=(
            "We log product_events (page_view, feature_used, export) to S3 as raw JSON. "
            "Build a pipeline aggregating them into weekly per-user feature counts in "
            "dw.user_engagement. Visualize the weekly trend per feature type. "
            "Then compute Pearson correlations between each feature count and 30-day churn "
            "(labeled in dw.user_labels) to rank which behaviors matter most."
        ),
        expected_domains=["data_engineer", "analytics", "data_scientist"],
        notes=(
            "Included: data_engineer (S3 ingestion, aggregation pipeline to dw.user_engagement), "
            "analytics (weekly trend visualization per feature type), "
            "data_scientist (Pearson correlations, churn signal ranking — statistical analysis). "
            "Excluded: ml_engineer (correlation ranking is not model deployment — no scoring "
            "pipeline asked; a logistic-regression 'validation' step is model-building scope creep "
            "that the problem — 'rank which behaviors matter most,' correlation only — does not ask for), "
            "software_dev (no service), devops_mlops (no CI/CD — scheduling/monitoring not requested)."
        ),
        verified=True,
    ),
    EvalCase(
        id="md-09",
        problem=(
            "Every night at 2am: pull the previous day's user activity from Snowflake, "
            "apply SQL transforms to produce inference-ready feature vectors, "
            "score them with churn_model_v3, write results to ml.churn_scores, "
            "and page on-call if more than 5% of the batch scores above 0.9. "
            "The model is already trained and serialized to S3. "
            "The 0.9 alert threshold is pre-agreed with the ML team."
        ),
        expected_domains=["data_engineer", "ml_engineer", "devops_mlops"],
        notes=(
            "Included: data_engineer (Snowflake pull, SQL feature transforms, result write-back — "
            "feature generation is SQL transforms, not feature registry logic), "
            "ml_engineer (model loading from S3, scoring logic, inference), "
            "devops_mlops (nightly scheduling, on-call alerting). "
            "Excluded: data_scientist (model already exists, alert threshold is pre-agreed — "
            "if the threshold needed design justification, data_scientist would be added), "
            "analytics ('page on-call' is an ops alert, not a reporting dashboard — "
            "the on-call page is operational infrastructure, not a visualization or reporting deliverable), "
            "software_dev (no user-facing service). "
            "Note: if feature generation involved a feature registry or feature engineering logic "
            "beyond SQL, ml_engineer would absorb that step and data_engineer's scope would shrink."
        ),
        verified=True,
    ),
    EvalCase(
        id="md-10",
        problem=(
            "Build POST /transactions/score: receives a transaction payload, runs it through "
            "our fraud model loaded in memory via ONNX runtime, and returns "
            "{risk_score, recommendation} in <50ms p99. Add rate limiting (100 req/s per API key), "
            "structured JSON logging, and a PagerDuty alert if the 5-min error rate exceeds 1%."
        ),
        expected_domains=["software_dev", "ml_engineer", "devops_mlops"],
        notes=(
            "Included: software_dev (REST endpoint, rate limiting, structured logging), "
            "ml_engineer (ONNX runtime integration — the <50ms p99 latency constraint "
            "requires ONNX-specific knowledge: batching strategy, memory management, "
            "runtime optimization; without the latency constraint, software_dev could "
            "absorb the ONNX integration as a black-box dependency), "
            "devops_mlops (PagerDuty alerting, error rate monitoring). "
            "Excluded: data_engineer (no data pipeline — synchronous inference, not batch), "
            "data_scientist (no experimentation — fraud model already exists), "
            "analytics (PagerDuty alert is ops, not a reporting dashboard — "
            "monitoring dashboards for an ops endpoint are devops_mlops territory, not business analytics)."
        ),
        verified=True,
    ),
    EvalCase(
        id="md-11",
        problem=(
            "Our pricing model (price_v4) uses behavioral features only. We have demographic "
            "data available. Design an offline evaluation: split a holdout, train a version "
            "with demographics added, compare RMSE and calibration curves. "
            "If the improvement is statistically significant (p<0.05 on a paired test), "
            "build and register price_v5. Include feature importance analysis."
        ),
        expected_domains=["data_scientist", "ml_engineer"],
        notes=(
            "Included: data_scientist (full research cycle — holdout design, significance threshold, "
            "train price_v5 with demographics, compare RMSE + calibration, feature importance, "
            "verdict on whether improvement is real — surfacing methodological risks like disparate "
            "impact and RMSE≠business-improvement is core data science, not orchestrator scope creep). "
            "ml_engineer (production cycle — validate price_v5 for production, register it). "
            "Handoff trigger: data_scientist delivers a trained, evaluated model with a clear verdict; "
            "ml_engineer takes it from there. "
            "Excluded: data_engineer (demographic features assumed available — no pipeline building), "
            "analytics (no dashboard asked), "
            "devops_mlops (no deployment to serving asked — registration is the handoff, not a rollout; "
            "model-registry registration is ml_engineer, deployment-to-serving is devops_mlops), "
            "software_dev (no service or API)."
        ),
        verified=True,
    ),
    EvalCase(
        id="md-12",
        problem=(
            "Analysts keep requesting one-off SQL pulls from engineers. "
            "Build an internal web app with a form to select date range, region, and product "
            "category, returning a downloadable CSV of order-level data from our warehouse. "
            "Parameterized queries only — no custom SQL input. Auth via existing Google SSO."
        ),
        expected_domains=["analytics", "software_dev"],
        notes=(
            "Included: analytics (report and metric design, query logic — 'which order-level fields, "
            "what filtering semantics for region/category' is analytics report-design, not pipeline-building), "
            "software_dev (web UI, parameterized query layer, CSV export, SSO integration). "
            "Excluded: data_engineer (data already in warehouse — no pipeline building; the parameterized "
            "query design belongs to analytics as query logic and software_dev as the data layer of the app), "
            "ml_engineer (no model), data_scientist (no statistical inference), "
            "devops_mlops (no CI/CD asked — just build the tool)."
        ),
        verified=True,
        gold_decomposition=[
            # the analytics row is the discriminating one (md-12's stable regression is
            # the orchestrator folding everything into software_dev, dropping analytics);
            # note it overlaps with Coverage, which already penalises the analytics drop.
            {"deliverable": "report and metric design: which order-level fields and filter semantics", "domain": "analytics"},
            {"deliverable": "web app form to select date range, region, and product category", "domain": "software_dev"},
            {"deliverable": "parameterized query layer for the app", "domain": "software_dev"},
            {"deliverable": "downloadable CSV export", "domain": "software_dev"},
            {"deliverable": "Google SSO authentication", "domain": "software_dev"},
        ],
    ),
    EvalCase(
        id="md-13",
        problem=(
            "We have 50k labeled support tickets across 8 categories. "
            "Fine-tune a BERT model on that dataset, evaluate it on a held-out split, "
            "and wrap it in a nightly batch scoring job that runs against new tickets "
            "and writes predictions to ml.ticket_predictions."
        ),
        expected_domains=["data_scientist", "ml_engineer"],
        notes=(
            "Included: data_scientist (fine-tuning and held-out evaluation are research-cycle "
            "acts — training and evaluation always belong to data_scientist regardless of how "
            "specified the approach is; a fully-specified 'fine-tune BERT' instruction is still "
            "data_scientist's domain — specification does not transfer ownership to another domain). "
            "ml_engineer (nightly batch scoring job + writing predictions to ml.ticket_predictions "
            "— this is the production artifact, the handoff point). "
            "Excluded: devops_mlops (batch scoring job is ML deployment, not CI/CD infra — "
            "the model-serving batch job belongs to ml_engineer; deployment automation belongs to devops_mlops), "
            "data_engineer (no pipeline building — data is already labeled), "
            "software_dev (not a user-facing API), analytics (no dashboard)."
        ),
        verified=True,
        gold_decomposition=[
            {"deliverable": "fine-tune BERT on labeled tickets", "domain": "data_scientist"},
            {"deliverable": "held-out evaluation",               "domain": "data_scientist"},
            {"deliverable": "nightly batch scoring job writing to ml.ticket_predictions", "domain": "ml_engineer"},
        ],
    ),
    EvalCase(
        id="md-14",
        problem=(
            "We're decommissioning our on-prem Hadoop cluster in 90 days. "
            "Re-platform all 14 Spark ETL jobs to AWS Glue or EMR; "
            "migrate Airflow DAGs and secrets to MWAA; "
            "run old and new pipelines in parallel for 2 weeks and validate parity "
            "using dbt tests and warehouse queries; "
            "cut over once confirmed. "
            "Existing Tableau dashboards must keep producing correct output throughout "
            "— analytics owns sign-off."
        ),
        expected_domains=["data_engineer", "devops_mlops", "analytics"],
        notes=(
            "Included: data_engineer (re-platform Spark ETL jobs, parallel run, "
            "dbt tests and warehouse queries for parity validation — diffing is "
            "warehouse-native, not custom scripting; Spark→Glue/EMR code conversion "
            "is data_engineer's re-platforming, not a software_dev build), "
            "devops_mlops (AWS infra setup, MWAA migration, secrets management, "
            "cutover automation), "
            "analytics (sign-off that Tableau dashboards keep producing correct output "
            "— analytics owns the dashboards, so they validate them even if no new "
            "dashboard is being built; sign-off responsibility is a real deliverable). "
            "Excluded: software_dev (parity validation is explicitly dbt tests and "
            "warehouse queries — no custom diffing scripts needed; ETL code conversion "
            "belongs to data_engineer who owns the pipelines, not software_dev), "
            "ml_engineer (no models), data_scientist (no experimentation — parity "
            "validation is deterministic row-count and aggregate reconciliation, "
            "not statistical inference)."
        ),
        verified=True,
    ),
    EvalCase(
        id="md-15",
        problem=(
            "Our dbt repo lives in GitHub. Wire up GitHub Actions so that "
            "dbt compile --select state:modified runs on every PR, "
            "the full dbt test suite runs on merge to main, "
            "and dbt run deploys to the production target on a version tag. "
            "No new dbt models needed."
        ),
        expected_domains=["devops_mlops", "data_engineer"],
        notes=(
            "Included: devops_mlops — GitHub Actions workflow configuration. "
            "Included: data_engineer — dbt project readiness for CI/CD (profiles.yml target setup, "
            "state comparison artifact logic, CI/CD environment config). A devops engineer owns the "
            "workflow files; a data engineer owns whether the dbt project supports them. "
            "Excluded: software_dev (no service or API), "
            "analytics (no analysis), ml_engineer (no model), data_scientist (no experimentation)."
        ),
    ),
]

# ---------------------------------------------------------------------------
# Broad (bd-*)
# ---------------------------------------------------------------------------

BROAD_DOMAIN: list[EvalCase] = [
    EvalCase(
        id="bd-01",
        problem=(
            "Launch product recommendations on our e-commerce homepage: "
            "instrument clickstream events for product views and add-to-carts; "
            "train a collaborative filtering model on 6 months of purchase history; "
            "package the trained model, integrate it into a recommendation serving layer, "
            "and monitor it for prediction drift; "
            "expose a GET /recommendations/{user_id} endpoint backed by that serving layer; "
            "deploy with A/B traffic splitting; "
            "build a dashboard tracking CTR and conversion lift vs. the control group."
        ),
        expected_domains=[
            "data_engineer",
            "data_scientist",
            "ml_engineer",
            "software_dev",
            "devops_mlops",
            "analytics",
        ],
        notes=(
            "Included: data_engineer (clickstream instrumentation and ingestion pipeline), "
            "data_scientist (train the collaborative filtering model — training always belongs "
            "to data_scientist regardless of how specified the approach is), "
            "ml_engineer (package the trained model, integrate into serving layer, monitor "
            "prediction drift — monitoring is ml_engineer per contract), "
            "software_dev (GET /recommendations/{user_id} endpoint — API contract, routing, auth), "
            "devops_mlops (A/B traffic splitting — routing infrastructure), "
            "analytics (CTR and conversion lift dashboard vs. control group). "
            "Boundary notes: ml_engineer owns drift monitoring; devops_mlops owns A/B routing "
            "infrastructure — these are deliberately split to test that distinction. "
            "software_dev owns the API surface; ml_engineer owns the inference layer behind it."
        ),
        verified=True,
        gold_decomposition=[
            {"deliverable": "instrument clickstream events and build ingestion pipeline", "domain": "data_engineer"},
            {"deliverable": "train collaborative-filtering model on purchase history", "domain": "data_scientist"},
            {"deliverable": "package the trained model and integrate into the serving layer", "domain": "ml_engineer"},
            {"deliverable": "monitor the model for prediction drift", "domain": "ml_engineer"},
            {"deliverable": "expose GET /recommendations/{user_id} endpoint", "domain": "software_dev"},
            {"deliverable": "deploy with A/B traffic splitting", "domain": "devops_mlops"},
            {"deliverable": "dashboard tracking CTR and conversion lift vs control", "domain": "analytics"},
        ],
    ),
    EvalCase(
        id="bd-02",
        problem=(
            "We want to predict and understand customer lifetime value: "
            "unify purchase, support, and engagement events from three source systems "
            "into a single customer-level dataset; "
            "identify which early behaviors are the strongest predictors of 12-month LTV "
            "using correlation and partial dependence; "
            "train a regression model to score new customers at day 7; "
            "package the model, integrate it into a weekly batch scoring pipeline, "
            "and monitor it for drift; "
            "automate the pipeline to run every Monday and alert on failures; "
            "surface the latest scores and key drivers in a weekly-refreshed executive dashboard."
        ),
        expected_domains=[
            "data_engineer",
            "data_scientist",
            "ml_engineer",
            "devops_mlops",
            "analytics",
        ],
        notes=(
            "Included: data_engineer (unify events from three source systems into a "
            "customer-level dataset), "
            "data_scientist (LTV predictor analysis via correlation and partial dependence, "
            "train the regression model — training always belongs to data_scientist), "
            "ml_engineer (package the model, integrate into batch scoring pipeline, "
            "monitor for drift), "
            "devops_mlops (weekly schedule automation, failure alerting — a weekly-refreshed "
            "dashboard powered by a scoring model implies a deployment pipeline; made explicit "
            "here to avoid ambiguity), "
            "analytics (executive dashboard surfacing scores and key drivers). "
            "Excluded: software_dev (no user-facing API or service asked)."
        ),
        gold_decomposition=[
            {"deliverable": "unify purchase, support, and engagement events from three source systems into a customer-level dataset", "domain": "data_engineer"},
            {"deliverable": "identify LTV predictors via correlation and partial dependence", "domain": "data_scientist"},
            {"deliverable": "train regression model to score customers at day 7", "domain": "data_scientist"},
            {"deliverable": "package model and integrate into weekly batch scoring pipeline", "domain": "ml_engineer"},
            {"deliverable": "prediction-drift monitoring", "domain": "ml_engineer"},
            {"deliverable": "automate weekly schedule and alert on failures", "domain": "devops_mlops"},
            {"deliverable": "executive dashboard surfacing scores and key drivers", "domain": "analytics"},
        ],
    ),
    EvalCase(
        id="bd-03",
        problem=(
            "Stand up an MLOps platform for our 4-person ML team from scratch: "
            "orchestrate feature pipelines and training runs with Airflow; "
            "track experiments with MLflow; "
            "define the promotion criteria — metric, threshold, and statistical test "
            "that determines when a challenger beats the champion; "
            "automate model promotion, Docker build, and rollout to the serving cluster "
            "when criteria are met; "
            "monitor model performance and feature drift per model, and monitor serving "
            "infrastructure for latency and error rate."
        ),
        expected_domains=[
            "data_engineer",
            "data_scientist",
            "ml_engineer",
            "devops_mlops",
        ],
        notes=(
            "Included: data_engineer (feature pipelines orchestrated with Airflow), "
            "data_scientist (define promotion criteria — metric, threshold, statistical test; "
            "'beats the champion' requires design, not just automation; if criteria were "
            "pre-defined, data_scientist would be excluded), "
            "ml_engineer (training infrastructure, MLflow experiment tracking, model "
            "performance and drift monitoring per model), "
            "devops_mlops (Docker build/push, rollout automation, serving infra monitoring "
            "for latency and error rate). "
            "Excluded: analytics (no data analysis phase — monitoring dashboard is model "
            "health owned by ml_engineer and infra health owned by devops_mlops), "
            "software_dev (no user-facing API or service)."
        ),
        gold_decomposition=[
            {"deliverable": "orchestrate feature pipelines with Airflow", "domain": "data_engineer"},
            {"deliverable": "define promotion criteria: metric, threshold, and statistical test for challenger vs champion", "domain": "data_scientist"},
            {"deliverable": "track experiments with MLflow and training infrastructure", "domain": "ml_engineer"},
            {"deliverable": "monitor model performance and feature drift per model", "domain": "ml_engineer"},
            {"deliverable": "automate model promotion, Docker build, and rollout to serving cluster", "domain": "devops_mlops"},
            {"deliverable": "monitor serving infrastructure for latency and error rate", "domain": "devops_mlops"},
        ],
    ),
]

# ---------------------------------------------------------------------------
# Full suite
# ---------------------------------------------------------------------------

ALL_CASES: list[EvalCase] = SINGLE_DOMAIN + MULTI_DOMAIN + BROAD_DOMAIN
