# Platform and operations crossovers

Scope: running application code, splitting code into deployable units, running scheduled and background jobs, collecting logs and metrics, and storing and delivering secrets.
Use: open this file only after the components of the input design are listed. Use it to look up bands, costs, and sources. Do not use it to decide which components to discuss.

## Run application code
Contract that matters: requests are served at the required uptime; a deploy replaces the running version without dropping requests; failed instances restart on their own; the team can patch, upgrade, and debug the runtime without outside help.
Axes that usually bind: team_ops_capacity, availability, cost

| Band | Option family (examples) | Why it fits | Breaks when | Evidence |
|---|---|---|---|---|
| Load fits on one machine, plus a second for failover; the team will own OS patching and deploy scripts | Virtual machines or bare servers with a process manager behind a load balancer (systemd plus a reverse proxy; Kamal-style deploy tools) | Cheapest and simplest. A few machines carry a lot: one large Q&A site served about 209 million HTTP requests a day from 9 web servers in 2016 and said 1 server could carry the load | Uptime, not load: one cloud's SLA for a single instance is 99.5% a month (about 3.6 hours of allowed downtime); its 99.99% SLA applies only to instances in 2 or more zones | source: https://nickcraver.com/blog/2016/02/17/stack-overflow-the-architecture-2016-edition/ ; source: https://aws.amazon.com/compute/sla/ |
| One or a few deployable units; no engineer assigned to the platform | Managed application platform or serverless containers (Heroku, Cloud Run, App Runner); functions for short event handlers | No cluster to upgrade; rollouts, TLS, and scale-out are built in. One platform's monthly free tier (request-based billing) is 180,000 vCPU-seconds, 360,000 GiB-seconds, and 2 million requests | Platform limits: one platform defaults to 100 instances per region (raisable), 60-minute requests, and 8 vCPU with 32 GiB per instance; functions stop at 15 minutes; GPUs, sidecars, or custom networking push you out. Under steady round-the-clock load, per-second pricing often costs more than reserved machines | source: https://cloud.google.com/run/pricing ; source: https://cloud.google.com/run/quotas ; source: https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html ; rule of thumb (band and cost crossover): no engineer assigned to the platform, stateless web and worker processes; list prices, no committed-use discount, steady 24×7 utilization |
| Many services and several teams share one fleet; a platform team owns the cluster | Container orchestration, usually with a managed control plane (Kubernetes on EKS, GKE, or AKS; Nomad) | One API for scheduling, rollout, and discovery across teams. Bin-packing saves machines at fleet scale: Google measured that splitting prod and non-prod work into separate cells would need 20–30% more machines in the median cell | Per-cluster design limits: 5,000 nodes, 150,000 pods, 110 pods per node; past that, run several clusters | source: https://research.google/pubs/large-scale-cluster-management-at-google-with-borg/ ; source: https://kubernetes.io/docs/setup/best-practices/cluster-large/ ; rule of thumb (band): a platform team owns upgrades, add-ons, and on-call for the cluster; conditions: many services from several product teams |

Traps:
- Orchestration for one small team is the usual substitute-down case, and the binding axis is team_ops_capacity, not cost. The control-plane fee is small: one managed offering charges $0.10 per cluster-hour (about $73 a month) for 14 months of standard support per version, then $0.60 an hour during up to 12 months of extended support (source: https://aws.amazon.com/eks/pricing/); another gives each billing account a monthly credit equal to one zonal or Autopilot cluster's fee (source: https://cloud.google.com/kubernetes-engine/pricing). The work is the upgrade treadmill, about three minor releases a year, each patched for roughly 12 months (source: https://kubernetes.io/releases/release/), plus ingress, DNS, autoscaling, and certificate add-ons that need an owner.
- Functions chained by a workflow service on a hot data path: Prime Video's stream-monitoring tool hit a hard scaling limit at about 5% of expected load, and moving its components into one process on containers cut infrastructure cost by over 90% (source: https://web.archive.org/web/20231230202019/https://www.primevideotech.com/video-streaming/scaling-up-the-prime-video-audio-video-monitoring-service-and-reducing-costs-by-90).
- The single machine fails on availability long before throughput. The Q&A site above ran 9 web servers for redundancy and headroom, not for load.

## Split code into deployable units
Contract that matters: a change ships without waiting on unrelated work; module boundaries are enforced so the code stays changeable; every deployable unit has an owner who is on call for it; a fault in one area is contained or rolled back fast.
Axes that usually bind: team_ops_capacity, change_rate, isolation_compliance

| Band | Option family (examples) | Why it fits | Breaks when | Evidence |
|---|---|---|---|---|
| One team (a "two-pizza" team is fewer than 10 people) up to several teams on one release train; one company runs a modular monolith that more than 1,000 developers have worked on | Modular monolith: one repository, one build, one pipeline; modules with enforced public interfaces (Packwerk-style boundary checks, Java modules, internal packages); web and worker as process types of the same build | One pipeline and one set of infrastructure; in-process calls; cheap refactors while boundaries are still being found. Segment merged 140+ services into one after 3 full-time engineers spent most of their time keeping them alive; afterwards one engineer could deploy in minutes, and shared-library improvements rose from 32 to 46 the next year | Teams need different release cadences, separate scaling, or fault isolation that one process cannot give: a single regression takes everything down, deploys turn slow and risky, teams cannot ship on their own | source: https://aws.amazon.com/executive-insights/content/amazon-two-pizza-team/ ; source: https://www.twilio.com/en-us/blog/developers/best-practices/goodbye-microservices ; source: https://shopify.engineering/deconstructing-monolith-designing-software-maximizes-developer-productivity |
| Many teams that must deploy independently; Uber split as it grew from tens to hundreds of engineers | Services along team and domain boundaries, each owned by one team; at large counts, grouped behind domain gateways | Independent deploys, independent scaling, and clear ownership | Service count outgrows understanding: at about 2,200 critical services, one Uber investigation crossed about 50 services and 12 teams; Uber then grouped its services into about 70 domains | source: https://www.uber.com/blog/microservice-architecture/ |

Traps:
- Many services for one small team is the usual substitute-down case. Each unit adds a pipeline, alerts, an on-call surface, and shared-library version drift; Segment's overhead "increased linearly with each added destination" (source above). Rule of thumb: keep independently deployed units at or below the number of teams that can own them on call (conditions: each unit has its own pipeline, alerts, and on-call rotation).
- The first symptoms of a big codebase (unrelated test failures, slow CI, steep onboarding) are boundary problems. Shopify fixed them by modularizing inside one deploy unit, not by splitting (source above). Moving code between services is much harder than inside one codebase (source: https://martinfowler.com/bliki/MonolithFirst.html), and services that must deploy together are a "networked monolith" (Uber, above).
- A small team can still need a split for isolation_compliance. Without segmentation the entire network is in PCI DSS scope; segmentation is one way to shrink it, and outsourcing card handling to a provider is another (source: https://listings.pcisecuritystandards.org/documents/Guidance-PCI-DSS-Scoping-and-Segmentation_v1.pdf).
- Merging costs fault isolation: a crash in one module takes the process down (Segment's stated trade-off). Separate web and worker processes from one build win some of it back.

## Run scheduled and background jobs
Contract that matters: each job runs at least once per schedule window; a duplicate or missed run is harmless (idempotent) or detected; a run does not overlap itself unless allowed; failures and the time of the last success are visible.
Axes that usually bind: availability, change_rate, team_ops_capacity, cost

| Band | Option family (examples) | Why it fits | Breaks when | Evidence |
|---|---|---|---|---|
| Independent jobs, each much shorter than its interval, where a rare missed or doubled run is harmless or caught | One scheduler calling idempotent commands (crontab on one host, platform scheduler add-ons, cloud scheduler services, orchestrator cron jobs) | Almost free, nothing to run: one cloud scheduler charges $0.10 per job per 31 days after 3 free jobs per billing account | Delivery is best effort: one platform's scheduler may skip a job or run it twice and stops a run at its interval; orchestrator cron may create two jobs or none, and after more than 100 missed schedules it does not start the job | source: https://cloud.google.com/scheduler/pricing ; source: https://devcenter.heroku.com/articles/scheduler ; source: https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/ |
| Work triggered by user actions plus recurring jobs; one production system runs about 20 million jobs a day this way | Job queue in the relational database already in use, with a built-in recurring scheduler (Solid Queue, GoodJob, Oban, River); workers claim rows with `FOR UPDATE SKIP LOCKED` | No new infrastructure; retries, delays, and concurrency limits included; when the queue shares the database, a job can commit in the same transaction as the data change (its README calls this a sharp tool) | Queue traffic competes with the main database. At about 20 million jobs a day, that system runs the queue in its own database (32 CPUs, 64 GB) with 800 workers on 74 VMs in two datacenters: the queue has become a system someone owns | source: https://www.postgresql.org/docs/current/sql-select.html ; source: https://github.com/rails/solid_queue ; source: https://dev.37signals.com/solid-queue-v1-0/ |
| Interdependent pipelines with backfills, owned by several teams | Workflow orchestrator, usually managed (Airflow, Dagster, Temporal; MWAA, Cloud Composer) | Task dependencies, per-task retries, backfills of past runs, rerun of only the failed tasks, one view across teams | Last band; it is built for batch workflows, not request paths | source: https://airflow.apache.org/docs/apache-airflow/stable/index.html |

Traps:
- An orchestrator for nightly scripts that do not depend on each other: a small managed environment on one cloud costs $0.49 an hour (about $365 a month) before extra workers (source: https://aws.amazon.com/managed-workflows-for-apache-airflow/pricing/), against $0.10 per job per 31 days for a scheduler (source above).
- Plain cron on two hosts "for availability" runs every job twice. A database-backed scheduler can run on several hosts because, with default settings, a unique index on task and run time admits one enqueue per slot (Solid Queue README, above). Either way, alert on the last successful run, which Prometheus guidance calls the key metric of a batch job (source: https://prometheus.io/docs/practices/instrumentation/).
- Long work inside the scheduled process: one platform says anything longer than a couple of minutes belongs on a worker (Heroku Scheduler docs, above). Enqueue it instead.

## Collect and query logs and metrics
Contract that matters: the application writes structured events to stdout and never routes or stores them itself; on-call engineers can search recent events and graph metrics within minutes; retention covers debugging and audit needs; alerts fire on user-facing symptoms.
Axes that usually bind: cost, data_volume, team_ops_capacity

| Band | Option family (examples) | Why it fits | Breaks when | Evidence |
|---|---|---|---|---|
| From zero up to an ingest bill that rivals the cost of the engineers who would run a pipeline | Hosted logs and metrics: the platform's built-in tools or a service billed per GB and per series (CloudWatch, Grafana Cloud, Datadog, Honeycomb) | Nothing to run. Free tiers cover early volume: one cloud includes 5 GB of log data a month; one hosted service includes 50 GB of logs, 10,000 active series, and 14-day retention. Above that, one cloud lists $0.50 per GB ingested and $0.03 per GB-month archived | The bill tracks traffic: 1 TB of logs a day is about $15,000 a month at the $0.50 list price, and teams start dropping logs to stay in budget | source: https://aws.amazon.com/cloudwatch/pricing/ ; source: https://grafana.com/pricing/ ; rule of thumb (crossover point): compare the monthly bill with the loaded cost of a team that runs storage clusters; list prices, no volume discount |
| Multi-terabyte days across thousands of services; a dedicated observability team | Self-hosted pipeline: shipper, buffer, and a columnar store or object storage with an index (ClickHouse-style); a horizontally scaled time-series store for metrics | Uber's search-index stack could ingest only part of its logs. Its columnar replacement takes millions of logs a second, stores several PB, and cut hardware cost by more than half; in its test one columnar node ingested about 300,000 logs a second, about ten times one search node | Last band | source: https://www.uber.com/blog/logging/ |

Traps:
- High-cardinality labels: user IDs or request IDs in metric labels multiply series. Prometheus guidance: keep a metric's cardinality below 10 and look for alternatives past 100; a per-user metric for 10,000 users on 10,000 nodes reaches tens of millions of series (source: https://prometheus.io/docs/practices/instrumentation/). Put those fields in logs or traces.
- A self-hosted log search cluster at small volume: a resilient cluster needs at least three master-eligible nodes (source: https://www.elastic.co/docs/deploy-manage/production-guidance/availability-and-resilience/resilience-in-small-clusters); at Uber's scale the same stack meant 20+ clusters and 50+ ingest pipelines per region, and only 5% of indexed fields were used (Uber, above).
- Emission is a keep at every scale: write to stdout and let the platform route the stream (source: https://12factor.net/logs). An application that ships logs straight to a vendor couples every service to that vendor.

## Store and deliver secrets
Contract that matters: secrets never sit in code, images, or the repository; each workload reads only its own secrets; every read and change is audited; rotation needs no code change; the store is available when workloads start.
Axes that usually bind: isolation_compliance, availability, team_ops_capacity

| Band | Option family (examples) | Why it fits | Breaks when | Evidence |
|---|---|---|---|---|
| One cloud, from 1 secret to the store's quota (one provider: 500,000 secrets per region, 10,000 reads a second) | The cloud's managed secret store with per-workload identity and audit logs (AWS Secrets Manager, Google Secret Manager, Azure Key Vault); read at process start, cache in memory, refresh on rotation | Encryption, access policy, audit, and rotation hooks are built in, and cost scales with use: $0.40 per secret a month plus $0.05 per 10,000 calls, about $6 a month for 15 secrets and about $4,060 for 10,000 | Not on a scale axis in this range. It changes for geography or compliance: workloads span clouds or on-premises sites, or policy demands short-lived dynamic credentials across many systems; then a dedicated secret engine, often hosted | source: https://aws.amazon.com/secrets-manager/pricing/ ; source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/reference_limits.html |

Traps:
- Orchestrator secret objects are not a secret store by default: they sit unencrypted in etcd, and anyone allowed to create a Pod in a namespace can read every Secret in it (source: https://kubernetes.io/docs/concepts/configuration/secret/).
- Self-hosting a secret engine "to stay cloud-neutral" with a small team: the reference design is 5 nodes across 3 zones (it survives losing 2), small nodes with 2–4 cores and 8–16 GB RAM, under 8 ms between zones, plus audit-log disks and careful node replacement (source: https://developer.hashicorp.com/vault/tutorials/day-one-raft/raft-reference-architecture).
- Fetching a secret on every request: at 1,000 requests a second that is about 2.6 billion calls a month, about $13,000 at $0.05 per 10,000 calls, and a tenth of the 10,000-per-second read quota (pricing and quota pages above).
- Environment variables leak: one platform logs scheduled commands with config values expanded and warns against referencing secrets in them (Heroku Scheduler docs, above). Litmus test: could the code be made open source today without leaking a credential (source: https://12factor.net/config)?

## Sources
- Stack Overflow: The Architecture, 2016 Edition — https://nickcraver.com/blog/2016/02/17/stack-overflow-the-architecture-2016-edition/
- Amazon Compute Service Level Agreement — https://aws.amazon.com/compute/sla/
- Cloud Run pricing — https://cloud.google.com/run/pricing
- Cloud Run quotas and limits — https://cloud.google.com/run/quotas
- Lambda quotas — https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html
- Large-scale cluster management at Google with Borg (EuroSys 2015) — https://research.google/pubs/large-scale-cluster-management-at-google-with-borg/
- Considerations for large clusters (Kubernetes) — https://kubernetes.io/docs/setup/best-practices/cluster-large/
- Kubernetes release cycle — https://kubernetes.io/releases/release/
- Amazon EKS pricing — https://aws.amazon.com/eks/pricing/
- Google Kubernetes Engine pricing — https://cloud.google.com/kubernetes-engine/pricing
- Scaling up the Prime Video audio/video monitoring service and reducing costs by 90% (archived copy) — https://web.archive.org/web/20231230202019/https://www.primevideotech.com/video-streaming/scaling-up-the-prime-video-audio-video-monitoring-service-and-reducing-costs-by-90
- Powering Innovation and Speed with Amazon's Two-Pizza Teams — https://aws.amazon.com/executive-insights/content/amazon-two-pizza-team/
- Goodbye Microservices: From 100s of problem children to 1 superstar (Segment) — https://www.twilio.com/en-us/blog/developers/best-practices/goodbye-microservices
- Deconstructing the Monolith (Shopify) — https://shopify.engineering/deconstructing-monolith-designing-software-maximizes-developer-productivity
- Introducing Domain-Oriented Microservice Architecture (Uber) — https://www.uber.com/blog/microservice-architecture/
- Monolith First (Martin Fowler) — https://martinfowler.com/bliki/MonolithFirst.html
- Guidance for PCI DSS Scoping and Network Segmentation (PCI SSC) — https://listings.pcisecuritystandards.org/documents/Guidance-PCI-DSS-Scoping-and-Segmentation_v1.pdf
- Cloud Scheduler pricing — https://cloud.google.com/scheduler/pricing
- Heroku Scheduler — https://devcenter.heroku.com/articles/scheduler
- CronJob (Kubernetes) — https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/
- SELECT, the locking clause (PostgreSQL) — https://www.postgresql.org/docs/current/sql-select.html
- Solid Queue README — https://github.com/rails/solid_queue
- Solid Queue 1.0 released (37signals) — https://dev.37signals.com/solid-queue-v1-0/
- What is Airflow? — https://airflow.apache.org/docs/apache-airflow/stable/index.html
- Amazon MWAA pricing — https://aws.amazon.com/managed-workflows-for-apache-airflow/pricing/
- Instrumentation (Prometheus) — https://prometheus.io/docs/practices/instrumentation/
- Amazon CloudWatch pricing — https://aws.amazon.com/cloudwatch/pricing/
- Grafana Cloud pricing — https://grafana.com/pricing/
- Fast and Reliable Schema-Agnostic Log Analytics Platform (Uber) — https://www.uber.com/blog/logging/
- Resilience in small clusters (Elasticsearch) — https://www.elastic.co/docs/deploy-manage/production-guidance/availability-and-resilience/resilience-in-small-clusters
- The Twelve-Factor App: Logs — https://12factor.net/logs
- The Twelve-Factor App: Config — https://12factor.net/config
- AWS Secrets Manager pricing — https://aws.amazon.com/secrets-manager/pricing/
- AWS Secrets Manager quotas — https://docs.aws.amazon.com/secretsmanager/latest/userguide/reference_limits.html
- Secrets (Kubernetes) — https://kubernetes.io/docs/concepts/configuration/secret/
- Vault with integrated storage reference architecture (HashiCorp) — https://developer.hashicorp.com/vault/tutorials/day-one-raft/raft-reference-architecture
