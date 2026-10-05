# Scale axes

Scale is not one number. Fill every axis that could matter for a component, then pick the one that binds. Use canonical names so `explainer diversity` can compare plans. Add a new snake_case name only when none of these fit, and add it to this file through a retro.

| Axis | What it measures | Typical units | How to estimate when the input is silent |
|---|---|---|---|
| latency | Time budget for one operation on the critical path | ns, µs, ms at p50 / p99 | Ask what a slow response costs. Work back from the user-visible deadline. |
| throughput | Sustained operations per unit time | requests/s, messages/s, MB/s | Daily total ÷ 86,400, then multiply by a peak factor (often 3x to 10x for consumer traffic). State the factor. |
| data_volume | Data at rest, and its growth | GB, TB, rows; growth per month | Records per day × bytes per record × retention. |
| fan_out | How many readers or destinations each write reaches | consumers per event, readers per object | Count downstream teams or services. Count viewers per item for media. |
| consistency | What readers must see after a write | strict / read-your-writes / eventual; allowed staleness | Ask what goes wrong if two readers see different values for one second. Money and inventory usually need strict. |
| durability | What loss is acceptable | RPO (seconds of data that may be lost) | Ask what one lost write costs. Audit and money: zero. |
| availability | What downtime is acceptable | SLO %, RTO | Ask who notices an outage and how fast. |
| isolation_compliance | Separation required by law, contract, or tenancy | regimes, tenant isolation level, data residency | Look for regulated data (payments, health, personal data) and enterprise customers. |
| team_ops_capacity | People and skill available to run the thing | engineers, on-call rotation size, skills | Count engineers who would carry a pager for it. |
| cost | Money per month at this scale, including people | currency per month | Infrastructure list price plus a share of engineer time. |
| change_rate | How often the logic or schema changes | deploys per week, schema changes per month | Early products change weekly. Hardware logic changes slowly. |
| geography | Where users and data are | regions, round-trip time between them | User distribution, residency rules. |

## Picking the binding axis

- The binding axis is the one whose limit the current option will hit first inside the user's range. Others may be large but still have room.
- Check the axes that people forget before accepting throughput: fan_out, durability (replay and retention), team_ops_capacity, isolation_compliance, change_rate.
- If two axes bind at the same point, the component may be two jobs. Consider `split`.
- If no axis gets close to a limit in the user's range, the outcome is probably `keep`.

## Units

Write values in the workload's units and convert once for the reader: "1M messages/min (about 16.7k/s)". Keep the conversion in the plan so the script uses the same number.
