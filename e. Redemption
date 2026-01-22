# redemption.py
from __future__ import annotations

import csv
import os
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Tuple


REDEEM_HEADER = [
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

D_BAL_HEADER = ["household_id", "denomination", "voucher_balance", "date", "hour"]

AUDIT_HEADER = [
    "date",
    "hour",
    "household_id",
    "denomination",
    "prev_balance",
    "redeemed_count",
    "expected_balance",
    "actual_balance",
    "status",
]


# ---------- tiny helpers ----------

def _parse_tx_datetime(s: str) -> datetime:
    s = (s or "").strip()
    for fmt in ("%Y-%m-%d-%H%M%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    raise ValueError(f"Bad Transaction_Date_Time: {s!r}")


def _hour_key(dt: datetime) -> str:
    return dt.strftime("%Y%m%d%H")


def _prev_hour_key(key: str) -> str:
    dt = datetime.strptime(key, "%Y%m%d%H")
    return (dt - timedelta(hours=1)).strftime("%Y%m%d%H")


def _parse_denom(s: str) -> int:
    s = (s or "").strip().replace("$", "")
    return int(float(s))  # supports "$2", "$2.00", "2", "2.00"


def _read_rows(path: str, header: List[str]) -> List[Dict[str, str]]:
    with open(path, "r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        return [{k: (row.get(k, "") or "").strip() for k in header} for row in r]


def _append_rows(path: str, header: List[str], rows: List[Dict[str, str]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    existed = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header)
        if not existed:
            w.writeheader()
        w.writerows(rows)


def list_csv_files(input_dir: str) -> List[str]:
    return [
        os.path.join(input_dir, f)
        for f in sorted(os.listdir(input_dir))
        if f.lower().endswith(".csv")
    ]


# ---------- step (d) hourly balance loader ----------

def _load_balance_file(path: str) -> Dict[Tuple[str, int], int]:
    """
    Loads one file: RedemptionBalanceYYYYMMDDHH.csv
    Returns: (household_id, denom_int) -> voucher_balance_int
    """
    if not os.path.exists(path):
        return {}
    out: Dict[Tuple[str, int], int] = {}
    with open(path, "r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            hh = (row.get("household_id") or "").strip()
            denom = _parse_denom(row.get("denomination"))
            bal = int((row.get("voucher_balance") or "0").strip())
            out[(hh, denom)] = bal
    return out


# ---------- step (e) compile + audit ----------

def compile_redemptions_by_hour_with_audit(
    step_c_csv_paths: Iterable[str],
    redeem_output_dir: str,
    d_balance_dir: str,      # contains RedemptionBalanceYYYYMMDDHH.csv files
    audit_output_dir: str,
) -> Tuple[List[str], List[str]]:
    """
    (e) Redemption:
      - compile step (c) rows into hourly RedeemYYYYMMDDHH.csv
      - audit against step (d) hourly snapshots:
          expected = prev_hour_balance - redeemed_count_this_hour
          compare with current_hour_balance

    Returns: (redeem_files_written, audit_files_written)
    """
    os.makedirs(redeem_output_dir, exist_ok=True)
    os.makedirs(d_balance_dir, exist_ok=True)
    os.makedirs(audit_output_dir, exist_ok=True)

    # Bucket redemptions by hour and count redeemed vouchers per (hour, household, denom)
    redeem_buckets: Dict[str, List[Dict[str, str]]] = {}
    redeemed_counts: Dict[Tuple[str, str, int], int] = {}

    for p in step_c_csv_paths:
        for row in _read_rows(p, REDEEM_HEADER):
            hk = _hour_key(_parse_tx_datetime(row["Transaction_Date_Time"]))
            redeem_buckets.setdefault(hk, []).append(row)

            hh = row["Household_ID"]
            denom = _parse_denom(row["Denomination_Used"])
            redeemed_counts[(hk, hh, denom)] = redeemed_counts.get((hk, hh, denom), 0) + 1

    redeem_written: List[str] = []
    audit_written: List[str] = []

    for hk, rows in sorted(redeem_buckets.items()):
        # 1) Write RedeemYYYYMMDDHH.csv
        redeem_path = os.path.join(redeem_output_dir, f"Redeem{hk}.csv")
        _append_rows(redeem_path, REDEEM_HEADER, rows)
        redeem_written.append(redeem_path)

        # 2) Load step (d) hourly snapshots: prev hour + current hour
        prev_hk = _prev_hour_key(hk)
        prev_bal = _load_balance_file(os.path.join(d_balance_dir, f"RedemptionBalance{prev_hk}.csv"))
        curr_bal = _load_balance_file(os.path.join(d_balance_dir, f"RedemptionBalance{hk}.csv"))

        date, hour = hk[:8], hk[8:10]
        audit_rows: List[Dict[str, str]] = []

        for (hkey, household_id, denom), redeemed in sorted(redeemed_counts.items()):
            if hkey != hk:
                continue

            prev = prev_bal.get((household_id, denom))
            actual = curr_bal.get((household_id, denom))

            if prev is None or actual is None:
                audit_rows.append({
                    "date": date,
                    "hour": hour,
                    "household_id": household_id,
                    "denomination": f"${denom}",
                    "prev_balance": "" if prev is None else str(prev),
                    "redeemed_count": str(redeemed),
                    "expected_balance": "",
                    "actual_balance": "" if actual is None else str(actual),
                    "status": "SKIP_NO_PREV" if prev is None else "SKIP_NO_ACTUAL",
                })
                continue

            expected = prev - redeemed
            audit_rows.append({
                "date": date,
                "hour": hour,
                "household_id": household_id,
                "denomination": f"${denom}",
                "prev_balance": str(prev),
                "redeemed_count": str(redeemed),
                "expected_balance": str(expected),
                "actual_balance": str(actual),
                "status": "OK" if expected == actual else "MISMATCH",
            })

        audit_path = os.path.join(audit_output_dir, f"Audit{hk}.csv")
        _append_rows(audit_path, AUDIT_HEADER, audit_rows)
        audit_written.append(audit_path)

    return redeem_written, audit_written


# ---------- minimal example runner ----------

if __name__ == "__main__":
    # Example folder layout:
    #   step_c_output/  (contains step c csv files)
    #   step_d_output/  (contains RedemptionBalanceYYYYMMDDHH.csv)
    # Outputs:
    #   redemption_files/RedeemYYYYMMDDHH.csv
    #   audit_files/AuditYYYYMMDDHH.csv

    step_c_paths = list_csv_files("step_c_output")
    redeem_files, audit_files = compile_redemptions_by_hour_with_audit(
        step_c_csv_paths=step_c_paths,
        redeem_output_dir="redemption_files",
        d_balance_dir="step_d_output",
        audit_output_dir="audit_files",
    )

    print("Redeem files:")
    for p in redeem_files:
        print(" -", p)

    print("Audit files:")
    for p in audit_files:
        print(" -", p)
