'''
Merchant Account Registration API (Flask)
- Store merchant data as a .txt file (CSV format text)
- Provide HTML page with 2 forms (Register + Search) similar to Workshop5
'''

from flask import Flask, request, jsonify
import csv
import os
from datetime import date, datetime

app = Flask(__name__)

# ====== Config ======
MERCHANT_TXT = "Merchant.txt"  # required: stored as .txt
FIELDNAMES = [
    "Merchant_ID",
    "Merchant_Name",
    "UEN",
    "Bank_Name",
    "Bank_Code",
    "Branch_Code",
    "Account_Number",
    "Account_Holder_Name",
    "Registration_Date",
    "Status"
]
VALID_STATUS = {"Active", "Pending", "Suspended"}

# In-memory indexes (fast lookup)
merchants_by_id = {}   # Merchant_ID -> row(dict)
merchants_by_uen = {}  # UEN -> Merchant_ID


# ====== Helper functions ======
def ensure_file_has_header():
    """Create Merchant.txt with header if not exist or empty."""
    if (not os.path.exists(MERCHANT_TXT)) or os.path.getsize(MERCHANT_TXT) == 0:
        with open(MERCHANT_TXT, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()

def normalize_mid(mid: str) -> str:
    mid = (mid or "").strip()
    if not mid:
        return ""
    if mid.upper().startswith("M") and mid[1:].isdigit():
        num = int(mid[1:])
        return f"M{num:03d}"
    return mid

def next_merchant_id() -> str:
    max_num = 0
    for mid in merchants_by_id.keys():
        if mid.upper().startswith("M") and mid[1:].isdigit():
            max_num = max(max_num, int(mid[1:]))
    return f"M{max_num + 1:03d}"

def parse_date_yyyy_mm_dd(s: str) -> str:
    s = (s or "").strip()
    if not s:
        return date.today().isoformat()
    # only accept YYYY-MM-DD
    datetime.strptime(s, "%Y-%m-%d")
    return s

def load_merchants_from_file():
    """Load Merchant.txt into in-memory dicts at server start."""
    ensure_file_has_header()
    merchants_by_id.clear()
    merchants_by_uen.clear()

    with open(MERCHANT_TXT, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return
        for raw in reader:
            row = {}
            for k in FIELDNAMES:
                row[k] = (raw.get(k, "") or "").strip()

            mid = normalize_mid(row.get("Merchant_ID", ""))
            if not mid:
                continue
            row["Merchant_ID"] = mid

            merchants_by_id[mid] = row
            uen = row.get("UEN", "").strip()
            if uen:
                merchants_by_uen[uen] = mid

def append_merchant_to_file(row: dict):
    ensure_file_has_header()
    with open(MERCHANT_TXT, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow({k: row.get(k, "") for k in FIELDNAMES})


# ====== Routes (Workshop-style) ======
@app.route("/merchant/main")
def merchant_main():
    # Similar to Workshop5: one page contains 2 forms (register + search)
    return """
<html>
<div id="rightdiv">
  <h3>Merchant Registration</h3>
  <form action="/merchant/register" method="post">
    <label><strong>Merchant_ID</strong> (optional, auto-generate if blank)</label><br>
    <input type="text" name="Merchant_ID" placeholder="e.g., M001"><br><br>

    <label><strong>Merchant_Name</strong></label><br>
    <input type="text" name="Merchant_Name" placeholder="e.g., ABC Minimart" required><br><br>

    <label><strong>UEN</strong></label><br>
    <input type="text" name="UEN" placeholder="e.g., 201234567A"><br><br>

    <label><strong>Bank_Name</strong></label><br>
    <input type="text" name="Bank_Name" placeholder="e.g., DBS Bank Ltd"><br><br>

    <label><strong>Bank_Code</strong></label><br>
    <input type="text" name="Bank_Code" placeholder="e.g., 7171" required><br><br>

    <label><strong>Branch_Code</strong></label><br>
    <input type="text" name="Branch_Code" placeholder="e.g., 001" required><br><br>

    <label><strong>Account_Number</strong></label><br>
    <input type="text" name="Account_Number" placeholder="e.g., 123-456-789" required><br><br>

    <label><strong>Account_Holder_Name</strong></label><br>
    <input type="text" name="Account_Holder_Name" placeholder="e.g., ABC Minimart Pte Ltd"><br><br>

    <label><strong>Registration_Date</strong> (YYYY-MM-DD, optional)</label><br>
    <input type="text" name="Registration_Date" placeholder="e.g., 2025-10-01"><br><br>

    <label><strong>Status</strong> (Active/Pending/Suspended, optional)</label><br>
    <input type="text" name="Status" placeholder="default Active"><br><br>

    <input type="submit" value="Register">
  </form>

  <hr>

  <h3>Search Merchant</h3>
  <form method="get" action="/merchant/search">
    <label><strong>Search by Merchant_ID</strong></label><br>
    <input type="text" name="merchant_id" placeholder="e.g., M001"><br><br>

    <label><strong>OR Search by UEN</strong></label><br>
    <input type="text" name="uen" placeholder="e.g., 201234567A"><br><br>

    <input type="submit" value="Search">
  </form>

  <hr>

  <h3>List All Merchants</h3>
  <form method="get" action="/merchant/list">
    <input type="submit" value="List">
  </form>
</div>
</html>
"""

@app.route("/merchant/register", methods=["POST"])
def merchant_register():
    # Read form data (Workshop-style)
    payload = {}
    for k in FIELDNAMES:
        payload[k] = (request.form.get(k) or "").strip()

    # Normalize / default
    mid = normalize_mid(payload.get("Merchant_ID", ""))
    if not mid:
        mid = next_merchant_id()
    payload["Merchant_ID"] = mid

    payload["Registration_Date"] = parse_date_yyyy_mm_dd(payload.get("Registration_Date", ""))
    status = (payload.get("Status") or "").strip()
    if not status:
        status = "Active"
    if status not in VALID_STATUS:
        return {"ok": False, "error": f"Invalid Status: {status}. Use {sorted(VALID_STATUS)}."}
    payload["Status"] = status

    # Required field checks
    if not payload["Merchant_Name"]:
        return {"ok": False, "error": "Merchant_Name is required."}
    if not payload["Bank_Code"] or not payload["Branch_Code"]:
        return {"ok": False, "error": "Bank_Code and Branch_Code are required."}
    if not payload["Account_Number"]:
        return {"ok": False, "error": "Account_Number is required."}

    # Unique constraints
    if mid in merchants_by_id:
        return {"ok": False, "error": f"Merchant_ID already exists: {mid}"}

    uen = payload.get("UEN", "").strip()
    if uen and uen in merchants_by_uen:
        return {"ok": False, "error": f"UEN already exists: {uen}"}

    # Save to file + memory
    append_merchant_to_file(payload)
    merchants_by_id[mid] = payload
    if uen:
        merchants_by_uen[uen] = mid

    return {"ok": True, "message": "Merchant registered", "merchant": payload}

@app.route("/merchant/search", methods=["GET"])
def merchant_search():
    mid = normalize_mid(request.args.get("merchant_id", ""))
    uen = (request.args.get("uen") or "").strip()

    if mid:
        row = merchants_by_id.get(mid)
        if row:
            return {"ok": True, "merchant": row}
        return {"ok": False, "error": f"Merchant not found: {mid}"}

    if uen:
        mid2 = merchants_by_uen.get(uen)
        if not mid2:
            return {"ok": False, "error": f"Merchant not found for UEN: {uen}"}
        return {"ok": True, "merchant": merchants_by_id[mid2]}

    return {"ok": False, "error": "Please provide merchant_id or uen in query string."}

@app.route("/merchant/list", methods=["GET"])
def merchant_list():
    items = sorted(merchants_by_id.values(), key=lambda r: r["Merchant_ID"])
    return {"ok": True, "count": len(items), "merchants": items}

@app.route("/")
def index():
    return "Merchant API is running. Go to /merchant/main"

if __name__ == "__main__":
    load_merchants_from_file()
    app.run(host="localhost", port=8000, debug=False)
