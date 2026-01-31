# services.py
import csv
import os
import random
import calendar
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple
import json

from data_structure import store, Household, Merchant, Voucher, Transaction


# -------- Flat-file persistence (minimal) --------

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_BASE_DIR, "flat_files")

_HOUSEHOLDS_CSV = os.path.join(_DATA_DIR, "households.csv")
_MERCHANTS_CSV  = os.path.join(_DATA_DIR, "merchants.csv")


def _norm_unit(unit: str) -> str:
    return (unit or "").strip().upper()

def _norm_uen(uen: str) -> str:
    return (uen or "").strip().upper()

def _ensure_flat_files() -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)

    if not os.path.exists(_HOUSEHOLDS_CSV):
        with open(_HOUSEHOLDS_CSV, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([
                "household_id",
                "num_people",
                "full_name",
                "nric",
                "postal_code",
                "unit_number",
                "created_at_iso"
                ])

    if not os.path.exists(_MERCHANTS_CSV):
        with open(_MERCHANTS_CSV, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([
                "merchant_id",
                "merchant_name",
                "uen",
                "bank_name",
                "bank_code",
                "branch_code",
                "account_number",
                "account_holder_name",
                "created_at_iso"])


def _ensure_indexes() -> None:
    """Indexes for fast duplicate checks."""
    if not hasattr(store, "household_addr_index"):
        store.household_addr_index: Dict[tuple, str] = {}  # (unit, postal) -> household_id
    if not hasattr(store, "merchant_uen_index"):
        store.merchant_uen_index: Dict[str, str] = {}      # uen -> merchant_id


def _load_registrations_from_files() -> None:
    """Load existing registrations into in-memory store + indexes (minimal fields)."""
    _ensure_flat_files()
    _ensure_indexes()

    # Households
    with open(_HOUSEHOLDS_CSV, "r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            hid = (row.get("household_id") or "").strip()
            if not hid:
                continue
            try:
                postal = int(row.get("postal_code") or 0)
            except ValueError:
                postal = 0
            unit = _norm_unit(row.get("unit_number") or "")
            try:
                num_people = int(row.get("num_people") or 0)
            except ValueError:
                num_people = 0

            # If already in memory (e.g., tests), skip
            if hid not in store.households:
                store.households[hid] = Household(
                    household_id=hid,
                    num_people=num_people,
                    nric={},          # minimal rehydrate
                    full_names={},    # minimal rehydrate
                    postal_code=postal,
                    unit_number=unit,
                )

            if unit and postal:
                store.household_addr_index.setdefault((unit, postal), hid)

    # Merchants
    with open(_MERCHANTS_CSV, "r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            mid = (row.get("merchant_id") or "").strip()
            if not mid:
                continue
            mname = (row.get("merchant_name") or "").strip()
            uen = _norm_uen(row.get("uen") or "")

            if mid not in store.merchants:
                store.merchants[mid] = Merchant(
                    merchant_id=mid,
                    merchant_name=mname,
                    uen=uen,
                )

            if uen:
                store.merchant_uen_index.setdefault(uen, mid)


def _append_household_row(household_id: str, num_people: int, postal_code: int, unit_number: str) -> None:
    _ensure_flat_files()
    with open(_HOUSEHOLDS_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([household_id, num_people, postal_code, unit_number, datetime.utcnow().isoformat()])


def _append_merchant_row(merchant_id: str, merchant_name: str, uen: str) -> None:
    _ensure_flat_files()
    with open(_MERCHANTS_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([merchant_id, merchant_name, uen, datetime.utcnow().isoformat()])



# -------- Internal voucher storage (in-memory) --------

def _ensure_voucher_store() -> None:
    """Attach voucher-related stores onto the shared in-memory store."""
    if not hasattr(store, "vouchers_by_household"):
        store.vouchers_by_household: Dict[str, List[Voucher]] = {}
    if not hasattr(store, "voucher_owner"):
        store.voucher_owner: Dict[str, str] = {}
    if not hasattr(store, "redeemed_voucher_ids"):
        store.redeemed_voucher_ids: set[str] = set()
    # Household-level dates (grant/expiry are set when household is registered)
    if not hasattr(store, "household_grant_date"):
        store.household_grant_date: Dict[str, date] = {}
    if not hasattr(store, "household_expiry_date"):
        store.household_expiry_date: Dict[str, date] = {}

def _add_months(d: date, months: int) -> date:
    """Add months to a date, clamping day to month-end when needed."""
    y = d.year + (d.month - 1 + months) // 12
    mth = (d.month - 1 + months) % 12 + 1
    last_day = calendar.monthrange(y, mth)[1]
    day = min(d.day, last_day)
    return date(y, mth, day)


def _household_dates(household_id: str) -> Tuple[date, date]:
    """Return (grant_date, expiry_date) for a household, defaulting to today/+6mo."""
    grant = store.household_grant_date.get(household_id) or date.today()
    expiry = store.household_expiry_date.get(household_id) or _add_months(grant, 6)
    store.household_grant_date.setdefault(household_id, grant)
    store.household_expiry_date.setdefault(household_id, expiry)
    return grant, expiry


def _new_voucher_id() -> str:
    """Generate unique randomized voucher id: VXXXXXXX (7 digits)."""
    _ensure_voucher_store()
    while True:
        n = random.randint(0, 9_999_999)
        vid = f"V{n:07d}"
        if vid not in store.voucher_owner and vid not in store.redeemed_voucher_ids:
            return vid


def _add_vouchers(household_id: str, denomination: int, count: int) -> None:
    _ensure_voucher_store()
    bucket = store.vouchers_by_household.setdefault(household_id, [])
    for _ in range(count):
        vid = _new_voucher_id()
        grant_date, expiry_date = _household_dates(household_id)
        v = Voucher(voucher_id=vid, denomination=denomination, grant_date=grant_date, expiry_date=expiry_date, redemption_date=date.min)
        bucket.append(v)
        store.voucher_owner[vid] = household_id


def _balances_by_denom(vouchers: List[Voucher]) -> Dict[int, int]:
    out: Dict[int, int] = {2: 0, 5: 0, 10: 0}
    for v in vouchers:
        out[v.denomination] = out.get(v.denomination, 0) + 1
    return out


def serialize_household(h: Household) -> Dict[str, Any]:
    """Serialize household + voucher balances."""
    _ensure_voucher_store()
    vouchers = store.vouchers_by_household.get(h.household_id, [])
    balances = _balances_by_denom(vouchers)
    return {
        "household_id": h.household_id,
        "num_people": h.num_people,
        "nric": h.nric,
        "full_names": h.full_names,
        "postal_code": h.postal_code,
        "unit_number": h.unit_number,
        "voucher_balances": balances,
        "voucher_count": len(vouchers),
        "vouchers": [{"voucher_id": v.voucher_id, "denomination": v.denomination} for v in vouchers],
    }


# -------- Registration --------

def register_household(
    household_id: str,
    num_people: int,
    postal_code: int,
    unit_number: str,
    nric: Optional[Dict[str, str]],
    full_names: Optional[Dict[str, str]],
) -> Dict[str, Any]:
    _ensure_voucher_store()
    _ensure_indexes()   # ADD

    household_id = (household_id or "").strip()
    postal_code = int(postal_code)
    unit_number = _norm_unit(unit_number)

    # ADD: prevent duplicate household_id
    if household_id in store.households:
        return {"error": f"Household_ID already exists: {household_id}"}

    # ADD: prevent duplicate address (unit_number + postal_code)
    addr_key = (unit_number, postal_code)
    if unit_number and postal_code and addr_key in store.household_addr_index:
        existing = store.household_addr_index[addr_key]
        return {"error": f"Household already registered for {unit_number} {postal_code} (existing household_id={existing})"}

    grant = date.today()
    expiry = _add_months(grant, 6)
    store.household_grant_date[household_id] = grant
    store.household_expiry_date[household_id] = expiry

    h = Household(
        household_id=household_id,
        num_people=num_people,
        nric=nric,
        full_names=full_names,
        postal_code=postal_code,
        unit_number=unit_number
    )
    store.households[household_id] = h

    # ADD: update index + append to flat file
    if unit_number and postal_code:
        store.household_addr_index[addr_key] = household_id
    _append_household_row(household_id, num_people, postal_code, unit_number)

    # Default allocation at registration:
    _add_vouchers(household_id, 2, 30)
    _add_vouchers(household_id, 5, 12)
    _add_vouchers(household_id, 10, 15)

    return serialize_household(h)



def register_merchant(
    merchant_id: str,
    merchant_name: str,
    uen: str = "",
    bank_name: str = "",
    bank_code: str = "",
    branch_code: str = "",
    account_number: str = "",
    account_holder_name: str = "",
) -> Dict[str, Any]:
    _ensure_indexes()  # ADD

    merchant_id = (merchant_id or "").strip()
    merchant_name = (merchant_name or "").strip()
    uen = _norm_uen(uen)

    # ADD: prevent duplicate merchant_id
    if merchant_id in store.merchants:
        return {"error": f"Merchant_ID already exists: {merchant_id}"}

    # ADD: prevent duplicate uen
    if uen and uen in store.merchant_uen_index:
        existing = store.merchant_uen_index[uen]
        return {"error": f"Merchant already registered for UEN={uen} (existing merchant_id={existing})"}

    m = Merchant(
        merchant_id=merchant_id,
        merchant_name=merchant_name,
        uen=uen,
        bank_name=bank_name,
        bank_code=bank_code,
        branch_code=branch_code,
        account_number=account_number,
        account_holder_name=account_holder_name,
    )
    store.merchants[merchant_id] = m

    # ADD: update index + append to flat file
    if uen:
        store.merchant_uen_index[uen] = merchant_id
    _append_merchant_row(merchant_id, merchant_name, uen)

    return {
        "merchant_id": merchant_id,
        "merchant_name": merchant_name,
        "uen": uen,
        "bank_name": bank_name,
        "bank_code": bank_code,
        "branch_code": branch_code,
        "account_number": account_number,
        "account_holder_name": account_holder_name,
        }




# -------- Voucher Claim (optional; kept for compatibility) --------

def claim_tranche(household_id: str, tranche_id: str) -> Dict[str, Any]:
    # Example bundle for compatibility; adjust if your spec requires.
    bundle = {2: 30, 5: 12, 10: 15}
    for denom, qty in bundle.items():
        _add_vouchers(household_id, denom, qty)
    return serialize_household(store.households[household_id])


# -------- Redemption (user-indicated, non-greedy) --------

def redeem(
    tx: Transaction,
    *,
    voucher_ids: Optional[List[str]] = None,
    denominations: Optional[List[Dict[str, int]]] = None,
) -> Dict[str, Any]:
    """Redeem vouchers as indicated by the user.

    Input options (choose one):
    - voucher_ids: explicit list of voucher ids to redeem
    - denominations: list of {"denomination": int, "count": int}

    Output CSV rows are written per voucher redeemed.
    Amount_Redeemed is repeated as: Denomination_Used * number of vouchers of that denomination in this transaction.
    Remarks is the usage sequence for that denomination inside the transaction: 1..N-1, Final denomination used.
    """
    _ensure_voucher_store()

    bucket = store.vouchers_by_household.get(tx.household_id, [])
    yyyymmdd, hh, yyyymmddhh = derive_hour(tx.datetime_iso)

    # Build list of Voucher objects to redeem in this transaction.
    to_redeem: List[Voucher] = []

    if voucher_ids:
        # Redeem exactly these vouchers (assume valid for minimal version).
        lookup = {v.voucher_id: v for v in bucket}
        for vid in voucher_ids:
            v = lookup.get(vid)
            if v is not None:
                to_redeem.append(v)

    elif denominations:
        # Redeem counts by denomination (not greedy; follow user-requested counts).
        by_denom: Dict[int, List[Voucher]] = {2: [], 5: [], 10: []}
        for v in bucket:
            by_denom.setdefault(v.denomination, []).append(v)

        for item in denominations:
            denom = int(item["denomination"])
            count = int(item["count"])
            to_redeem.extend(by_denom.get(denom, [])[:count])

    # Group selected vouchers by denomination to compute Amount_Redeemed and Remarks.
    selected_by_denom: Dict[int, List[Voucher]] = {}
    for v in to_redeem:
        selected_by_denom.setdefault(v.denomination, []).append(v)

    rows: List[dict] = []
    for denom, vs in sorted(selected_by_denom.items(), key=lambda x: x[0], reverse=True):
        count = len(vs)
        amount_redeemed = denom * count
        for idx, v in enumerate(vs, start=1):
            remark = str(idx) if idx < count else "Final denomination used"
            rows.append(
                {
                    "Transaction_ID": tx.transaction_id,
                    "Household_ID": tx.household_id,
                    "Merchant_ID": tx.merchant_id,
                    "Voucher_ID": v.voucher_id,
                    "Denomination_Used": f"${denom:.2f}",
                    "Amount_Redeemed": f"${amount_redeemed:.2f}",
                    "Remarks": remark,
                }
            )

    # Remove redeemed vouchers from the household bucket.
    if rows:
        redeem_ids = {r["Voucher_ID"] for r in rows}
        store.vouchers_by_household[tx.household_id] = [v for v in bucket if v.voucher_id not in redeem_ids]
        for vid in redeem_ids:
            store.redeemed_voucher_ids.add(vid)
            store.voucher_owner.pop(vid, None)

    store.redemptions_by_hour.setdefault(yyyymmddhh, []).extend(rows)

    os.makedirs("output", exist_ok=True)
    path = f"output/Redeem{yyyymmdd}{hh}.csv"
    append_csv(path, rows)

    return {
        "transaction_id": tx.transaction_id,
        "rows_written": len(rows),
        "balances_after": serialize_household(store.households[tx.household_id])["voucher_balances"],
        "file": path,
    }


# -------- Balance Extract --------

def export_balance_snapshot(date: str, hour: str) -> Dict[str, Any]:
    _ensure_voucher_store()
    os.makedirs("output", exist_ok=True)
    path = f"output/RedemptionBalance{date}{hour}.csv"

    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["household_id", "denomination", "voucher_balance", "date", "hour"])
        for household_id in store.households.keys():
            balances = _balances_by_denom(store.vouchers_by_household.get(household_id, []))
            for denom in (2, 5, 10):
                w.writerow([household_id, f"${denom}", balances.get(denom, 0), date, hour])

    return {"file": path}


# -------- Helpers --------

def derive_hour(dt_iso: str) -> Tuple[str, str, str]:
    dt = datetime.fromisoformat(dt_iso)
    return dt.strftime("%Y%m%d"), dt.strftime("%H"), dt.strftime("%Y%m%d%H")


def append_csv(path: str, rows: List[dict]) -> None:
    if not rows:
        return
    new = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        if new:
            w.writeheader()
        w.writerows(rows)

# Load persisted registrations at import time (minimal)
_load_registrations_from_files()
