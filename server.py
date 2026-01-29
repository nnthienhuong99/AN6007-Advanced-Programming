from flask import Flask, jsonify, render_template_string, request
from typing import List
from data_structure import Transaction, store
from services import (
    claim_tranche,
    export_balance_snapshot,
    redeem,
    register_household,
    register_merchant,
    serialize_household,
)

app = Flask(__name__)


# -------- Simple Browser UI --------

INDEX_HTML = """<!doctype html>
<html>
  <head>
    <meta charset='utf-8'/>
    <title>CDC Voucher API</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 24px; line-height: 1.4; }
      code, pre { background: #f5f5f5; padding: 2px 4px; border-radius: 4px; }
      .card { border: 1px solid #ddd; border-radius: 10px; padding: 14px; margin: 12px 0; }
      input { padding: 6px 8px; margin: 6px 0; width: 420px; }
      button { padding: 7px 10px; }
      .row { display: flex; gap: 16px; flex-wrap: wrap; }
      .col { flex: 1 1 520px; }
      .hint { color: #555; font-size: 13px; }
    </style>
  </head>
  <body>
    <h2>CDC Voucher API (Browser Test)</h2>
    <p class='hint'>Tip: browser URL bar sends GET. This page provides forms for POST.</p>

    <div class='card'>
      <h3>Quick links (GET)</h3>
      <ul>
        <li><a href='/api/households'>GET /api/households</a></li>
        <li><a href='/api/merchants'>GET /api/merchants</a></li>
        <li><a href='/api/redemptions'>GET /api/redemptions</a></li>
      </ul>
      <p class='hint'>Household detail: <code>/api/households/&lt;household_id&gt;</code></p>
    </div>

    <div class='row'>
      <div class='col card'>
        <h3>Create household (POST)</h3>
        <form method='post' action='/households/create'>
          <div><input name='household_id' placeholder='household_id (e.g. H001)' required></div>
          <div><input name='num_people' placeholder='num_people (optional, default 0)'></div>
          <button type='submit'>Create</button>
        </form>
        <p class='hint'>Default vouchers generated: 30x$2, 12x$5, 15x$10.</p>
      </div>

      <div class='col card'>
        <h3>Create merchant (POST)</h3>
        <form method='post' action='/merchants/create'>
          <div><input name='merchant_id' placeholder='merchant_id (e.g. M001)' required></div>
          <div><input name='merchant_name' placeholder='merchant_name (e.g. FairPrice)' required></div>
          <button type='submit'>Create</button>
        </form>
      </div>
    </div>

    <div class='row'>
      <div class='col card'>
        <h3>Redeem (POST) — user-indicated (non-greedy)</h3>
        <p class='hint'>Provide either (a) voucher_ids (comma-separated) OR (b) denomination + count.</p>
        <form method='post' action='/redemptions/create'>
          <div><input name='transaction_id' placeholder='transaction_id (e.g. TX001)' required></div>
          <div><input name='household_id' placeholder='household_id (e.g. H001)' required></div>
          <div><input name='merchant_id' placeholder='merchant_id (e.g. M001)' required></div>
          <div><input name='datetime_iso' placeholder='datetime_iso (e.g. 2025-11-02T08:15:32)' required></div>
          <div><input name='voucher_ids' placeholder='voucher_ids (optional, e.g. V0000001,V0000002)'></div>
          <div><input name='denomination' placeholder='denomination (optional, e.g. 5)'></div>
          <div><input name='count' placeholder='count (optional, e.g. 3)'></div>
          <div><input name='amount' placeholder='amount (optional, for reference only)'></div>
          <button type='submit'>Redeem</button>
        </form>
        <p class='hint'>Output rows: one per voucher. For a denomination used N times, Remarks = 1..N-1, Final denomination used.</p>
      </div>

      <div class='col card'>
        <h3>Export balance snapshot (GET)</h3>
        <p class='hint'>Example: <code>/api/balances/export?date=20251102&amp;hour=08</code></p>
      </div>
    </div>
  </body>
</html>"""


@app.get("/")
def home():
    return render_template_string(INDEX_HTML)


# -------- Households --------

@app.post("/api/households")
def api_create_household():
    data = request.get_json(force=True) or {}
    res = register_household(
        household_id=data["household_id"],
        num_people=int(data.get("num_people", 0) or 0),
        nric=data.get("nric") or {},
        full_names=data.get("full_names") or {},
    )
    return jsonify(res)


@app.get("/api/households")
def api_list_households():
    return jsonify({"households": list(store.households.keys())})


@app.get("/api/households/<household_id>")
def api_get_household(household_id: str):
    h = store.households.get(household_id)
    if not h:
        return jsonify({"error": "Household not found"}), 404
    return jsonify(serialize_household(h))


@app.post("/api/households/<household_id>/claim")
def api_claim_tranche(household_id: str):
    data = request.get_json(force=True) or {}
    tranche_id = data.get("tranche_id", "T1")
    return jsonify(claim_tranche(household_id, tranche_id))


@app.post("/households/create")
def web_create_household():
    household_id = request.form.get("household_id", "").strip()
    num_people = int(request.form.get("num_people") or 0)
    return jsonify(register_household(household_id=household_id, num_people=num_people))


# -------- Merchants --------

@app.post("/api/merchants")
def api_create_merchant():
    data = request.get_json(force=True) or {}
    return jsonify(register_merchant(
        merchant_id=data["merchant_id"],
        merchant_name=data["merchant_name"],
        uen=data.get("uen", ""),
        bank_name=data.get("bank_name", ""),
        bank_code=data.get("bank_code", ""),
        branch_code=data.get("branch_code", ""),
        account_number=data.get("account_number", ""),
        account_holder_name=data.get("account_holder_name", ""),
    ))


@app.get("/api/merchants")
def api_list_merchants():
    return jsonify({"merchants": list(store.merchants.keys())})


@app.post("/merchants/create")
def web_create_merchant():
    merchant_id = request.form.get("merchant_id", "").strip()
    merchant_name = request.form.get("merchant_name", "").strip()
    return jsonify(register_merchant(merchant_id=merchant_id, merchant_name=merchant_name))


# -------- Redemptions --------

def _parse_voucher_ids_from_str(s: str) -> List[str]:
    return [x.strip() for x in (s or "").split(",") if x.strip()]


@app.post("/api/redemptions")
def api_redeem():
    data = request.get_json(force=True) or {}
    tx = Transaction(
        transaction_id=data["transaction_id"],
        household_id=data["household_id"],
        merchant_id=data["merchant_id"],
        amount=float(data.get("amount", 0) or 0),
        datetime_iso=data.get("datetime_iso") or data.get("datetime") or "",
    )

    voucher_ids = data.get("voucher_ids")
    denominations = data.get("denominations")
    # Convenience single-denomination form
    if not voucher_ids and not denominations and data.get("denomination") is not None and data.get("count") is not None:
        denominations = [{"denomination": int(data["denomination"]), "count": int(data["count"])}]

    return jsonify(redeem(tx, voucher_ids=voucher_ids, denominations=denominations))


@app.get("/api/redemptions")
def api_list_redemptions():
    return jsonify({
        "hours": [
            {"hour_key": k, "rows": len(v)}
            for k, v in store.redemptions_by_hour.items()
        ]
    })


@app.get("/api/redemptions/<hour_key>")
def api_get_redemptions_hour(hour_key: str):
    return jsonify({"hour_key": hour_key, "rows": store.redemptions_by_hour.get(hour_key, [])})


@app.post("/redemptions/create")
def web_redeem():
    voucher_ids_str = request.form.get("voucher_ids", "")
    voucher_ids = _parse_voucher_ids_from_str(voucher_ids_str)

    denom = request.form.get("denomination")
    count = request.form.get("count")
    denominations = None
    if (not voucher_ids) and denom and count:
        denominations = [{"denomination": int(denom), "count": int(count)}]

    tx = Transaction(
        transaction_id=request.form.get("transaction_id", "").strip(),
        household_id=request.form.get("household_id", "").strip(),
        merchant_id=request.form.get("merchant_id", "").strip(),
        amount=float(request.form.get("amount") or 0),
        datetime_iso=request.form.get("datetime_iso", "").strip(),
    )
    return jsonify(redeem(tx, voucher_ids=voucher_ids or None, denominations=denominations))


# -------- Balance extract --------

@app.get("/api/balances/export")
def export_balance():
    return jsonify(export_balance_snapshot(request.args["date"], request.args["hour"]))


if __name__ == "__main__":
    app.run(port=8000, debug=True)
