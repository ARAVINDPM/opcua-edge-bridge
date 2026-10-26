# Demo walkthrough (about 5 minutes)

Start everything with `./scripts/demo.sh` and open <http://localhost:1880/dashboard>. In a Codespace the demo starts by itself; to stop the bridge there, use the terminal it runs in. Also keep a terminal open on the repository folder.

## 1. The problem (30 s)
Machines speak OPC UA; dashboards and cloud tools speak MQTT. The bridge sits on the OT/IT boundary. That means two things go wrong here first:
- data quietly goes stale;
- remote writes become a way in.

## 2. Data you can trust (1 min)
- **Process values:** values arrive only when they change. Memory usage has a deadband, so its jitter is not published. Every message carries a source timestamp, a bridge timestamp, a quality flag and a sequence number.
- **Bridge status:** the source→bridge delay is shown live. Ask the audience: *"Which hurts users more, latency or not knowing that data is stale?"* (Assumption H1 in `PRODUCT_NOTES.md`.)

## 3. Dead or alive? (30 s)
In the terminal, stop the bridge process (for example `pkill -f bridge.main`). Bridge status turns to **OFFLINE**: the broker sends the bridge's Last Will. Consumers can tell "unchanged" apart from "dead".

## 4. Guarded remote write (1 min)
- Switch **LED_1**. The command goes over MQTT and the bridge writes it to the OPC UA server. The audit row shows `written`, with the value before the write.
- Press the red button. It tries to write the read-only `sample_01`, and the audit row shows `rejected` with the reason.
- Point to `logs/audit.jsonl`: the same records are stored as a file.

## 5. Lifecycle and security (1 min)
- `make security` lists the server's endpoints and flags demo defaults: the `None` policy and anonymous login.
- `docs/SECURITY_NOTES.md` covers the ECC gap. The board offers ECC_nistP256, but this client stack does not support it. A secure product depends on the weakest stack in the chain.
- `sbom.cdx.json` is the SBOM of the Python dependencies.

## 6. How would someone pay for lifelong updates? (1 min)
`make pricing` compares four models: subscription, lifetime licence, usage-based, and free tier plus paid tier. The numbers are hypothetical; the question is which feature makes the recurring value visible.

## Honest limits (say them before you are asked)
- Validated against a simulator; the physical board run is still pending (`docs/HARDWARE_RUNBOOK.md`).
- No TLS or user identity in the lab setup.
- AI-assisted coding. The design decisions, tests and documentation are mine.
