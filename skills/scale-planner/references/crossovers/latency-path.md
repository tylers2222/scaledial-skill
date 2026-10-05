# Latency-path crossovers

Scope: jobs on and beside a trading system's hot path: receiving market data into a process, sending orders to a venue, fanning market data out to internal consumers, timestamping events for audit, and capturing order events for audit and post-trade checks.
Use: open this file only after the components of the input design are listed. Use it to look up bands, costs, and sources. Do not use it to decide which components to discuss.

## Receive market data into the strategy process

Contract that matters: every packet of each feed channel is processed in sequence-number order; a gap is detected and recovered from the venue's re-request or snapshot service, never skipped silently; the redundant A and B lines are arbitrated; the host drops nothing during bursts; latency is counted from the last needed bit on the wire to the decision, tails included.
Axes that usually bind: latency, throughput, team_ops_capacity, change_rate

| Band | Option family (examples) | Why it fits | Breaks when | Evidence |
|---|---|---|---|---|
| Fastest rival reacts in roughly 100 µs or more; signals stay valid for milliseconds or longer | Kernel UDP sockets, tuned: busy polling, receive thread pinned away from the interrupt core, interrupt coalescing off | No special hardware, licences, or skills. With 32-byte UDP payloads on 10GbE, tuning cut the round trip from about 60 µs average (44 µs minimum) to about 31 µs average (26 µs minimum). The kernel needs about 4 µs to hand a packet to a busy-polling process and about 8 µs to an idle one | Budget falls below roughly 100 µs: kernel delivery plus jitter (round-trip standard deviation of 9 to 33 µs) loses races. Or bursts outrun one receive core: one multicast flow hashes to one receive queue, and one kernel receive core topped out near 350,000 packets/s | source: https://blog.cloudflare.com/how-to-achieve-low-latency/ (2015; two hosts with 2 GHz Xeon, 2 x 6 cores; one 10Gb switch); source: https://blog.cloudflare.com/how-to-receive-a-million-packets/ (2015, one receive queue); rule of thumb: the 100 µs edge is a few times the tuned path's delay plus jitter |
| Rival reaction from roughly 100 µs down to about 2 µs | Kernel bypass: user-space network stack on a supported NIC, through a sockets-compatible library first and a raw frame API only if needed (Onload, ef_vi, VMA, DPDK) | In the same 2015 test, delivery to the application fell from 4.3 µs to 0.47 µs and jitter fell about tenfold. An audited benchmark measured a mean of 2.3 µs half round trip between two applications at 100,000 and 1 million messages/s. A sockets-compatible library needs no application change | The race is decided below about 2 µs: software still crosses PCIe and the CPU, while hardware stacks act in tens of ns (next row) | source: https://blog.cloudflare.com/how-to-achieve-low-latency/; source: https://www.supermicro.com/en/pressreleases/supermicro-redhat-and-solarflare-set-world-record-performance-mark-double-digit (STAC-N1, 2018; 2 x 8-core Xeon Gold 6144 overclocked to 4.18 GHz, RHEL 7.5, X2522 NICs; round trip divided by two per https://docs.stacresearch.com/system/files/central/stac-n%20backgrounder%20-%20updated.pdf); source: https://www.amd.com/content/dam/amd/en/support/downloads/solarflare/quick-start-guides/SF-120482-CD-4_X2522-25G_online_Quick_Start_Guide.pdf (POSIX sockets, no application change); rule of thumb: the 2 µs edge sits at the audited 2.3 µs software mean |
| Rivals trade from hardware; budget below about 2 µs | FPGA: feed decode, trigger, pre-trade checks, and order send in hardware; software only loads parameters (FPGA card or FPGA NIC with network IP cores) | Audited tick-to-trade network I/O, from the last needed bit in to the first order bit out, with almost no trading logic: minimum 13.9 ns (2024); minimum 24.2 ns and means of 27.9 to 29.2 ns (2020) | Strategy logic changes faster than hardware build-and-test cycles allow, or the firm's edge is not speed | source: https://docs.stacresearch.com/news/AMD240422 (UL3524 card, Exegy IP cores, wire timestamps); source: https://docs.stacresearch.com/news/XLX200514 (VU9P FPGA, LDA IP cores); rule of thumb: the 2 µs edge as in the row above; team and change costs assume hardware (RTL or HLS) engineers and simulation plus wire-capture testing |

Traps:
- Kernel bypass does not fix a slow decision. It removes about 4 µs of kernel time per packet (source: https://blog.cloudflare.com/how-to-achieve-low-latency/). If the decision code is slower than that, profile the code first.
- Throughput can force the move before latency does. The full US options feed is projected to burst to about 169,000 packets per 10 ms on one stream in mid-2026 (source: https://cdn.opraplan.com/documents/notices/OPRA_Capacity_Projections_Update_0925.pdf), far above one kernel receive core in the test above. For a firm whose edge is not speed, substitute down: fewer channels, or a vendor's normalized, conflated feed (rule of thumb: assumes the strategy tolerates conflated updates).
- Hardware acceleration in a firm whose edge is not speed is a substitute-down case. It buys nanoseconds that a strategy holding positions for seconds cannot use, and it slows every logic change (rule of thumb: software team without RTL skills; strategy logic that changes weekly).
- The two audited benchmarks measure different things: STAC-N1 is half a software round trip between two hosts; STAC-T0 is time inside one box (source: https://docs.stacresearch.com/system/files/central/STAC-T0%20backgrounder.pdf). Do not subtract one from the other; compare candidates with wire timestamps on your own feed.

## Send an order to a venue

Contract that matters: each order reaches the venue's gateway on the venue's session protocol, with sequence numbers and resend; before it leaves, every order passes credit, price, size, and duplicate checks that stay under the direct and exclusive control of the broker-dealer that holds market access; latency is counted from the decision to the venue's gateway.
Axes that usually bind: geography, latency, isolation_compliance

| Band | Option family (examples) | Why it fits | Breaks when | Evidence |
|---|---|---|---|---|
| Venue tens to thousands of km away; strategy horizon of tens of ms or more | Broker algorithm or direct market access over a WAN circuit, kernel TCP | Distance dominates: fiber adds about 5 µs per km one way, so 1,000 km costs about 5 ms each way, and no host tuning changes that | Colocated rivals act on the same signal in µs, and fills depend on queue position | source: https://www.itu.int/rec/T-REC-G.114-200305-I/en (planning value for optical fibre systems, repeaters included); rule of thumb: the horizon edge keeps distance delay a small share of the time a signal stays valid |
| The venue's own data center (colocation) | Rack in the venue's data center, cross-connect to the order gateway, tuned kernel or kernel-bypass TCP | Distance shrinks to metres at about 4.9 ns per metre of fiber, so the host stack and the venue gateway dominate | The trading signal comes from another venue hundreds of km away: the link between venues now decides the race | source: https://engineering.fb.com/2022/11/21/production-engineering/precision-time-protocol-at-meta/ (fiber delay per metre as stated by the operator for in-building fiber runs) |
| Signal at one venue, order at another (for example Chicago futures to New Jersey equities) | Line-of-sight microwave or millimetre-wave links between venues, fiber as backup | Radio in air beats light in glass. Chicago to New Jersey: best fiber route above 6.55 ms one way; 2012 microwave networks estimated at 4.2 to 5.2 ms; speed-of-light floor 3.93 ms | Rain fades and other propagation effects cause outages; one radio channel carries roughly 140 to 190 Mbps, too little for full feeds; industry spend estimated above $500 million (infrastructure plus 5 years of operations) | source: https://arxiv.org/abs/1302.5966 (tick data April 2010 to August 2012; network latencies and costs estimated from publicly available information) |

Traps:
- Substitute down for distant firms: kernel bypass or an FPGA 1,000 km from the venue saves about 4 µs of a roughly 5 ms one-way trip (source: https://www.itu.int/rec/T-REC-G.114-200305-I/en; source: https://blog.cloudflare.com/how-to-achieve-low-latency/).
- A pre-trade risk service on another host adds a network hop to every order: about 13 to 30 µs one way on the kernel path (half the tuned and untuned round trips in https://blog.cloudflare.com/how-to-achieve-low-latency/), about 2.3 µs with kernel bypass (source: https://www.supermicro.com/en/pressreleases/supermicro-redhat-and-solarflare-set-world-record-performance-mark-double-digit). Keep the checks in the sending process; when orders start in an FPGA, the checks go into the FPGA too (rule of thumb: assumes the firm holds market access itself).
- Sponsored access moves the check: the broker-dealer with market access must keep the controls under its direct and exclusive control (source: https://www.ecfr.gov/current/title-17/section-240.15c3-5), so the broker's checks stay in the path whatever the client builds.

## Fan out market data to internal consumers

Contract that matters: every consumer sees the same updates in the same order and can detect a gap; a slow consumer never stalls the publisher or the fast consumers; latency-sensitive consumers get updates without a broker hop.
Axes that usually bind: fan_out, latency, durability

| Band | Option family (examples) | Why it fits | Breaks when | Evidence |
|---|---|---|---|---|
| A few consumers on the same host | Single-writer ring buffer in shared memory; each reader tracks its own sequence number (Disruptor-style rings, Aeron IPC) | Mean 52 ns per hop against 32,757 ns for a lock-based bounded queue; 99% of hops under 128 ns against about 2.1 ms | Consumers move to other hosts, or a slow reader forces the writer to wait for it or to overwrite unread slots | source: https://lmax-exchange.github.io/disruptor/disruptor.html (2011; three-stage pipeline, 2.2 GHz Core i7-2720QM, Java 1.6, Linux) |
| Many hosts in one data center, latency-sensitive | UDP multicast on the switched LAN, with a sequence-numbered recovery layer (MoldUDP64-style re-request server) and A and B lines | The publisher sends each packet once whatever the number of listeners, and the switch copies it; one switch hop between two hosts took about 4 µs in a 2015 10GbE test | Consumers sit outside the multicast domain (another site, a cloud region), or need replay from hours ago | source: https://www.nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/moldudp64.pdf; source: https://blog.cloudflare.com/how-to-achieve-low-latency/ |
| Consumers that tolerate milliseconds: risk dashboards, research capture, surveillance | Durable replicated log or broker (Kafka, Pulsar) | Retention, replay, and many independent consumers; p99 about 5 ms end to end at 200 MB/s of 1 KB messages | A trading decision is moved onto it | source: https://www.confluent.io/blog/kafka-fastest-messaging-system/ (vendor benchmark, 2020: 3 brokers on i3en.2xlarge, acks=all, min.insync.replicas=2, 100 partitions) |

Traps:
- The company-standard broker on the trading path: about 5 ms at p99 (source: https://www.confluent.io/blog/kafka-fastest-messaging-system/) where a same-host ring averages about 52 ns per hop (source: https://lmax-exchange.github.io/disruptor/disruptor.html). Feed the broker from a thread that is not on the hot path.
- One ring shared by the strategy and a slow consumer: the writer tracks reader sequences so that it never overwrites unread entries, so the slowest reader sets the pace (source: https://lmax-exchange.github.io/disruptor/disruptor.html). Give slow consumers their own copy, republished off the hot path.
- Substitute down: multicast with recovery servers for two consumers on one host. A shared-memory ring keeps the contract and has nothing to operate.

## Timestamp events for audit (clock synchronization)

Contract that matters: every reportable event carries a time traceable to UTC within the tolerance for the firm's activity, at the required granularity; each synchronization is logged and kept as a record; drift beyond tolerance is detected.
Axes that usually bind: isolation_compliance, geography, team_ops_capacity, cost

| Band | Option family (examples) | Why it fits | Breaks when | Evidence |
|---|---|---|---|---|
| US broker-dealer recording events in NMS or OTC equity securities, with no high-frequency trading on EU venues | NTP client (chrony, ntpd) against several internal or provider servers; sync log kept as a record; alert on drift | The US rule allows computer clocks 50 ms from NIST time and asks for a sync log. NTP typically holds a few ms over the Internet and tens of µs on a LAN | The firm uses high-frequency algorithmic trading on an EU venue, or must line up events across hosts to within µs | source: https://www.finra.org/rules-guidance/rulebooks/finra-rules/4590; source: https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/7/html/system_administrators_guide/ch-configuring_ntp_using_the_chrony_suite |
| Member of an EU venue using high-frequency algorithmic trading, or µs cross-host measurement | PTP: GNSS-disciplined grandmaster, hardware-timestamping NICs, switches acting as transparent clocks, independent monitoring | EU rule from 2 March 2026: at most 100 µs from UTC with 0.1 µs granularity for high-frequency trading. One operator holds offsets near ±100 ns with transparent clocks, where its NTP service gave millisecond precision | One switch on the path without transparent-clock support: the same operator saw an offset move from about ±100 ns to −400 µs | source: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32025R1155 (Annex IV Table 2; replaces Regulation (EU) 2017/574); source: https://engineering.fb.com/2022/11/21/production-engineering/precision-time-protocol-at-meta/ (data-center fleet) |

Traps:
- Substitute down: copying the high-frequency reference design (roof antenna, grandmaster, PTP switches) into a US firm whose binding rule is 50 ms (source: https://www.finra.org/rules-guidance/rulebooks/finra-rules/4590).
- A stable offset is not accuracy: an NTP client stable to nanoseconds can still be off by milliseconds through asymmetric routes or switch queues (source: https://chrony-project.org/faq.html). The EU rule asks for documented traceability to UTC, reviewed at least once a year (source: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32025R1155).
- Granularity follows your own systems: if order systems stamp finer than the audit-trail minimum of one millisecond, the finer increment must be reported (source: https://www.ecfr.gov/current/title-17/section-242.613).

## Capture order events and run post-trade checks off the critical path

Contract that matters: every order, cancel, acknowledgment, and fill is recorded when it happens, with its timestamp; no event is lost across a crash, and the record reconciles with an independent copy; the US consolidated audit trail receives it by 8:00 a.m. Eastern on the next trading day; order records are kept at least 3 years, the first 2 easily accessible, with a complete audit trail or in non-rewriteable form; surveillance staff get execution reports immediately; the order path never waits on this IO.
Axes that usually bind: durability, isolation_compliance, latency

| Band | Option family (examples) | Why it fits | Breaks when | Evidence |
|---|---|---|---|---|
| Every scale in this file's range, from one strategy host to many | The hot path copies a fixed-size event into an in-memory ring; a journaler thread on another core appends it to a local append-only file and ships the file to retained storage; a nightly batch loads an ordinary database and builds the report; a reconciler compares the journal with the venue's drop-copy session during the day | The deadline is the next morning, so completeness matters and speed does not. Keeping IO on other threads is how one low-latency exchange keeps its single business-logic thread (about 6 million orders/s) free of IO. The drop copy is a real-time, read-only copy of order events from the venue | Does not break on volume in range. The shape changes only if a rule moves the reporting deadline into the trading day | source: https://www.ecfr.gov/current/title-17/section-242.613 (record contemporaneously; report by 8:00 a.m. ET next trading day); source: https://www.ecfr.gov/current/title-17/section-240.17a-4 (retention, audit trail or non-rewriteable storage); source: https://martinfowler.com/articles/lmax.html (3 GHz dual-socket quad-core Nehalem); source: https://cmegroupclientsite.atlassian.net/wiki/spaces/EPICSANDBOX/pages/665190402/Drop+Copy+4.0+Service+for+iLink (futures venue); source: https://nasdaqtrader.com/content/technicalsupport/specifications/TradingProducts/drop2.2.pdf (equities venue) |

Traps:
- A synchronous database write or broker publish before each order send puts IO on the hot path to meet a deadline that is the next morning.
- "Real-time compliance" as the reason for a streaming platform: the market-access rule asks for immediate post-trade execution reports to surveillance personnel, who are people (source: https://www.ecfr.gov/current/title-17/section-240.15c3-5). A screen fed from the drop copy meets it (rule of thumb: human reviewers act in seconds, not microseconds).
- The local journal as the only copy: a crash between send and flush loses the event. Reconcile with the venue's drop copy and the order session's sequence numbers.

## Sources
- How to achieve low latency with 10Gbps Ethernet (Cloudflare) — https://blog.cloudflare.com/how-to-achieve-low-latency/
- How to receive a million packets per second (Cloudflare) — https://blog.cloudflare.com/how-to-receive-a-million-packets/
- Supermicro, Red Hat and Solarflare set world record on STAC-N1 (press release) — https://www.supermicro.com/en/pressreleases/supermicro-redhat-and-solarflare-set-world-record-performance-mark-double-digit
- STAC-N1 overview (measurement method) — https://docs.stacresearch.com/system/files/central/stac-n%20backgrounder%20-%20updated.pdf
- Solarflare X2522-25G quick start guide (AMD) — https://www.amd.com/content/dam/amd/en/support/downloads/solarflare/quick-start-guides/SF-120482-CD-4_X2522-25G_online_Quick_Start_Guide.pdf
- STAC Report: New STAC-T0 results with an Exegy/AMD FPGA solution — https://docs.stacresearch.com/news/AMD240422
- STAC Report: New LDA/Xilinx solution under STAC-T0 — https://docs.stacresearch.com/news/XLX200514
- STAC-T0 overview — https://docs.stacresearch.com/system/files/central/STAC-T0%20backgrounder.pdf
- Revised OPRA capacity projections (SIAC, September 2025) — https://cdn.opraplan.com/documents/notices/OPRA_Capacity_Projections_Update_0925.pdf
- ITU-T G.114: One-way transmission time — https://www.itu.int/rec/T-REC-G.114-200305-I/en
- How Precision Time Protocol is being deployed at Meta — https://engineering.fb.com/2022/11/21/production-engineering/precision-time-protocol-at-meta/
- Information Transmission Between Financial Markets in Chicago and New York (Laughlin, Aguirre, Grundfest) — https://arxiv.org/abs/1302.5966
- 17 CFR 240.15c3-5: Risk management controls for brokers or dealers with market access — https://www.ecfr.gov/current/title-17/section-240.15c3-5
- LMAX Disruptor: high performance alternative to bounded queues — https://lmax-exchange.github.io/disruptor/disruptor.html
- MoldUDP64 protocol specification (Nasdaq) — https://www.nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/moldudp64.pdf
- Benchmarking Apache Kafka, Apache Pulsar, and RabbitMQ (Confluent) — https://www.confluent.io/blog/kafka-fastest-messaging-system/
- FINRA Rule 4590: Synchronization of Member Business Clocks — https://www.finra.org/rules-guidance/rulebooks/finra-rules/4590
- Configuring NTP using the chrony suite (Red Hat Enterprise Linux 7) — https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/7/html/system_administrators_guide/ch-configuring_ntp_using_the_chrony_suite
- Commission Delegated Regulation (EU) 2025/1155 (business clocks, Articles 11 to 16) — https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32025R1155
- chrony FAQ — https://chrony-project.org/faq.html
- 17 CFR 242.613: Consolidated audit trail — https://www.ecfr.gov/current/title-17/section-242.613
- 17 CFR 240.17a-4: Records to be preserved by certain exchange members, brokers and dealers — https://www.ecfr.gov/current/title-17/section-240.17a-4
- The LMAX Architecture (Martin Fowler) — https://martinfowler.com/articles/lmax.html
- Drop Copy 4.0 Service for iLink (CME Group) — https://cmegroupclientsite.atlassian.net/wiki/spaces/EPICSANDBOX/pages/665190402/Drop+Copy+4.0+Service+for+iLink
- DROP protocol specification (Nasdaq) — https://nasdaqtrader.com/content/technicalsupport/specifications/TradingProducts/drop2.2.pdf
