# server.py
from flask import Flask, jsonify, render_template_string, request, abort
import base64
import json
import time
from datetime import datetime
from typing import List
from data_structure2 import Transaction, store
from services2 import (
    claim_tranche,
    redeem,
    register_household,
    register_merchant,
    serialize_household,
    load_state,
)

app = Flask(__name__)

# Load persisted data from JSON file on startup
load_state()

# -------- Error Handling --------

@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error="Not Found", message=str(e.description)), 404

@app.errorhandler(400)
def bad_request(e):
    return jsonify(error="Bad Request", message=str(e.description)), 400

@app.errorhandler(Exception)
def handle_unexpected_error(e):
    return jsonify(error="Internal Server Error", message=str(e)), 500

# -------- Mobile App API Support --------

@app.route("/api/households/balance", methods=["GET"])
def get_balance():
    """Endpoint for mobile app: Retrieves household balance across all tranches"""
    household_id = request.args.get("household_id")
    if not household_id or household_id not in store.households:
        abort(404, description="Household not found")
    
    hh = store.households[household_id]
    # Calculate balance for each claimed tranche
    balances = {tranche: hh.get_balance_by_tranche(tranche) for tranche in hh.vouchers.keys()}
    
    return jsonify(balances=balances)

@app.post("/redemptions/create")
def create_redemption():
    """
    Executes redemption: Supports both Web form (Form Data) and Mobile app (JSON) requests.
    Mobile app sends: {"household_id": "...", "merchant_id": "...", "tranche": "...", "denominations": {"10": 1, "5": 1}}
    """
    # Handle both JSON and Form Data formats
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    household_id = data.get("household_id", "").strip()
    merchant_id = data.get("merchant_id", "").strip()
    tranche = data.get("tranche", "MAY2025")
    
    if household_id not in store.households:
        abort(404, description="Household not found.")
    if merchant_id not in store.merchants:
        abort(404, description="Merchant not found.")

    # Get denomination mapping (e.g., {"10": 1, "2": 3})
    denominations = data.get("denominations")
    
    # Adapt simple parameters from Web UI to the standard dictionary format
    if not denominations and data.get("denomination"):
        denominations = {str(data.get("denomination")): int(data.get("count", 1))}

    try:
        # Create Transaction object (logic handled within services2.redeem)
        tx = Transaction(
            transaction_id=f"TXN{int(time.time()*1000)}",
            household_id=household_id,
            merchant_id=merchant_id,
            amount=0.0, # Will be calculated during voucher selection
            datetime_iso=datetime.now().isoformat()
        )
        
        # Call service layer to process the specific vouchers
        result = redeem(tx, tranche=tranche, denominations=denominations)
        return jsonify(result)
    except Exception as e:
        abort(400, description=str(e))

# -------- QR Code Simulation --------

@app.get("/api/qr/<merchant_id>")
def get_merchant_qr(merchant_id: str):
    """Simulates merchant QR generation by encoding merchant data into a Base64 string."""
    if merchant_id not in store.merchants:
        abort(404, description=f"Merchant {merchant_id} not found.")
    
    merchant = store.merchants[merchant_id]
    qr_payload = {
        "merchant_id": merchant.merchant_id,
        "merchant_name": merchant.merchant_name,
        "timestamp": int(time.time()),
        "token": f"secure_{hash(merchant_id + str(time.time()))}"
    }
    # Encode JSON to Base64 to simulate a QR code scan string
    qr_string = base64.b64encode(json.dumps(qr_payload).encode()).decode()
    
    return jsonify({
        "merchant_id": merchant_id,
        "qr_code_data": qr_string,
        "instructions": "In a real-world scenario, this string would be rendered as a QR image."
    })

# -------- Business Logic APIs --------

@app.post("/register/household")
def api_register_household():
    """
    Registers a household using NRIC, Name, and Postal Code.
    The system validates input and assigns a unique Household ID.
    """
    data = request.form
    nric = data.get("nric", "").strip()
    name = data.get("full_name", "").strip()
    postal_code = data.get("postal_code", "").strip()
    
    if not nric or not name or not postal_code:
        abort(400, description="NRIC, Full Name, and Postal Code are all required.")
    
    try:
        # Service logic handles NRIC format validation and database entry
        result = register_household(nric=nric, name=name, postal_code=postal_code)
        return jsonify(result)
    except ValueError as e:
        abort(400, description=str(e))

@app.post("/register/merchant")
def api_register_merchant():
    """Registers a merchant into the system store."""
    data = request.form
    mid = data.get("merchant_id")
    if not mid:
        abort(400, description="merchant_id is required.")
    
    res = register_merchant(
        merchant_id=mid,
        merchant_name=data.get("merchant_name", "New Merchant"),
        uen=data.get("uen", "N/A")
    )
    return jsonify(res)

@app.post("/claim")
def api_claim():
    """Allows a household to claim a specific voucher tranche."""
    hid = request.form.get("household_id")
    tranche = request.form.get("tranche", "MAY2025")
    
    if hid not in store.households:
        abort(404, description=f"Household ID {hid} not found. Please register first.")
    
    try:
        res = claim_tranche(hid, tranche)
        return jsonify(res)
    except ValueError as e:
        abort(400, description=str(e))

@app.get("/api/household/<hid>")
def get_household_status(hid):
    """Retrieves data for a specific household ID."""
    if hid not in store.households:
        abort(404, description="Household not found.")
    return jsonify(serialize_household(store.households[hid]))

# -------- Test UI Template --------

INDEX_HTML = """<!doctype html>
<html>
  <head>
    <meta charset='utf-8'/>
    <title>CDC Voucher System v2.0</title>
    <style>
      body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background: #f8f9fa; color: #333; }
      .container { max-width: 900px; margin: auto; }
      .box { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 25px; }
      h2 { color: #2c3e50; margin-top: 0; border-bottom: 2px solid #eee; padding-bottom: 10px; }
      h3 { color: #34495e; margin-top: 0; }
      input, select { padding: 10px; margin: 8px 0; border: 1px solid #ddd; border-radius: 6px; width: 100%; box-sizing: border-box; }
      button { padding: 12px 20px; background: #3498db; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; width: 100%; }
      button:hover { background: #2980b9; }
      .merchant-btn { background: #27ae60; }
      .claim-btn { background: #f39c12; }
      .link-group a { margin-right: 15px; text-decoration: none; color: #3498db; font-size: 0.9em; }
      .hint { font-size: 0.85em; color: #7f8c8d; margin-top: -5px; margin-bottom: 10px; }
    </style>
  </head>
  <body>
    <div class="container">
      <h1>CDC Voucher System Control Panel</h1>
      
      <div class="box">
        <h3>1. Household Registration</h3>
        <p class="hint">Verify details to receive your unique Household ID.</p>
        <form action="/register/household" method="post" target="_blank">
          <input type="text" name="nric" placeholder="NRIC (e.g., S1234567A)" required>
          <input type="text" name="full_name" placeholder="Full Name (as per NRIC)" required>
          <input type="text" name="postal_code" placeholder="6-Digit Postal Code" required>
          <button type="submit">Register & Get Household ID</button>
        </form>
      </div>

      <div class="box">
        <h3>2. Merchant Setup</h3>
        <form action="/register/merchant" method="post" target="_blank">
          <input type="text" name="merchant_id" placeholder="Merchant ID (e.g., M101)" required>
          <input type="text" name="merchant_name" placeholder="Business Name">
          <input type="text" name="uen" placeholder="UEN Number">
          <button type="submit" class="merchant-btn">Register Merchant</button>
        </form>
      </div>

      <div class="box">
        <h3>3. Voucher Claiming</h3>
        <form action="/claim" method="post" target="_blank">
          <input type="text" name="household_id" placeholder="Enter assigned Household ID" required>
          <select name="tranche">
            <option value="MAY2025">May 2025 Tranche ($500)</option>
            <option value="JAN2026">Jan 2026 Tranche ($300)</option>
          </select>
          <button type="submit" class="claim-btn">Claim Vouchers</button>
        </form>
      </div>

      <div class="box">
        <h3>4. Redemption Simulation</h3>
        <form action="/redemptions/create" method="post" target="_blank">
          <input type="text" name="household_id" placeholder="Household ID"><br>
          <input type="text" name="merchant_id" placeholder="Merchant ID"><br>
          <select name="tranche">
            <option value="MAY2025">May 2025 Tranche</option>
            <option value="JAN2026">Jan 2026 Tranche</option>
          </select>
          <div style="display: flex; gap: 10px;">
            <input type="number" name="denomination" placeholder="Denom (2/5/10)">
            <input type="number" name="count" placeholder="Quantity">
          </div>
          <button type="submit" style="background: #e74c3c;">Execute Redemption</button>
        </form>
      </div>

      <div class="box" style="border: none; background: none; box-shadow: none;">
        <div class="link-group">
          <a href="/api/qr/M1" target="_blank">Simulation: Generate Merchant QR</a>
        </div>
      </div>
    </div>
  </body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(INDEX_HTML)

if __name__ == "__main__":
    # Ensure state is loaded before the server starts accepting requests
    load_state()
    print("[*] CDC System starting...")
    # Using port 5000 as default for Flask
    app.run(port=5000, debug=True)