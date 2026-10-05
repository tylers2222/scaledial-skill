# Consistency crossovers

Scope: jobs where a wrong answer is lost money, oversold stock, or a duplicate charge: recording money movements, decrementing scarce stock under concurrent orders, making API writes idempotent, writing in more than one region, and keeping derived copies (replicas, search indexes, caches, analytics stores) in agreement with the system of record.
Use: open this file only after the components of the input design are listed. Use it to look up bands, costs, and sources. Do not use it to decide which components to discuss.

## Record money movements (double-entry ledger)

Contract that matters: the entries of each transaction sum to zero and commit together; entries are append-only; a sufficient-funds check and the debit it guards are serialized per account; no committed entry is lost.
Axes that usually bind: consistency, contention (new axis: writes per second on one row or key, such as a hot account), throughput, durability

| Band | Option family (examples) | Why it fits | Breaks when | Evidence |
|---|---|---|---|---|
| 0 to low thousands of transfers/s on one primary; no account on most transfers | One relational database: entries table plus a per-account balance row updated in the same transaction (PostgreSQL, MySQL) | Atomic multi-row commits, check constraints, and row locks give the whole contract. Published runs: about 10,600 transfers/s with 50 accounts on a laptop, about 1,600/s on a 2 vCPU hosted instance across a WAN; one ledger vendor held 1,200 transactions (4,800 entries)/s plus 3,600 balance reads/s | One account (settlement, fees, revenue) is on most transfers and its balance row becomes a lock queue: write latency spikes | source: https://www.pgrs.net/2025/05/16/pgledger-in-postgresql-is-fast/ (M3 laptop, stock PostgreSQL 17.5, 20 workers; 2 vCPU / 8 GB hosted instance); source: https://www.moderntreasury.com/journal/behind-the-scenes-how-we-built-ledgers-for-high-throughput |
| Hot accounts at hundreds of transfers/s; total still fits one primary | Same database: lock only entries that carry a balance condition; queue the other hot-account entries and apply them to the balance in batches | Removes the lock queue and keeps balanced, atomic transactions; one vendor applies queued entries with p90 of 1 s | Total writes or data size outgrow one primary even with batching | source: https://www.moderntreasury.com/journal/behind-the-scenes-how-we-built-ledgers-for-high-throughput; source: https://softwaremill.com/tigetbeetle-vs-postgresql-performance-benchmark-harness-cloud-tests/ (GCP 4 vCPU / 32 GB nodes, primary + 2 synchronous standbys: about 2,900 to 3,100 transfers/s at moderate skew, 750 to 980/s at heavy hotspot skew) |
| Sustained tens of thousands of transfers/s and up (payment switches, very large processors) | Purpose-built debit/credit engine with batched, lock-free execution (TigerBeetle), or customer-sharded ledger cells | Batching amortizes replication and removes row locks: about 100,000 transfers/s in the same 3-node cloud setup | Transfers between cells need a two-phase or saga protocol; ad hoc queries move to another store | source: https://softwaremill.com/tigetbeetle-vs-postgresql-performance-benchmark-harness-cloud-tests/; source: https://tigerbeetle.com/blog/2026-09-17-performant-use-of-tigerbeetle/ (vendor benchmark, TPC-A-style hot rows: about 450,000 transactions/s with large batches vs about 7,000/s for a stored-procedure SQL baseline; vendor calls these rough order-of-magnitude figures) |

Traps:
- Distributed SQL does not cure hot accounts. Optimistic engines abort the loser of each same-row race, and their vendors advise against single-key contention (source: https://docs.aws.amazon.com/aurora-dsql/latest/userguide/working-with-concurrency-control.html); consensus engines hold each lock for at least one replication round trip.
- An event stream with asynchronous balance projections, or a cache that holds balances, cannot serialize a funds check with its debit. Two concurrent debits can both pass.
- Copying a giant's ledger copies the wrong contract. A ledger that sees five billion events/day and verifies 99.99% of dollar volume within four days is an asynchronous audit system, not a synchronous balance authority (source: https://stripe.dev/blog/ledger-stripe-system-for-tracking-and-validating-money-movement).

## Keep stock counts correct under concurrent orders

Contract that matters: never sell more units than exist; a reservation and the final stock deduction commit together; never refuse a buyer while sellable stock exists; abandoned reservations expire.
Axes that usually bind: contention, consistency, latency

| Band | Option family (examples) | Why it fits | Breaks when | Evidence |
|---|---|---|---|---|
| Up to roughly hundreds of purchases/s on any single item | Conditional decrement of one row per item, in the database that holds orders (`UPDATE ... SET qty = qty - n WHERE qty >= n`) | In read-committed mode a blocked updater re-checks the WHERE clause against the newest row version, so the last unit cannot sell twice; order and stock commit in one transaction | A flash sale puts most checkouts on one item. They queue on one row lock, and one row sustains about 1 / (lock hold time) updates/s | source: https://www.postgresql.org/docs/current/transaction-iso.html; rule of thumb: about 1,500 updates/s on one row, derived from the pgledger 10-account run (7,559 transfers/s × 2 rows ÷ 10 rows; laptop, one short in-database transaction per transfer); far fewer when the application holds the lock across network round trips or commits wait for a synchronous standby |
| Flash sales: one item takes a large share of checkouts | One row per sellable unit in a bounded pool, refilled from the stock ledger and claimed with `SELECT ... FOR UPDATE SKIP LOCKED`, in the same database as the stock ledger | Concurrent buyers lock different rows instead of queuing on one, and reservation and claim stay in one ACID transaction. One large commerce platform caps the pool at 1,000 rows per item and location | The pool empties faster than refill (refill takes a lock and buyers wait); database connections become the next limit | source: https://shopify.engineering/scaling-inventory-reservations |

Traps:
- Moving the counter to an in-memory store (DECR/INCR) splits reservation and stock ledger into two systems. The claim step cannot be atomic, which causes oversell or undersell (source: https://shopify.engineering/scaling-inventory-reservations), and asynchronous replication can lose acknowledged decrements on failover (source: https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/). This is a substitute-down case: the platform above moved reservations from the cache into the relational database that holds its stock ledger.
- Optimistic-concurrency distributed SQL turns the hot-row queue into aborts (SQLSTATE 40001) and client retries (source: https://docs.aws.amazon.com/aurora-dsql/latest/userguide/working-with-concurrency-control.html).
- Partitioned key-value stores cap one key: a partition serves at most 1,000 writes/s for items up to 1 KB (source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html). Splitting a count into N shard rows multiplies the write rate by about N (source: https://firebase.google.com/docs/firestore/solutions/counters), but each shard must enforce its own floor and buyers need fallback to other shards, or you undersell.

## Make API writes idempotent

Contract that matters: a retry with the same key takes effect at most once and returns the first response; the same key with different parameters is rejected; a concurrent duplicate gets a conflict, not a second execution; keys live longer than any client retry window.
Axes that usually bind: consistency, durability, data_volume

| Band | Option family (examples) | Why it fits | Breaks when | Evidence |
|---|---|---|---|---|
| Every scale in range, from a few requests/day to payment-processor volume | Key table with a unique constraint on (account, key), written in the same database transaction as the effect; store the response and a request fingerprint; prune after the retry window (at least 24 hours at one large payments API); shard the key table by key when one database is not enough | The unique constraint settles concurrent duplicates. One commit means "key recorded" and "effect applied" cannot disagree. Keys have high cardinality and spread evenly, so sharding by key works | Does not break on volume. The shape changes only when the effect is a call to another system: split the request into atomic local phases with recovery points, and send your own key downstream | source: https://docs.stripe.com/api/idempotent_requests; source: https://brandur.org/idempotency-keys; source: https://medium.com/airbnb-engineering/avoiding-double-payments-in-a-distributed-payments-system-2981f6b070bb |

Traps:
- A separate fast key store (a cache or a standalone idempotency service) commits the key and the effect in different systems; eviction, expiry, or failover loss then produces a duplicate charge. One payments team rejected a standalone service because it "would suffer from the same problems it was originally intended to solve" (source: Airbnb, above).
- Reading keys from a replica: a few seconds of replica lag make a completed payment look new, and it runs again (source: Airbnb, above).
- Holding a database transaction open across the remote call exhausts the connection pool. Keep network calls outside database phases (source: Airbnb, above).
- Checking the key only: compare request parameters too, and reject a reused key with different parameters (source: Stripe, above).

## Write in more than one region

Contract that matters: committed writes survive the loss of a region up to a stated recovery point objective (RPO); invariants such as balanced entries and no overdraft hold across regions; commit latency stays within budget.
Axes that usually bind: availability, geography, latency, team_ops_capacity

| Band | Option family (examples) | Why it fits | Breaks when | Evidence |
|---|---|---|---|---|
| Availability target up to 99.95 to 99.99% per month; region-loss RPO of seconds and RTO of minutes acceptable | One write region: primary with a synchronous standby in a second zone, plus an asynchronous replica or continuous backup in another region | One serial commit order and in-region latency. Managed offerings publish 99.95% for multi-zone instances and 99.99% for regional distributed SQL; cross-region asynchronous copies typically give RPO in seconds and RTO in minutes | The business requires zero loss on region failure (RPO = 0) or 99.999%; or distant users need writes faster than one inter-region round trip | source: https://aws.amazon.com/rds/sla/; source: https://cloud.google.com/spanner/sla; source: https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-global-database-disaster-recovery.html |
| Customers on several continents, or data-residency rules | Home-region partitioning: each customer's rows live in, and are written in, one region; read-mostly reference data is replicated everywhere | Local write latency for most requests; each row keeps one serial order | Transfers between customers with different home regions need a cross-region protocol | source: https://www.cockroachlabs.com/docs/stable/table-localities |
| RPO = 0 on region loss, or 99.999% per month | Consensus replication across at least 3 regions (multi-region distributed SQL; strongly consistent multi-region tables) | A write is acknowledged only after replicas in other regions hold it | Every write pays at least one inter-region round trip (P50 about 66 to 73 ms between US east and west, about 17 ms between West Europe and North Europe); a row updated serially sustains at most about 1 / RTT updates/s (about 14/s at 70 ms) | source: https://www.cockroachlabs.com/docs/stable/multiregion-survival-goals; source: https://learn.microsoft.com/en-us/azure/networking/azure-network-latency (Azure backbone, 30-day P50, July 2026); rule of thumb: 1 / RTT assumes each update waits for the previous cross-region commit on that row |

Traps:
- Substitute down for small scale. Two-region active-active with asynchronous replication resolves concurrent writes to one item by last writer wins, and multi-item transactions are atomic only in the region that ran them, so other regions can see them half-applied (source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/V2globaltables_HowItWorks.html). For a ledger that is unbalanced or lost money.
- RPO = 0 needs a third region. Strongly consistent multi-region tables run in exactly three regions and do not support transactions (source: DynamoDB global tables, above); region survival in distributed SQL needs at least three regions (source: CockroachDB survival goals, above).
- Most of the cost is people: three regions of capacity, cross-region failover drills, and retry handling on every transaction. For a small team, one region plus a tested restore usually meets a 99.95 to 99.99% target (source: the RDS and Spanner SLAs, above).

## Keep derived copies in agreement with the system of record

Contract that matters: each copy (replica, search index, cache, analytics store) converges to committed data within a stated lag and never shows an older version after a newer one; no committed change is silently lost; reads that must be exact (balances, stock) go to the system of record; heavy reads never slow or block its writes.
Axes that usually bind: consistency, data_volume, fan_out, change_rate

| Band | Option family (examples) | Why it fits | Breaks when | Evidence |
|---|---|---|---|---|
| Reads, search features, and report scans fit the database and its replicas | No second store: indexed queries, the database's own full-text index with ranking, and streaming read replicas for heavy reads | Nothing to keep in agreement except replica lag; replica reads see one snapshot | Read load or search features outgrow the database, or report scans run for minutes: replay conflicts cancel replica queries after 30 s by default, and the workaround (`hot_standby_feedback`) bloats the primary | source: https://www.postgresql.org/docs/current/textsearch-intro.html; source: https://www.postgresql.org/docs/current/hot-standby.html; source: https://www.postgresql.org/docs/current/runtime-config-replication.html |
| Beyond that | Separate search index, cache, or column store fed from the database's commit log (change data capture) or an outbox table written in the same transaction; version-checked upserts; idempotent consumers; periodic reconciliation of totals | The log fixes one order for all writers, which removes dual-write races, and the outbox row commits with the business row. Column stores scan large histories much faster: on one 16 vCPU / 32 GiB VM, an untuned row store took about 258 s to count 100 million rows (106 GB), while a column store ran all 43 queries in about 26 s | Never exact at read time: search engines expose writes after a refresh (within about 1 s by default) and consumers can lag; very large fleets still measure divergence | source: https://martin.kleppmann.com/2015/05/27/logs-for-data-infrastructure.html; source: https://debezium.io/blog/2019/02/19/reliable-microservices-data-exchange-with-the-outbox-pattern/; source: https://www.elastic.co/guide/en/elasticsearch/reference/current/near-real-time.html; source: https://github.com/ClickHouse/ClickBench (c6a.4xlarge, 500 GB gp2, untuned PostgreSQL 2026-09-21 vs DuckDB 2026-05-11 results, hot runs; wide web-analytics rows) |

Traps:
- Dual writes from application code (write the database, then the index): race conditions and partial failures cause permanent, silent divergence (source: Kleppmann, above).
- "Eventually consistent" is not "never wrong". At more than one quadrillion cache queries/day, one operator measures 99.99999999% of cache writes consistent within five minutes and still builds tracing to find the rest (source: https://engineering.fb.com/2022/06/08/core-infra/cache-made-consistent/). Balance and stock checks must read the system of record.
- Version checks stop an older value from overwriting a newer one only while the cache still holds the newer version; after an eviction, a late older fill can win (source: Meta, above).

## Sources
- A Ledger In PostgreSQL Is Fast! (pgledger benchmark) — https://www.pgrs.net/2025/05/16/pgledger-in-postgresql-is-fast/
- Behind the Scenes: How We Built Ledgers for High Throughput (Modern Treasury) — https://www.moderntreasury.com/journal/behind-the-scenes-how-we-built-ledgers-for-high-throughput
- TigerBeetle vs PostgreSQL Performance: Benchmark Harness, Cloud Tests (SoftwareMill) — https://softwaremill.com/tigetbeetle-vs-postgresql-performance-benchmark-harness-cloud-tests/
- High-Throughput OLTP in Three Simple Steps (TigerBeetle) — https://tigerbeetle.com/blog/2026-09-17-performant-use-of-tigerbeetle/
- Ledger: Stripe's system for tracking and validating money movement — https://stripe.dev/blog/ledger-stripe-system-for-tracking-and-validating-money-movement
- Concurrency control in Aurora DSQL — https://docs.aws.amazon.com/aurora-dsql/latest/userguide/working-with-concurrency-control.html
- PostgreSQL: Transaction Isolation — https://www.postgresql.org/docs/current/transaction-iso.html
- We replaced Redis with MySQL for inventory reservations (Shopify) — https://shopify.engineering/scaling-inventory-reservations
- Redis cluster specification — https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/
- DynamoDB: Best practices for designing and using partition keys — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html
- Firestore: Distributed counters — https://firebase.google.com/docs/firestore/solutions/counters
- Stripe API: Idempotent requests — https://docs.stripe.com/api/idempotent_requests
- Implementing Stripe-like Idempotency Keys in Postgres (Brandur Leach) — https://brandur.org/idempotency-keys
- Avoiding double payments in a distributed payments system (Airbnb) — https://medium.com/airbnb-engineering/avoiding-double-payments-in-a-distributed-payments-system-2981f6b070bb
- Amazon RDS Service Level Agreement — https://aws.amazon.com/rds/sla/
- Cloud Spanner Service Level Agreement — https://cloud.google.com/spanner/sla
- Using switchover or failover in Amazon Aurora Global Database — https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-global-database-disaster-recovery.html
- CockroachDB: Table localities — https://www.cockroachlabs.com/docs/stable/table-localities
- CockroachDB: Multi-region survival goals — https://www.cockroachlabs.com/docs/stable/multiregion-survival-goals
- Azure network round-trip latency statistics — https://learn.microsoft.com/en-us/azure/networking/azure-network-latency
- DynamoDB global tables: how it works — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/V2globaltables_HowItWorks.html
- PostgreSQL: Full Text Search introduction — https://www.postgresql.org/docs/current/textsearch-intro.html
- PostgreSQL: Hot Standby — https://www.postgresql.org/docs/current/hot-standby.html
- PostgreSQL: Replication settings (max_standby_streaming_delay) — https://www.postgresql.org/docs/current/runtime-config-replication.html
- Using logs to build a solid data infrastructure (or: why dual writes are a bad idea) (Martin Kleppmann) — https://martin.kleppmann.com/2015/05/27/logs-for-data-infrastructure.html
- Reliable Microservices Data Exchange With the Outbox Pattern (Debezium) — https://debezium.io/blog/2019/02/19/reliable-microservices-data-exchange-with-the-outbox-pattern/
- Elasticsearch: Near real-time search — https://www.elastic.co/guide/en/elasticsearch/reference/current/near-real-time.html
- ClickBench: a benchmark for analytical databases — https://github.com/ClickHouse/ClickBench
- Cache made consistent (Meta) — https://engineering.fb.com/2022/06/08/core-infra/cache-made-consistent/
