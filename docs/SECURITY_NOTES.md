# Security notes

These notes are not legal advice and not a compliance assessment. They record how I think about this bridge against the direction of the EU Cyber Resilience Act (CRA) and IEC 62443 practice.

## Lab setup vs. product

| Topic | This lab prototype | What a shipped product would need |
|---|---|---|
| OPC UA security policy | `None` (simulator; asyncua has no ECC policies) | Encrypted policy only by default (e.g. Basic256Sha256 or ECC_nistP256), `None` disabled or explicit opt-in |
| Authentication | Anonymous | Certificates or user accounts; no default passwords |
| MQTT | Plain TCP to a local broker | TLS, per-device credentials, topic ACLs |
| Write-back | Allow-list + type checks + audit trail (JSONL + MQTT topic) | Plus user identity in the audit record, rate limits, role-based permissions and tamper-evident log storage |
| Dependencies | Pinned in `requirements.txt`; SBOM in `sbom.cdx.json` | SBOM per release, vulnerability monitoring, documented patch process |
| Updates | Manual | Signed updates, staged rollout, documented support period |

## CRA points that touch a component like this

- **Secure by default** (Annex I): `tools/security_report.py` flags an offered `None` policy and anonymous login, because these are typical "demo defaults" that must not ship.
- **Vulnerability handling for the support period:** know your components (SBOM), monitor them, ship fixes, and tell users how long they will get updates.
- **Reporting:** actively exploited vulnerabilities and severe incidents have to be reported within 24 h (early warning), followed by fuller notifications. These reporting duties apply from 11 September 2026. Most other obligations apply from 11 December 2027.

## The ECC gap (a product lesson)

The board demo supports `ECC_nistP256`, an elliptic-curve policy that suits small devices well. The Python client used here does not support ECC policies, so in the lab the bridge would fall back to `None`.

That is a real-world pattern: **the security a system offers is limited by the weakest stack in the chain.** A product team has to check this across devices, gateways and clients before promising "secure by default". Options are a client stack with ECC support (some C stacks implement ECC policies) or an RSA policy that both sides support.

## SBOM

`sbom.cdx.json` is generated with `cyclonedx-py` from `requirements.txt`. To regenerate it: `make sbom`.
