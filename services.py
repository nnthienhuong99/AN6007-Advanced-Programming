# services.py
import csv
import os
import random
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from data_structure import store, Household, Merchant, Voucher, Transaction


# -------- Internal voucher storage (in-memory) --------

def _ensure_voucher_store() -> None:
    """Attach voucher-related stores onto the shared in-memory store."""
    if not hasattr(store, "vouchers_by_household"):
        store.vouchers_by_household: Dict[str, List[Voucher]] = {}
    if not hasattr(store, "voucher_owner"):
        store.voucher_owner: Dict[str, str] = {}
    if not hasattr(store, "redeemed_voucher_ids"):
        store.redeemed_voucher_ids: set[str] = set()


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
        v = Voucher(voucher_id=vid, denomination=denomination)
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
        "voucher_balances": balances,
        "voucher_count": len(vouchers),
        "vouchers": [{"voucher_id": v.voucher_id, "denomination": v.denomination} for v in vouchers],
    }


# -------- Registration --------

def register_household(
    household_id: str,
    num_people: int = 0,
    nric: Optional[Dict[str, str]] = None,
    full_names: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    _ensure_voucher_store()

    h = Household(
        household_id=household_id,
        num_people=num_people,
        nric=nric or {},
        full_names=full_names or {},
    )
    store.households[household_id] = h

    # Default allocation at registration:
    # 30 x $2, 12 x $5, 15 x $10
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
    return {"merchant_id": merchant_id, "merchant_name": merchant_name}


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
