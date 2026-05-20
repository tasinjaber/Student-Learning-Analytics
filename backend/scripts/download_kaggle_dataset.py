"""
Download Kaggle/Open edX course engagement CSV via kagglehub (no manual zip unzip).

Requirements:
    pip install kagglehub
    Kaggle API credentials (https://www.kaggle.com/docs/api) or kagglehub browser auth if prompted.

Examples:
    python scripts/download_kaggle_dataset.py
    python scripts/download_kaggle_dataset.py --seed
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent


def resolve_csv(root: Path, prefer: str | None) -> Path:
    csvs = sorted(root.rglob("*.csv"))
    if not csvs:
        raise FileNotFoundError(f"No .csv under {root}")
    if prefer:
        for p in csvs:
            if p.name.lower() == prefer.lower() or prefer.lower() in p.name.lower():
                return p
    return csvs[0]


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Kaggle dataset with kagglehub")
    parser.add_argument(
        "dataset_slug",
        nargs="?",
        default="thedevastator/online-course-user-engagement-data",
        help="Dataset id, e.g. thedevastator/online-course-user-engagement-data",
    )
    parser.add_argument(
        "--csv-name",
        default=None,
        help="Substring or exact CSV filename hint (optional)",
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="After download, pipe the main CSV into seed_kaggle_data.py (Mongo)",
    )
    args = parser.parse_args()

    try:
        import kagglehub  # type: ignore[import-untyped]
    except ImportError as exc:
        raise SystemExit("Install deps: pip install kagglehub") from exc

    path = Path(kagglehub.dataset_download(args.dataset_slug))
    print("Path to dataset files:", path)

    csv_path = resolve_csv(path, args.csv_name)
    print("Using CSV:", csv_path)

    if args.seed:
        seed_script = BACKEND_ROOT / "scripts" / "seed_kaggle_data.py"
        cmd = [sys.executable, str(seed_script), "--csv", str(csv_path)]
        subprocess.check_call(cmd, cwd=str(BACKEND_ROOT))


if __name__ == "__main__":
    main()
