# redemption.py
from __future__ import annotations

import csv
import os
from datetime import datetime
from typing import Dict, Iterable, List, Tuple, Optional

HEADER = [
    "Transaction_ID",
    "Household_ID",
    "Merchant_ID",
    "Transaction_Date_Time",
    "Voucher_Code",
    "Denomination_Used",
    "Amount_Redeemed",
    "Payment_Status",
    "Remarks",
]


def _parse_tx_datetime(s: str) -> datetime:
    """
    Supports common formats seen in the project:
    - 'YYYY-MM-DD-HHMMSS'  (e.g., 2025-01-01-031530)
    - 'YYYY-MM-DD HH:MM:SS'
    - ISO-ish 'YYYY-MM-DDTHH:MM:SS'
    """
    s = s.strip()
    for fmt in ("%Y-%m-%d-%H%M%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    raise ValueError(f"Unrecognized Transaction_Date_Time format: {s!r}")


def _hour_key(dt: datetime) -> str:
    """Return 'YYYYMMDDHH' for RedeemYYYYMMDDHH.csv naming."""
    return dt.strftime("%Y%m%d%H")


def _read_rows_from_csv(path: str) -> List[Dict[str, str]]:
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # Keep only required columns; ignore extras if any
        rows = []
        for r in reader:
            rows.append({k: (r.get(k, "") or "").strip() for k in HEADER})
        return rows


def _append_rows(path: str, rows: List[Dict[str, str]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)

    file_exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADER)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)


def compile_redemptions_by_hour(
    input_csv_paths: Iterable[str],
    output_dir: str,
) -> List[str]:
    """
    Step (e): compile prepared redemption rows into hourly files:
      RedeemYYYYMMDDHH.csv

    Input rows are assumed to ALREADY contain all required columns (from step c).
    Returns list of output filepaths written/appended.
    """
    os.makedirs(output_dir, exist_ok=True)

    buckets: Dict[str, List[Dict[str, str]]] = {}

    for path in input_csv_paths:
        for row in _read_rows_from_csv(path):
            dt = _parse_tx_datetime(row["Transaction_Date_Time"])
            key = _hour_key(dt)  # 'YYYYMMDDHH'
            buckets.setdefault(key, []).append(row)

    written: List[str] = []
    for key, rows in sorted(buckets.items()):
        out_path = os.path.join(output_dir, f"Redeem{key}.csv")
        _append_rows(out_path, rows)
        written.append(out_path)

    return written


def list_csv_files(input_dir: str) -> List[str]:
    """Convenience: collect all .csv in a folder (non-recursive)."""
    return [
        os.path.join(input_dir, f)
        for f in sorted(os.listdir(input_dir))
        if f.lower().endswith(".csv")
    ]


if __name__ == "__main__":
    # Minimal example usage:
    # - step c outputs are in ./step_c_output/
    # - step e writes hourly files to ./redemption_files/
    in_dir = "step_c_output"
    out_dir = "redemption_files"

    inputs = list_csv_files(in_dir)
    outputs = compile_redemptions_by_hour(inputs, out_dir)

    print("Wrote / appended:")
    for p in outputs:
        print(" -", p)