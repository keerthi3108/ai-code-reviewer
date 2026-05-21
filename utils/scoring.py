"""Score computation and aggregation from review data."""
from config import SEVERITY_ORDER


def compute_issue_stats(issues: list[dict]) -> dict:
    counts = {s: 0 for s in SEVERITY_ORDER}
    for issue in issues:
        sev = (issue.get("severity") or "info").lower()
        if sev in counts:
            counts[sev] += 1
        else:
            counts["info"] += 1
    return counts


def estimate_technical_debt(issues: list[dict], scores: dict) -> dict:
    """Estimate technical debt in hours and priority."""
    hours = 0.0
    weights = {"critical": 4.0, "high": 2.0, "medium": 1.0, "low": 0.5, "info": 0.1}
    for issue in issues:
        sev = (issue.get("severity") or "info").lower()
        hours += weights.get(sev, 0.1)

    readiness = scores.get("production_readiness", 70)
    debt_multiplier = max(1.0, (100 - readiness) / 25)
    total_hours = round(hours * debt_multiplier, 1)

    if total_hours > 40:
        priority = "High"
        color = "#dc2626"
    elif total_hours > 16:
        priority = "Medium"
        color = "#ca8a04"
    else:
        priority = "Low"
        color = "#16a34a"

    return {
        "estimated_hours": total_hours,
        "priority": priority,
        "color": color,
        "issue_count": len(issues),
    }
