"""
HarvardX / MITx-style Open edX person–course exports (many Kaggle engagement datasets use this).

Known columns (sample): course_id, userid_DI, viewed, explored, certified, grade, start_time_DI,
last_event_DI, nevents, ndays_act, nplay_video, nchapters, nforum_posts, registered.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from math import sqrt
from statistics import mean
from typing import Any


def _lookup(record: dict[str, Any], *names: str) -> Any | None:
    lowered = {k.lower(): k for k in record}
    for name in names:
        if name in record:
            return record[name]
        key = lowered.get(name.lower())
        if key is not None:
            return record[key]
    return None


def _is_na(value: Any) -> bool:
    if value is None or value == "":
        return True
    return str(value).strip().upper() in {"NA", "N/A", "NULL", "NAN"}


def looks_like_edx_row(record: dict[str, Any]) -> bool:
    if not record:
        return False
    course = _lookup(record, "course_id", "courseid")
    uid = _lookup(record, "userid_di", "userid", "student_id", "user_id")
    if _is_na(course) or _is_na(uid):
        return False
    for metric in ("nevents", "ndays_act", "nchapters", "nplay_video", "nforum_posts", "grade"):
        val = _lookup(record, metric)
        if not _is_na(val):
            return True
    if not _is_na(_lookup(record, "viewed")) or not _is_na(_lookup(record, "explored")):
        return True
    return False


def infer_edx_person_course(records: list[dict[str, Any]]) -> bool:
    if not records:
        return False
    sample_size = min(200, len(records))
    hits = sum(looks_like_edx_row(r) for r in records[:sample_size])
    threshold = max(3, int(sample_size * 0.2))
    return hits >= threshold


def _parse_di_date(value: Any) -> datetime | None:
    if _is_na(value):
        return None
    s = str(value).strip().split()[0]
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    except ValueError:
        return None


def _truthy_bin(value: Any) -> float | None:
    if _is_na(value):
        return None
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return 1.0 if float(value) >= 1 else 0.0
    lowered = str(value).strip().lower()
    if lowered in {"1", "true", "yes", "y"}:
        return 1.0
    if lowered in {"0", "false", "no", "n"}:
        return 0.0
    return None


def _safe_float_optional(value: Any) -> float | None:
    if _is_na(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _scale_grade_value(g_raw: float, dataset_max_grade: float) -> float:
    if dataset_max_grade <= 1.05 and g_raw <= 1.05:
        return min(100, g_raw * 100)
    return g_raw


def normalize_edx_records(raw_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grades: list[float] = []
    for r in raw_records:
        g = _safe_float_optional(_lookup(r, "grade"))
        if g is not None:
            grades.append(g)
    grade_max = max(grades) if grades else 0.0

    rows: list[dict[str, Any]] = []
    for r in raw_records:
        cid = _lookup(r, "course_id", "courseid")
        gid = _lookup(r, "userid_di", "userid", "student_id", "user_id")
        if _is_na(cid) or _is_na(gid):
            continue

        g_raw = _safe_float_optional(_lookup(r, "grade"))
        score_percent: float | None = None
        if g_raw is not None and grades:
            score_percent = _scale_grade_value(g_raw, grade_max)

        rows.append(
            {
                "user_id": str(gid).strip(),
                "course_id": str(cid).strip(),
                "nevents": _safe_float_optional(_lookup(r, "nevents")),
                "ndays_act": _safe_float_optional(_lookup(r, "ndays_act")),
                "nplay_video": _safe_float_optional(_lookup(r, "nplay_video")),
                "nchapters": _safe_float_optional(_lookup(r, "nchapters")),
                "nforum_posts": _safe_float_optional(_lookup(r, "nforum_posts")),
                "score": score_percent,
                "grade_raw": g_raw,
                "viewed": _truthy_bin(_lookup(r, "viewed")),
                "explored": _truthy_bin(_lookup(r, "explored")),
                "certified": _truthy_bin(_lookup(r, "certified", "certificate")),
                "last_event": _parse_di_date(_lookup(r, "last_event_di", "last_event", "lastevent")),
                "start_time": _parse_di_date(_lookup(r, "start_time_di", "start_time", "launch_time")),
                "registered": _truthy_bin(_lookup(r, "registered")),
            }
        )
    return rows


def apply_edx_filters(
    rows: list[dict[str, Any]],
    start_date: str | None,
    end_date: str | None,
    course: str | None,
) -> list[dict[str, Any]]:
    filtered = rows
    if course:
        c = course.strip()
        filtered = [r for r in filtered if r["course_id"] == c]

    start_dt = datetime.fromisoformat(start_date).date() if start_date else None
    end_dt = datetime.fromisoformat(end_date).date() if end_date else None
    if not start_dt and not end_dt:
        return filtered

    narrowed: list[dict[str, Any]] = []
    for r in filtered:
        ts = r.get("last_event") or r.get("start_time")
        if not isinstance(ts, datetime):
            narrowed.append(r)
            continue
        dt = ts.date()
        if start_dt and dt < start_dt:
            continue
        if end_dt and dt > end_dt:
            continue
        narrowed.append(r)
    return narrowed


def _mean_optional(values: list[float]) -> float:
    clean = [v for v in values if isinstance(v, (int, float))]
    return round(mean(clean), 2) if clean else 0.0


def edx_overview(rows: list[dict[str, Any]]) -> dict[str, Any]:
    students = {r["user_id"] for r in rows}
    scores = [r["score"] for r in rows if isinstance(r["score"], (int, float))]

    viewed = [r["viewed"] for r in rows if r["viewed"] is not None]
    explored = [r["explored"] for r in rows if r["explored"] is not None]
    certified = [r["certified"] for r in rows if r["certified"] is not None]

    nevents_series = [r["nevents"] for r in rows if r["nevents"] is not None]
    ndays_series = [r["ndays_act"] for r in rows if r["ndays_act"] is not None]
    chapters_series = [r["nchapters"] for r in rows if r["nchapters"] is not None]
    video_series = [r["nplay_video"] for r in rows if r["nplay_video"] is not None]
    forum_series = [r["nforum_posts"] for r in rows if r["nforum_posts"] is not None]

    total_platform_events = int(sum(float(x) for x in nevents_series))

    def pct_rate(flags: list[float]) -> float:
        if not flags:
            return 0.0
        return round(100 * sum(flags) / len(flags), 2)

    events_grade_r = edx_pearson_nevents_grade(rows)

    return {
        "dataset_mode": "edx_person_course",
        "dataset_label": "Kaggle / Open edX person-course metrics (HarvardX-style columns)",
        "total_students": len(students),
        "total_enrollments": len(rows),
        "total_interactions": total_platform_events,
        "average_score": round(mean(scores), 2) if scores else 0.0,
        "average_grade_raw_note": "% scale when grades are recorded as proportions (0-1).",
        "average_study_duration": _mean_optional([float(x) for x in ndays_series]),
        "duration_unit": "avg_active_days",
        "average_events_per_enrollment": _mean_optional([float(x) for x in nevents_series]),
        "average_video_plays": _mean_optional([float(x) for x in video_series]),
        "average_chapters": _mean_optional([float(x) for x in chapters_series]),
        "average_forum_posts": _mean_optional([float(x) for x in forum_series]),
        "viewed_rate_percent": pct_rate(viewed),
        "explored_rate_percent": pct_rate(explored),
        "certification_rate_percent": pct_rate(certified),
        "events_grade_correlation": events_grade_r,
    }


def edx_engagement_trend(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    month_bucket: dict[str, float] = defaultdict(float)
    for r in rows:
        dt = r.get("last_event") or r.get("start_time")
        if not isinstance(dt, datetime):
            continue
        key = dt.strftime("%Y-%m")
        ev = r.get("nevents")
        month_bucket[key] += float(ev) if ev is not None else 0.0

    ordered = sorted(month_bucket.items())
    trimmed = ordered[-24:]
    return [{"date": k, "interactions": int(v)} for k, v in trimmed]


def edx_activity_breakdown(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "activity": "Avg platform events/enrollment",
            "count": _mean_optional([float(r["nevents"]) for r in rows if r["nevents"] is not None]),
        },
        {"activity": "Avg active days/enrollment", "count": _mean_optional([float(r["ndays_act"]) for r in rows if r["ndays_act"] is not None])},
        {"activity": "Avg video plays/enrollment", "count": _mean_optional([float(r["nplay_video"]) for r in rows if r["nplay_video"] is not None])},
        {"activity": "Avg chapters/enrollment", "count": _mean_optional([float(r["nchapters"]) for r in rows if r["nchapters"] is not None])},
        {"activity": "Avg forum posts/enrollment", "count": _mean_optional([float(r["nforum_posts"]) for r in rows if r["nforum_posts"] is not None])},
    ]


def edx_score_distribution(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
    scores = [r["score"] for r in rows if isinstance(r["score"], (int, float))]
    for raw in scores:
        s = float(raw)
        if s <= 20:
            buckets["0-20"] += 1
        elif s <= 40:
            buckets["21-40"] += 1
        elif s <= 60:
            buckets["41-60"] += 1
        elif s <= 80:
            buckets["61-80"] += 1
        else:
            buckets["81-100"] += 1
    if not scores:
        return [{"range": k, "students": 0} for k in buckets]
    return [{"range": k, "students": value} for k, value in buckets.items()]


def edx_active_days_distribution(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    labels = ["0", "1-3", "4-7", "8-14", "15-30", "31+"]
    counts = defaultdict(int)

    for r in rows:
        nd = r.get("ndays_act")
        if nd is None:
            continue
        try:
            d = float(nd)
        except (TypeError, ValueError):
            continue
        if d <= 0:
            counts["0"] += 1
        elif d <= 3:
            counts["1-3"] += 1
        elif d <= 7:
            counts["4-7"] += 1
        elif d <= 14:
            counts["8-14"] += 1
        elif d <= 30:
            counts["15-30"] += 1
        else:
            counts["31+"] += 1

    return [{"bucket": lbl, "enrollments": counts[lbl]} for lbl in labels]


def edx_at_risk(limit: int, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        grouped[r["user_id"]].append(r)

    now = datetime.utcnow()
    ranked: list[dict[str, Any]] = []

    for uid, recs in grouped.items():
        scores = [r["score"] for r in recs if isinstance(r["score"], (int, float))]
        avg_score = mean(scores) if scores else 0.0
        ne_mean = mean([float(r["nevents"]) for r in recs if r["nevents"] is not None]) if any(r["nevents"] is not None for r in recs) else 0
        ndays_mean = (
            mean([float(r["ndays_act"]) for r in recs if r["ndays_act"] is not None])
            if any(r["ndays_act"] is not None for r in recs)
            else 0
        )
        certs = [r["certified"] for r in recs if r["certified"] is not None]
        cert_ratio = sum(certs) / len(certs) if certs else 0.0
        recent_ts = None
        for r in recs:
            cand = r.get("last_event")
            if isinstance(cand, datetime) and (recent_ts is None or cand > recent_ts):
                recent_ts = cand

        inactive_days = (now - recent_ts).days if recent_ts else 999

        risk = 0
        if avg_score < 55:
            risk += 35
        if ne_mean < 50:
            risk += 35
        if ndays_mean < 3:
            risk += 20
        if cert_ratio < 0.1:
            risk += 10
        if inactive_days > 60:
            risk += 15

        ranked.append(
            {
                "student_id": uid,
                "avg_score": round(avg_score, 2),
                "total_duration_minutes": round(ndays_mean, 2),
                "avg_events": round(ne_mean, 2),
                "inactivity_days": inactive_days if recent_ts else 999,
                "risk_score": min(round(risk), 100),
            }
        )

    return sorted(ranked, key=lambda x: x["risk_score"], reverse=True)[:limit]


def edx_engagement_grade_points(rows: list[dict[str, Any]]) -> list[dict[str, float]]:
    points: list[dict[str, float]] = []
    for r in rows:
        if not isinstance(r.get("score"), (int, float)) or r["nevents"] is None:
            continue
        points.append({"nevents": float(r["nevents"]), "grade_percent": float(r["score"])})
        if len(points) >= 500:
            break
    return points


def edx_pearson_nevents_grade(rows: list[dict[str, Any]]) -> float | None:
    xs: list[float] = []
    ys: list[float] = []
    for r in rows:
        if r["nevents"] is None:
            continue
        if not isinstance(r.get("score"), (int, float)):
            continue
        xs.append(float(r["nevents"]))
        ys.append(float(r["score"]))
    return _pearson(xs, ys)


def edx_available_courses(rows: list[dict[str, Any]]) -> list[str]:
    return sorted({r["course_id"] for r in rows})


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 12 or len(ys) != n:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
    den_x = sum((xs[i] - mx) ** 2 for i in range(n))
    den_y = sum((ys[i] - my) ** 2 for i in range(n))
    if den_x <= 0 or den_y <= 0:
        return None
    return round(num / (sqrt(den_x) * sqrt(den_y)), 4)


def edx_student_detail(student_id: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        return {}

    scores = [r["score_percent"] for r in records if r.get("score_percent") is not None]
    avg_score = sum(scores) / len(scores) if scores else 0.0
    nevents = sum(r.get("nevents") or 0 for r in records)
    ndays = sum(r.get("ndays_act") or 0 for r in records)
    nvideos = sum(r.get("nplay_video") or 0 for r in records)
    nchapters = sum(r.get("nchapters") or 0 for r in records)
    nforum = sum(r.get("nforum_posts") or 0 for r in records)
    certified = any((r.get("certified") or 0) >= 1 for r in records)

    last_dates = [_parse_di_date(r.get("last_event_DI")) for r in records if r.get("last_event_DI")]
    last_event = max(last_dates) if last_dates else None
    inactivity = (datetime.utcnow() - last_event).days if last_event else 999

    courses = [r.get("course_id", "—") for r in records]

    risk_score = 0
    if avg_score < 40:
        risk_score += 50
    elif avg_score < 60:
        risk_score += 25
    if ndays < 5:
        risk_score += 30
    if inactivity > 30:
        risk_score += 20

    activity_breakdown = []
    if nvideos > 0:
        activity_breakdown.append({"activity": "video_watch", "count": int(nvideos)})
    if nforum > 0:
        activity_breakdown.append({"activity": "forum_post", "count": int(nforum)})
    if nchapters > 0:
        activity_breakdown.append({"activity": "chapter_view", "count": int(nchapters)})

    return {
        "student_id": student_id,
        "avg_score": round(avg_score, 2),
        "total_duration_minutes": int(ndays),
        "inactivity_days": inactivity,
        "total_events": int(nevents),
        "risk_score": min(risk_score, 100),
        "certified": certified,
        "courses": courses,
        "activity_breakdown": activity_breakdown,
        "timeline": [],
        "score_trend": [
            {"date": r.get("last_event_DI", ""), "avg_score": r["score_percent"]}
            for r in sorted(records, key=lambda x: x.get("last_event_DI") or "")
            if r.get("score_percent") is not None and r.get("last_event_DI")
        ],
    }
