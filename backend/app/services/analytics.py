from __future__ import annotations

import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any

from pymongo.errors import PyMongoError

from app.db import collection, database
from app.services import kaggle_edx

Record = dict[str, Any]

_CACHE: dict[str, Any] = {}
_CACHE_TTL = 300  # 5 minutes


def _cache_key(dataset_id: str | None) -> str:
    return dataset_id or "__default__"


def _get_cached(dataset_id: str | None) -> list[Record] | None:
    key = _cache_key(dataset_id)
    entry = _CACHE.get(key)
    if entry and time.time() - entry["ts"] < _CACHE_TTL:
        return entry["data"]
    return None


def _set_cache(dataset_id: str | None, data: list[Record]) -> None:
    _CACHE[_cache_key(dataset_id)] = {"data": data, "ts": time.time()}


def _get_result_cache(key: str) -> Any | None:
    entry = _CACHE.get(f"result:{key}")
    if entry and time.time() - entry["ts"] < _CACHE_TTL:
        return entry["data"]
    return None


def _set_result_cache(key: str, data: Any) -> None:
    _CACHE[f"result:{key}"] = {"data": data, "ts": time.time()}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_ts(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not value:
        return None

    candidates = [
        str(value),
        str(value).replace("Z", "+00:00"),
    ]
    for candidate in candidates:
        try:
            return datetime.fromisoformat(candidate)
        except ValueError:
            continue
    return None


def _get_user_id(record: Record) -> str:
    for key in ("user_id", "student_id", "learner_id", "userid_di", "userid"):
        val = record.get(key)
        if val is not None and str(val).strip() and str(val).strip().upper() not in {"NA", "NAN"}:
            return str(val)
    return "unknown"


def _get_event_type(record: Record) -> str:
    for key in ("event_type", "activity_type", "interaction_type", "action"):
        if record.get(key):
            return str(record[key]).lower()
    return "unknown"


def _get_course(record: Record) -> str:
    for key in ("course", "course_id", "course_name", "courseid"):
        val = record.get(key)
        if val is not None and str(val).strip():
            return str(val)
    return "General"


def _mock_event_data() -> list[Record]:
    now = datetime.utcnow()
    mock: list[Record] = []
    event_types = ["video_watch", "quiz_attempt", "forum_post", "resource_download"]
    courses = ["Python Basics", "Data Analytics", "Machine Learning"]
    for idx in range(1, 51):
        for day_shift in range(10):
            mock.append(
                {
                    "user_id": f"S{idx:03d}",
                    "event_type": event_types[(idx + day_shift) % len(event_types)],
                    "course": courses[(idx + day_shift) % len(courses)],
                    "score": (idx * 3 + day_shift * 2) % 100,
                    "duration_minutes": 10 + ((idx + day_shift) % 45),
                    "timestamp": now - timedelta(days=day_shift),
                }
            )
    return mock


async def _load_raw_records(dataset_id: str | None = None) -> list[Record]:
    cached = _get_cached(dataset_id)
    if cached is not None:
        return cached

    col = database[f"ds_{dataset_id}"] if dataset_id else collection
    try:
        records = await col.find({}, {"_id": 0}).to_list(length=50_000)
    except PyMongoError:
        records = []

    if not records:
        return _mock_event_data()

    _set_cache(dataset_id, records)
    return records


_EDX_NORMALIZED: dict[int, list[dict[str, Any]]] = {}


def _edx_pipeline(
    records: list[Record],
    start_date: str | None,
    end_date: str | None,
    course: str | None,
) -> list[dict[str, Any]]:
    rid = id(records)
    if rid not in _EDX_NORMALIZED:
        _EDX_NORMALIZED.clear()
        _EDX_NORMALIZED[rid] = kaggle_edx.normalize_edx_records(records)
    base = _EDX_NORMALIZED[rid]
    return kaggle_edx.apply_edx_filters(base, start_date, end_date, course)


async def overview_metrics(
    start_date: str | None = None,
    end_date: str | None = None,
    course: str | None = None,
    dataset_id: str | None = None,
) -> dict[str, Any]:
    raw = await _load_raw_records(dataset_id)
    if kaggle_edx.infer_edx_person_course(raw):
        rows = _edx_pipeline(raw, start_date, end_date, course)
        data = kaggle_edx.edx_overview(rows)
        if not rows:
            data["note"] = "No enrollment rows matched the current filters."
        return data

    filtered = _apply_event_filters(raw, start_date=start_date, end_date=end_date, course=course)
    students = {_get_user_id(r) for r in filtered}
    avg_score = sum(_safe_float(r.get("score")) for r in filtered) / max(len(filtered), 1)
    avg_duration = sum(_safe_float(r.get("duration_minutes")) for r in filtered) / max(len(filtered), 1)
    cutoff = datetime.utcnow() - timedelta(days=7)
    recent_active = 0
    for uid in students:
        user_records = [r for r in filtered if _get_user_id(r) == uid]
        latest_ts = max((_parse_ts(r.get("timestamp")) for r in user_records), default=None)
        if latest_ts and latest_ts >= cutoff:
            recent_active += 1

    return {
        "dataset_mode": "event_stream",
        "dataset_label": "Granular interaction timeline. Import the Kaggle/Open edX CSV to unlock person-course charts.",
        "total_students": len(students),
        "total_enrollments": len(filtered),
        "total_interactions": len(filtered),
        "average_score": round(avg_score, 2),
        "average_study_duration": round(avg_duration, 2),
        "duration_unit": "minutes_avg_per_event",
        "active_last_7_days": recent_active,
        "average_events_per_enrollment": round(len(filtered) / max(len(students), 1), 2),
        "average_video_plays": 0,
        "average_chapters": 0,
        "average_forum_posts": 0,
        "viewed_rate_percent": 0,
        "explored_rate_percent": 0,
        "certification_rate_percent": 0,
        "events_grade_correlation": None,
    }


async def engagement_trend(
    start_date: str | None = None,
    end_date: str | None = None,
    course: str | None = None,
    dataset_id: str | None = None,
) -> list[dict[str, Any]]:
    raw = await _load_raw_records(dataset_id)
    if kaggle_edx.infer_edx_person_course(raw):
        rows = _edx_pipeline(raw, start_date, end_date, course)
        return kaggle_edx.edx_engagement_trend(rows)

    records = _apply_event_filters(raw, start_date=start_date, end_date=end_date, course=course)
    day_bucket: dict[str, int] = defaultdict(int)
    for record in records:
        ts = _parse_ts(record.get("timestamp"))
        if not ts:
            continue
        day_bucket[ts.strftime("%Y-%m-%d")] += 1

    return [{"date": day, "interactions": day_bucket[day]} for day in sorted(day_bucket.keys())][-30:]


async def activity_breakdown(
    start_date: str | None = None,
    end_date: str | None = None,
    course: str | None = None,
    dataset_id: str | None = None,
) -> list[dict[str, Any]]:
    raw = await _load_raw_records(dataset_id)
    if kaggle_edx.infer_edx_person_course(raw):
        rows = _edx_pipeline(raw, start_date, end_date, course)
        return kaggle_edx.edx_activity_breakdown(rows)

    records = _apply_event_filters(raw, start_date=start_date, end_date=end_date, course=course)
    counter = Counter(_get_event_type(r) for r in records)
    return [{"activity": activity, "count": count} for activity, count in counter.most_common()]


async def score_distribution(
    start_date: str | None = None,
    end_date: str | None = None,
    course: str | None = None,
    dataset_id: str | None = None,
) -> list[dict[str, Any]]:
    raw = await _load_raw_records(dataset_id)
    if kaggle_edx.infer_edx_person_course(raw):
        rows = _edx_pipeline(raw, start_date, end_date, course)
        return kaggle_edx.edx_score_distribution(rows)

    records = _apply_event_filters(raw, start_date=start_date, end_date=end_date, course=course)
    buckets = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
    for record in records:
        score = _safe_int(record.get("score"))
        if score <= 20:
            buckets["0-20"] += 1
        elif score <= 40:
            buckets["21-40"] += 1
        elif score <= 60:
            buckets["41-60"] += 1
        elif score <= 80:
            buckets["61-80"] += 1
        else:
            buckets["81-100"] += 1

    return [{"range": key, "students": value} for key, value in buckets.items()]


async def at_risk_students(
    limit: int = 10,
    start_date: str | None = None,
    end_date: str | None = None,
    course: str | None = None,
    dataset_id: str | None = None,
) -> list[dict[str, Any]]:
    raw = await _load_raw_records(dataset_id)
    if kaggle_edx.infer_edx_person_course(raw):
        rows = _edx_pipeline(raw, start_date, end_date, course)
        return kaggle_edx.edx_at_risk(limit, rows)

    records = _apply_event_filters(raw, start_date=start_date, end_date=end_date, course=course)
    grouped: dict[str, list[Record]] = defaultdict(list)
    for record in records:
        grouped[_get_user_id(record)].append(record)

    risk_rows: list[dict[str, Any]] = []
    for uid, user_records in grouped.items():
        avg_score = sum(_safe_float(r.get("score")) for r in user_records) / max(len(user_records), 1)
        total_duration = sum(_safe_float(r.get("duration_minutes")) for r in user_records)
        latest = max((_parse_ts(r.get("timestamp")) for r in user_records), default=None)
        inactivity_days = (datetime.utcnow() - latest).days if latest else 999

        risk_score = 0
        if avg_score < 40:
            risk_score += 50
        elif avg_score < 60:
            risk_score += 25
        if total_duration < 120:
            risk_score += 30
        if inactivity_days > 7:
            risk_score += 20

        risk_rows.append(
            {
                "student_id": uid,
                "avg_score": round(avg_score, 2),
                "total_duration_minutes": round(total_duration, 2),
                "avg_events": 0,
                "inactivity_days": inactivity_days,
                "risk_score": min(risk_score, 100),
            }
        )

    return sorted(risk_rows, key=lambda x: x["risk_score"], reverse=True)[:limit]


async def active_days_histogram(
    start_date: str | None = None,
    end_date: str | None = None,
    course: str | None = None,
    dataset_id: str | None = None,
) -> list[dict[str, Any]]:
    raw = await _load_raw_records(dataset_id)
    if not kaggle_edx.infer_edx_person_course(raw):
        return []
    rows = _edx_pipeline(raw, start_date, end_date, course)
    return kaggle_edx.edx_active_days_distribution(rows)


async def engagement_grade_scatter(
    start_date: str | None = None,
    end_date: str | None = None,
    course: str | None = None,
    dataset_id: str | None = None,
) -> dict[str, Any]:
    raw = await _load_raw_records(dataset_id)
    if not kaggle_edx.infer_edx_person_course(raw):
        return {"dataset_mode": "event_stream", "points": [], "hint": "Requires person–course edX CSV fields (nevents, grade)."}

    rows = _edx_pipeline(raw, start_date, end_date, course)
    correlation = kaggle_edx.edx_pearson_nevents_grade(rows)
    return {
        "dataset_mode": "edx_person_course",
        "correlation": correlation,
        "points": kaggle_edx.edx_engagement_grade_points(rows),
    }


async def available_courses(dataset_id: str | None = None) -> list[str]:
    raw = await _load_raw_records(dataset_id)
    if kaggle_edx.infer_edx_person_course(raw):
        rows = _edx_pipeline(raw, None, None, None)
        return kaggle_edx.edx_available_courses(rows)
    courses = {_get_course(r) for r in raw}
    return sorted(courses)


async def student_detail(
    student_id: str,
    dataset_id: str | None = None,
) -> dict[str, Any]:
    raw = await _load_raw_records(dataset_id)

    if kaggle_edx.infer_edx_person_course(raw):
        rows = _edx_pipeline(raw, None, None, None)
        records = [r for r in rows if r.get("user_id") == student_id]
        if not records:
            return {}
        return kaggle_edx.edx_student_detail(student_id, records)

    records = [r for r in raw if _get_user_id(r) == student_id]
    if not records:
        return {}

    avg_score = sum(_safe_float(r.get("score")) for r in records) / max(len(records), 1)
    total_dur = sum(_safe_float(r.get("duration_minutes")) for r in records)
    latest = max((_parse_ts(r.get("timestamp")) for r in records), default=None)
    inactivity = (datetime.utcnow() - latest).days if latest else 999

    timeline: dict[str, int] = defaultdict(int)
    score_by_date: dict[str, list] = defaultdict(list)
    for r in records:
        ts = _parse_ts(r.get("timestamp"))
        if ts:
            day = ts.strftime("%Y-%m-%d")
            timeline[day] += 1
            score = r.get("score")
            if score is not None:
                score_by_date[day].append(_safe_float(score))

    activity_counter = Counter(_get_event_type(r) for r in records)

    risk_score = 0
    if avg_score < 40:
        risk_score += 50
    elif avg_score < 60:
        risk_score += 25
    if total_dur < 120:
        risk_score += 30
    if inactivity > 7:
        risk_score += 20

    return {
        "student_id": student_id,
        "avg_score": round(avg_score, 2),
        "total_duration_minutes": round(total_dur, 2),
        "inactivity_days": inactivity,
        "total_events": len(records),
        "risk_score": min(risk_score, 100),
        "courses": list({_get_course(r) for r in records}),
        "activity_breakdown": [{"activity": k, "count": v} for k, v in activity_counter.most_common()],
        "timeline": [{"date": d, "events": timeline[d]} for d in sorted(timeline.keys())],
        "score_trend": [
            {"date": d, "avg_score": round(sum(vals) / len(vals), 2)}
            for d, vals in sorted(score_by_date.items())
        ],
    }


async def compare_students(
    student_a: str,
    student_b: str,
    dataset_id: str | None = None,
) -> dict[str, Any]:
    raw = await _load_raw_records(dataset_id)

    if kaggle_edx.infer_edx_person_course(raw):
        rows = _edx_pipeline(raw, None, None, None)

        def _edx_summarise(uid: str) -> dict:
            recs = [r for r in rows if r.get("user_id") == uid]
            if not recs:
                return {"student_id": uid, "found": False}
            avg_score = sum(_safe_float(r.get("score_percent", 0)) for r in recs) / max(len(recs), 1)
            nevents = sum(_safe_float(r.get("nevents", 0)) for r in recs)
            ndays = sum(_safe_float(r.get("ndays_act", 0)) for r in recs)
            last_event = max(
                (_parse_ts(r.get("last_event_DI")) for r in recs if r.get("last_event_DI")),
                default=None,
            )
            inactivity = (datetime.utcnow() - last_event).days if last_event else 999
            courses = list({r.get("course_id", "—") for r in recs})
            certified = any(_safe_float(r.get("certified", 0)) >= 1 for r in recs)
            return {
                "student_id": uid,
                "found": True,
                "avg_score": round(avg_score, 2),
                "total_events": int(nevents),
                "total_duration_minutes": int(ndays),
                "inactivity_days": inactivity,
                "top_activity": "certified" if certified else "not certified",
                "courses": courses,
            }

        return {"a": _edx_summarise(student_a), "b": _edx_summarise(student_b)}

    def _summarise(uid: str) -> dict:
        recs = [r for r in raw if _get_user_id(r) == uid]
        if not recs:
            return {"student_id": uid, "found": False}
        avg_score = sum(_safe_float(r.get("score")) for r in recs) / max(len(recs), 1)
        total_dur = sum(_safe_float(r.get("duration_minutes")) for r in recs)
        latest = max((_parse_ts(r.get("timestamp")) for r in recs), default=None)
        inactivity = (datetime.utcnow() - latest).days if latest else 999
        counter = Counter(_get_event_type(r) for r in recs)
        return {
            "student_id": uid,
            "found": True,
            "avg_score": round(avg_score, 2),
            "total_events": len(recs),
            "total_duration_minutes": round(total_dur, 2),
            "inactivity_days": inactivity,
            "top_activity": counter.most_common(1)[0][0] if counter else "—",
            "courses": list({_get_course(r) for r in recs}),
        }

    return {"a": _summarise(student_a), "b": _summarise(student_b)}


async def heatmap_data(dataset_id: str | None = None) -> list[dict[str, Any]]:
    raw = await _load_raw_records(dataset_id)
    bucket: dict[str, int] = defaultdict(int)
    cutoff = datetime.utcnow() - timedelta(days=365)
    for r in raw:
        ts = _parse_ts(r.get("timestamp"))
        if ts and ts >= cutoff:
            bucket[ts.strftime("%Y-%m-%d")] += 1
    return [{"date": d, "count": bucket[d]} for d in sorted(bucket.keys())]


async def list_student_ids(dataset_id: str | None = None) -> list[str]:
    raw = await _load_raw_records(dataset_id)
    if kaggle_edx.infer_edx_person_course(raw):
        rows = _edx_pipeline(raw, None, None, None)
        ids = sorted({r["user_id"] for r in rows if r.get("user_id")})
    else:
        ids = sorted({_get_user_id(r) for r in raw if _get_user_id(r) != "unknown"})
    return ids


async def export_data(
    fmt: str = "csv",
    start_date: str | None = None,
    end_date: str | None = None,
    course: str | None = None,
    dataset_id: str | None = None,
) -> bytes:
    import io
    import pandas as pd

    raw = await _load_raw_records(dataset_id)
    filtered = _apply_event_filters(raw, start_date=start_date, end_date=end_date, course=course)
    df = pd.DataFrame(filtered)

    buf = io.BytesIO()
    if fmt == "excel":
        df.to_excel(buf, index=False, engine="openpyxl")
    else:
        df.to_csv(buf, index=False)
    return buf.getvalue()


def _apply_event_filters(
    records: list[Record],
    start_date: str | None = None,
    end_date: str | None = None,
    course: str | None = None,
) -> list[Record]:
    filtered = records
    if course:
        course_lower = course.strip().lower()
        filtered = [r for r in filtered if _get_course(r).lower() == course_lower]

    start_dt = _parse_ts(start_date) if start_date else None
    end_dt = _parse_ts(end_date) if end_date else None
    if start_dt or end_dt:
        date_filtered: list[Record] = []
        for record in filtered:
            ts = _parse_ts(record.get("timestamp"))
            if not ts:
                continue
            if start_dt and ts < start_dt:
                continue
            if end_dt and ts > end_dt:
                continue
            date_filtered.append(record)
        filtered = date_filtered

    return filtered
