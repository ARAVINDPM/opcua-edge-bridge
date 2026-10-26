"""Toy comparison of four ways to charge for lifelong device updates.

Context: the EU Cyber Resilience Act makes security updates an obligation for
the declared support period. Vendors answer this with different models
(observed publicly in 2024-2026):

  subscription   per device per month (e.g. a device-management Pro tier)
  lifetime       one-off fee per device covering updates for its lifetime
  usage          free device connection, pay per MB of OTA/logs
  tiered         free tier + paid tier; a share of the fleet converts

ALL NUMBERS ARE HYPOTHETICAL PARAMETERS, not data about any company. The point
is the structure of the trade-off (cash timing, churn risk, cost coverage over
a long support period), not the absolute values.

  python -m tools.pricing_model
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Fleet:
    devices_per_year: int = 1_000     # new devices shipped per year
    years: int = 10                   # horizon = support period
    churn_per_year: float = 0.03      # devices retired/disconnected per year
    updates_per_year: int = 6         # firmware updates per year
    mb_per_update: float = 25.0       # OTA size per update
    cost_per_device_year: float = 4.0  # vendor cost to keep one device supported (cloud, QA, security response)
    discount_rate: float = 0.08


@dataclass
class Prices:
    sub_per_month: float = 2.0
    lifetime_once: float = 15.0
    usage_per_mb: float = 0.02
    tiered_conversion: float = 0.25   # share of fleet on paid tier
    tiered_paid_per_month: float = 2.0


def installed_base(f: Fleet) -> list[float]:
    base, out = 0.0, []
    for _ in range(f.years):
        base = base * (1 - f.churn_per_year) + f.devices_per_year
        out.append(base)
    return out


def npv(cash: list[float], r: float) -> float:
    return sum(c / (1 + r) ** (t + 1) for t, c in enumerate(cash))


def model(f: Fleet, p: Prices) -> dict[str, dict[str, float]]:
    base = installed_base(f)
    cost = [b * f.cost_per_device_year for b in base]
    rev = {
        "subscription": [b * p.sub_per_month * 12 for b in base],
        "lifetime": [f.devices_per_year * p.lifetime_once for _ in base],
        "usage": [b * f.updates_per_year * f.mb_per_update * p.usage_per_mb for b in base],
        "tiered": [b * p.tiered_conversion * p.tiered_paid_per_month * 12 for b in base],
    }
    out = {}
    for k, r in rev.items():
        margin = [a - c for a, c in zip(r, cost)]
        cum, payback = 0.0, None
        for t, m in enumerate(margin):
            cum += m
            if cum < 0:
                payback = None
            elif payback is None:
                payback = t + 1
        out[k] = {
            "npv_revenue": round(npv(r, f.discount_rate)),
            "npv_margin": round(npv(margin, f.discount_rate)),
            "year1_revenue": round(r[0]),
            "last_year_margin": round(margin[-1]),
            "cost_covered_every_year": all(m >= 0 for m in margin),
        }
    return out


def main() -> None:
    f, p = Fleet(), Prices()
    res = model(f, p)
    print(f"Hypothetical fleet: {f}\nPrices: {p}\n")
    print(f"{'model':<14}{'NPV revenue':>13}{'NPV margin':>13}{'yr1 rev':>10}{'last-yr margin':>16}  covers cost yearly")
    for k, v in res.items():
        print(f"{k:<14}{v['npv_revenue']:>13,}{v['npv_margin']:>13,}{v['year1_revenue']:>10,}"
              f"{v['last_year_margin']:>16,}  {v['cost_covered_every_year']}")
    print("\nReading: lifetime pricing front-loads cash but the installed base keeps costing money every year;"
          "\nsubscription matches cost over a long CRA support period but needs a reason to pay monthly.")


if __name__ == "__main__":
    main()
