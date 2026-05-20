"""
Load the Kaggle/Open edX person–course CSV (HarvardX / MITx schema) into MongoDB.

Supports common CSV headers like:
course_id, userid_DI, viewed, explored, certified, grade, start_time_DI, last_event_DI,
nevents, ndays_act, nplay_video, nchapters, nforum_posts, registered.

Other column names can be fuzzy-matched (see KNOWN_COLUMNS).
"""

import argparse
import re
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient

from app.config import settings

load_dotenv()

NORMALIZE_KEY = re.compile(r"[^\w]")


KNOWN_COLUMNS: dict[str, str] = {
    "userid_di": "userid_DI",
    "userid": "userid_DI",
    "user_id": "userid_DI",
    "student_id": "userid_DI",
    "course_id": "course_id",
    "courseid": "course_id",
    "start_time_di": "start_time_DI",
    "last_event_di": "last_event_DI",
    "loe_di": "LoE_DI",
    "gender": "gender",
    "grade": "grade",
    "nevents": "nevents",
    "ndays_act": "ndays_act",
    "nplay_video": "nplay_video",
    "nchapters": "nchapters",
    "nforum_posts": "nforum_posts",
    "viewed": "viewed",
    "explored": "explored",
    "certified": "certified",
    "registered": "registered",
    "roles": "roles",
    "incomplete_flag": "incomplete_flag",
}


def _norm_label(value: str) -> str:
    return NORMALIZE_KEY.sub("", value.strip().lower())


def canon_column(name: str) -> str | None:
    key = _norm_label(str(name))
    alias = KNOWN_COLUMNS.get(key)
    if alias:
        return alias
    if key in {"course_di"}:
        return "course_id"
    return None


def reorder_to_canonical(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [str(col).strip().lstrip("\ufeff") for col in df.columns]
    renames = {}
    for original in df.columns:
        canon = canon_column(original)
        if canon:
            renames[original] = canon

    renamed = df.rename(columns=renames)

    duplicated = renamed.columns.duplicated()
    cols = renamed.columns[~duplicated]
    return renamed.loc[:, cols]


def seed_from_csv(csv_path: Path) -> None:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    df = pd.read_csv(csv_path)
    df = reorder_to_canonical(df)

    if "userid_DI" not in df.columns:
        guess = None
        for col in df.columns:
            lc = col.lower().replace("_", "")
            if "userid" in lc or "userid_di" == lc.lower() or lc.startswith("userid"):
                guess = col
                break
        if guess:
            df = df.rename(columns={guess: "userid_DI"})
        else:
            raise ValueError("Could not locate a userid column (expected userid_DI or similar).")

    if "course_id" not in df.columns:
        raise ValueError("Could not locate course_id column.")

    records = df.to_dict(orient="records")

    client = MongoClient(settings.mongodb_uri)
    db = client[settings.mongodb_database]
    col = db[settings.mongodb_collection]

    col.delete_many({})
    if records:
        col.insert_many(records)

    print(f"Inserted {len(records)} enrollment rows → {settings.mongodb_database}.{settings.mongodb_collection}")
    sample_cols = sorted({k for doc in records[:5] for k in doc})
    preview = ", ".join(sample_cols[:15])
    if preview:
        print(f"Sample detected fields: {preview} ...")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed MongoDB with Kaggle / Open edX person–course CSV")
    parser.add_argument("--csv", required=True, help="Path to CSV (e.g., from Kaggle download)")
    args = parser.parse_args()
    seed_from_csv(Path(args.csv))
