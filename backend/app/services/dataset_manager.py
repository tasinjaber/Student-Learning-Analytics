from __future__ import annotations

import io
import re
import uuid
from datetime import datetime, timezone
from typing import Any

import pandas as pd
from pymongo.errors import PyMongoError

from app.db import database

_META = database["datasets"]


def _ds_col(dataset_id: str):
    return database[f"ds_{dataset_id}"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _df_to_records(df: pd.DataFrame) -> list[dict]:
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    return df.where(pd.notna(df), None).to_dict(orient="records")


async def list_datasets() -> list[dict[str, Any]]:
    default = {
        "dataset_id": None,
        "name": "Default (Kaggle / MongoDB)",
        "source": "default",
        "record_count": None,
        "created_at": None,
    }
    try:
        docs = await _META.find({}, {"_id": 0}).to_list(length=200)
    except PyMongoError:
        docs = []
    return [default, *docs]


async def save_from_bytes(
    raw: bytes,
    filename: str,
    name: str,
) -> dict[str, Any]:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "csv"
    if ext in ("xlsx", "xls"):
        df = pd.read_excel(io.BytesIO(raw))
    else:
        df = pd.read_csv(io.BytesIO(raw))

    records = _df_to_records(df)
    ds_id = uuid.uuid4().hex[:12]
    col = _ds_col(ds_id)
    if records:
        await col.insert_many(records)

    meta = {
        "dataset_id": ds_id,
        "name": name,
        "source": "upload",
        "filename": filename,
        "record_count": len(records),
        "created_at": _now(),
    }
    await _META.insert_one({**meta, "_id": ds_id})
    return meta


async def save_from_url(url: str, name: str) -> dict[str, Any]:
    import httpx

    csv_url = _resolve_url(url)
    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        resp = await client.get(csv_url)
        resp.raise_for_status()

    df = pd.read_csv(io.BytesIO(resp.content))
    records = _df_to_records(df)
    ds_id = uuid.uuid4().hex[:12]
    col = _ds_col(ds_id)
    if records:
        await col.insert_many(records)

    meta = {
        "dataset_id": ds_id,
        "name": name,
        "source": "url",
        "source_url": url,
        "record_count": len(records),
        "created_at": _now(),
    }
    await _META.insert_one({**meta, "_id": ds_id})
    return meta


def _resolve_url(url: str) -> str:
    sheets_match = re.search(r"docs\.google\.com/spreadsheets/d/([^/]+)", url)
    if sheets_match:
        sheet_id = sheets_match.group(1)
        gid_match = re.search(r"gid=(\d+)", url)
        gid = gid_match.group(1) if gid_match else "0"
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    return url


async def delete_dataset(dataset_id: str) -> bool:
    try:
        await _ds_col(dataset_id).drop()
        result = await _META.delete_one({"_id": dataset_id})
        return result.deleted_count > 0
    except PyMongoError:
        return False


async def save_from_kaggle(
    dataset_path: str,
    name: str,
    kaggle_username: str,
    kaggle_key: str,
) -> dict[str, Any]:
    import json
    import os
    import pathlib
    import glob as _glob

    # Write credentials temporarily
    kaggle_dir = pathlib.Path.home() / ".kaggle"
    kaggle_dir.mkdir(exist_ok=True)
    cred_file = kaggle_dir / "kaggle.json"
    cred_file.write_text(json.dumps({"username": kaggle_username, "key": kaggle_key}))
    cred_file.chmod(0o600)

    # Extract path from full URL if needed
    url_match = re.search(r"kaggle\.com/datasets/([^/?#]+/[^/?#]+)", dataset_path)
    if url_match:
        dataset_path = url_match.group(1)

    import kagglehub
    local_path = kagglehub.dataset_download(dataset_path)

    csv_files = _glob.glob(os.path.join(local_path, "**", "*.csv"), recursive=True)
    if not csv_files:
        raise ValueError("No CSV files found in downloaded dataset.")

    df = pd.read_csv(csv_files[0])
    records = _df_to_records(df)
    ds_id = uuid.uuid4().hex[:12]
    col = _ds_col(ds_id)
    if records:
        await col.insert_many(records)

    meta = {
        "dataset_id": ds_id,
        "name": name,
        "source": "kaggle",
        "source_url": dataset_path,
        "filename": os.path.basename(csv_files[0]),
        "record_count": len(records),
        "created_at": _now(),
    }
    await _META.insert_one({**meta, "_id": ds_id})
    return meta


# ── Field compatibility ───────────────────────────────────────────────────────

_USER_ID_FIELDS  = {"user_id", "student_id", "learner_id", "userid_di", "userid"}
_TIMESTAMP_FIELDS = {"timestamp", "date", "created_at", "event_time", "time"}
_SCORE_FIELDS    = {"score", "grade", "final_grade", "grade_percent"}
_EVENT_FIELDS    = {"event_type", "activity_type", "interaction_type", "action"}
_COURSE_FIELDS   = {"course", "course_id", "course_name", "courseid"}
_DUR_FIELDS      = {"duration_minutes", "duration", "time_spent", "minutes"}


def check_compatibility(columns: list[str]) -> dict[str, Any]:
    cols = {c.lower() for c in columns}

    def _find(candidates: set) -> str | None:
        for c in candidates:
            if c in cols:
                return c
        return None

    user_id   = _find(_USER_ID_FIELDS)
    timestamp = _find(_TIMESTAMP_FIELDS)
    score     = _find(_SCORE_FIELDS)
    event     = _find(_EVENT_FIELDS)
    course    = _find(_COURSE_FIELDS)
    duration  = _find(_DUR_FIELDS)

    critical_ok = bool(user_id and timestamp)
    score_ok    = bool(score)

    if critical_ok and score_ok:
        level = "full"
        summary = "All key fields detected — full analytics available."
    elif critical_ok:
        level = "partial"
        summary = "Student ID and timestamp found, but no score field — charts will work, risk scores may be zero."
    else:
        level = "low"
        summary = "Missing student ID or timestamp — limited analytics. Check column names."

    return {
        "compatibility": level,
        "summary": summary,
        "columns_detected": len(columns),
        "field_mapping": {
            "user_id": user_id,
            "timestamp": timestamp,
            "score": score,
            "event_type": event,
            "course": course,
            "duration": duration,
        },
    }


async def validate_dataset(dataset_id: str | None) -> dict[str, Any]:
    if not dataset_id:
        return {"compatibility": "full", "summary": "Default dataset — always compatible.", "field_mapping": {}}
    try:
        sample = await _ds_col(dataset_id).find({}, {"_id": 0}).to_list(length=5)
        if not sample:
            return {"compatibility": "empty", "summary": "Dataset has no records.", "field_mapping": {}}
        cols = list(sample[0].keys())
        return check_compatibility(cols)
    except PyMongoError:
        return {"compatibility": "error", "summary": "Could not read dataset.", "field_mapping": {}}


async def get_dataset_records(dataset_id: str | None) -> list[dict]:
    if not dataset_id:
        return []
    try:
        return await _ds_col(dataset_id).find({}, {"_id": 0}).to_list(length=400_000)
    except PyMongoError:
        return []
