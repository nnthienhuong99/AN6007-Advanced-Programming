
"""
CDC Voucher - Mobile Redemption App (Flet)

Goal (from AN6007 project brief):
- "A mobile application that can load the redemption balance of a registered household
  and allow selection of balanced denominations for redemptions."  (see project spec)

How to run (dev):
1) pip install flet requests
2) python cdc_mobile_app.py

How to point at your backend:
- Set BASE_URL to your server (Flask/FastAPI/etc).
- Implement/route these endpoints (or change paths in the code):
    GET  /households/balance?household_id=Hxxxx
    POST /redemptions/preview
    POST /redemptions/confirm

This file also supports a MOCK mode (no backend needed) for demo/testing the UI+algorithm.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Any, List

import flet as ft

try:
    import requests  # type: ignore
except Exception:
    requests = None  # allow running UI in mock-only mode


# ---------------------------- Configuration ----------------------------

USE_MOCK_BACKEND = True  # set False when your real backend is ready
BASE_URL = "http://127.0.0.1:5000"  # your backend
TIMEOUT_S = 8

# Supported denominations for non-supermarket vendor per spec: $2, $5, $10
DENOMS = (10, 5, 2)


# ---------------------------- Data models ----------------------------

@dataclass(frozen=True)
class TrancheBalance:
    tranche_id: str                     # e.g. "2025-05", "2026-01"
    denom_counts: Dict[int, int]         # {2: n2, 5: n5, 10: n10}

    @property
    def total_value(self) -> int:
        return sum(d * c for d, c in self.denom_counts.items())


@dataclass(frozen=True)
class HouseholdBalance:
    household_id: str
    tranches: Dict[str, TrancheBalance]  # tranche_id -> balance

    @property
    def total_value(self) -> int:
        return sum(t.total_value for t in self.tranches.values())

    def tranche(self, tranche_id: str) -> TrancheBalance:
        return self.tranches[tranche_id]


# ---------------------------- Balanced denomination algorithm ----------------------------

@dataclass(frozen=True)
class Combo:
    used: Dict[int, int]  # denom -> count used
    amount: int

    @property
    def num_vouchers(self) -> int:
        return sum(self.used.values())


def _imbalance_score(original_counts: Dict[int, int], remaining_counts: Dict[int, int]) -> float:
    """
    "Balanced denominations" heuristic:
    - prefer leaving remaining vouchers in a similar *mix* as before redemption
    - implemented as L2 distance between original and remaining *share vectors*
    """
    def shares(counts: Dict[int, int]) -> Dict[int, float]:
        total = sum(counts.values())
        if total <= 0:
            return {d: 0.0 for d in DENOMS}
        return {d: counts.get(d, 0) / total for d in DENOMS}

    s0 = shares(original_counts)
    s1 = shares(remaining_counts)
    return math.sqrt(sum((s0[d] - s1[d]) ** 2 for d in DENOMS))


def suggest_balanced_combo(
    target_amount: int,
    available_counts: Dict[int, int],
) -> Tuple[Optional[Combo], int]:
    """
    Return (best_combo, suggested_amount).

    If exact match is possible -> suggested_amount == target_amount.
    If not, we suggest the closest achievable amount <= target_amount.

    Objective order:
    1) Minimize leftover (target - achieved)
    2) Minimize number of vouchers used
    3) Keep remaining denominations "balanced" (mix close to original)
    """
    if target_amount <= 0:
        return None, 0

    # Cap target by max spendable
    max_spendable = sum(d * available_counts.get(d, 0) for d in DENOMS)
    cap_target = min(target_amount, max_spendable)

    orig = {d: int(available_counts.get(d, 0)) for d in DENOMS}

    best: Optional[Combo] = None
    best_score: Tuple[int, int, float] = (10**9, 10**9, 10**9)

    # brute force is fine here (values are small; typical voucher counts are not huge)
    max10 = min(orig[10], cap_target // 10)
    for c10 in range(max10 + 1):
        remaining_after_10 = cap_target - 10 * c10
        max5 = min(orig[5], remaining_after_10 // 5)
        for c5 in range(max5 + 1):
            remaining_after_5 = remaining_after_10 - 5 * c5
            max2 = min(orig[2], remaining_after_5 // 2)
            # To maximize achieved amount, we want as many $2 as possible (up to remaining)
            # BUT for balancing, we still consider all possible c2 (0..max2)
            for c2 in range(max2 + 1):
                achieved = 10 * c10 + 5 * c5 + 2 * c2
                if achieved <= 0:
                    continue

                leftover = cap_target - achieved
                used = {10: c10, 5: c5, 2: c2}
                remaining = {d: orig[d] - used[d] for d in DENOMS}

                # Primary objective: minimize leftover, so achieved closer to cap_target
                # Secondary: fewer vouchers
                # Tertiary: balanced remaining mix
                score = (leftover, c10 + c5 + c2, _imbalance_score(orig, remaining))

                if score < best_score:
                    best_score = score
                    best = Combo(used=used, amount=achieved)

    if best is None:
        return None, 0
    return best, best.amount


# ---------------------------- Backend adapters ----------------------------

class BackendError(RuntimeError):
    pass


def _mock_balance(household_id: str) -> HouseholdBalance:
    # A small, realistic-ish balance for demo (two tranches; $2/$5/$10 mix)
    return HouseholdBalance(
        household_id=household_id,
        tranches={
            "2025-05": TrancheBalance("2025-05", {2: 20, 5: 10, 10: 30}),  # total = 400
            "2026-01": TrancheBalance("2026-01", {2: 10, 5: 8, 10: 12}),   # total = 200
        },
    )


def fetch_household_balance(household_id: str) -> HouseholdBalance:
    """
    Expected API response shape (suggested):
    {
      "household_id": "H...",
      "tranches": {
        "2025-05": {"denoms": {"2": 20, "5": 10, "10": 30}},
        "2026-01": {"denoms": {"2": 10, "5": 8, "10": 12}}
      }
    }
    """
    if USE_MOCK_BACKEND:
        return _mock_balance(household_id)

    if requests is None:
        raise BackendError("requests not installed (pip install requests)")

    url = f"{BASE_URL}/households/balance"
    try:
        r = requests.get(url, params={"household_id": household_id}, timeout=TIMEOUT_S)
        if r.status_code != 200:
            raise BackendError(f"Balance API failed: {r.status_code} {r.text}")
        data = r.json()
    except Exception as ex:
        raise BackendError(f"Balance API error: {ex}")

    try:
        tranches: Dict[str, TrancheBalance] = {}
        for tid, tinfo in data["tranches"].items():
            denoms_raw = tinfo["denoms"]
            denoms = {int(k): int(v) for k, v in denoms_raw.items()}
            tranches[tid] = TrancheBalance(tranche_id=tid, denom_counts=denoms)
        return HouseholdBalance(household_id=str(data["household_id"]), tranches=tranches)
    except Exception as ex:
        raise BackendError(f"Bad balance payload: {ex}")


def confirm_redemption(
    household_id: str,
    merchant_id: str,
    tranche_id: str,
    amount: int,
    used_counts: Dict[int, int],
) -> Dict[str, Any]:
    """
    Expected API request/response (suggested):

    POST /redemptions/confirm
    {
      "household_id": "H...",
      "merchant_id": "M001",
      "tranche_id": "2025-05",
      "amount": 18,
      "denoms_used": {"2": 4, "5": 2, "10": 0}
    }

    Response:
    {
      "transaction_id": "TX1234",
      "accepted_amount": 18,
      "balance": {... same as balance response ...}
    }
    """
    if USE_MOCK_BACKEND:
        # simulate success + return a "transaction id"
        tx = f"TX{int(time.time())}"
        return {"transaction_id": tx, "accepted_amount": amount}

    if requests is None:
        raise BackendError("requests not installed (pip install requests)")

    url = f"{BASE_URL}/redemptions/confirm"
    payload = {
        "household_id": household_id,
        "merchant_id": merchant_id,
        "tranche_id": tranche_id,
        "amount": amount,
        "denoms_used": {str(k): int(v) for k, v in used_counts.items()},
    }
    try:
        r = requests.post(url, json=payload, timeout=TIMEOUT_S)
        if r.status_code != 200:
            raise BackendError(f"Redeem API failed: {r.status_code} {r.text}")
        return r.json()
    except Exception as ex:
        raise BackendError(f"Redeem API error: {ex}")


# ---------------------------- UI (Flet) ----------------------------

def money(v: int) -> str:
    return f"${v:.2f}" if isinstance(v, float) else f"${v}"


class DenomStepper(ft.Row):
    """A simple +/- stepper for a voucher denomination.

    Newer Flet versions no longer expose `UserControl`, so we build this as a plain `ft.Row`.
    Also: avoid calling `update()` before the control is mounted on the page.
    """

    def __init__(self, denom: int, max_value: int, on_change):
        super().__init__(alignment=ft.MainAxisAlignment.START)
        self.denom = int(denom)
        self.max_value = max(0, int(max_value))
        self.on_change = on_change
        self.count = 0

        self.label = ft.Text(f"${self.denom}", width=60)
        self.txt = ft.Text("0", width=40, text_align=ft.TextAlign.CENTER)
        self.btn_minus = ft.IconButton(icon=ft.Icons.REMOVE, on_click=self._minus)
        self.btn_plus = ft.IconButton(icon=ft.Icons.ADD, on_click=self._plus)
        self.max_txt = ft.Text(f"/ max {self.max_value}")

        self.controls = [self.label, self.btn_minus, self.txt, self.btn_plus, self.max_txt]
        # Do NOT call update() during __init__. Flet will mount the control later.
        self.btn_minus.disabled = True
        self.btn_plus.disabled = self.max_value <= 0

    def _safe_update(self):
        """Best-effort update.

        Even if `page` is present, Flet may still raise until the control is mounted
        into the page tree. We swallow that specific lifecycle error.
        """
        try:
            self.update()
        except Exception:
            # "Control must be added to the page first" (or similar)
            pass

    def set_max(self, max_value: int):
        self.max_value = max(0, int(max_value))
        if self.count > self.max_value:
            self.count = self.max_value
            self.txt.value = str(self.count)
        self.max_txt.value = f"/ max {self.max_value}"
        self._sync_buttons(safe=True)

    def set_count(self, count: int):
        self.count = max(0, min(int(count), self.max_value))
        self.txt.value = str(self.count)
        self._sync_buttons(safe=True)

    def _sync_buttons(self, safe: bool = False):
        # Keep signature `safe` to avoid touching call sites, but always do best-effort update.
        self.btn_minus.disabled = self.count <= 0
        self.btn_plus.disabled = self.count >= self.max_value
        self._safe_update()

    def _minus(self, e):
        if self.count > 0:
            self.count -= 1
            self.txt.value = str(self.count)
            self._sync_buttons(safe=True)
            self.on_change()

    def _plus(self, e):
        if self.count < self.max_value:
            self.count += 1
            self.txt.value = str(self.count)
            self._sync_buttons(safe=True)
            self.on_change()


def main(page: ft.Page):
    page.title = "CDC Voucher Redemption (Mobile)"
    page.scroll = ft.ScrollMode.AUTO

    household_field = ft.TextField(label="Household ID", width=360, hint_text="e.g., H52298800781")
    load_btn = ft.ElevatedButton("Load Balance")
    status = ft.Text("", selectable=True)

    tranche_dd = ft.Dropdown(label="Tranche", width=220, options=[])
    merchant_field = ft.TextField(label="Merchant ID", width=220, hint_text="e.g., M001")
    amount_field = ft.TextField(label="Amount to redeem ($)", width=220, hint_text="e.g., 18")

    suggest_btn = ft.OutlinedButton("Suggest balanced denominations")
    confirm_btn = ft.ElevatedButton("Confirm redemption", disabled=True)

    balance_card = ft.Card(
        content=ft.Container(
            padding=12,
            content=ft.Column([ft.Text("Balance", size=16, weight=ft.FontWeight.BOLD),
                               ft.Text("Load a household to view balances.")]),
        )
    )

    stepper10 = DenomStepper(10, 0, on_change=lambda: on_stepper_change())
    stepper5 = DenomStepper(5, 0, on_change=lambda: on_stepper_change())
    stepper2 = DenomStepper(2, 0, on_change=lambda: on_stepper_change())

    combo_summary = ft.Text("No selection yet.")
    suggestion_note = ft.Text("", color=ft.Colors.GREY_700)

    current_balance: Optional[HouseholdBalance] = None

    def render_balance(bal: HouseholdBalance):
        nonlocal current_balance
        current_balance = bal

        lines: List[ft.Control] = [
            ft.Text("Balance", size=16, weight=ft.FontWeight.BOLD),
            ft.Text(f"Household: {bal.household_id}"),
            ft.Text(f"Total remaining: {money(bal.total_value)}"),
            ft.Divider(),
        ]
        for tid, t in bal.tranches.items():
            counts = t.denom_counts
            lines.append(ft.Text(f"Tranche {tid}: {money(t.total_value)}", weight=ft.FontWeight.BOLD))
            lines.append(ft.Text(f"$10 × {counts.get(10,0)}   $5 × {counts.get(5,0)}   $2 × {counts.get(2,0)}"))
            lines.append(ft.Divider())

        balance_card.content = ft.Container(padding=12, content=ft.Column(lines))
        balance_card.update()

        tranche_dd.options = [ft.dropdown.Option(tid) for tid in bal.tranches.keys()]
        tranche_dd.value = next(iter(bal.tranches.keys()), None)
        tranche_dd.update()

    def refresh_ui_limits():
        nonlocal current_balance
        if not current_balance or not tranche_dd.value:
            stepper10.set_max(0); stepper5.set_max(0); stepper2.set_max(0)
            return

        t = current_balance.tranche(tranche_dd.value)
        stepper10.set_max(t.denom_counts.get(10, 0))
        stepper5.set_max(t.denom_counts.get(5, 0))
        stepper2.set_max(t.denom_counts.get(2, 0))

    def on_stepper_change():
        # recompute selected total and enable/disable confirm
        try:
            target = int(float(amount_field.value.strip()))
        except Exception:
            target = None

        selected = 10 * stepper10.count + 5 * stepper5.count + 2 * stepper2.count
        combo_summary.value = f"Selected: $10×{stepper10.count}, $5×{stepper5.count}, $2×{stepper2.count}  =>  Total {money(selected)}"
        if target is not None and target > 0 and selected == target:
            confirm_btn.disabled = False
            suggestion_note.value = ""
        else:
            confirm_btn.disabled = True
            if target is not None and target > 0:
                diff = (target - selected)
                suggestion_note.value = f"Need {money(diff)} more." if diff > 0 else f"Over by {money(-diff)}."
            else:
                suggestion_note.value = ""
        combo_summary.update()
        suggestion_note.update()
        confirm_btn.update()

    def load_balance(e):
        hid = household_field.value.strip()
        if not hid:
            status.value = "⚠️ Please enter Household ID."
            page.update()
            return
        try:
            bal = fetch_household_balance(hid)
            render_balance(bal)
            refresh_ui_limits()
            stepper10.set_count(0); stepper5.set_count(0); stepper2.set_count(0)
            status.value = "✅ Balance loaded."
        except Exception as ex:
            status.value = f"❌ {ex}"
        page.update()

    def on_tranche_change(e):
        refresh_ui_limits()
        stepper10.set_count(0); stepper5.set_count(0); stepper2.set_count(0)
        on_stepper_change()

    def suggest_combo(e):
        if not current_balance:
            status.value = "⚠️ Load a household first."
            page.update()
            return
        if not tranche_dd.value:
            status.value = "⚠️ Select a tranche."
            page.update()
            return

        try:
            target = int(float(amount_field.value.strip()))
        except Exception:
            status.value = "⚠️ Amount must be a number."
            page.update()
            return

        if target <= 0:
            status.value = "⚠️ Amount must be > 0."
            page.update()
            return

        t = current_balance.tranche(tranche_dd.value)
        combo, suggested_amount = suggest_balanced_combo(target, t.denom_counts)

        if combo is None or suggested_amount <= 0:
            status.value = "❌ No valid combination found with available vouchers."
            page.update()
            return

        # Set steppers to suggested combo
        stepper10.set_count(combo.used.get(10, 0))
        stepper5.set_count(combo.used.get(5, 0))
        stepper2.set_count(combo.used.get(2, 0))

        if suggested_amount != target:
            status.value = f"ℹ️ Exact {money(target)} not possible. Suggested closest: {money(suggested_amount)}"
            amount_field.value = str(suggested_amount)
        else:
            status.value = "✅ Suggested an exact-match combination."

        on_stepper_change()
        page.update()

    def confirm(e):
        if not current_balance:
            status.value = "⚠️ Load a household first."
            page.update()
            return
        hid = current_balance.household_id
        mid = merchant_field.value.strip() or "M001"
        tid = tranche_dd.value
        try:
            amt = int(float(amount_field.value.strip()))
        except Exception:
            status.value = "⚠️ Amount must be a number."
            page.update()
            return

        used = {10: stepper10.count, 5: stepper5.count, 2: stepper2.count}
        selected = sum(d * c for d, c in used.items())
        if selected != amt:
            status.value = "⚠️ Selected vouchers must equal the redemption amount."
            page.update()
            return

        try:
            resp = confirm_redemption(hid, mid, tid, amt, used)
            tx = resp.get("transaction_id", "(no tx id)")
            status.value = f"✅ Redeemed {money(amt)} successfully. Transaction: {tx}"
            # In real backend case, refresh the balance from server
            if not USE_MOCK_BACKEND:
                render_balance(fetch_household_balance(hid))
                refresh_ui_limits()
            stepper10.set_count(0); stepper5.set_count(0); stepper2.set_count(0)
            on_stepper_change()
        except Exception as ex:
            status.value = f"❌ {ex}"

        page.update()

    load_btn.on_click = load_balance
    tranche_dd.on_change = on_tranche_change
    suggest_btn.on_click = suggest_combo
    confirm_btn.on_click = confirm

    denom_panel = ft.Card(
        content=ft.Container(
            padding=12,
            content=ft.Column(
                controls=[
                    ft.Text("Choose denominations", size=16, weight=ft.FontWeight.BOLD),
                    ft.Text("Tip: tap “Suggest…” for an auto-picked, balanced combo."),
                    stepper10, stepper5, stepper2,
                    ft.Divider(),
                    combo_summary,
                    suggestion_note,
                ],
                spacing=8,
            ),
        )
    )

    page.add(
        ft.Column(
            controls=[
                ft.Text("CDC Voucher Redemption", size=22, weight=ft.FontWeight.BOLD),
                ft.Text("Load household balance, then pick (or auto-suggest) a denomination mix to redeem."),
                ft.Divider(),
                ft.Row([household_field, load_btn], alignment=ft.MainAxisAlignment.START),
                balance_card,
                ft.Divider(),
                ft.Text("Redemption", size=18, weight=ft.FontWeight.BOLD),
                ft.Row([tranche_dd, merchant_field, amount_field], wrap=True),
                ft.Row([suggest_btn, confirm_btn]),
                denom_panel,
                status,
                ft.Text(
                    "Note: QR generation is out-of-scope; refresh-based confirmation is acceptable per brief.",
                    italic=True,
                    color=ft.Colors.GREY_700,
                ),
            ],
            spacing=12,
        )
    )


if __name__ == "__main__":
    ft.app(target=main)
