from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
import io

from app.auth import admin_only
from app.services.analytics import (
    active_days_histogram,
    activity_breakdown,
    at_risk_students,
    available_courses,
    compare_students,
    engagement_grade_scatter,
    engagement_trend,
    export_data,
    heatmap_data,
    list_student_ids,
    overview_metrics,
    score_distribution,
    student_detail,
)
from app.services.ai_insights import generate_insights
from app.services.ml_analytics import detect_anomalies, forecast_engagement, ml_at_risk

router = APIRouter(prefix="/analytics", tags=["analytics"])

# ── helpers ──────────────────────────────────────────────────────────────────

def _filters(
    start_date: str | None,
    end_date: str | None,
    course: str | None,
    dataset_id: str | None,
) -> dict:
    return dict(start_date=start_date, end_date=end_date, course=course, dataset_id=dataset_id)


# ── existing endpoints ────────────────────────────────────────────────────────

@router.get("/overview")
async def get_overview(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    course: str | None = Query(default=None),
    dataset_id: str | None = Query(default=None),
):
    return await overview_metrics(**_filters(start_date, end_date, course, dataset_id))


@router.get("/engagement-trend")
async def get_engagement_trend(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    course: str | None = Query(default=None),
    dataset_id: str | None = Query(default=None),
):
    return await engagement_trend(**_filters(start_date, end_date, course, dataset_id))


@router.get("/activity-breakdown")
async def get_activity_breakdown(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    course: str | None = Query(default=None),
    dataset_id: str | None = Query(default=None),
):
    return await activity_breakdown(**_filters(start_date, end_date, course, dataset_id))


@router.get("/score-distribution")
async def get_score_distribution(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    course: str | None = Query(default=None),
    dataset_id: str | None = Query(default=None),
):
    return await score_distribution(**_filters(start_date, end_date, course, dataset_id))


@router.get("/at-risk-students")
async def get_at_risk_students(
    limit: int = Query(default=10, ge=1, le=100),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    course: str | None = Query(default=None),
    dataset_id: str | None = Query(default=None),
    _admin=Depends(admin_only),
):
    return await at_risk_students(limit=limit, **_filters(start_date, end_date, course, dataset_id))


@router.get("/courses")
async def get_courses(dataset_id: str | None = Query(default=None)):
    return await available_courses(dataset_id=dataset_id)


@router.get("/active-days-histogram")
async def get_active_days_histogram(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    course: str | None = Query(default=None),
    dataset_id: str | None = Query(default=None),
):
    return await active_days_histogram(**_filters(start_date, end_date, course, dataset_id))


@router.get("/engagement-vs-grade")
async def get_engagement_vs_grade(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    course: str | None = Query(default=None),
    dataset_id: str | None = Query(default=None),
):
    return await engagement_grade_scatter(**_filters(start_date, end_date, course, dataset_id))


# ── AI insights ───────────────────────────────────────────────────────────────

@router.get("/ai-insights")
async def get_ai_insights(
    provider: str = Query(default="groq"),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    course: str | None = Query(default=None),
    dataset_id: str | None = Query(default=None),
):
    f = _filters(start_date, end_date, course, dataset_id)
    import asyncio
    overview, activity, risk_rows = await asyncio.gather(
        overview_metrics(**f),
        activity_breakdown(**f),
        at_risk_students(limit=100, **f),
    )
    return await generate_insights(overview, activity, len(risk_rows), provider=provider)


# ── ML / forecasting / anomaly ────────────────────────────────────────────────

@router.get("/ml-risk")
async def get_ml_risk(
    limit: int = Query(default=10, ge=1, le=100),
    dataset_id: str | None = Query(default=None),
    _admin=Depends(admin_only),
):
    from app.services.analytics import _load_raw_records
    raw = await _load_raw_records(dataset_id)
    return ml_at_risk(raw, limit=limit)


@router.get("/forecast")
async def get_forecast(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    course: str | None = Query(default=None),
    dataset_id: str | None = Query(default=None),
):
    trend = await engagement_trend(**_filters(start_date, end_date, course, dataset_id))
    return forecast_engagement(trend)


@router.get("/anomalies")
async def get_anomalies(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    course: str | None = Query(default=None),
    dataset_id: str | None = Query(default=None),
):
    trend = await engagement_trend(**_filters(start_date, end_date, course, dataset_id))
    return {"anomalies": detect_anomalies(trend)}


# ── student profile & comparison ──────────────────────────────────────────────

@router.get("/students")
async def get_student_ids(dataset_id: str | None = Query(default=None)):
    return await list_student_ids(dataset_id=dataset_id)


@router.get("/student/{student_id}")
async def get_student_detail(
    student_id: str,
    dataset_id: str | None = Query(default=None),
):
    data = await student_detail(student_id, dataset_id=dataset_id)
    if not data:
        raise HTTPException(404, f"Student '{student_id}' not found")
    return data


@router.get("/compare")
async def get_compare(
    a: str = Query(...),
    b: str = Query(...),
    dataset_id: str | None = Query(default=None),
):
    return await compare_students(a, b, dataset_id=dataset_id)


# ── heatmap ───────────────────────────────────────────────────────────────────

@router.get("/heatmap")
async def get_heatmap(dataset_id: str | None = Query(default=None)):
    return await heatmap_data(dataset_id=dataset_id)


# ── export ────────────────────────────────────────────────────────────────────

@router.get("/export")
async def get_export(
    fmt: str = Query(default="csv"),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    course: str | None = Query(default=None),
    dataset_id: str | None = Query(default=None),
):
    raw_bytes = await export_data(
        fmt=fmt,
        start_date=start_date,
        end_date=end_date,
        course=course,
        dataset_id=dataset_id,
    )
    if fmt == "excel":
        media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = "analytics_export.xlsx"
    else:
        media = "text/csv"
        filename = "analytics_export.csv"

    return StreamingResponse(
        io.BytesIO(raw_bytes),
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
