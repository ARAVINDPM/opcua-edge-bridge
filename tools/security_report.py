"""Endpoint security report for an OPC UA server.

Lists offered endpoints/security policies and flags findings that matter for
"secure by default" thinking (EU Cyber Resilience Act, Annex I) and IEC 62443
style hardening. It is a learning aid, not a compliance assessment.

  python -m tools.security_report --endpoint opc.tcp://127.0.0.1:4842
"""
from __future__ import annotations

import argparse
import asyncio
import json

from asyncua import Client, ua

WEAK = {"Basic128Rsa15", "Basic256"}          # deprecated by OPC Foundation
STRONG = {"Basic256Sha256", "Aes128_Sha256_RsaOaep", "Aes256_Sha256_RsaPss",
          "ECC_nistP256", "ECC_nistP384", "ECC_brainpoolP256r1", "ECC_brainpoolP384r1"}


def policy_name(uri: str) -> str:
    return uri.rsplit("#", 1)[-1]


def assess(endpoints: list[dict]) -> list[dict]:
    findings = []
    policies = {e["policy"] for e in endpoints}
    tokens = {t for e in endpoints for t in e["user_tokens"]}
    if "None" in policies:
        findings.append({"severity": "high", "id": "SEC-01",
                         "text": "Unencrypted endpoint (SecurityPolicy None) is offered. Acceptable for a lab demo; "
                                 "a product shipped 'secure by default' should disable it or require explicit opt-in."})
    if policies & WEAK:
        findings.append({"severity": "high", "id": "SEC-02",
                         "text": f"Deprecated policies offered: {sorted(policies & WEAK)}."})
    if not policies & STRONG:
        findings.append({"severity": "high", "id": "SEC-03", "text": "No current-generation security policy offered."})
    if "Anonymous" in tokens:
        findings.append({"severity": "medium", "id": "SEC-04",
                         "text": "Anonymous login accepted. Production setups should require user or certificate authentication."})
    if not findings:
        findings.append({"severity": "info", "id": "SEC-00", "text": "No basic hardening findings."})
    return findings


async def collect(endpoint: str) -> list[dict]:
    client = Client(endpoint)
    eps = await client.connect_and_get_server_endpoints()
    out = []
    for e in eps:
        out.append({
            "url": e.EndpointUrl,
            "policy": policy_name(e.SecurityPolicyUri),
            "mode": e.SecurityMode.name,
            "user_tokens": sorted({ua.UserTokenType(t.TokenType).name for t in e.UserIdentityTokens}),
        })
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoint", default="opc.tcp://127.0.0.1:4842")
    args = ap.parse_args()
    eps = asyncio.run(collect(args.endpoint))
    print(json.dumps({"endpoints": eps, "findings": assess(eps)}, indent=2))


if __name__ == "__main__":
    main()
