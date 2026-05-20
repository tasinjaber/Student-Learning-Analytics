from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _parse_ts(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not value:
        return None
    for candidate in (str(value), str(value).replace("Z", "+00:00")):
        try:
            return datetime.fromisoformat(candidate)
        except ValueError:
            continue
    return None


def _get_user_id(r: dict) -> str:
    for key in ("user_id", "student_id", "learner_id", "userid_di", "userid"):
        v = r.get(key)
        if v and str(v).strip().upper() not in {"NA", "NAN", ""}:
            return str(v)
    return "unknown"


def _build_student_features(records: list[dict]) -> list[dict]:
    grouped: dict[str, list] = defaultdict(list)
    for r in records:
        grouped[_get_user_id(r)].append(r)

    rows = []
    now = datetime.utcnow()
    for uid, recs in grouped.items():
        avg_score = sum(_safe_float(r.get("score")) for r in recs) / max(len(recs), 1)
        total_dur = sum(_safe_float(r.get("duration_minutes")) for r in recs)
        latest = max((_parse_ts(r.get("timestamp")) for r in recs), default=None)
        inactivity = (now - latest).days if latest else 999
        event_types = len({str(r.get("event_type", "")).lower() for r in recs})

        risk_label = 0
        if avg_score < 40:
            risk_label = 1
        elif avg_score < 60 and inactivity > 7:
            risk_label = 1

        rows.append({
            "student_id": uid,
            "avg_score": avg_score,
            "event_count": len(recs),
            "total_duration": total_dur,
            "inactivity_days": inactivity,
            "event_variety": event_types,
            "risk_label": risk_label,
        })
    return rows


def ml_at_risk(records: list[dict], limit: int = 10) -> list[dict[str, Any]]:
    rows = _build_student_features(records)
    if len(rows) < 5:
        return []

    try:
        from sklearn.ensemble import RandomForestClassifier
        import numpy as np

        feature_cols = ["avg_score", "event_count", "total_duration", "inactivity_days", "event_variety"]
        X = np.array([[r[c] for c in feature_cols] for r in rows], dtype=float)
        y = np.array([r["risk_label"] for r in rows])

        clf = RandomForestClassifier(n_estimators=50, random_state=42)
        clf.fit(X, y)
        probs = clf.predict_proba(X)
        risk_idx = list(clf.classes_).index(1) if 1 in clf.classes_ else 0

        result = []
        for row, prob in zip(rows, probs):
            result.append({
                "student_id": row["student_id"],
                "avg_score": round(row["avg_score"], 2),
                "event_count": row["event_count"],
                "inactivity_days": row["inactivity_days"],
                "ml_risk_probability": round(float(prob[risk_idx]) * 100, 1),
            })

        return sorted(result, key=lambda x: x["ml_risk_probability"], reverse=True)[:limit]
    except Exception:
        return []


def forecast_engagement(trend: list[dict[str, Any]], days_ahead: int = 7) -> dict[str, Any]:
    if len(trend) < 5:
        return {"historical": trend, "forecast": [], "trend_direction": "insufficient_data"}

    try:
        import numpy as np

        dates = [t["date"] for t in trend]
        counts = [float(t.get("interactions", t.get("count", 0))) for t in trend]
        x = np.arange(len(counts))
        coeffs = np.polyfit(x, counts, 1)
        slope = float(coeffs[0])

        last_date = datetime.strptime(dates[-1], "%Y-%m-%d")
        forecast = []
        for i in range(1, days_ahead + 1):
            pred = float(np.polyval(coeffs, len(counts) - 1 + i))
            pred = max(0.0, pred)
            forecast.append({
                "date": (last_date + timedelta(days=i)).strftime("%Y-%m-%d"),
                "interactions": round(pred, 1),
                "is_forecast": True,
            })

        if slope > 0.5:
            direction = "increasing"
        elif slope < -0.5:
            direction = "decreasing"
        else:
            direction = "stable"

        return {
            "historical": trend,
            "forecast": forecast,
            "trend_direction": direction,
            "slope": round(slope, 4),
        }
    except Exception:
        return {"historical": trend, "forecast": [], "trend_direction": "error"}


def detect_anomalies(trend: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if len(trend) < 7:
        return []

    counts = [float(t.get("interactions", t.get("count", 0))) for t in trend]
    mean = sum(counts) / len(counts)
    variance = sum((c - mean) ** 2 for c in counts) / len(counts)
    std = math.sqrt(variance) if variance > 0 else 1.0

    anomalies = []
    for point, count in zip(trend, counts):
        z = (count - mean) / std
        if abs(z) > 2.0:
            anomalies.append({
                **point,
                "z_score": round(z, 2),
                "type": "spike" if z > 0 else "drop",
            })
    return anomalies
