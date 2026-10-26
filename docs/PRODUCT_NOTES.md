# Product notes

Written the way I would approach this as a product manager: problem first, then users, assumptions, metrics, decisions. Everything here is my own reasoning on a learning project. No customer interviews have been run yet; where something is an assumption, it is labelled as one.

## 1. Problem

Machines and plants speak OT protocols (OPC UA, Modbus, S7). Dashboards, analytics and cloud services expect IT-style messaging (MQTT, REST). Someone has to bridge the two, and the bridge sits exactly where the security boundary between OT and IT lies. If it is unreliable, data goes stale silently. If it is insecure, it becomes the way in.

## 2. Users and jobs to be done

| Persona | Job to be done | What would make them distrust the product |
|---|---|---|
| Service engineer at a machine builder | "See the state of my machines at customer sites and change a setpoint remotely, without driving there." | Writes that are not controlled or not logged |
| OT/automation engineer at a utility (critical infrastructure) | "Get process values into SCADA/cloud without opening the plant network." | Anything that weakens segmentation; unclear update path |
| Data / IT team | "Consume clean, timestamped signals with known quality." | Values with no timestamp or quality; can't tell stale from unchanged |
| Security / compliance officer | "Prove the component is maintained: updates, SBOM, vulnerability handling." | No support period, no SBOM, insecure defaults |

## 3. Assumptions to test (and how)

| # | Assumption | Cheapest test |
|---|---|---|
| H1 | Users care more about knowing whether data is *stale* than about latency | Ask 5 service engineers which failure has cost them more |
| H2 | Write-back is wanted, but only with an allow-list and an audit trail | Offer read-only first; count how many ask for writes and for which signals |
| H3 | Report-by-exception with a deadband cuts traffic noticeably without losing information users need | Measure messages per hour with and without deadband on a real line; ask users whether they noticed a difference |
| H4 | In regulated sectors, the update/support promise is a buying criterion, not just a feature | Ask procurement/compliance what they check before approving an edge device |
| H5 | A free entry tier lowers the barrier, but users only pay for things that save them time or audit effort (e.g. automated updates, API) | Look at which features free users ask for most in support |

## 4. Metrics I would track

- **Data trust:** share of signals with good quality and a fresh timestamp. Median source→broker delay.
- **Efficiency:** messages per signal per hour (exception reporting vs. polling).
- **Safety of writes:** rejected-command rate. Every accepted write is logged.
- **Lifecycle:** time from a published CVE in a dependency to a patched release (patch latency). Share of the fleet on a supported version.
- **Business (if this were a product):** free→paid conversion, paid share of the installed base (attach rate), support cost per free user.

## 5. Decisions so far (decision log)

| Decision | Why | Trade-off |
|---|---|---|
| Subscription instead of polling | Lower load on small devices; source timestamps preserved | More complex client logic |
| JSON payload, one topic per signal | Easy for Node-RED and IT tools; human-readable | Bigger than Sparkplug B Protobuf; no standard data model |
| Birth/death via retained state + Last Will | Consumers can detect a dead bridge | Not full Sparkplug state management |
| Nothing writable by default | Least privilege; writes are the riskiest feature | Extra configuration for users who need writes |
| Simulator before hardware | Unblocks development; makes tests reproducible | Simulator ≠ vendor firmware; must validate on the board |
| Python + asyncua | Fast to prototype, readable | No ECC security policies; not a footprint for small devices |

## 6. Paying for lifelong updates: reading `tools/pricing_model.py`

Four models I saw discussed publicly in 2024–2026:
1. **Subscription** per device per month.
2. **One-off lifetime licence** per device.
3. **Usage-based**: device connection free, pay per MB of updates or logs.
4. **Free tier plus paid tier**, with part of the fleet converting.

With the toy parameters, the subscription and the tiered model cover the yearly cost of supporting a growing installed base. The lifetime and usage models do not over a 10-year horizon. Lifetime pricing brings cash in early, but the installed base keeps costing money every year.

The interesting product question is therefore not "which price" but **"which feature makes the recurring value visible?"** Under the CRA, automated, auditable security updates are a strong candidate. Numbers are hypothetical; the structure is the point.

## 7. Next steps

1. Run on the physical board. Record real node IDs, update rates and memory use.
2. Store-and-forward buffer for broker outages, with backfill flagged as such.
3. Audit log of all write commands (who, when, old and new value).
4. Compare with OPC UA PubSub over MQTT (Part 14) and Sparkplug B. When is a standard data model worth the extra complexity?
5. Talk to two service engineers and one OT security person to test H1, H2 and H4.
